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

SERVER = "kind ILIKE '%server%' AND name NOT ILIKE '%healthz%'"
DUR = "(end_time_unix_nano - start_time_unix_nano) / 1e6"
ERR = "coalesce(status.code, '') ILIKE '%error%'"
UHASH = "variant_get(attributes, '$[\"user.id_hash\"]', 'string')"
SESS = "variant_get(attributes, '$[\"session.id\"]', 'string')"
MODEL = "replace(coalesce(variant_get(attributes, '$[\"gen_ai.request.model\"]', 'string'), ''), '\"', '')"
IN_TOK = "coalesce(variant_get(attributes, '$[\"gen_ai.usage.input_tokens\"]', 'long'), 0)"
OUT_TOK = "coalesce(variant_get(attributes, '$[\"gen_ai.usage.output_tokens\"]', 'long'), 0)"


def views_sql(fq: str) -> list[tuple[str, str]]:
    return [
        (
            "v_usage_daily",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_usage_daily
          COMMENT 'Adoption per app per day: requests, distinct users/sessions, errors (GA-style)' AS
          SELECT date, service_name AS name, count(*) AS requests,
                 count(DISTINCT {UHASH}) AS users,
                 count(DISTINCT {SESS}) AS sessions,
                 sum(CASE WHEN {ERR} THEN 1 ELSE 0 END) AS errors,
                 round(avg({DUR}), 1) AS avg_ms
          FROM {fq}.otel_spans WHERE {SERVER}
          GROUP BY 1, 2""",
        ),
        (
            "v_users",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_users
          COMMENT 'Per (hashed) user history per app: first/last seen, activity, tokens, errors' AS
          SELECT service_name AS name, {UHASH} AS user_hash,
                 min(time) AS first_seen, max(time) AS last_seen,
                 count(*) AS requests, count(DISTINCT {SESS}) AS sessions,
                 count(DISTINCT date) AS active_days,
                 sum(CASE WHEN {ERR} THEN 1 ELSE 0 END) AS errors,
                 sum({IN_TOK} + {OUT_TOK}) AS tokens
          FROM {fq}.otel_spans WHERE {SERVER} AND {UHASH} IS NOT NULL
          GROUP BY 1, 2""",
        ),
        (
            "v_error_groups",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_error_groups
          COMMENT 'Error fingerprints: normalized+hashed error logs grouped (first/last seen, count)' AS
          SELECT service_name AS name,
                 substr(sha2(regexp_replace(substr(lower(cast(body AS string)), 1, 400),
                        '[0-9a-f\\\\-]{{8,}}|\\\\d+', '#'), 256), 1, 10) AS fingerprint,
                 count(*) AS occurrences, min(time) AS first_seen, max(time) AS last_seen,
                 any_value(substr(cast(body AS string), 1, 400)) AS sample
          FROM {fq}.otel_logs
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
          SELECT date, service_name AS name, {MODEL} AS model,
                 count(*) AS calls, sum({IN_TOK}) AS input_tokens, sum({OUT_TOK}) AS output_tokens,
                 round(avg({DUR}), 1) AS avg_ms, round(approx_percentile({DUR}, 0.95), 1) AS p95_ms,
                 sum(CASE WHEN {ERR} THEN 1 ELSE 0 END) AS errors
          FROM {fq}.otel_spans WHERE {MODEL} != ''
          GROUP BY 1, 2, 3""",
        ),
        (
            "v_genai_sessions",
            f"""
          CREATE OR REPLACE VIEW {fq}.v_genai_sessions
          COMMENT 'Top GenAI consumers: tokens per session/user per app (last 30 days)' AS
          SELECT service_name AS name, {SESS} AS session_id, {UHASH} AS user_hash,
                 count(*) AS calls, sum({IN_TOK} + {OUT_TOK}) AS tokens,
                 min(time) AS first_call, max(time) AS last_call
          FROM {fq}.otel_spans
          WHERE {MODEL} != '' AND date >= current_date() - 30
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
                 round(100 * sum(CASE WHEN coalesce(s.status.code, '') ILIKE '%error%' THEN 1 ELSE 0 END) / greatest(count(s.span_id), 1), 2) AS error_pct,
                 sum(coalesce(variant_get(s.attributes, '$["gen_ai.usage.input_tokens"]', 'long'), 0)
                   + coalesce(variant_get(s.attributes, '$["gen_ai.usage.output_tokens"]', 'long'), 0)) AS tokens
          FROM {fq}.v_release_windows w
          LEFT JOIN {fq}.otel_spans s
            ON s.service_name = w.name AND s.kind ILIKE '%server%' AND s.name NOT ILIKE '%healthz%'
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
  auto_stop STRING, idle_hours INT, updated_at TIMESTAMP, updated_by STRING
) COMMENT 'Per-app governance config: tags (team/cost_center/env/tier), monthly budget, auto-stop mode (none|idle|night)'"""

# system.access.audit is ACCOUNT-wide — without the workspace_id filter this table
# would show apps events from every workspace in the account (it did; user caught it)
AUDIT_SQL = """
CREATE OR REPLACE TABLE {fq}.monitor_audit
COMMENT 'Apps-service audit events, last 7 days, THIS workspace (from system.access.audit)' AS
SELECT event_time, user_identity.email AS user, service_name, action_name,
       coalesce(request_params['name'], request_params['app_name'], request_params['resourceName']) AS app,
       response.status_code AS status_code, to_json(request_params) AS params_json
FROM system.access.audit
WHERE event_date >= current_date() - 7 AND service_name = 'apps'
  AND workspace_id = {ws}"""

PERMS_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.app_permissions (
  snapshot_ts TIMESTAMP, name STRING, principal STRING, principal_type STRING, level STRING
) COMMENT 'App ACL snapshots (hourly) — source for permission drift detection'"""

DEPLOYS_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.app_deployments (
  name STRING, deployment_id STRING, create_time STRING, state STRING, mode STRING, source_code_path STRING
) COMMENT 'App deployment history (CI/CD health) — latest 20 per app, refreshed hourly'"""


def snapshot_permissions(w: WorkspaceClient, spark, cat: str, sch: str, apps: list, ts) -> None:
    fq = f"`{cat}`.`{sch}`"
    tbl = f"{cat}.{sch}.app_permissions"
    spark.sql(PERMS_DDL.format(fq=fq))
    prev = {
        (r["name"], r["principal"], r["level"])
        for r in spark.sql(f"""SELECT name, principal, level FROM {fq}.app_permissions
                               WHERE snapshot_ts = (SELECT max(snapshot_ts) FROM {fq}.app_permissions)""").collect()
    }
    rows, cur = [], set()
    for a in apps:
        try:
            acl = w.api_client.do("GET", f"/api/2.0/permissions/apps/{a.name}").get(
                "access_control_list", []
            )
        except Exception as e:  # noqa: BLE001
            print(f"perms {a.name}: {e}")
            continue
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
        if alerts:
            from source_scan import emit_alerts

            emit_alerts(spark, cat, sch, alerts)
            print(f"permission drift: {len(alerts)} changes")


def snapshot_deployments(w: WorkspaceClient, spark, cat: str, sch: str, apps: list) -> None:
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
                    "create_time": d.get("create_time"),
                    "state": (d.get("status") or {}).get("state", "?"),
                    "mode": d.get("mode"),
                    "source_code_path": d.get("source_code_path"),
                }
            )
    spark.sql(DEPLOYS_DDL.format(fq=f"`{cat}`.`{sch}`"))
    tbl = f"{cat}.{sch}.app_deployments"
    if rows:
        spark.createDataFrame(rows, schema=spark.table(tbl).schema).write.mode(
            "overwrite"
        ).saveAsTable(tbl)
    print(f"deployments: {len(rows)} rows")


def detect_anomalies(spark, fq: str) -> None:
    rows = spark.sql(f"""
      WITH hourly AS (
        SELECT service_name AS name, date_trunc('hour', time) AS h, count(*) AS req,
               approx_percentile({DUR}, 0.95) AS p95
        FROM {fq}.otel_spans WHERE {SERVER} AND time >= now() - INTERVAL 8 DAYS
        GROUP BY 1, 2),
      base AS (SELECT name, avg(req) AS mu, stddev(req) AS sd, avg(p95) AS mu95, stddev(p95) AS sd95
               FROM hourly WHERE h < date_trunc('hour', now() - INTERVAL 1 HOUR) GROUP BY name),
      cur AS (SELECT name, req, p95 FROM hourly WHERE h = date_trunc('hour', now() - INTERVAL 1 HOUR))
      SELECT c.name, c.req, c.p95, b.mu, b.sd, b.mu95, b.sd95
      FROM cur c JOIN base b ON c.name = b.name
      WHERE (b.sd > 0 AND abs(c.req - b.mu) > 3 * b.sd AND abs(c.req - b.mu) > 10)
         OR (b.sd95 > 0 AND c.p95 > b.mu95 + 3 * b.sd95 AND c.p95 > 500)""").collect()
    if not rows:
        print("anomalies: none")
        return
    recent = {
        (r["rule"], r["app"])
        for r in spark.sql(f"""SELECT DISTINCT rule, app FROM {fq}.alert_events
                               WHERE rule LIKE 'anomaly%' AND ts >= now() - INTERVAL 3 HOURS""").collect()
    }
    alerts = []
    for r in rows:
        if (
            abs(r["req"] - r["mu"]) > 3 * (r["sd"] or 1e9)
            and ("anomaly_traffic", r["name"]) not in recent
        ):
            alerts.append(
                {
                    "rule": "anomaly_traffic",
                    "app": r["name"],
                    "severity": "info",
                    "message": f"traffic {r['req']}/h vs 7d baseline {r['mu']:.0f}±{r['sd']:.0f}",
                    "value": r["req"],
                }
            )
        if (
            r["sd95"]
            and r["p95"]
            and r["p95"] > r["mu95"] + 3 * r["sd95"]
            and ("anomaly_latency", r["name"]) not in recent
        ):
            alerts.append(
                {
                    "rule": "anomaly_latency",
                    "app": r["name"],
                    "severity": "warning",
                    "message": f"p95 {r['p95']:.0f}ms vs 7d baseline {r['mu95']:.0f}±{r['sd95']:.0f}ms",
                    "value": r["p95"],
                }
            )
    if alerts:
        from source_scan import emit_alerts

        emit_alerts(spark, fq.strip("`").split("`.`")[0], fq.strip("`").split("`.`")[1], alerts)
    print(f"anomalies: {len(alerts)} alerts")


def check_budgets(spark, fq: str) -> None:
    rows = spark.sql(f"""
      SELECT c.name, c.budget_usd_month, round(sum(d.dbu_usd), 2) AS mtd
      FROM {fq}.app_config c JOIN {fq}.costs_daily d ON c.name = d.name
      WHERE c.budget_usd_month > 0 AND d.date >= date_trunc('MONTH', current_date())
      GROUP BY 1, 2 HAVING sum(d.dbu_usd) > 0.7 * c.budget_usd_month""").collect()
    recent = {
        r["app"]
        for r in spark.sql(f"""SELECT DISTINCT app FROM {fq}.alert_events
                  WHERE rule = 'budget_burn' AND ts >= now() - INTERVAL 20 HOURS""").collect()
    }
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
        if r["name"] not in recent
    ]
    if alerts:
        from source_scan import emit_alerts

        emit_alerts(spark, fq.strip("`").split("`.`")[0], fq.strip("`").split("`.`")[1], alerts)
    print(f"budgets: {len(alerts)} alerts")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--monitor-app", default="apps-monitor")
    p.add_argument("--jobs-dir", default="")
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"

    w = WorkspaceClient()
    spark = SparkSession.builder.getOrCreate()
    ts = datetime.now(timezone.utc)
    apps = list(w.apps.list())

    spark.sql(CONFIG_DDL.format(fq=fq))
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

    for tbl, comment in TABLE_COMMENTS:
        try:  # platform-created tables may not exist yet / may be owned elsewhere
            spark.sql(f"COMMENT ON TABLE {fq}.`{tbl}` IS '{comment.replace(chr(39), chr(39) * 2)}'")
        except Exception as e:  # noqa: BLE001
            print(f"comment {tbl} skipped: {e}")

    try:
        spark.sql(AUDIT_SQL.format(fq=fq, ws=w.get_workspace_id()))
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
