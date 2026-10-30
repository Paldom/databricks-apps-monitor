"""Analytics & governance materialization — task 3 of the hourly inventory job.

1. Gold VIEWS over telemetry + tables (idempotent CREATE OR REPLACE):
   usage/users (adoption), error groups, dependency latency, GenAI usage,
   release windows + per-release performance, cost forecast, chargeback by tag.
2. Governance TABLES: app_config (tags/budget/auto-stop; monitor can write),
   monitor_audit (system.access.audit snapshot), app_permissions (+drift → alerts),
   app_deployments (CI/CD history).
3. Smart detection: hourly anomaly baselines (traffic/latency z-scores) → alert_events.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession


def aggregate_sql(fq: str, table: str, predicate: str) -> str:
    """Each source bucket is replaced, so retries and late spans cannot double-count."""
    from telemetry_sql import BILLABLE, DUR, ERR, IN_TOK, OUT_TOK, SESS, UHASH, enriched_spans
    from telemetry_sql import SERVER as ALL_SERVER

    hourly = table == "agg_app_hourly"
    period = "date_trunc('hour', time)" if hourly else "date"
    ai = f"((model IS NOT NULL OR billable = true) AND {BILLABLE})"
    if table == "agg_genai_daily":
        select = f"""date, service_name AS name, traffic_kind,
          coalesce(model, '(unknown)') AS model,
          count_if({ai}) AS calls,
          sum(CASE WHEN {ai} THEN {IN_TOK} ELSE 0 END) AS input_tokens,
          sum(CASE WHEN {ai} THEN {OUT_TOK} ELSE 0 END) AS output_tokens,
          avg(CASE WHEN {ai} THEN {DUR} END) AS avg_ms,
          approx_percentile(CASE WHEN {ai} THEN {DUR} END, 0.95) AS p95_ms,
          count_if({ai} AND {ERR}) AS errors, :ws AS workspace_id, now() AS computed_at"""
        body = f"SELECT {select} FROM marked WHERE model IS NOT NULL OR billable = true GROUP BY 1, 2, 3, 4"
        keys = "t.date = s.date AND t.name = s.name AND t.model = s.model"
    else:
        select = f"""{period} AS {"hour" if hourly else "date"}, service_name AS name, traffic_kind,
          count_if({ALL_SERVER}) AS requests,
          count_if({ALL_SERVER} AND {ERR}) AS errors,
          count(DISTINCT CASE WHEN {ALL_SERVER} THEN {UHASH} END) AS users,
          count(DISTINCT CASE WHEN {ALL_SERVER} THEN {SESS} END) AS sessions,
          hll_sketch_agg(CASE WHEN {ALL_SERVER} THEN {UHASH} END) AS users_hll,
          hll_sketch_agg(CASE WHEN {ALL_SERVER} THEN {SESS} END) AS sessions_hll,
          avg(CASE WHEN {ALL_SERVER} THEN {DUR} END) AS avg_ms,
          approx_percentile(CASE WHEN {ALL_SERVER} THEN {DUR} END, 0.5) AS p50_ms,
          approx_percentile(CASE WHEN {ALL_SERVER} THEN {DUR} END, 0.95) AS p95_ms,
          count_if({ai}) AS ai_calls,
          sum(CASE WHEN {ai} THEN {IN_TOK} ELSE 0 END) AS in_tokens,
          sum(CASE WHEN {ai} THEN {OUT_TOK} ELSE 0 END) AS out_tokens,
          :ws AS workspace_id, now() AS computed_at"""
        body = f"SELECT {select} FROM marked WHERE {ALL_SERVER} OR {ai} GROUP BY 1, 2, 3"
        key = "hour" if hourly else "date"
        keys = f"t.{key} = s.{key} AND t.name = s.name"
    return f"""MERGE INTO {fq}.{table} t USING (
      {enriched_spans(fq, predicate)} {body}) s
      ON {keys} AND t.traffic_kind = s.traffic_kind AND t.workspace_id = s.workspace_id
      WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *"""


def materialize_aggregates(spark, fq: str, workspace_id: str) -> None:
    for table, period in (("agg_app_daily", "date DATE"), ("agg_app_hourly", "hour TIMESTAMP")):
        spark.sql(f"""CREATE TABLE IF NOT EXISTS {fq}.{table} (
          {period}, name STRING, traffic_kind STRING, requests LONG, errors LONG,
          users LONG, sessions LONG, users_hll BINARY, sessions_hll BINARY,
          avg_ms DOUBLE, p50_ms DOUBLE, p95_ms DOUBLE,
          ai_calls LONG, in_tokens LONG, out_tokens LONG,
          workspace_id STRING, computed_at TIMESTAMP
        ) CLUSTER BY (name, {period.split()[0]})
        COMMENT 'Retained app usage by traffic kind; HLL sketches support distinct counts across buckets'""")
    spark.sql(f"""CREATE TABLE IF NOT EXISTS {fq}.agg_genai_daily (
      date DATE, name STRING, traffic_kind STRING, model STRING, calls LONG,
      input_tokens LONG, output_tokens LONG, avg_ms DOUBLE, p95_ms DOUBLE, errors LONG,
      workspace_id STRING, computed_at TIMESTAMP
    ) CLUSTER BY (name, date)
    COMMENT 'Retained billable GenAI usage and latency by model and traffic kind'""")
    for table in ("agg_app_daily", "agg_app_hourly", "agg_genai_daily"):
        existing = spark.sql(
            f"SELECT 1 FROM {fq}.{table} WHERE workspace_id = :ws LIMIT 1",
            args={"ws": workspace_id},
        ).collect()
        # Bootstrap all available raw history before retention is allowed to delete it.
        predicate = "date >= current_date() - 2" if existing else "true"
        spark.sql(aggregate_sql(fq, table, predicate), args={"ws": workspace_id})


def views_sql(fq: str) -> list[tuple[str, str]]:
    from telemetry_sql import (
        BILLABLE,
        DUR,
        ERR,
        IN_TOK,
        NOT_PROBE,
        OUT_TOK,
        SESS,
        UHASH,
        enriched_spans,
    )
    from telemetry_sql import SERVER as ALL_SERVER

    server = f"{ALL_SERVER} AND {NOT_PROBE}"
    return [
        (
            "v_alerts_open",
            f"""CREATE OR REPLACE VIEW {fq}.v_alerts_open
            COMMENT 'Current firing state per workspace/source/rule/app, without a lookback cutoff' AS
            SELECT * EXCEPT (rn) FROM (
              SELECT *, row_number() OVER (
                PARTITION BY workspace_id, source, rule, app ORDER BY ts DESC, state DESC) rn
              FROM {fq}.alert_events)
            WHERE rn = 1 AND state = 'firing'""",
        ),
        (
            "v_usage_daily",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_usage_daily
          COMMENT 'Adoption per app per day: requests, distinct users/sessions, errors (GA-style)' AS
          SELECT date, name, requests, users, sessions, errors, round(avg_ms, 1) AS avg_ms,
                 users_hll, sessions_hll, workspace_id
          FROM {fq}.agg_app_daily WHERE traffic_kind = 'real'""",
        ),
        (
            "v_users",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_users
          COMMENT 'Per hashed-user history within raw retention; cross-day counts use HLL in agg_app_daily' AS
          SELECT service_name AS name, {UHASH} AS user_hash,
                 min(time) AS first_seen, max(time) AS last_seen,
                 count(*) AS requests, count(DISTINCT {SESS}) AS sessions,
                 count(DISTINCT date) AS active_days,
                 sum(CASE WHEN {ERR} THEN 1 ELSE 0 END) AS errors,
                 sum({IN_TOK} + {OUT_TOK}) AS tokens
          FROM {fq}.otel_spans WHERE {server} AND {UHASH} IS NOT NULL
          GROUP BY 1, 2""",
        ),
        (
            "v_error_groups",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_error_groups
          COMMENT 'SDK exception fingerprints (log or matching span), with normalized-log fallback' AS
          WITH fingerprints AS (
            SELECT service_name, trace_id, span_id,
                   any_value(variant_get(attributes, '$["exception.fingerprint"]', 'string')) AS fingerprint
            FROM {fq}.otel_spans
            WHERE variant_get(attributes, '$["exception.fingerprint"]', 'string') IS NOT NULL
            GROUP BY 1, 2, 3),
          logs AS (
            SELECT l.*, s.fingerprint AS span_fingerprint
            FROM {fq}.otel_logs l LEFT JOIN fingerprints s
              ON l.service_name = s.service_name AND l.trace_id = s.trace_id AND l.span_id = s.span_id)
          SELECT service_name AS name,
                 coalesce(variant_get(attributes, '$["exception.fingerprint"]', 'string'), span_fingerprint,
                 substr(sha2(regexp_replace(substr(lower(cast(body AS string)), 1, 400),
                        '[0-9a-f\\\\-]{{8,}}|\\\\d+', '#'), 256), 1, 10)) AS fingerprint,
                 count(*) AS occurrences, min(time) AS first_seen, max(time) AS last_seen,
                 any_value(substr(cast(body AS string), 1, 400)) AS sample
          FROM logs
          WHERE upper(coalesce(severity_text, '')) IN ('ERROR', 'FATAL', 'CRITICAL')
          GROUP BY 1, 2""",
        ),
        (
            "v_dependencies",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_dependencies
          COMMENT 'Outbound dependency latency per app: peer host, calls, p95, errors (CLIENT spans)' AS
          SELECT service_name AS name,
                 coalesce(variant_get(attributes, '$["server.address"]', 'string'),
                          variant_get(attributes, '$["net.peer.name"]', 'string'),
                          variant_get(attributes, '$["db.system"]', 'string'), name) AS dependency,
                 date, count(*) AS calls, round(avg({DUR}), 1) AS avg_ms,
                 round(approx_percentile({DUR}, 0.95), 1) AS p95_ms,
                 sum(CASE WHEN {ERR} THEN 1 ELSE 0 END) AS errors
          FROM {fq}.otel_spans WHERE kind ILIKE '%client%'
          GROUP BY 1, 2, 3""",
        ),
        (
            "v_genai_daily",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_genai_daily
          COMMENT 'GenAI usage per app/model/day: calls, tokens, latency, errors (gen_ai spans)' AS
          SELECT date, name, model, calls, input_tokens, output_tokens,
                 round(avg_ms, 1) AS avg_ms, round(p95_ms, 1) AS p95_ms, errors, workspace_id
          FROM {fq}.agg_genai_daily WHERE traffic_kind = 'real' AND calls > 0""",
        ),
        (
            "v_genai_sessions",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_genai_sessions
          COMMENT 'Top GenAI consumers: billable tokens per session/user per app (last 30 days)' AS
          {enriched_spans(fq, "date >= current_date() - 30")}
          SELECT service_name AS name, {SESS} AS session_id, {UHASH} AS user_hash,
                 count(*) AS calls, sum({IN_TOK} + {OUT_TOK}) AS tokens,
                 min(time) AS first_call, max(time) AS last_call
          FROM marked
          WHERE (model IS NOT NULL OR billable = true) AND {BILLABLE} AND {NOT_PROBE}
          GROUP BY 1, 2, 3""",
        ),
        (
            "v_release_windows",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_release_windows
          COMMENT 'Deployment windows per app derived from inventory snapshots' AS
          SELECT name, deployment_id, min(snapshot_ts) AS start_ts,
                 lead(min(snapshot_ts)) OVER (PARTITION BY name ORDER BY min(snapshot_ts)) AS end_ts
          FROM {fq}.apps_inventory WHERE deployment_id IS NOT NULL
          GROUP BY name, deployment_id""",
        ),
        (
            "v_release_perf",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_release_perf
          COMMENT 'Regression-by-version: request perf per deployment window' AS
          SELECT w.name, w.deployment_id, w.start_ts, w.end_ts,
                 count(s.span_id) AS requests,
                 round(approx_percentile({DUR.replace("(end_time", "(s.end_time").replace(" start_time", " s.start_time")}, 0.95), 1) AS p95_ms,
                 round(100 * sum(CASE WHEN {ERR.replace("status.code", "s.status.code").replace("variant_get(attributes", "variant_get(s.attributes")} THEN 1 ELSE 0 END) / greatest(count(s.span_id), 1), 2) AS error_pct,
                 sum(coalesce(variant_get(s.attributes, '$["gen_ai.usage.input_tokens"]', 'long'), 0)
                   + coalesce(variant_get(s.attributes, '$["gen_ai.usage.output_tokens"]', 'long'), 0)) AS tokens
          FROM {fq}.v_release_windows w
          LEFT JOIN {fq}.otel_spans s
            ON s.service_name = w.name AND s.kind ILIKE '%server%' AND {NOT_PROBE.replace("variant_get(attributes", "variant_get(s.attributes").replace("WHEN name", "WHEN s.name")}
           AND s.time >= w.start_ts AND (w.end_ts IS NULL OR s.time < w.end_ts)
          GROUP BY 1, 2, 3, 4""",
        ),
        (
            "v_cost_forecast",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_cost_forecast
          COMMENT '30-day compute cost forecast per app (linear fit over last 14 days)' AS
          WITH d AS (SELECT name, datediff(date, current_date()) AS x, dbu_usd
                     FROM {fq}.costs_daily WHERE date >= current_date() - 14 AND dbu_usd IS NOT NULL)
          SELECT name, round(avg(dbu_usd), 2) AS avg_daily_usd,
                 round(greatest(0, 30 * coalesce(regr_intercept(dbu_usd, x), avg(dbu_usd))
                                  + 465 * coalesce(regr_slope(dbu_usd, x), 0)), 2) AS forecast_30d_usd,
                 count(*) AS days_observed
          FROM d GROUP BY name""",
        ),
        (
            "v_chargeback",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_chargeback
          COMMENT 'Showback: month-to-date cost grouped by governance tags (team, cost_center)' AS
          SELECT coalesce(get_json_object(c.tags_json, '$.team'), 'untagged') AS team,
                 coalesce(get_json_object(c.tags_json, '$.cost_center'), 'untagged') AS cost_center,
                 d.name, round(sum(d.dbu_usd), 2) AS mtd_usd,
                 sum(d.ai_input_tokens + d.ai_output_tokens) AS mtd_tokens,
                 sum(d.ai_calls) AS mtd_ai_calls
          FROM {fq}.costs_daily d LEFT JOIN {fq}.app_config c ON d.name = c.name
          WHERE d.date >= date_trunc('MONTH', current_date())
          GROUP BY 1, 2, 3""",
        ),
        (
            "v_feedback",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_feedback
          COMMENT 'In-app user feedback (middleware /monitor/feedback route → otel_logs): rating 1-5, comment, hashed user' AS
          SELECT time, date, service_name AS name,
                 cast(get_json_object(cast(body AS string), '$.rating') AS int) AS rating,
                 get_json_object(cast(body AS string), '$.comment') AS comment,
                 get_json_object(cast(body AS string), '$.user') AS user_hash,
                 get_json_object(cast(body AS string), '$.sid') AS session_id,
                 get_json_object(cast(body AS string), '$.rid') AS client_request_id
          FROM {fq}.otel_logs
          WHERE get_json_object(cast(body AS string), '$.event') = 'feedback'""",
        ),
    ]


# semantic metadata on the platform-created telemetry tables — Genie/consumers read these
TABLE_COMMENTS = [
    (
        "otel_logs",
        "Raw OTel log records from every fleet app (platform telemetry export). "
        "service_name = app name; trace_id/span_id join to otel_spans; body is the log line.",
    ),
    (
        "otel_spans",
        "Raw OTel spans from every fleet app (platform telemetry export). "
        "service_name = app name (tenant key); attributes is VARIANT "
        "(app.client_request_id, session.id, user.id_hash, gen_ai.*); "
        "duration ms = (end_time_unix_nano-start_time_unix_nano)/1e6.",
    ),
    (
        "otel_metrics",
        "Raw OTel metrics from every fleet app (platform telemetry export). "
        "Counters/gauges/histograms; monitor.* = fleet-monitor instruments.",
    ),
    (
        "costs_daily",
        "Per-app daily cost: compute DBU $ (system.billing.usage x list_prices) "
        "+ AI tokens/calls from the app''s own gen_ai spans.",
    ),
    (
        "alert_events",
        "Alert firings/resolutions from the in-app rule engine and the jobs "
        "(anomaly, budget, drift, review, journey).",
    ),
]


CONFIG_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.app_config (
  name STRING, tags_json STRING, budget_usd_month DOUBLE,
  auto_stop STRING, idle_hours INT, updated_at TIMESTAMP, updated_by STRING,
  capacity_path STRING, workspace_id STRING
) COMMENT 'Per-app governance config: tags (team/cost_center/env/tier), monthly budget, auto-stop mode (none|idle|night)'"""

# system.access.audit is ACCOUNT-wide — without the workspace_id filter this table
# would show apps events from every workspace in the account (it did; user caught it)
AUDIT_SQL = """
CREATE TABLE IF NOT EXISTS {fq}.monitor_audit
COMMENT 'Apps-service audit events, last 7 days, THIS workspace (from system.access.audit)' AS
SELECT event_time, user_identity.email AS user, service_name, action_name,
       coalesce(request_params['name'], request_params['app_name'], request_params['resourceName']) AS app,
       response.status_code AS status_code, to_json(request_params) AS params_json,
       cast(workspace_id AS STRING) AS workspace_id
FROM system.access.audit
WHERE event_date >= current_date() - 7 AND service_name = 'apps'
  AND workspace_id = {ws}"""

PERMS_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.app_permissions (
  snapshot_ts TIMESTAMP, name STRING, principal STRING, principal_type STRING, level STRING,
  workspace_id STRING
) COMMENT 'App ACL snapshots (hourly) — source for permission drift detection'"""

DEPLOYS_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.app_deployments (
  name STRING, deployment_id STRING, create_time STRING, state STRING, mode STRING, source_code_path STRING,
  workspace_id STRING
) COMMENT 'App deployment history (CI/CD health) — latest 20 per app, refreshed hourly'"""


def snapshot_permissions(w: WorkspaceClient, spark, cat: str, sch: str, apps: list, ts) -> None:
    from schema_utils import workspace_column

    fq = f"`{cat}`.`{sch}`"
    tbl = f"{cat}.{sch}.app_permissions"
    spark.sql(PERMS_DDL.format(fq=fq))
    workspace_column(spark, f"{fq}.app_permissions", str(w.get_workspace_id()))
    prev = {
        (r["name"], r["principal"], r["level"])
        for r in spark.sql(f"""SELECT name, principal, level FROM {fq}.app_permissions
                               WHERE snapshot_ts = (SELECT max(snapshot_ts) FROM {fq}.app_permissions)""").collect()
    }
    rows, cur = [], set()
    evaluated = set()
    for a in apps:
        try:
            acl = w.api_client.do("GET", f"/api/2.0/permissions/apps/{a.name}").get(
                "access_control_list", []
            )
        except Exception as e:  # noqa: BLE001
            print(f"perms {a.name}: {e}")
            continue
        evaluated.add(a.name)
        for e in acl:
            principal = (
                e.get("user_name") or e.get("group_name") or e.get("service_principal_name") or "?"
            )
            ptype = "user" if e.get("user_name") else "group" if e.get("group_name") else "sp"
            for p in e.get("all_permissions", []):
                if p.get("inherited"):
                    continue
                rows.append(
                    {
                        "snapshot_ts": ts,
                        "workspace_id": str(w.get_workspace_id()),
                        "name": a.name,
                        "principal": principal,
                        "principal_type": ptype,
                        "level": p.get("permission_level", "?"),
                    }
                )
                cur.add((a.name, principal, p.get("permission_level", "?")))
    if rows:
        spark.createDataFrame(rows, schema=spark.table(tbl).schema).write.mode(
            "append"
        ).saveAsTable(tbl)
    if prev:
        prev = {key for key in prev if key[0] in evaluated}
        added, removed = cur - prev, prev - cur
        alerts = [
            {
                "rule": "permission_drift",
                "app": n,
                "severity": "warning",
                "message": f"ACL change: +{level} for {principal}",
                "value": 0,
            }
            for (n, principal, level) in added
        ] + [
            {
                "rule": "permission_drift",
                "app": n,
                "severity": "info",
                "message": f"ACL change: -{level} removed for {principal}",
                "value": 0,
            }
            for (n, principal, level) in removed
        ]
        from source_scan import emit_alerts

        emit_alerts(
            spark, cat, sch, alerts, owned_rules=("permission_drift",), evaluated_apps=evaluated
        )
        print(f"permission drift: {len(alerts)} changes")


def snapshot_deployments(w: WorkspaceClient, spark, cat: str, sch: str, apps: list) -> None:
    from schema_utils import workspace_column

    rows = []
    for a in apps:
        try:
            deps = w.api_client.do("GET", f"/api/2.0/apps/{a.name}/deployments").get(
                "app_deployments", []
            )
        except Exception as e:  # noqa: BLE001
            print(f"deployments {a.name}: {e}")
            continue
        for d in deps[:20]:
            rows.append(
                {
                    "name": a.name,
                    "deployment_id": d.get("deployment_id"),
                    "workspace_id": str(w.get_workspace_id()),
                    "create_time": d.get("create_time"),
                    "state": (d.get("status") or {}).get("state", "?"),
                    "mode": d.get("mode"),
                    "source_code_path": d.get("source_code_path"),
                }
            )
    spark.sql(DEPLOYS_DDL.format(fq=f"`{cat}`.`{sch}`"))
    tbl = f"{cat}.{sch}.app_deployments"
    workspace_column(spark, tbl, str(w.get_workspace_id()))
    if rows:
        spark.createDataFrame(rows, schema=spark.table(tbl).schema).write.mode(
            "overwrite"
        ).saveAsTable(tbl)
    print(f"deployments: {len(rows)} rows")


def detect_anomalies(spark, fq: str) -> None:
    rows = spark.sql(f"""
      WITH hourly AS (
        SELECT name, hour AS h, requests AS req, p95_ms AS p95
        FROM {fq}.agg_app_hourly WHERE traffic_kind = 'real' AND hour >= now() - INTERVAL 8 DAYS),
      base AS (SELECT name, avg(req) AS mu, stddev(req) AS sd, avg(p95) AS mu95, stddev(p95) AS sd95
               FROM hourly WHERE h < date_trunc('hour', now() - INTERVAL 1 HOUR) GROUP BY name),
      cur AS (SELECT name, req, p95 FROM hourly WHERE h = date_trunc('hour', now() - INTERVAL 1 HOUR))
      SELECT c.name, c.req, c.p95, b.mu, b.sd, b.mu95, b.sd95
      FROM cur c JOIN base b ON c.name = b.name
      WHERE (b.sd > 0 AND abs(c.req - b.mu) > 3 * b.sd AND abs(c.req - b.mu) > 10)
         OR (b.sd95 > 0 AND c.p95 > b.mu95 + 3 * b.sd95 AND c.p95 > 500)""").collect()
    alerts = []
    for r in rows:
        if abs(r["req"] - r["mu"]) > 3 * (r["sd"] or 1e9) and abs(r["req"] - r["mu"]) > 10:
            alerts.append(
                {
                    "rule": "anomaly_traffic",
                    "app": r["name"],
                    "severity": "info",
                    "message": f"traffic {r['req']}/h vs 7d baseline {r['mu']:.0f}±{r['sd']:.0f}",
                    "value": r["req"],
                }
            )
        if r["sd95"] and r["p95"] and r["p95"] > r["mu95"] + 3 * r["sd95"] and r["p95"] > 500:
            alerts.append(
                {
                    "rule": "anomaly_latency",
                    "app": r["name"],
                    "severity": "warning",
                    "message": f"p95 {r['p95']:.0f}ms vs 7d baseline {r['mu95']:.0f}±{r['sd95']:.0f}ms",
                    "value": r["p95"],
                }
            )
    from source_scan import emit_alerts

    emit_alerts(
        spark,
        fq.strip("`").split("`.`")[0],
        fq.strip("`").split("`.`")[1],
        alerts,
        owned_rules=("anomaly_traffic", "anomaly_latency"),
    )
    print(f"anomalies: {len(alerts)} alerts")


def check_budgets(spark, fq: str) -> None:
    rows = spark.sql(f"""
      SELECT c.name, c.budget_usd_month, round(sum(d.dbu_usd), 2) AS mtd
      FROM {fq}.app_config c JOIN {fq}.costs_daily d ON c.name = d.name
      WHERE c.budget_usd_month > 0 AND d.date >= date_trunc('MONTH', current_date())
      GROUP BY 1, 2 HAVING sum(d.dbu_usd) > 0.7 * c.budget_usd_month""").collect()
    alerts = [
        {
            "rule": "budget_burn",
            "app": r["name"],
            "severity": "critical" if r["mtd"] >= r["budget_usd_month"] else "warning",
            "message": f"month-to-date ${r['mtd']:.2f} of ${r['budget_usd_month']:.2f} budget "
            f"({100 * r['mtd'] / r['budget_usd_month']:.0f}%)",
            "value": r["mtd"],
        }
        for r in rows
    ]
    from source_scan import emit_alerts

    emit_alerts(
        spark,
        fq.strip("`").split("`.`")[0],
        fq.strip("`").split("`.`")[1],
        alerts,
        owned_rules=("budget_burn",),
    )
    print(f"budgets: {len(alerts)} alerts")


def token_policy(today: int, last_hour: int, budget: int | None) -> str:
    if not budget or budget <= 0:
        return "none"
    if today >= budget:
        return "block"
    return "warn" if today >= 0.8 * budget or today + last_hour >= budget else "none"


def check_token_budgets(spark, fq: str, workspace_id: str, cat: str, sch: str) -> None:
    from product_sql import token_usage_sql

    rows = spark.sql(
        f"""WITH tokens AS ({token_usage_sql(fq, 1, spark.catalog.tableExists(f"{fq}.otel_metrics"))}), totals AS (
          SELECT name,
            sum(CASE WHEN date = current_date() THEN tokens ELSE 0 END) AS today,
            sum(CASE WHEN hour = date_trunc('hour', now()) - INTERVAL 1 HOUR THEN tokens ELSE 0 END) AS last_hour
          FROM tokens GROUP BY name
        ) SELECT c.name, c.token_budget_day, coalesce(t.today, 0) AS today,
                 coalesce(t.last_hour, 0) AS last_hour
          FROM {fq}.app_config c LEFT JOIN totals t USING (name) WHERE c.workspace_id = :ws""",
        args={"ws": workspace_id},
    ).collect()
    alerts = []
    for row in rows:
        state = token_policy(row["today"], row["last_hour"], row["token_budget_day"])
        spark.sql(
            f"""UPDATE {fq}.app_config SET throttle = :state, tokens_today = :today,
              tokens_last_hour = :last_hour, policy_updated_at = now()
              WHERE workspace_id = :ws AND name = :app""",
            args={
                "state": state,
                "today": row["today"],
                "last_hour": row["last_hour"],
                "ws": workspace_id,
                "app": row["name"],
            },
        )
        if state != "none":
            alerts.append(
                {
                    "rule": f"token_budget_{state}",
                    "app": row["name"],
                    "severity": "critical" if state == "block" else "warning",
                    "message": f"token policy {state}: {row['today']} today / {row['token_budget_day']} budget; "
                    f"{row['last_hour']} in last completed hour",
                    "value": row["today"],
                }
            )
    from source_scan import emit_alerts

    emit_alerts(
        spark,
        cat,
        sch,
        alerts,
        owned_rules=("token_budget_warn", "token_budget_block"),
        evaluated_apps={r["name"] for r in rows},
    )


def main() -> None:
    from product_sql import CONFIG_COLUMNS, FUNNEL_DDL, MODEL_PRICES_DDL, product_views_sql
    from schema_utils import ensure_columns, workspace_column

    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--monitor-app", default="apps-monitor")
    p.add_argument("--jobs-dir", default="")
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"

    w = WorkspaceClient()
    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    ts = datetime.now(timezone.utc)
    apps = list(w.apps.list())

    spark.sql(CONFIG_DDL.format(fq=fq))
    ensure_columns(spark, f"{fq}.app_config", {"capacity_path": "STRING", **CONFIG_COLUMNS})
    workspace_column(spark, f"{fq}.app_config", str(w.get_workspace_id()))
    spark.sql(MODEL_PRICES_DDL.format(fq=fq))
    spark.sql(FUNNEL_DDL.format(fq=fq))
    # Gold may run before the daily cost job on a fresh installation.
    from cost_rollup import DDL as COST_DDL
    from llm_review import DDL as REVIEW_DDL

    from source_scan import DDL_SCANS

    spark.sql(COST_DDL.format(fq=fq))
    spark.sql(DDL_SCANS.format(fq=fq))
    spark.sql(REVIEW_DDL.format(fq=fq))
    ensure_columns(spark, f"{fq}.costs_daily", {"idle_usd": "DOUBLE"})
    materialize_aggregates(spark, fq, str(w.get_workspace_id()))
    monitor = next((a for a in apps if a.name == args.monitor_app), None)
    if monitor and monitor.service_principal_client_id:
        try:  # the monitor edits tags/budgets/auto-stop itself
            spark.sql(
                f"GRANT MODIFY ON TABLE {fq}.`app_config` TO `{monitor.service_principal_client_id}`"
            )
        except Exception as e:  # noqa: BLE001
            print(f"app_config grant failed: {e}")

    for name, sql in views_sql(fq):
        try:
            spark.sql(sql)
            print(f"view {name} ok")
        except Exception as e:  # noqa: BLE001 — base table may not exist yet
            print(f"view {name} failed: {e}")

    for name, sql in product_views_sql(fq, str(w.get_workspace_id())):
        spark.sql(sql)
        print(f"view {name} ok")
    check_token_budgets(spark, fq, str(w.get_workspace_id()), args.catalog, args.schema)

    for tbl, comment in TABLE_COMMENTS:
        try:  # platform-created tables may not exist yet / may be owned elsewhere
            spark.sql(f"COMMENT ON TABLE {fq}.`{tbl}` IS '{comment.replace(chr(39), chr(39) * 2)}'")
        except Exception as e:  # noqa: BLE001
            print(f"comment {tbl} skipped: {e}")

    try:
        audit_sql = AUDIT_SQL.format(fq=fq, ws=w.get_workspace_id())
        spark.sql(audit_sql)
        workspace_column(spark, f"{fq}.monitor_audit", str(w.get_workspace_id()))
        # Preserve monitor-authored admin actions; only refresh the platform snapshot.
        spark.sql(
            f"DELETE FROM {fq}.monitor_audit WHERE service_name = 'apps' AND workspace_id = :ws",
            args={"ws": str(w.get_workspace_id())},
        )
        spark.sql(f"INSERT INTO {fq}.monitor_audit " + audit_sql.split(" AS\n", 1)[1])
        print("monitor_audit refreshed (workspace-filtered)")
    except Exception as e:  # noqa: BLE001
        print(f"audit snapshot failed: {e}")

    try:
        snapshot_permissions(w, spark, args.catalog, args.schema, apps, ts)
    except Exception as e:  # noqa: BLE001
        print(f"permission snapshot failed: {e}")
    try:
        snapshot_deployments(w, spark, args.catalog, args.schema, apps)
    except Exception as e:  # noqa: BLE001
        print(f"deployment snapshot failed: {e}")
    try:
        detect_anomalies(spark, fq)
    except Exception as e:  # noqa: BLE001
        print(f"anomaly detection failed: {e}")
    try:
        check_budgets(spark, fq)
    except Exception as e:  # noqa: BLE001
        print(f"budget check failed: {e}")
    print("gold views & governance done")


if __name__ == "__main__":
    import sys

    _jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
    if _jobs_dir:
        sys.path.append(_jobs_dir)
    main()
