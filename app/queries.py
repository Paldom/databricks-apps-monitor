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
IS_ERROR = "coalesce(status.code, '') ILIKE '%error%'"
# monitor probes hit /healthz every minute — synthetic traffic stays out of request metrics
NOT_PROBE = "name NOT ILIKE '%healthz%'"
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
    cols = [c.name for c in resp.manifest.schema.columns]
    rows = [dict(zip(cols, r, strict=False)) for r in (resp.result.data_array or [])]
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
  SELECT coalesce({vg("http.route")}, name) AS route,
         count(*) AS requests,
         sum(CASE WHEN {IS_ERROR} THEN 1 ELSE 0 END) AS errors,
         round(avg({DUR_MS}), 1) AS avg_ms,
         round(approx_percentile({DUR_MS}, 0.95), 1) AS p95_ms
  FROM {t("otel_spans")}
  WHERE service_name = :app AND {IS_SERVER} AND {NOT_PROBE} AND time >= :since::timestamp
  GROUP BY 1 ORDER BY requests DESC LIMIT 25"""

ERROR_SPANS = f"""
  SELECT time, trace_id, name, round({DUR_MS}, 1) AS duration_ms,
         status.message AS message, {vg("http.status_code", "int")} AS http_status
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
         coalesce({vg("http.route")}, '') AS route
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
         CASE WHEN {IS_ERROR.replace("status.code", "s.status.code")} THEN 'error' ELSE 'ok' END AS status,
         replace(coalesce(variant_get(s.attributes, '$["mlflow.spanType"]', 'string'), ''), '"', '') AS span_type,
         variant_get(s.attributes, '$["gen_ai.usage.input_tokens"]', 'long') AS in_tokens,
         variant_get(s.attributes, '$["gen_ai.usage.output_tokens"]', 'long') AS out_tokens
  FROM {t("otel_spans")} s JOIN tids ON s.trace_id = tids.trace_id
  WHERE s.time >= now() - INTERVAL 7 DAYS
  ORDER BY s.start_time_unix_nano LIMIT 300"""

TRACE_LOGS = f"""
  SELECT time, coalesce(severity_text, 'INFO') AS severity, cast(body AS string) AS body, span_id
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
  SELECT date, dbus, dbu_usd, ai_calls, ai_input_tokens, ai_output_tokens, ai_usd
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
  SELECT run_ts, journey, ok, status_code, latency_ms, detail, artifact
  FROM {t("synthetic_runs")} WHERE app = :app AND kind = 'playwright'
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
  SELECT ts, rule, severity, message, value, state, source FROM {t("alert_events")}
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
  SELECT tags_json, budget_usd_month, auto_stop, idle_hours, updated_at, updated_by
  FROM {t("app_config")} WHERE name = :app"""

CONFIGS_ALL = f"SELECT name, tags_json, budget_usd_month, auto_stop FROM {t('app_config')}"

CONFIG_UPSERT = f"""
  MERGE INTO {t("app_config")} tgt USING (SELECT :app AS name) s ON tgt.name = s.name
  WHEN MATCHED THEN UPDATE SET tags_json = :tags, budget_usd_month = :budget::double,
       auto_stop = :auto_stop, idle_hours = :idle::int, updated_at = current_timestamp(), updated_by = :who
  WHEN NOT MATCHED THEN INSERT (name, tags_json, budget_usd_month, auto_stop, idle_hours, updated_at, updated_by)
  VALUES (:app, :tags, :budget::double, :auto_stop, :idle::int, current_timestamp(), :who)"""

MTD_BY_APP = f"""
  SELECT name, round(sum(dbu_usd), 2) AS mtd_usd
  FROM {t("costs_daily")} WHERE date >= date_trunc('MONTH', current_date())
  GROUP BY name"""

CHARGEBACK = f"""
  SELECT team, cost_center, count(DISTINCT name) AS apps, round(sum(mtd_usd), 2) AS mtd_usd,
         sum(mtd_tokens) AS mtd_tokens, sum(mtd_ai_calls) AS ai_calls
  FROM {t("v_chargeback")} GROUP BY 1, 2 ORDER BY mtd_usd DESC NULLS LAST"""

USAGE_FLEET = f"""
  SELECT name, sum(requests) AS requests_7d, max(users) AS peak_dau, sum(sessions) AS sessions_7d
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
      WHEN msg RLIKE '429|rate.?limit' THEN 'rate_limit'
      WHEN msg RLIKE 'timeout|timed.?out|deadline' THEN 'timeout'
      WHEN msg RLIKE 'content.?(filter|policy)|moderation|blocked' THEN 'content_policy'
      WHEN msg RLIKE 'schema|validation|json|pydantic' THEN 'schema_validation'
      ELSE 'other' END AS category,
    count(*) AS errors, max(time) AS last_seen, any_value(substr(msg, 1, 200)) AS sample
  FROM (SELECT time, lower(coalesce(status.message,
                variant_get(attributes, '$["error.type"]', 'string'), '')) AS msg
        FROM {t("otel_spans")}
        WHERE service_name = :app AND {_GENAI} AND coalesce(status.code, '') ILIKE '%error%'
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
  INSERT INTO {t("alert_events")} VALUES
  (:ts::timestamp, :rule, :app, :severity, :message, :value::double, :state, 'monitor')"""

RECENT_ALERTS = f"""
  SELECT ts, rule, app, severity, message, value, state, source
  FROM {t("alert_events")} WHERE ts >= current_timestamp() - INTERVAL 3 DAYS
  ORDER BY ts DESC LIMIT 100"""
