"""Product gold objects shared by hourly inventory and daily cost jobs."""

MODEL_PRICES_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.model_prices (
  workspace_id STRING, model STRING, effective_from DATE,
  input_usd_per_mtok DOUBLE, output_usd_per_mtok DOUBLE, source STRING
) COMMENT 'Effective-dated USD per million model tokens; estimates, not invoiced charges'"""

FUNNEL_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.funnel_specs (
  workspace_id STRING, name STRING, funnel STRING, steps ARRAY<STRING>
) COMMENT 'Ordered event or journey-step names; session conversion window is 30 minutes'"""

CONFIG_COLUMNS = {
    "outcome_event": "STRING",
    "token_budget_day": "BIGINT",
    "throttle": "STRING",
    "tokens_today": "BIGINT",
    "tokens_last_hour": "BIGINT",
    "policy_updated_at": "TIMESTAMP",
}


def token_usage_sql(fq: str, days: int, metrics_available: bool = True) -> str:
    """Metrics win per app/model/day/direction, never add spans to the same metric.

    Read flattened OTLP histogram sums (including VARIANT value/data wrappers).
    Cumulative streams are differenced with a preceding-day seed and restart key;
    delta streams are summed. Unknown temporality is treated as cumulative (OTel default).
    """
    from telemetry_sql import BILLABLE, IN_TOK, OUT_TOK, enriched_spans

    metric_source = (
        f"SELECT to_json(struct(*)) AS j FROM {fq}.otel_metrics WHERE date >= current_date() - {days + 1}"
        if metrics_available
        else "SELECT cast(NULL AS STRING) AS j WHERE false"
    )
    return f"""
      WITH raw_metrics AS (
        {metric_source}
      ), metric_rows AS (
        SELECT get_json_object(j, '$.service_name') AS name,
          coalesce(get_json_object(j, '$.name'), get_json_object(j, '$.metric_name')) AS metric,
          coalesce(nullif(replace(variant_get(try_parse_json(j), '$.attributes["gen_ai.request.model"]', 'string'), '"', ''), ''), '(unknown)') AS model,
          variant_get(try_parse_json(j), '$.attributes["gen_ai.token.type"]', 'string') AS direction,
          try_cast(get_json_object(j, '$.time') AS TIMESTAMP) AS time,
          coalesce(get_json_object(j, '$.start_time_unix_nano'),
                   get_json_object(j, '$.value.start_time_unix_nano'), '0') AS start_id,
          coalesce(variant_get(try_parse_json(j), '$.resource.attributes["service.instance.id"]', 'string'),
                   variant_get(try_parse_json(j), '$.resource_attributes["service.instance.id"]', 'string'), '') AS instance,
          coalesce(get_json_object(j, '$.attributes'), '') AS dimensions,
          upper(coalesce(get_json_object(j, '$.aggregation_temporality'),
                         get_json_object(j, '$.histogram.aggregation_temporality'),
                         get_json_object(j, '$.value.aggregation_temporality'), 'CUMULATIVE')) AS temporality,
          coalesce(try_cast(get_json_object(j, '$.histogram.sum') AS DOUBLE),
                   try_cast(get_json_object(j, '$.value.sum') AS DOUBLE),
                   try_cast(get_json_object(j, '$.data.sum') AS DOUBLE),
                   try_cast(get_json_object(j, '$.sum') AS DOUBLE)) AS total
        FROM raw_metrics
      ), dedup AS (
        SELECT DISTINCT * FROM metric_rows
        WHERE metric = 'gen_ai.client.token.usage' AND direction IN ('input', 'output')
          AND total >= 0 AND time IS NOT NULL
      ), deltas AS (
        SELECT *, lag(total) OVER (
          PARTITION BY name, model, direction, instance, dimensions, start_id ORDER BY time) AS previous
        FROM dedup
      ), metrics AS (
        SELECT date(time) AS date, name, model, direction, date_trunc('hour', time) AS hour,
          sum(CASE WHEN temporality IN ('1', 'DELTA', 'AGGREGATION_TEMPORALITY_DELTA')
                     OR previous IS NULL OR total < previous THEN total
                   ELSE total - previous END)::BIGINT AS tokens
        FROM deltas WHERE date(time) >= current_date() - {days}
        GROUP BY 1, 2, 3, 4, 5
      ), spans AS (
        {enriched_spans(fq, f"date >= current_date() - {days}")}
        SELECT date, service_name AS name, coalesce(model, '(unknown)') AS model,
          date_trunc('hour', time) AS hour, sum({IN_TOK}) AS input, sum({OUT_TOK}) AS output
        FROM marked WHERE (model IS NOT NULL OR billable = true) AND {BILLABLE}
        GROUP BY 1, 2, 3, 4
      ), span_tokens AS (
        SELECT date, name, model, hour, 'input' AS direction, input AS tokens FROM spans
        UNION ALL
        SELECT date, name, model, hour, 'output' AS direction, output AS tokens FROM spans
      )
      SELECT date, name, model, hour, direction, tokens, 'metric' AS basis FROM metrics
      UNION ALL
      SELECT s.*, 'span' AS basis FROM span_tokens s
      LEFT ANTI JOIN (SELECT DISTINCT date, name, model, direction FROM metrics) m
        ON s.date = m.date AND s.name = m.name AND s.model = m.model AND s.direction = m.direction
    """


def product_views_sql(fq: str, workspace_id: str) -> list[tuple[str, str]]:
    from telemetry_sql import NOT_PROBE, SERVER, SESS, TRAFFIC_KIND, UHASH, vg

    # Workspace IDs come from the SDK; never interpolate an HTTP parameter here.
    ws = str(int(workspace_id))
    body = "cast(body AS string)"

    def field(key):
        return f"get_json_object({body}, '$.{key}')"

    logger = f"coalesce({vg('logger.name')}, get_json_object(to_json(struct(*)), '$.scope.name'), get_json_object(to_json(struct(*)), '$.instrumentation_scope.name'), get_json_object(to_json(struct(*)), '$.logger'), {field('logger')})"
    return [
        (
            "v_events",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_events
          COMMENT 'Deduplicated real business events and server journey steps within raw retention' AS
          WITH envelopes AS (
            SELECT service_name AS name, trace_id, {vg("app.client_request_id")} AS request_id,
              any_value({vg("app.version")}) AS version, any_value({TRAFFIC_KIND}) AS traffic_kind
            FROM {fq}.otel_spans WHERE {SERVER} GROUP BY 1, 2, 3
          ), logs AS (
            SELECT time, date, service_name AS name, '{ws}' AS workspace_id,
              coalesce({field("event_id")}, sha2(concat_ws('|', trace_id, cast(time AS STRING), {body}), 256)) AS event_id,
              {field("name")} AS event_name, {field("sid")} AS session_id,
              {field("user")} AS user_hash, {field("rid")} AS request_id, trace_id,
              coalesce({vg("app.version")}, {field("version")}) AS app_version,
              'event' AS event_source,
              coalesce({vg("traffic.kind")}, {field("traffic_kind")}) AS traffic_kind
            FROM {fq}.otel_logs
            WHERE ({logger} = 'monitor.events' OR {field("event")} = 'custom')
          ), correlated AS (
            SELECT l.* EXCEPT (app_version, traffic_kind), coalesce(l.app_version, e.version, '(unknown)') AS app_version
            FROM logs l LEFT JOIN envelopes e ON l.name = e.name AND l.trace_id = e.trace_id
              AND l.request_id <=> e.request_id
            WHERE coalesce(l.traffic_kind, e.traffic_kind, 'real') = 'real'
          ), events AS (
            SELECT time, date, name, workspace_id, event_id, event_name, session_id, user_hash,
              request_id, trace_id, app_version, event_source FROM correlated QUALIFY row_number() OVER (
              PARTITION BY workspace_id, name, event_id ORDER BY time) = 1
            UNION ALL
            SELECT time, date, service_name, '{ws}', concat('span:', span_id),
              {vg("journey.step")}, {SESS}, {UHASH}, {vg("app.client_request_id")}, trace_id,
              coalesce({vg("app.version")}, '(unknown)'), 'journey'
            FROM {fq}.otel_spans WHERE {SERVER} AND {NOT_PROBE}
              AND {vg("journey.step")} IS NOT NULL
          ) SELECT * FROM events WHERE event_name IS NOT NULL
        """,
        ),
        (
            "v_unit_economics",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_unit_economics
          COMMENT 'Daily unit costs; AI is a list-price estimate, missing prices keep totals unknown' AS
          WITH outcomes AS (
            SELECT e.workspace_id, e.date, e.name, count(*) AS completions
            FROM {fq}.v_events e JOIN {fq}.app_config c
              ON e.workspace_id = c.workspace_id AND e.name = c.name AND e.event_name = c.outcome_event
            WHERE e.event_source = 'event' GROUP BY 1, 2, 3
          ), units AS (
            SELECT c.*, CASE WHEN c.ai_usd IS NULL AND c.ai_input_tokens + c.ai_output_tokens > 0
                         THEN NULL ELSE coalesce(c.dbu_usd, 0) + coalesce(c.ai_usd, 0) END AS total_usd,
              a.requests, a.sessions, a.users, a.sessions_hll, a.users_hll,
              CASE WHEN cfg.outcome_event IS NOT NULL THEN coalesce(e.completions, 0) END AS completions
            FROM {fq}.costs_daily c LEFT JOIN {fq}.agg_app_daily a
              ON c.workspace_id = a.workspace_id AND c.date = a.date AND c.name = a.name AND a.traffic_kind = 'real'
            LEFT JOIN {fq}.app_config cfg ON c.workspace_id = cfg.workspace_id AND c.name = cfg.name
            LEFT JOIN outcomes e ON c.workspace_id = e.workspace_id AND c.date = e.date AND c.name = e.name
          ) SELECT *, total_usd / nullif(requests, 0) * 1000 AS usd_per_1k_requests,
             total_usd / nullif(sessions, 0) AS usd_per_session,
             total_usd / nullif(users, 0) AS usd_per_user,
             total_usd / nullif(completions, 0) AS usd_per_outcome FROM units
        """,
        ),
        ("v_funnels", funnel_view_sql(fq)),
        (
            "v_cohorts",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_cohorts
          COMMENT 'Observed first-week retention within raw retention; HLL cannot recover user membership' AS
          WITH active AS (
            SELECT DISTINCT '{ws}' AS workspace_id, service_name AS name, {UHASH} AS user_hash,
              date_trunc('week', time)::DATE AS week
            FROM {fq}.otel_spans WHERE {SERVER} AND {NOT_PROBE} AND {UHASH} IS NOT NULL
          ), members AS (
            SELECT *, min(week) OVER (PARTITION BY workspace_id, name, user_hash) AS cohort_week FROM active
          ), sizes AS (
            SELECT workspace_id, name, cohort_week, count(*) AS cohort_size FROM members
            WHERE week = cohort_week GROUP BY 1, 2, 3
          ), retained AS (
            SELECT workspace_id, name, cohort_week, week, count(*) AS retained_users
            FROM members GROUP BY 1, 2, 3, 4
          ), weeks AS (
            SELECT s.*, explode(sequence(cohort_week, date_trunc('week', current_date())::DATE,
                                         INTERVAL 7 DAYS)) AS week FROM sizes s
          ) SELECT w.workspace_id, w.name, w.cohort_week, datediff(w.week, w.cohort_week) DIV 7 AS week_number,
              w.cohort_size, coalesce(r.retained_users, 0) AS retained_users,
              100.0 * coalesce(r.retained_users, 0) / w.cohort_size AS retention_pct,
              w.week = date_trunc('week', current_date())::DATE AS partial_week
          FROM weeks w LEFT JOIN retained r USING (workspace_id, name, cohort_week, week)
        """,
        ),
        ("v_leaderboard", leaderboard_view_sql(fq)),
        ("v_rum_daily", rum_view_sql(fq, ws, logger)),
    ]


def funnel_view_sql(fq: str) -> str:
    # Try every occurrence of step one. Greedy advancement after each start is sufficient
    # to find any valid subsequence, including a later successful retry in the same session.
    return f"""CREATE OR REPLACE VIEW {fq}.v_funnels
      COMMENT 'Ordered 30-minute session funnels by release; each session counted once at its deepest step' AS
      WITH streams AS (
        SELECT workspace_id, name, session_id, app_version,
          sort_array(collect_list(named_struct('time', time, 'id', event_id, 'event', event_name))) AS events
        FROM {fq}.v_events WHERE session_id IS NOT NULL GROUP BY 1, 2, 3, 4
      ), attempts AS (
        SELECT s.workspace_id, s.name, s.session_id, s.app_version, f.funnel, f.steps, s.events,
          start.time AS started, start.id AS start_id
        FROM streams s JOIN {fq}.funnel_specs f USING (workspace_id, name)
        LATERAL VIEW explode(filter(s.events, e -> e.event = element_at(f.steps, 1))) starts AS start
      ), progress AS (
        SELECT *, aggregate(filter(events, e -> (e.time > started OR (e.time = started AND e.id >= start_id))
                   AND e.time <= started + INTERVAL 30 MINUTES), 0,
                   (n, e) -> CASE WHEN e.event = try_element_at(steps, n + 1) THEN n + 1 ELSE n END) AS reached
        FROM attempts
      ), sessions AS (
        SELECT workspace_id, name, session_id, app_version, funnel, steps, max(reached) AS reached
        FROM progress GROUP BY 1, 2, 3, 4, 5, 6
      ), counts AS (
        SELECT workspace_id, name, app_version, funnel, pos + 1 AS step_number, step AS step_name,
          count_if(reached >= pos + 1) AS sessions
        FROM sessions LATERAL VIEW posexplode(steps) AS pos, step GROUP BY 1, 2, 3, 4, 5, 6
      ) SELECT *, 100.0 * (1 - sessions / nullif(lag(sessions) OVER (
          PARTITION BY workspace_id, name, app_version, funnel ORDER BY step_number), 0)) AS dropoff_pct
      FROM counts"""


def leaderboard_view_sql(fq: str) -> str:
    return f"""CREATE OR REPLACE VIEW {fq}.v_leaderboard
      COMMENT 'Active-app score components; Python applies published weights and reports missing evidence' AS
      WITH usage AS (
        SELECT workspace_id, name, sum(requests) AS requests, sum(errors) AS errors,
          max(p95_ms) AS p95_ms, hll_sketch_estimate(hll_union_agg(users_hll)) AS users
        FROM {fq}.agg_app_daily WHERE traffic_kind = 'real' AND date >= current_date() - 7 GROUP BY 1, 2
      ), cost AS (
        SELECT workspace_id, name,
          avg(CASE WHEN date >= current_date() - 7 THEN dbu_usd END) AS recent_cost,
          avg(CASE WHEN date < current_date() - 7 THEN dbu_usd END) AS prior_cost
        FROM {fq}.costs_daily WHERE date >= current_date() - 14 AND date < current_date() GROUP BY 1, 2
      ), scans AS (
        SELECT name, quality_score FROM {fq}.code_scans
        QUALIFY row_number() OVER (PARTITION BY name ORDER BY scanned_at DESC) = 1
      ), reviews AS (
        SELECT name, score_overall FROM {fq}.llm_reviews
        QUALIFY row_number() OVER (PARTITION BY name ORDER BY reviewed_at DESC) = 1
      ) SELECT a.workspace_id, a.name, u.requests, u.users, u.p95_ms,
        2500.0 AS latency_budget_ms, 100.0 * u.errors / nullif(u.requests, 0) AS error_pct,
        s.quality_score AS scan_score, r.score_overall * 10 AS review_score,
        (c.recent_cost - c.prior_cost) / nullif(c.prior_cost, 0) AS cost_growth
      FROM {fq}.v_apps_latest a LEFT JOIN usage u USING (workspace_id, name)
      LEFT JOIN cost c USING (workspace_id, name) LEFT JOIN scans s ON a.name = s.name
      LEFT JOIN reviews r ON a.name = r.name
      WHERE a.app_state = 'RUNNING' AND a.compute_state = 'ACTIVE'"""


def rum_view_sql(fq: str, ws: str, logger: str) -> str:
    event_type = """STRUCT<type:STRING,name:STRING,metric:STRING,route:STRING,path:STRING,
      value:DOUBLE,message:STRING,stack:STRING,top_frame:STRING,rid:STRING>"""
    return f"""CREATE OR REPLACE VIEW {fq}.v_rum_daily
      COMMENT 'Real browser page views, p75 LCP/CLS/INP and hashed JS error groups per route/day' AS
      WITH logs AS (
        SELECT date, service_name AS name, trace_id, cast(body AS STRING) AS body
        FROM {fq}.otel_logs WHERE ({logger} = 'monitor.rum'
          OR get_json_object(cast(body AS STRING), '$.event') = 'rum')
          AND coalesce(variant_get(attributes, '$["traffic.kind"]', 'string'),
                       get_json_object(cast(body AS STRING), '$.traffic_kind'), 'real') = 'real'
      ), events AS (
        SELECT date, name, get_json_object(body, '$.rid') AS envelope_rid,
          get_json_object(body, '$.route') AS envelope_route,
          explode(coalesce(from_json(get_json_object(body, '$.events'), 'ARRAY<{event_type}>'),
                           array(from_json(body, '{event_type}')))) AS event
        FROM logs
      ), parsed AS (
        SELECT date, name, coalesce(event.rid, envelope_rid) AS request_id,
          coalesce(event.type, event.name) AS kind,
          regexp_replace(coalesce(event.route, event.path, envelope_route, '/'), '[?#].*$', '') AS route,
          event.value AS value, coalesce(event.name, event.metric, event.type) AS metric,
          CASE WHEN event.type IN ('error', 'js_error', 'unhandledrejection') THEN
            sha2(concat_ws('|', regexp_replace(coalesce(event.message, ''), '[0-9]+', '#'),
              coalesce(event.top_frame,
                try_element_at(filter(split(event.stack, chr(10)), line -> trim(line) LIKE 'at %'), 1),
                try_element_at(split(event.stack, chr(10)), 1), '')), 256) END AS fingerprint
        FROM events
      ), backend AS (
        SELECT service_name AS name, variant_get(attributes, '$["app.client_request_id"]', 'string') AS request_id,
          max_by(trace_id, time) AS trace_id
        FROM {fq}.otel_spans WHERE kind ILIKE '%server%'
          AND variant_get(attributes, '$["app.client_request_id"]', 'string') IS NOT NULL
        GROUP BY 1, 2
      ), correlated AS (
        SELECT p.*, b.trace_id FROM parsed p LEFT JOIN backend b USING (name, request_id)
      ) SELECT '{ws}' AS workspace_id, date, name, route, fingerprint,
        count_if(kind IN ('page_view', 'pageview', 'route_view')) AS page_views,
        approx_percentile(CASE WHEN upper(metric) = 'LCP' THEN value END, 0.75) AS p75_lcp,
        approx_percentile(CASE WHEN upper(metric) = 'CLS' THEN value END, 0.75) AS p75_cls,
        approx_percentile(CASE WHEN upper(metric) = 'INP' THEN value END, 0.75) AS p75_inp,
        count_if(fingerprint IS NOT NULL) AS js_errors,
        any_value(trace_id) AS trace_id, any_value(request_id) AS request_id
      FROM correlated GROUP BY 1, 2, 3, 4, 5"""
