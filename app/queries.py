"""SQL access for the telemetry pages (otel_* tables via statement execution API).

Every query is parameterized; results get a short in-memory TTL cache so a dashboard
refresh doesn't hammer the warehouse. Values come back as strings (data_array) —
the UI casts numerics.
"""

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timedelta, timezone

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem

w = WorkspaceClient()

CATALOG = os.environ.get("MONITOR_CATALOG", "main")
SCHEMA = os.environ.get("MONITOR_SCHEMA", "monitor")
WAREHOUSE = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")


def t(name: str) -> str:
    return f"`{CATALOG}`.`{SCHEMA}`.`{name}`"


def vg(key: str, typ: str = "string") -> str:
    """variant_get on the attributes column for keys containing dots."""
    return f"variant_get(attributes, '$[\"{key}\"]', '{typ}')"


DUR_MS = "(end_time_unix_nano - start_time_unix_nano) / 1e6"
IS_SERVER = "kind ILIKE '%server%'"
HTTP_STATUS = f"coalesce({vg('http.response.status_code', 'int')}, {vg('http.status_code', 'int')})"
HTTP_ROUTE = f"coalesce({vg('http.route')}, name)"
IS_ERROR = f"(coalesce({HTTP_STATUS} >= 400, false) OR coalesce(status.code, '') ILIKE '%error%')"
TRAFFIC_KIND = (
    f"coalesce({vg('traffic.kind')}, CASE WHEN name ILIKE '%healthz%' THEN 'probe' ELSE 'real' END)"
)
NOT_PROBE = f"{TRAFFIC_KIND} = 'real'"
IS_ERROR_LOG = "upper(coalesce(severity_text, '')) IN ('ERROR', 'FATAL', 'CRITICAL')"

_cache: dict = {}


def _run(sql: str, params: dict, ttl: int) -> list[dict]:
    key = (sql, tuple(sorted(params.items())))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    resp = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE,
        statement=sql,
        wait_timeout="50s",
        parameters=[StatementParameterListItem(name=k, value=str(v)) for k, v in params.items()],
    )
    state = resp.status.state.value if resp.status and resp.status.state else "UNKNOWN"
    if state != "SUCCEEDED":
        msg = resp.status.error.message if resp.status and resp.status.error else state
        raise RuntimeError(f"query failed: {msg}")
    if resp.manifest.truncated is True:
        raise RuntimeError("query result truncated")
    cols = [c.name for c in resp.manifest.schema.columns]
    rows = [dict(zip(cols, r, strict=False)) for r in (resp.result.data_array or [])]
    chunk = resp.result
    while isinstance(chunk.next_chunk_index, int):
        # Never acknowledge only part of a job-alert batch (timestamps can be shared).
        chunk = w.statement_execution.get_statement_result_chunk_n(
            resp.statement_id, chunk.next_chunk_index
        )
        rows.extend(dict(zip(cols, r, strict=False)) for r in (chunk.data_array or []))
    _cache[key] = (time.time(), rows)
    if len(_cache) > 200:
        _cache.clear()
    return rows


async def run(sql: str, ttl: int = 30, **params) -> list[dict]:
    return await asyncio.to_thread(_run, sql, params, ttl)


async def run_dml(sql: str, **params) -> None:
    """Uncached write statement (alert events etc.) — rare, transition-driven."""
    await asyncio.to_thread(_run, sql, params, 0)


def since(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")


def gran(hours: float) -> str:
    # whitelisted literals interpolated into SQL (never user input)
    return (
        "1 minute"
        if hours <= 2
        else "5 minutes"
        if hours <= 12
        else "15 minutes"
        if hours <= 48
        else "1 hour"
    )


# --------------------------------------------------------------------- queries

JOB_ALERTS = f"""
  SELECT ts, source, rule, app, severity, message, value, state, muted, workspace_id
  FROM {t("alert_events")}
  WHERE workspace_id = :ws AND source = 'job' AND ts > :cursor::timestamp
  ORDER BY ts, rule, app, state"""

DRIFT_REPORTS = f"""
  SELECT workspace_id, name, week, k, silhouette, novel_share, samples, computed_at
  FROM {t("drift_reports")} WHERE workspace_id = :ws AND name = :app
  ORDER BY week DESC LIMIT 12"""


def requests_timeline(hours: float) -> str:
    return f"""
      SELECT window.start AS ts, count(*) AS requests,
             sum(CASE WHEN {IS_ERROR} THEN 1 ELSE 0 END) AS errors,
             round(approx_percentile({DUR_MS}, 0.5), 1) AS p50_ms,
             round(approx_percentile({DUR_MS}, 0.95), 1) AS p95_ms
      FROM {t("otel_spans")}
      WHERE service_name = :app AND {IS_SERVER} AND {NOT_PROBE} AND time >= :since::timestamp
      GROUP BY window(time, '{gran(hours)}')
      ORDER BY ts"""


ROUTES = f"""
  SELECT {HTTP_ROUTE} AS route,
         count(*) AS requests,
         sum(CASE WHEN {IS_ERROR} THEN 1 ELSE 0 END) AS errors,
         round(avg({DUR_MS}), 1) AS avg_ms,
         round(approx_percentile({DUR_MS}, 0.5), 1) AS p50_ms,
         round(approx_percentile({DUR_MS}, 0.95), 1) AS p95_ms
  FROM {t("otel_spans")}
  WHERE service_name = :app AND {IS_SERVER} AND {NOT_PROBE} AND time >= :since::timestamp
  GROUP BY 1 ORDER BY requests DESC LIMIT 25"""

ERROR_SPANS = f"""
  SELECT time, trace_id, name, round({DUR_MS}, 1) AS duration_ms,
         status.message AS message, {HTTP_STATUS} AS http_status
  FROM {t("otel_spans")}
  WHERE service_name = :app AND {IS_ERROR} AND time >= :since::timestamp
  ORDER BY time DESC LIMIT 50"""

ERROR_LOGS = f"""
  SELECT time, severity_text, cast(body AS string) AS body, trace_id
  FROM {t("otel_logs")}
  WHERE service_name = :app AND {IS_ERROR_LOG} AND time >= :since::timestamp
  ORDER BY time DESC LIMIT 50"""

LOGS_TAIL = f"""
  SELECT time, coalesce(severity_text, 'INFO') AS severity, cast(body AS string) AS body, trace_id
  FROM {t("otel_logs")}
  WHERE service_name = :app AND time >= :since::timestamp
  ORDER BY time DESC LIMIT 200"""

TRACES = f"""
  SELECT time, trace_id, name, round({DUR_MS}, 1) AS duration_ms,
         CASE WHEN {IS_ERROR} THEN 'error' ELSE 'ok' END AS status,
         {HTTP_ROUTE} AS route
  FROM {t("otel_spans")}
  WHERE service_name = :app AND {IS_SERVER} AND {NOT_PROBE} AND time >= :since::timestamp
  ORDER BY time DESC LIMIT 50"""

TRACE_SPANS = f"""
  SELECT service_name, name, kind, span_id, coalesce(parent_span_id, '') AS parent_span_id,
         start_time_unix_nano, end_time_unix_nano,
         CASE WHEN {IS_ERROR} THEN 'error' ELSE 'ok' END AS status,
         status.message AS message, cast(attributes AS string) AS attributes
  FROM {t("otel_spans")}
  WHERE trace_id = :tid AND time >= now() - INTERVAL 7 DAYS
  ORDER BY start_time_unix_nano LIMIT 500"""

# all OTel spans of every trace tied to one MLflow trace / request id — includes spans
# from OTHER apps in the same trace (traceparent propagation = cross-app correlation).
# MLflow JSON-encodes attribute values, hence the replace() quote-stripping.
OTEL_BY_MLFLOW = f"""
  WITH tids AS (
    SELECT DISTINCT trace_id FROM {t("otel_spans")}
    WHERE (replace(coalesce(variant_get(attributes, '$["mlflow.traceRequestId"]', 'string'), ''), '"', '') = :tid
        OR variant_get(attributes, '$["app.client_request_id"]', 'string') = :rid)
      AND time >= now() - INTERVAL 7 DAYS
  )
  SELECT s.service_name, s.name, s.kind, s.trace_id, s.span_id,
         coalesce(s.parent_span_id, '') AS parent_span_id,
         s.start_time_unix_nano, s.end_time_unix_nano,
         CASE WHEN {IS_ERROR.replace("status.code", "s.status.code").replace("variant_get(attributes", "variant_get(s.attributes")} THEN 'error' ELSE 'ok' END AS status,
         replace(coalesce(variant_get(s.attributes, '$["mlflow.spanType"]', 'string'), ''), '"', '') AS span_type,
         variant_get(s.attributes, '$["gen_ai.usage.input_tokens"]', 'long') AS in_tokens,
         variant_get(s.attributes, '$["gen_ai.usage.output_tokens"]', 'long') AS out_tokens
  FROM {t("otel_spans")} s JOIN tids ON s.trace_id = tids.trace_id
  WHERE s.time >= now() - INTERVAL 7 DAYS
  ORDER BY s.start_time_unix_nano LIMIT 300"""

TRACE_LOGS = f"""
  SELECT time, service_name, coalesce(severity_text, 'INFO') AS severity, cast(body AS string) AS body, span_id
  FROM {t("otel_logs")}
  WHERE trace_id = :tid AND time >= now() - INTERVAL 7 DAYS
  ORDER BY time LIMIT 200"""

SCAN_LATEST = f"""
  SELECT scanned_at, deployment_id, quality_score, files, py_loc, deps, deps_pinned,
         findings_critical, findings_high, findings_medium, findings_low,
         has_tests, has_readme, deps_json, freshness_score, policy_violations
  FROM {t("v_scan_latest")} WHERE name = :app"""

FINDINGS_LATEST = f"""
  SELECT kind, severity, title, detail, file, line, package
  FROM {t("v_findings_latest")} WHERE name = :app
  ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END
  LIMIT 200"""

SEC_BY_APP = f"""
  SELECT name, quality_score, findings_critical, findings_high, findings_medium,
         findings_low, deps, deps_pinned, scanned_at, py_loc, files,
         contains(coalesce(deps_json, ''), '"npm"') AS has_npm
  FROM {t("v_scan_latest")}"""

REVIEW_BY_APP = f"""
  SELECT name, verdict, score_overall, model, left(summary, 220) AS summary, reviewed_at
  FROM {t("v_review_latest")}"""

SECURITY_SUMMARY = f"""
  SELECT count(*) AS apps_scanned,
         sum(findings_critical) AS critical,
         sum(findings_high) AS high,
         round(avg(quality_score), 0) AS avg_score,
         min(quality_score) AS worst_score
  FROM {t("v_scan_latest")}"""

REVIEW_LATEST = f"""
  SELECT reviewed_at, deployment_id, model, verdict, summary,
         score_security, score_reliability, score_maintainability, score_cost,
         score_monitoring, score_overall, strengths_json, findings_json,
         files_reviewed, input_tokens, output_tokens
  FROM {t("v_review_latest")} WHERE name = :app"""

COST_APP = f"""
  SELECT date, dbus, dbu_usd, ai_calls, ai_input_tokens, ai_output_tokens, ai_usd, ai_tokens_gateway
  FROM {t("costs_daily")} WHERE name = :app AND date >= current_date() - 30
  ORDER BY date"""

COST_SUMMARY = f"SELECT * FROM {t('v_cost_summary')}"

COST_FLEET = f"""
  SELECT name, round(sum(dbu_usd), 2) AS usd_7d, sum(ai_calls) AS ai_calls_7d,
         sum(ai_input_tokens + ai_output_tokens) AS tokens_7d
  FROM {t("costs_daily")} WHERE date >= current_date() - 7
  GROUP BY name ORDER BY usd_7d DESC NULLS LAST"""

SYNTH_RUNS = f"""
  SELECT run_ts, journey, step, step_name, ok, status_code, latency_ms, within_budget, detail, kind
  FROM {t("synthetic_runs")} WHERE app = :app AND run_ts >= :since::timestamp
  ORDER BY run_ts DESC, step LIMIT 200"""

# real-traffic latency (storyline: probe p95 "nem tudom mennyire valid" — it isn't the
# user experience; these are server spans from actual requests, probes excluded)
REAL_PERF_FLEET = f"""
  SELECT service_name AS name,
         round(approx_percentile({DUR_MS}, 0.95), 1) AS real_p95_ms,
         round(approx_percentile({DUR_MS}, 0.5), 1) AS p50_ms,
         round(approx_percentile({DUR_MS}, 0.99), 1) AS p99_ms,
         count_if({IS_ERROR}) AS errors_24h,
         count(DISTINCT {vg("user.id_hash")}) AS active_users,
         count(*) AS requests_24h
  FROM {t("otel_spans")}
  WHERE {IS_SERVER} AND {NOT_PROBE} AND time >= current_timestamp() - INTERVAL 24 HOURS
  GROUP BY 1"""

REAL_P95_FLEETWIDE = f"""
  SELECT round(approx_percentile({DUR_MS}, 0.95), 1) AS real_p95_ms, count(*) AS requests_24h
  FROM {t("otel_spans")}
  WHERE {IS_SERVER} AND {NOT_PROBE} AND time >= current_timestamp() - INTERVAL 24 HOURS"""

# the review's app-overview (purpose / tech stack / endpoints) — column exists after the
# updated llm-review job ran once; callers guard with try/except
REVIEW_OVERVIEW = f"""
  SELECT overview_json FROM {t("v_review_latest")} WHERE name = :app"""

# browser-mode (Playwright) runs incl. the UC-volume artifact path (column added by the job)
SYNTH_BROWSER = f"""
  SELECT run_ts, journey, step_name, ok, status_code, latency_ms, within_budget,
         detail, artifact, vantage, failure_stage
  FROM {t("synthetic_runs")} WHERE app = :app AND kind = 'playwright'
  AND run_ts >= :since::timestamp
  ORDER BY run_ts DESC LIMIT 50"""

# ---- adoption / genai / deps / timeline / governance (gold views from gold_views.py)

USAGE_DAILY = f"""
  SELECT date, requests, users, sessions, errors, avg_ms
  FROM {t("v_usage_daily")} WHERE name = :app AND date >= current_date() - 30 ORDER BY date"""

USERS_TOP = f"""
  SELECT user_hash, first_seen, last_seen, requests, sessions, active_days, errors, tokens
  FROM {t("v_users")} WHERE name = :app ORDER BY requests DESC LIMIT 50"""

ERROR_GROUPS = f"""
  SELECT fingerprint, occurrences, first_seen, last_seen, sample
  FROM {t("v_error_groups")} WHERE name = :app ORDER BY last_seen DESC LIMIT 30"""

DEPS_7D = f"""
  SELECT dependency, sum(calls) AS calls, round(avg(avg_ms), 1) AS avg_ms,
         round(max(p95_ms), 1) AS p95_ms, sum(errors) AS errors
  FROM {t("v_dependencies")} WHERE name = :app AND date >= current_date() - 7
  GROUP BY dependency ORDER BY calls DESC LIMIT 30"""

# The dependency view is local to the workspace's telemetry schema. Preserve that
# identity explicitly; never join remote apps by an unqualified name.
CONSOLE_DEPENDENCIES = f"""
  SELECT :ws AS workspace_id, name, dependency, sum(calls) AS calls,
         sum(avg_ms * calls) / nullif(sum(calls), 0) AS avg_ms,
         max(p95_ms) AS p95_ms, sum(errors) AS errors
  FROM {t("v_dependencies")} WHERE date >= current_date() - 7
  GROUP BY name, dependency ORDER BY name, dependency"""

CONSOLE_RESOURCES = f"""
  SELECT name, resources_json FROM {t("apps_inventory")}
  WHERE workspace_id = :ws
  QUALIFY row_number() OVER (PARTITION BY workspace_id, name ORDER BY snapshot_ts DESC) = 1"""

GENAI_DAILY = f"""
  SELECT date, model, calls, input_tokens, output_tokens, avg_ms, p95_ms, errors
  FROM {t("v_genai_daily")} WHERE name = :app AND date >= current_date() - 30 ORDER BY date"""

GENAI_TOP = f"""
  SELECT session_id, user_hash, calls, tokens, last_call
  FROM {t("v_genai_sessions")} WHERE name = :app ORDER BY tokens DESC LIMIT 15"""

RELEASES = f"""
  SELECT deployment_id, start_ts, end_ts, requests, p95_ms, error_pct, tokens
  FROM {t("v_release_perf")} WHERE name = :app ORDER BY start_ts DESC LIMIT 15"""

FORECAST = f"SELECT avg_daily_usd, forecast_30d_usd, days_observed FROM {t('v_cost_forecast')} WHERE name = :app"

ALERTS_APP = f"""
  SELECT ts, rule, severity, message, value, state, source, muted FROM {t("alert_events")}
  WHERE app = :app AND ts >= now() - INTERVAL 14 DAYS ORDER BY ts DESC LIMIT 100"""

DEPLOYMENTS = f"""
  SELECT deployment_id, create_time, state, mode FROM {t("app_deployments")}
  WHERE name = :app ORDER BY create_time DESC LIMIT 20"""

PERMS_APP = f"""
  SELECT principal, principal_type, level FROM {t("app_permissions")}
  WHERE name = :app AND snapshot_ts = (SELECT max(snapshot_ts) FROM {t("app_permissions")})
  ORDER BY principal"""

AUDIT_APP = f"""
  SELECT event_time, user, action_name, status_code FROM {t("monitor_audit")}
  WHERE app = :app ORDER BY event_time DESC LIMIT 60"""

AUDIT_FLEET = f"""
  SELECT event_time, user, action_name, app, status_code FROM {t("monitor_audit")}
  ORDER BY event_time DESC LIMIT 100"""

CONFIG_GET = f"""
  SELECT tags_json, budget_usd_month, auto_stop, idle_hours, updated_at, updated_by, capacity_path
  FROM {t("app_config")} WHERE name = :app"""

CONFIGS_ALL = f"SELECT name, tags_json, budget_usd_month, auto_stop FROM {t('app_config')}"

CONFIG_UPSERT = f"""
  MERGE INTO {t("app_config")} tgt USING (SELECT :app AS name) s ON tgt.name = s.name
  WHEN MATCHED THEN UPDATE SET tags_json = :tags, budget_usd_month = :budget::double,
       auto_stop = :auto_stop, idle_hours = :idle::int, updated_at = current_timestamp(), updated_by = :who,
       capacity_path = coalesce(nullif(:capacity_path, ''), tgt.capacity_path), workspace_id = :ws
  WHEN NOT MATCHED THEN INSERT (name, tags_json, budget_usd_month, auto_stop, idle_hours, updated_at, updated_by, capacity_path, workspace_id)
  VALUES (:app, :tags, :budget::double, :auto_stop, :idle::int, current_timestamp(), :who,
          coalesce(nullif(:capacity_path, ''), '/'), :ws)"""

OPEN_JOB_ALERTS = f"""
  SELECT rule, app, severity, message, value, ts AS since, muted FROM {t("v_alerts_open")}
  WHERE source = 'job' AND workspace_id = :ws"""

MTD_BY_APP = f"""
  SELECT name, round(sum(dbu_usd), 2) AS mtd_usd
  FROM {t("costs_daily")} WHERE date >= date_trunc('MONTH', current_date())
  GROUP BY name"""

CHARGEBACK = f"""
  SELECT team, cost_center, count(DISTINCT name) AS apps, round(sum(mtd_usd), 2) AS mtd_usd,
         sum(mtd_tokens) AS mtd_tokens, sum(mtd_ai_calls) AS ai_calls
  FROM {t("v_chargeback")} GROUP BY 1, 2 ORDER BY mtd_usd DESC NULLS LAST"""

USAGE_FLEET = f"""
  SELECT name, sum(requests) AS requests_7d, max(users) AS peak_dau,
         hll_sketch_estimate(hll_union_agg(sessions_hll)) AS sessions_7d
  FROM {t("v_usage_daily")} WHERE date >= current_date() - 7 GROUP BY name"""

TELEMETRY_ACTIVE = f"""
  SELECT DISTINCT service_name AS name FROM {t("otel_spans")} WHERE date >= current_date() - 1"""

# telemetry volume guardrail — watch "observability creep" per app (article: 30%+ DBU risk)
TELEMETRY_VOLUME = f"""
  SELECT 'logs' AS signal, count(*) AS rows_24h FROM {t("otel_logs")}
   WHERE service_name = :app AND time >= now() - INTERVAL 24 HOURS
  UNION ALL SELECT 'spans', count(*) FROM {t("otel_spans")}
   WHERE service_name = :app AND time >= now() - INTERVAL 24 HOURS
  UNION ALL SELECT 'metrics', count(*) FROM {t("otel_metrics")}
   WHERE service_name = :app AND time >= now() - INTERVAL 24 HOURS"""

_GENAI = "coalesce(variant_get(attributes, '$[\"gen_ai.request.model\"]', 'string'), '') != ''"

# LLM error taxonomy: rate-limit vs content-policy vs timeout vs schema vs other
GENAI_ERRORS = f"""
  SELECT CASE
      WHEN error_type = 'rate_limit' THEN 'rate_limit'
      WHEN error_type = 'timeout' THEN 'timeout'
      WHEN error_type = 'policy' THEN 'content_policy'
      WHEN error_type = 'schema' THEN 'schema_validation'
      WHEN error_type = 'server' THEN 'server'
      WHEN msg RLIKE '429|rate.?limit' THEN 'rate_limit'
      WHEN msg RLIKE 'timeout|timed.?out|deadline' THEN 'timeout'
      WHEN msg RLIKE 'content.?(filter|policy)|moderation|blocked' THEN 'content_policy'
      WHEN msg RLIKE 'schema|validation|json|pydantic' THEN 'schema_validation'
      ELSE 'other' END AS category,
    count(*) AS errors, max(time) AS last_seen, any_value(substr(msg, 1, 200)) AS sample
  FROM (SELECT time, lower(variant_get(attributes, '$["error.type"]', 'string')) AS error_type,
                lower(coalesce(nullif(status.message, ''),
                variant_get(attributes, '$["error.type"]', 'string'), '')) AS msg
        FROM {t("otel_spans")}
        WHERE service_name = :app AND {_GENAI} AND {IS_ERROR}
          AND time >= now() - INTERVAL 7 DAYS)
  GROUP BY 1 ORDER BY errors DESC"""

# spans per agent trace — runaway-agent / efficiency-degradation trend
AGENT_STEPS = f"""
  WITH agent_traces AS (
    SELECT DISTINCT trace_id FROM {t("otel_spans")}
    WHERE service_name = :app AND {_GENAI} AND time >= now() - INTERVAL 14 DAYS),
  per_trace AS (
    SELECT s.date, s.trace_id, count(*) AS steps
    FROM {t("otel_spans")} s JOIN agent_traces t ON s.trace_id = t.trace_id
    WHERE s.service_name = :app GROUP BY 1, 2)
  SELECT date, count(*) AS agent_runs, round(avg(steps), 1) AS avg_steps, max(steps) AS max_steps
  FROM per_trace GROUP BY date ORDER BY date"""

FEEDBACK_APP = f"""
  SELECT date, count(*) AS n, round(avg(rating), 2) AS avg_rating,
         sum(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) AS negative
  FROM {t("v_feedback")} WHERE name = :app AND date >= current_date() - 30
  GROUP BY date ORDER BY date DESC"""

FEEDBACK_RECENT = f"""
  SELECT time, rating, comment, user_hash FROM {t("v_feedback")}
  WHERE name = :app ORDER BY time DESC LIMIT 10"""

# bound-job health: system.lakeflow runs for the job ids an app declares (ids inlined, ints only)
JOB_HEALTH = """
  SELECT job_id, count(DISTINCT run_id) AS runs_7d,
         count(DISTINCT CASE WHEN result_state = 'SUCCEEDED' THEN run_id END) AS succeeded,
         round(avg(timestampdiff(SECOND, period_start_time, period_end_time)), 0) AS avg_s,
         max(period_end_time) AS last_run
  FROM system.lakeflow.job_run_timeline
  WHERE workspace_id = :ws::bigint AND job_id IN ({ids})
    AND period_start_time >= now() - INTERVAL 7 DAYS AND result_state IS NOT NULL
  GROUP BY job_id"""

QUALITY_APP = f"""
  SELECT ts, traces_sampled, relevance, faithfulness, toxicity, comment, model
  FROM {t("monitor_quality")} WHERE name = :app ORDER BY ts DESC LIMIT 20"""

INSERT_ALERT = f"""
  INSERT INTO {t("alert_events")}
  (ts, rule, app, severity, message, value, state, source, workspace_id, muted, incident_id) VALUES
  (:ts::timestamp, :rule, :app, :severity, :message, :value::double, :state, 'monitor', :ws, :muted::boolean, NULL)"""

OPEN_ALERTS = f"""
  SELECT rule, app, severity, message, value, ts AS since FROM (
    SELECT *, row_number() OVER (PARTITION BY rule, app ORDER BY ts DESC, state DESC) AS rn
    FROM {t("alert_events")}
    WHERE source = 'monitor' AND (workspace_id = :ws OR workspace_id IS NULL))
  WHERE rn = 1 AND state = 'firing'"""

RECENT_ALERTS = f"""
  SELECT ts, rule, app, severity, message, value, state, source, muted
  FROM {t("alert_events")} WHERE ts >= current_timestamp() - INTERVAL 3 DAYS
  ORDER BY ts DESC LIMIT 100"""

# ---- ops (S1/S2/S5/S6)

ACTIVE_MUTES = f"""SELECT * FROM {t("alert_mutes")}
  WHERE workspace_id = :ws AND ends_at > now()"""
MUTE_INSERT = f"""INSERT INTO {t("alert_mutes")}
  (id, app, rule, starts_at, ends_at, reason, created_by, created_at, workspace_id)
  VALUES (:id, :app, :rule, :starts_at::timestamp, :ends_at::timestamp, :reason, :actor, now(), :ws)"""
MUTE_DELETE = f"DELETE FROM {t('alert_mutes')} WHERE id = :id AND workspace_id = :ws"
MUTE_GET = f"SELECT * FROM {t('alert_mutes')} WHERE id = :id AND workspace_id = :ws"
OPS_AUDIT = f"""INSERT INTO {t("monitor_audit")}
  (event_time, user, service_name, action_name, app, status_code, params_json, workspace_id)
  VALUES (now(), :actor, 'monitor', :action, :app, 200, :params, :ws)"""
SLO_UPSERT = f"""MERGE INTO {t("slo_specs")} t USING
  (SELECT :ws AS workspace_id, :app AS name, :slo AS slo) s
  ON t.workspace_id = s.workspace_id AND t.name = s.name AND t.slo = s.slo
  WHEN MATCHED THEN UPDATE SET sli = :sli, target = :target::double,
    threshold_ms = nullif(:threshold_ms, '')::double, window_days = :window_days::int,
    route_filter = nullif(:route_filter, ''), updated_by = :actor, updated_at = now(),
    revision = CASE WHEN t.sli = :sli AND t.target = :target::double
      AND t.threshold_ms <=> nullif(:threshold_ms, '')::double
      AND t.route_filter <=> nullif(:route_filter, '') THEN t.revision ELSE :revision END
  WHEN NOT MATCHED THEN INSERT
    (workspace_id, name, slo, sli, target, threshold_ms, window_days, route_filter,
     updated_by, updated_at, revision)
    VALUES (:ws, :app, :slo, :sli, :target::double, nullif(:threshold_ms, '')::double,
      :window_days::int, nullif(:route_filter, ''), :actor, now(), :revision)"""
SLO_DELETE = f"""DELETE FROM {t("slo_specs")}
  WHERE workspace_id = :ws AND name = :app AND slo = :slo"""
SLO_SUMMARY = f"""SELECT s.*, sum(b.good) AS good, sum(b.total) AS total,
  100 * (1 - (sum(b.total) - sum(b.good)) / nullif(sum(b.total) * (1-s.target), 0))
    AS budget_remaining_pct, min(b.bucket) AS observed_since, max(b.bucket) AS last_bucket
  FROM {t("slo_specs")} s LEFT JOIN {t("sli_5m")} b
    ON b.workspace_id = s.workspace_id AND b.name = s.name AND b.slo = s.slo
    AND b.revision = s.revision
    AND b.bucket >= timestampadd(DAY, -s.window_days, now())
  WHERE s.workspace_id = :ws AND s.name = :app GROUP BY ALL ORDER BY s.slo"""
SLO_SERIES = f"""WITH daily AS (
  SELECT s.slo, s.target, date(b.bucket) AS date, sum(b.good) AS good, sum(b.total) AS total
  FROM {t("slo_specs")} s JOIN {t("sli_5m")} b
    ON b.workspace_id = s.workspace_id AND b.name = s.name AND b.slo = s.slo
    AND b.revision = s.revision
  WHERE s.workspace_id = :ws AND s.name = :app
    AND b.bucket >= timestampadd(DAY, -s.window_days, now()) GROUP BY ALL)
  SELECT *, 100 * (1 - sum(total-good) OVER w /
      nullif(sum(total) OVER w * (1-target), 0)) AS budget_remaining_pct
  FROM daily WINDOW w AS (PARTITION BY slo ORDER BY date ROWS UNBOUNDED PRECEDING)
  ORDER BY slo, date"""
TELEMETRY_HEALTH = f"""SELECT * FROM {t("v_telemetry_health")}
  WHERE workspace_id = :ws AND name = :app"""
MONITOR_COST = f"""SELECT * FROM {t("monitor_cost_daily")}
  WHERE workspace_id = :ws AND date >= current_date() - 30 ORDER BY date, component"""
MONITOR_STORAGE = f"""SELECT * FROM {t("monitor_storage_daily")}
  WHERE workspace_id = :ws AND date = (SELECT max(date) FROM {t("monitor_storage_daily")}
    WHERE workspace_id = :ws) ORDER BY size_bytes DESC"""
# ---- product (S4/S7/S8/K7)

POLICIES = f"""SELECT name, throttle, policy_updated_at FROM {t("app_config")}
  WHERE workspace_id = :ws"""

PRODUCT_CONFIG = f"""SELECT outcome_event, token_budget_day, throttle,
  tokens_today, tokens_last_hour, policy_updated_at FROM {t("app_config")}
  WHERE workspace_id = :ws AND name = :app"""

PRODUCT_CONFIG_UPSERT = f"""MERGE INTO {t("app_config")} t
  USING (SELECT :ws AS workspace_id, :app AS name) s
  ON t.workspace_id = s.workspace_id AND t.name = s.name
  WHEN MATCHED THEN UPDATE SET outcome_event = nullif(:outcome, ''),
    token_budget_day = :budget::BIGINT, updated_at = now(), updated_by = :actor
  WHEN NOT MATCHED THEN INSERT
    (workspace_id, name, outcome_event, token_budget_day, throttle, updated_at, updated_by)
    VALUES (:ws, :app, nullif(:outcome, ''), :budget::BIGINT, 'none', now(), :actor)"""

MODEL_PRICES = f"""SELECT model, effective_from, input_usd_per_mtok, output_usd_per_mtok, source
  FROM {t("model_prices")} WHERE workspace_id = :ws ORDER BY model, effective_from DESC"""
MODEL_PRICE_UPSERT = f"""MERGE INTO {t("model_prices")} t USING (
  SELECT :ws AS workspace_id, :model AS model, :effective::DATE AS effective_from,
    :input::DOUBLE AS input_usd_per_mtok, :output::DOUBLE AS output_usd_per_mtok, :source AS source) s
  ON t.workspace_id = s.workspace_id AND t.model = s.model AND t.effective_from = s.effective_from
  WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *"""

UNIT_ECONOMICS = f"""WITH totals AS (
  SELECT name, sum(dbu_usd) AS dbu_usd, sum(idle_usd) AS idle_usd,
    CASE WHEN count_if(ai_usd IS NULL AND ai_input_tokens + ai_output_tokens > 0) > 0
      THEN NULL ELSE sum(coalesce(ai_usd, 0)) END AS ai_usd,
    CASE WHEN count_if(total_usd IS NULL) > 0 THEN NULL ELSE sum(total_usd) END AS total_usd,
    count_if(total_usd IS NULL) AS unpriced_days,
    sum(requests) AS requests, sum(completions) AS completions,
    hll_sketch_estimate(hll_union_agg(users_hll)) AS users,
    hll_sketch_estimate(hll_union_agg(sessions_hll)) AS sessions
  FROM {t("v_unit_economics")} WHERE workspace_id = :ws AND date >= :since::DATE
    AND (:app = '' OR name = :app) GROUP BY name
  ) SELECT *, total_usd / nullif(requests, 0) * 1000 AS usd_per_1k_requests,
    total_usd / nullif(sessions, 0) AS usd_per_session,
    total_usd / nullif(users, 0) AS usd_per_user,
    total_usd / nullif(completions, 0) AS usd_per_outcome FROM totals ORDER BY total_usd DESC"""

EVENTS = f"""SELECT event_name, app_version, count(*) AS events,
  count(DISTINCT session_id) AS sessions, max(time) AS last_seen
  FROM {t("v_events")} WHERE workspace_id = :ws AND name = :app
    AND event_source = 'event' AND time >= :since::TIMESTAMP
  GROUP BY 1, 2 ORDER BY events DESC LIMIT 200"""
FUNNEL_SPECS = f"""SELECT funnel, to_json(steps) AS steps FROM {t("funnel_specs")}
  WHERE workspace_id = :ws AND name = :app ORDER BY funnel"""
FUNNEL_UPSERT = f"""MERGE INTO {t("funnel_specs")} t USING (
  SELECT :ws AS workspace_id, :app AS name, :funnel AS funnel,
    from_json(:steps, 'ARRAY<STRING>') AS steps) s
  ON t.workspace_id = s.workspace_id AND t.name = s.name AND t.funnel = s.funnel
  WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *"""
FUNNELS = f"""SELECT * FROM {t("v_funnels")} WHERE workspace_id = :ws AND name = :app
  ORDER BY funnel, app_version, step_number"""
COHORTS = f"""SELECT * FROM {t("v_cohorts")} WHERE workspace_id = :ws AND name = :app
  ORDER BY cohort_week, week_number"""
LEADERBOARD = f"SELECT * FROM {t('v_leaderboard')} WHERE workspace_id = :ws"
RUM = f"""SELECT * FROM {t("v_rum_daily")}
  WHERE workspace_id = :ws AND name = :app AND date >= :since::DATE
  ORDER BY date DESC, route, js_errors DESC LIMIT 500"""
GUARDRAILS = f"""SELECT ts, trace_id, kind, severity, excerpt_hash, excerpt_masked
  FROM {t("guardrail_findings")} WHERE workspace_id = :ws AND name = :app
  AND ts >= :since::TIMESTAMP ORDER BY ts DESC LIMIT 200"""
TEMPLATE_DRIFT = f"""WITH daily AS (
    SELECT date, template_hash, count(*) AS samples,
      sum(count(*)) OVER (PARTITION BY date) AS daily_samples
    FROM {t("guardrail_samples")} WHERE workspace_id = :ws AND name = :app
      AND date >= :since::DATE AND template_hash IS NOT NULL GROUP BY 1, 2
  ) SELECT *, samples / daily_samples AS share FROM daily ORDER BY date DESC, share DESC"""
# ---- reach (S10–S13)
DEPLOYMENT_MODE = os.environ.get("DEPLOYMENT_MODE", "standalone")

REACH_SLO = f"""
  SELECT s.name, s.slo, s.sli, s.target, s.window_days,
         sum(b.good) / nullif(sum(b.total), 0) AS attainment, sum(b.total) AS observations
  FROM {t("slo_specs")} s LEFT JOIN {t("sli_5m")} b
    ON s.name = b.name AND s.slo = b.slo AND s.workspace_id = b.workspace_id
   AND b.revision = s.revision
   AND b.bucket >= timestampadd(DAY, -s.window_days, current_timestamp())
  WHERE (:app = '' OR s.name = :app)
  GROUP BY s.name, s.slo, s.sli, s.target, s.window_days"""

REACH_INCIDENTS = f"""
  SELECT app, rule, severity, message, ts, muted, incident_id
  FROM {t("v_alerts_open")} WHERE workspace_id = :ws ORDER BY ts DESC"""

REACH_MAINTENANCE = f"""
  SELECT app, rule, starts_at, ends_at, reason FROM {t("alert_mutes")}
  WHERE workspace_id = :ws AND starts_at <= now() AND ends_at > now()"""

REACH_SYNTHETICS = f"""
  SELECT app, journey, vantage, run_id, run_ts, ok FROM {t("synthetic_runs")}
  WHERE workspace_id = :ws AND run_ts >= now() - INTERVAL 2 HOURS
    AND vantage IN ('internal', 'external') AND step = -1"""

REACH_INSERT_SYNTHETIC = f"""
  MERGE INTO {t("synthetic_runs")} t USING (
    SELECT :ws AS workspace_id, :run_id AS run_id, :app AS app,
           :journey AS journey, :step::int AS step, 'internal' AS vantage) s
  ON t.workspace_id = s.workspace_id AND t.run_id = s.run_id AND t.app = s.app
    AND t.journey = s.journey AND t.step = s.step AND t.vantage = s.vantage
  WHEN NOT MATCHED THEN INSERT
    (workspace_id, run_id, app, journey, step, vantage, run_ts, step_name, ok,
     status_code, latency_ms, within_budget, detail, kind, failure_stage)
  VALUES (s.workspace_id, s.run_id, s.app, s.journey, s.step, s.vantage, :ts::timestamp,
    :step_name, :ok::boolean, :code::int, :ms::double, :budget::boolean, :detail,
    'http', nullif(:failure_stage, ''))"""

REACH_FLEET = f"""
  WITH usage AS (
    SELECT workspace_id, name, sum(requests) AS requests_7d, sum(errors) AS errors_7d
    FROM {t("v_fleet_agg_app_daily")}
    WHERE traffic_kind = 'real' AND date >= current_date() - 7 GROUP BY 1, 2),
  costs AS (
    SELECT workspace_id, name, sum(dbus) AS dbus_7d, sum(dbu_usd) AS usd_7d
    FROM {t("v_fleet_costs_daily")} WHERE date >= current_date() - 7 GROUP BY 1, 2)
  SELECT i.workspace_id, i.workspace_name, i.name, i.url, i.app_state, i.compute_state,
         i.snapshot_ts, u.requests_7d, u.errors_7d, c.dbus_7d, c.usd_7d
  FROM {t("v_fleet_apps_current")} i
  LEFT JOIN usage u ON i.workspace_id = u.workspace_id AND i.name = u.name
  LEFT JOIN costs c ON i.workspace_id = c.workspace_id AND i.name = c.name
  WHERE (:ws = '' OR i.workspace_id = :ws) ORDER BY i.workspace_name, i.name"""

# ---- operations console: bounded fleet reads, never a query per inventory app.
CONSOLE_HOURLY = f"""SELECT name, hour, requests, errors, p95_ms
  FROM {t("agg_app_hourly")} WHERE workspace_id = :ws AND traffic_kind = 'real'
  AND hour >= date_trunc('hour', now()) - INTERVAL 23 HOURS ORDER BY name, hour"""
CONSOLE_SLOS = SLO_SUMMARY.replace(" AND s.name = :app", "")
CONSOLE_TELEMETRY = TELEMETRY_HEALTH.replace(" AND name = :app", "")
CONSOLE_DEPLOYMENTS = f"""SELECT name, deployment_id, create_time, state, mode
  FROM {t("app_deployments")} WHERE workspace_id = :ws
  QUALIFY row_number() OVER (PARTITION BY name ORDER BY create_time DESC) <= 10"""
CONSOLE_FINDINGS = f"""SELECT name,
  count_if(kind = 'cve' AND severity = 'critical') AS critical,
  count_if(kind = 'cve' AND severity = 'high') AS high,
  count_if(kind = 'cve' AND severity = 'medium') AS medium,
  count_if(kind = 'cve' AND severity = 'low') AS low,
  count_if(kind = 'secret') AS secrets
  FROM {t("v_findings_latest")} GROUP BY name"""
CONSOLE_SYNTHETICS = f"""SELECT * FROM {t("synthetic_runs")}
  WHERE workspace_id = :ws AND step = -1 AND run_ts >= now() - INTERVAL 24 HOURS
  QUALIFY row_number() OVER (PARTITION BY app, journey, vantage ORDER BY run_ts DESC) <= 12"""
CONSOLE_DAILY_COST = f"""SELECT name, date, dbu_usd, ai_usd, total_usd
  FROM {t("v_unit_economics")} WHERE workspace_id = :ws
  AND date >= current_date() - 29 ORDER BY name, date"""
# A missing priced day must not disappear inside SUM and become a complete MTD total.
CONSOLE_UNIT_ECONOMICS = UNIT_ECONOMICS.replace(
    "sum(dbu_usd) AS dbu_usd",
    "CASE WHEN count_if(dbu_usd IS NULL) > 0 THEN NULL ELSE sum(dbu_usd) END AS dbu_usd",
).replace(
    "sum(idle_usd) AS idle_usd",
    "CASE WHEN count_if(idle_usd IS NULL) > 0 THEN NULL ELSE sum(idle_usd) END AS idle_usd",
)
CONSOLE_FUNNELS = f"""SELECT * FROM {t("v_funnels")} WHERE workspace_id = :ws
  AND (name, funnel) IN (SELECT name, funnel FROM {t("funnel_specs")}
    WHERE workspace_id = :ws ORDER BY name, funnel LIMIT 1)
  ORDER BY app_version, step_number"""
CONSOLE_COHORTS = f"""SELECT * FROM {t("v_cohorts")} WHERE workspace_id = :ws
  AND name = (SELECT min(name) FROM {t("v_cohorts")} WHERE workspace_id = :ws)
  AND cohort_week >= current_date() - 56 ORDER BY cohort_week, week_number"""
CONSOLE_GENAI = f"""SELECT name, model, sum(calls) AS calls,
  sum(input_tokens) AS input_tokens, sum(output_tokens) AS output_tokens
  FROM {t("v_genai_daily")} WHERE workspace_id = :ws AND date = current_date() - 1
  GROUP BY name, model"""
CONSOLE_QUALITY = f"""SELECT * FROM {t("monitor_quality")}
  QUALIFY row_number() OVER (PARTITION BY name ORDER BY ts DESC) = 1"""
CONSOLE_FEEDBACK = f"""SELECT name, count(*) AS count_7d, avg(rating) AS avg_stars
  FROM {t("v_feedback")} WHERE date >= current_date() - 7 GROUP BY name"""
CONSOLE_GUARDRAILS = f"""SELECT name, kind, count(*) AS findings
  FROM {t("guardrail_findings")} WHERE workspace_id = :ws AND ts >= now() - INTERVAL 7 DAYS
  GROUP BY name, kind"""
CONSOLE_DRIFT = f"""SELECT name, novel_share, week FROM {t("drift_reports")}
  WHERE workspace_id = :ws
  QUALIFY row_number() OVER (PARTITION BY name ORDER BY week DESC) = 1"""
# The gold error view covers raw retention, not 24h, and carries no trace reference.
# Keep its fingerprint algorithm, but bound the source window and retain correlation.
CONSOLE_ERRORS = f"""WITH fingerprints AS (
  SELECT service_name, trace_id, span_id,
    any_value({vg("exception.fingerprint")}) AS fingerprint,
    any_value({vg("exception.type")}) AS exception_type,
    any_value({HTTP_ROUTE}) AS route
  FROM {t("otel_spans")} WHERE time >= now() - INTERVAL 24 HOURS GROUP BY 1, 2, 3
), logs AS (
  SELECT l.*, s.fingerprint AS span_fingerprint, s.exception_type, s.route
  FROM {t("otel_logs")} l LEFT JOIN fingerprints s
    ON l.service_name = s.service_name AND l.trace_id = s.trace_id AND l.span_id = s.span_id
  WHERE l.time >= now() - INTERVAL 24 HOURS
    AND upper(coalesce(l.severity_text, '')) IN ('ERROR', 'FATAL', 'CRITICAL')
    AND (:app = '' OR l.service_name = :app)
) SELECT service_name AS name,
  coalesce({vg("exception.fingerprint")}, span_fingerprint,
    substr(sha2(regexp_replace(substr(lower(cast(body AS string)), 1, 400),
      '[0-9a-f\\\\-]{{8,}}|\\\\d+', '#'), 256), 1, 10)) AS fingerprint,
  count(*) AS count_24h, min(time) AS first_seen, max(time) AS last_seen,
  max_by(substr(cast(body AS string), 1, 400), time) AS message,
  max_by(coalesce({vg("exception.type")}, exception_type), time) AS type,
  max_by(trace_id, time) AS sample_trace_id, max_by(route, time) AS route
  FROM logs GROUP BY 1, 2 ORDER BY count_24h DESC LIMIT 100"""
CONSOLE_REMOTE_COST = f"""SELECT workspace_id, name,
  CASE WHEN count_if(dbu_usd IS NULL) > 0 THEN NULL ELSE sum(dbu_usd) END AS dbu_usd
  FROM {t("v_fleet_costs_daily")} WHERE date >= date_trunc('MONTH', current_date())
  GROUP BY workspace_id, name"""
CONSOLE_REMOTE_ALERTS = f"SELECT * FROM {t('v_fleet_alerts_open')}"
CONSOLE_GENAI_SIGNALS = f"""SELECT service_name AS name,
  approx_percentile({vg("monitor.llm.ttft_ms", "double")}, 0.95) AS ttft_p95_ms,
  count_if({vg("error.type")} = 'rate_limit') AS rate_limit,
  count_if({vg("error.type")} = 'timeout') AS timeout,
  count_if({vg("error.type")} = 'policy') AS policy,
  count_if({vg("error.type")} = 'schema') AS schema,
  count_if({vg("error.type")} = 'server') AS server
  FROM {t("otel_spans")} WHERE time >= now() - INTERVAL 24 HOURS AND {NOT_PROBE}
  AND {vg("monitor.llm.billable", "boolean")} = true GROUP BY service_name"""
CONSOLE_PACKAGES = f"SELECT name, deps_json FROM {t('v_scan_latest')}"
