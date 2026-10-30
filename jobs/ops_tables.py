"""Operations tables are bootstrapped by inventory before SP grants."""


def ensure_ops_tables(spark, fq: str) -> None:
    definitions = {
        "alert_mutes": (
            "id STRING, app STRING, rule STRING, starts_at TIMESTAMP, ends_at TIMESTAMP, "
            "reason STRING, created_by STRING, created_at TIMESTAMP",
            "Notification maintenance windows; evaluation and event persistence continue",
        ),
        "slo_specs": (
            "name STRING, slo STRING, sli STRING, target DOUBLE, threshold_ms DOUBLE, "
            "window_days INT, route_filter STRING, updated_by STRING, updated_at TIMESTAMP, "
            "revision STRING",
            "Per-app availability or latency objectives; revision isolates changed definitions",
        ),
        "sli_5m": (
            "name STRING, slo STRING, revision STRING, bucket TIMESTAMP, good BIGINT, total BIGINT",
            "Five-minute real-traffic SLI counts from sampled server spans",
        ),
        "telemetry_health_samples": (
            "name STRING, bucket TIMESTAMP, orphan_ratio DOUBLE",
            "Quarter-hour observations of suspected orphan spans for sustained-condition alerts",
        ),
        "monitor_cost_daily": (
            "date DATE, component STRING, usd DOUBLE, basis STRING, input_tokens BIGINT, "
            "output_tokens BIGINT, computed_at TIMESTAMP",
            "Monitor cost components; null USD means unavailable or unpriced",
        ),
        "monitor_storage_daily": (
            "date DATE, table_name STRING, size_bytes BIGINT, computed_at TIMESTAMP",
            "Daily physical Delta storage size for monitor telemetry and gold tables",
        ),
        "monitor_model_usage": (
            "id STRING, ts TIMESTAMP, component STRING, model STRING, input_tokens BIGINT, "
            "output_tokens BIGINT",
            "Final FMAPI response usage for monitor reviews and evals, including unparseable output",
        ),
        "monitor_audit": (
            "event_time TIMESTAMP, user STRING, service_name STRING, action_name STRING, "
            "app STRING, status_code BIGINT, params_json STRING",
            "Platform Apps audit and durable monitor administrator actions",
        ),
    }
    for name, (columns, comment) in definitions.items():
        cluster = " CLUSTER BY (name, bucket)" if name == "sli_5m" else ""
        spark.sql(f"""CREATE TABLE IF NOT EXISTS {fq}.{name} (
          {columns}, workspace_id STRING){cluster} COMMENT '{comment}'""")
