"""Telemetry quality view and conservative, durable orphan-alert observations."""

from datetime import datetime, timedelta, timezone
from math import isfinite


def sampler_ratio(config: dict | None) -> float | None:
    env = {v.get("name"): v.get("value") for v in (config or {}).get("env", [])}
    if env.get("OTEL_TRACES_SAMPLER") in ("always_on", "parentbased_always_on"):
        return 1.0
    if env.get("OTEL_TRACES_SAMPLER") in ("always_off", "parentbased_always_off"):
        return 0.0
    try:
        ratio = float(env["OTEL_TRACES_SAMPLER_ARG"])
        return ratio if isfinite(ratio) and 0 <= ratio <= 1 else None
    except (KeyError, TypeError, ValueError):
        return None


def sustained_orphans(samples: list[dict], now: datetime) -> bool | None:
    """A missing observation is unknown; require every quarter-hour for six hours."""
    observed = {}
    for sample in samples:
        bucket = sample["bucket"]
        if bucket.tzinfo is None:
            bucket = bucket.replace(tzinfo=timezone.utc)
        observed[bucket] = sample["orphan_ratio"]
    end = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0)
    values = [observed.get(end - timedelta(minutes=15 * i)) for i in range(25)]
    if any(v is not None and v <= 0.2 for v in values):
        return False
    if any(v is None for v in values):
        return None
    return all(v > 0.2 for v in values)


def health_sql(fq: str) -> str:
    from telemetry_sql import NOT_PROBE, SERVER, vg

    return f"""CREATE OR REPLACE VIEW {fq}.v_telemetry_health
      COMMENT 'Telemetry freshness, envelope and semconv coverage; orphan ratios are suspected loss'
      AS WITH recent AS (
        SELECT * FROM {fq}.otel_spans
        WHERE date >= current_date() - 1 AND time >= now() - INTERVAL 24 HOURS),
      parents AS (SELECT DISTINCT trace_id, span_id FROM recent),
      orphans AS (
        SELECT s.service_name AS name,
          avg(CASE WHEN s.parent_span_id IS NOT NULL AND s.parent_span_id != ''
            AND s.parent_span_id NOT RLIKE '^0+$' AND p.span_id IS NULL THEN 1.0 ELSE 0 END)
            AS orphan_ratio_24h
        FROM recent s LEFT JOIN parents p
          ON s.trace_id = p.trace_id AND s.parent_span_id = p.span_id GROUP BY 1),
      envelope AS (
        SELECT service_name AS name,
          avg(CASE WHEN nullif({vg("app.client_request_id")}, '') IS NOT NULL THEN 1.0 ELSE 0 END)
            AS envelope_coverage,
          avg(CASE WHEN {vg("http.status_code", "int")} IS NOT NULL
             AND {vg("http.response.status_code", "int")} IS NULL THEN 1.0 ELSE 0 END) AS semconv_legacy_only,
          avg(CASE WHEN {vg("http.response.status_code", "int")} IS NOT NULL
             AND {vg("http.status_code", "int")} IS NULL THEN 1.0 ELSE 0 END) AS semconv_stable_only,
          avg(CASE WHEN {vg("http.status_code", "int")} IS NOT NULL
             AND {vg("http.response.status_code", "int")} IS NOT NULL THEN 1.0 ELSE 0 END) AS semconv_both
        FROM recent WHERE {SERVER} AND {NOT_PROBE} GROUP BY 1),
      spans AS (SELECT service_name AS name, max(time) AS last_span_at FROM {fq}.otel_spans GROUP BY 1),
      logs AS (SELECT service_name AS name, max(time) AS last_log_at FROM {fq}.otel_logs GROUP BY 1),
      metrics AS (SELECT service_name AS name, max(time) AS last_metric_at FROM {fq}.otel_metrics GROUP BY 1),
      costs AS (
        SELECT workspace_id, name, max_by(ai_tokens_gateway, date) AS gateway_tokens,
          max_by(ai_input_tokens + ai_output_tokens, date) AS otel_tokens, max(date) AS token_date
        FROM {fq}.costs_daily WHERE date < current_date() GROUP BY 1, 2)
      SELECT a.workspace_id, a.name, a.app_state, s.last_span_at, l.last_log_at, m.last_metric_at,
        e.envelope_coverage, o.orphan_ratio_24h, e.semconv_legacy_only, e.semconv_stable_only,
        e.semconv_both, to_json(named_struct('legacy_only', e.semconv_legacy_only,
          'stable_only', e.semconv_stable_only, 'both', e.semconv_both)) AS semconv_mix,
        c.gateway_tokens, c.otel_tokens, c.gateway_tokens - c.otel_tokens AS gateway_vs_otel_tokens,
        c.token_date, a.sampler_ratio,
        CASE WHEN s.last_span_at IS NULL THEN 'unknown'
          WHEN a.app_state = 'RUNNING' AND (s.last_span_at < now() - INTERVAL 30 MINUTES
            OR l.last_log_at IS NULL OR l.last_log_at < now() - INTERVAL 30 MINUTES
            OR m.last_metric_at IS NULL OR m.last_metric_at < now() - INTERVAL 30 MINUTES)
            THEN 'stale'
          WHEN o.orphan_ratio_24h > 0.2 OR e.envelope_coverage < 0.95 THEN 'check'
          ELSE 'ok' END AS quality
      FROM {fq}.v_apps_latest a
      LEFT JOIN spans s ON a.name = s.name LEFT JOIN logs l ON a.name = l.name
      LEFT JOIN metrics m ON a.name = m.name LEFT JOIN envelope e ON a.name = e.name
      LEFT JOIN orphans o ON a.name = o.name
      LEFT JOIN costs c ON a.name = c.name AND a.workspace_id = c.workspace_id"""


def check_telemetry(spark, fq: str, ws: str, catalog: str, schema: str) -> None:
    from schema_utils import ensure_costs_table

    from source_scan import emit_alerts

    ensure_costs_table(spark, fq, ws)
    spark.sql(health_sql(fq))
    spark.sql(
        f"""MERGE INTO {fq}.telemetry_health_samples t USING (
      SELECT workspace_id, name, window(now(), '15 minutes').start AS bucket,
        orphan_ratio_24h AS orphan_ratio FROM {fq}.v_telemetry_health WHERE workspace_id = :ws) s
      ON t.workspace_id = s.workspace_id AND t.name = s.name AND t.bucket = s.bucket
      WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *""",
        args={"ws": ws},
    )
    samples = spark.sql(
        f"""SELECT name, bucket, orphan_ratio FROM {fq}.telemetry_health_samples
      WHERE workspace_id = :ws AND bucket >= now() - INTERVAL 7 HOURS""",
        args={"ws": ws},
    ).collect()
    by_app: dict[str, list] = {}
    for r in samples:
        by_app.setdefault(r["name"], []).append(r.asDict())
    now = datetime.now(timezone.utc)
    alerts, evaluated = [], set()
    for name, observations in by_app.items():
        condition = sustained_orphans(observations, now)
        if condition is None:
            continue
        evaluated.add(name)
        if condition:
            alerts.append(
                {
                    "rule": "telemetry_orphans",
                    "app": name,
                    "severity": "warning",
                    "value": 100
                    * min(r["orphan_ratio"] for r in observations if r["orphan_ratio"] is not None),
                    "message": "suspected orphan spans >20% for six hours; sampling/late data can also cause this",
                }
            )
    emit_alerts(
        spark, catalog, schema, alerts, owned_rules=("telemetry_orphans",), evaluated_apps=evaluated
    )
    spark.sql(
        f"DELETE FROM {fq}.telemetry_health_samples WHERE workspace_id = :ws "
        "AND bucket < now() - INTERVAL 8 DAYS",
        args={"ws": ws},
    )
