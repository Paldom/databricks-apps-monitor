"""Monitor-owned compute, warehouse share, model usage and Delta storage, daily."""

from __future__ import annotations

import argparse
import math

STORAGE_TABLES = (
    "otel_spans",
    "otel_logs",
    "otel_metrics",
    "agg_app_daily",
    "agg_app_hourly",
    "agg_genai_daily",
    "costs_daily",
    "costs_ai_daily",
    "sli_5m",
    "slo_specs",
    "alert_events",
    "alert_mutes",
    "telemetry_health_samples",
    "monitor_model_usage",
    "monitor_cost_daily",
    "monitor_storage_daily",
    "apps_inventory",
    "monitor_audit",
    "llm_reviews",
    "monitor_quality",
    "code_scans",
    "scan_findings",
    "app_config",
    "app_permissions",
    "app_deployments",
    "synthetic_runs",
)


def cost_share(monitor: float | None, fleet: float | None) -> float | None:
    if monitor is None or fleet is None or fleet <= 0:
        return None
    return 100 * monitor / fleet


def billing_sql() -> str:
    return """WITH priced AS (
      SELECT u.*, u.usage_quantity * p.pricing.default AS usd
      FROM system.billing.usage u LEFT JOIN system.billing.list_prices p
        ON u.sku_name = p.sku_name AND u.cloud = p.cloud AND u.usage_unit = p.usage_unit
        AND p.currency_code = 'USD' AND u.usage_end_time >= p.price_start_time
        AND (p.price_end_time IS NULL OR u.usage_end_time < p.price_end_time)
      WHERE u.workspace_id = :ws AND u.usage_date BETWEEN current_date() - 30 AND current_date() - 1)
    SELECT usage_date AS date,
      CASE WHEN billing_origin_product = 'APPS' AND usage_metadata.app_name = :app
        THEN 'app' ELSE 'jobs' END AS component,
      CASE WHEN count_if(usd IS NULL) = 0 THEN sum(usd) END AS usd,
      'billing usage x USD list price' AS basis
    FROM priced WHERE (billing_origin_product = 'APPS' AND usage_metadata.app_name = :app)
      OR array_contains(split(:job_ids, ','), cast(usage_metadata.job_id AS STRING))
    GROUP BY 1, 2"""


def warehouse_sql() -> str:
    return """WITH durations AS (
      SELECT date(start_time) AS date, compute.warehouse_id AS warehouse_id,
        sum(CASE WHEN executed_by = :sp OR cast(executed_by_user_id AS STRING) = :sp_id
          THEN total_duration_ms ELSE 0 END) AS monitor_ms,
        sum(total_duration_ms) AS total_ms
      FROM system.query.history WHERE workspace_id = :ws AND compute.warehouse_id IS NOT NULL
        AND start_time >= current_date() - 30 AND start_time < current_date()
      GROUP BY 1, 2), billing AS (
      SELECT u.usage_date AS date, u.usage_metadata.warehouse_id AS warehouse_id,
        CASE WHEN count_if(p.pricing.default IS NULL) = 0
          THEN sum(u.usage_quantity * p.pricing.default) END AS usd
      FROM system.billing.usage u LEFT JOIN system.billing.list_prices p
        ON u.sku_name = p.sku_name AND u.cloud = p.cloud AND u.usage_unit = p.usage_unit
        AND p.currency_code = 'USD' AND u.usage_end_time >= p.price_start_time
        AND (p.price_end_time IS NULL OR u.usage_end_time < p.price_end_time)
      WHERE u.workspace_id = :ws AND u.usage_metadata.warehouse_id IS NOT NULL
        AND u.usage_date BETWEEN current_date() - 30 AND current_date() - 1 GROUP BY 1, 2)
    SELECT d.date, 'warehouse' AS component,
      CASE WHEN count_if(b.usd IS NULL) = 0 THEN sum(b.usd * d.monitor_ms / nullif(d.total_ms, 0)) END AS usd,
      'estimate: monitor SP query duration / all warehouse query duration x billed USD' AS basis
    FROM durations d LEFT JOIN billing b ON d.date = b.date AND d.warehouse_id = b.warehouse_id
    WHERE d.monitor_ms > 0 GROUP BY d.date"""


def model_sql(fq: str, prices: bool) -> str:
    if prices:
        priced = f"""SELECT u.*, p.input_usd_per_mtok, p.output_usd_per_mtok,
          row_number() OVER (PARTITION BY u.id ORDER BY p.effective_from DESC) AS rn
          FROM {fq}.monitor_model_usage u LEFT JOIN {fq}.model_prices p
            ON u.model = p.model AND p.effective_from <= date(u.ts)
            AND p.workspace_id = u.workspace_id
          WHERE u.workspace_id = :ws AND u.ts >= current_date() - 30 AND u.ts < current_date()"""
        price = "(input_tokens * input_usd_per_mtok + output_tokens * output_usd_per_mtok) / 1e6"
    else:
        priced = f"""SELECT *, 1 AS rn FROM {fq}.monitor_model_usage
          WHERE workspace_id = :ws AND ts >= current_date() - 30 AND ts < current_date()"""
        price = "cast(NULL AS DOUBLE)"
    return f"""WITH priced AS ({priced}), calls AS (
      SELECT *, {price} AS usd FROM priced WHERE rn = 1)
      SELECT date(ts) AS date, component,
        CASE WHEN count_if(usd IS NULL) = 0 THEN sum(usd) END AS usd,
        CASE WHEN count_if(usd IS NULL) > 0 THEN 'final response tokens; USD unpriced or usage unavailable'
          ELSE 'estimate: final response tokens x effective model list price' END AS basis,
        CASE WHEN count_if(input_tokens IS NULL) = 0 THEN sum(input_tokens) END AS input_tokens,
        CASE WHEN count_if(output_tokens IS NULL) = 0 THEN sum(output_tokens) END AS output_tokens
      FROM calls GROUP BY 1, 2"""


def merge_cost(spark, fq: str, ws: str, rows: list[dict]) -> None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    full = [
        {
            **r,
            "usd": float(r["usd"]) if r["usd"] is not None else None,
            "input_tokens": r.get("input_tokens"),
            "output_tokens": r.get("output_tokens"),
            "workspace_id": ws,
            "computed_at": now,
        }
        for r in rows
    ]
    spark.createDataFrame(
        full, schema=spark.table(f"{fq}.monitor_cost_daily").schema
    ).createOrReplaceTempView("monitor_cost_batch")
    spark.sql(f"""MERGE INTO {fq}.monitor_cost_daily t USING monitor_cost_batch s
      ON t.workspace_id = s.workspace_id AND t.date = s.date AND t.component = s.component
      WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *""")


def main() -> None:
    from datetime import datetime, timedelta, timezone

    from databricks.sdk import WorkspaceClient
    from ops_tables import ensure_ops_tables
    from pyspark.sql import SparkSession

    from source_scan import emit_alerts

    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--monitor-app", default="apps-monitor")
    p.add_argument("--job-ids", required=True)
    p.add_argument("--cost-pct", type=float, default=10)
    p.add_argument("--jobs-dir", default="")
    args = p.parse_args()
    if not math.isfinite(args.cost_pct) or args.cost_pct <= 0:
        raise ValueError("cost-pct must be positive and finite")
    if not all(j.isdigit() for j in args.job_ids.split(",")):
        raise ValueError("job-ids must be comma-separated numeric IDs")
    fq = f"`{args.catalog}`.`{args.schema}`"
    w, spark = WorkspaceClient(), SparkSession.builder.getOrCreate()
    ws = str(w.get_workspace_id())
    ensure_ops_tables(spark, fq)
    monitor = w.apps.get(args.monitor_app)
    sp = monitor.service_principal_client_id
    if not sp:
        raise ValueError("monitor service principal is unavailable")
    today = datetime.now(timezone.utc).date()
    results = []
    sources = (
        (
            ("app", "jobs"),
            billing_sql(),
            {"ws": ws, "app": args.monitor_app, "job_ids": args.job_ids},
        ),
        (
            ("warehouse",),
            warehouse_sql(),
            {"ws": ws, "sp": sp, "sp_id": str(getattr(monitor, "service_principal_id", "") or "")},
        ),
        (
            ("review", "eval"),
            model_sql(fq, spark.catalog.tableExists(f"{fq}.model_prices")),
            {"ws": ws},
        ),
    )
    for components, sql, params in sources:
        try:
            rows = [r.asDict() for r in spark.sql(sql, args=params).collect()]
            found = {(r["date"], r["component"]) for r in rows}
            results.extend(rows)
            for day in range(1, 31):
                for component in components:
                    date = today - timedelta(days=day)
                    if (date, component) not in found:
                        results.append(
                            {
                                "date": date,
                                "component": component,
                                "usd": 0.0,
                                "basis": "no attributed usage in available source; billing can lag",
                            }
                        )
        except Exception as e:  # noqa: BLE001 — permission gaps must remain visible as unknown
            print(f"{components} unavailable: {e}")
            for component in components:
                results.append(
                    {
                        "date": today - timedelta(days=1),
                        "component": component,
                        "usd": None,
                        "basis": f"unavailable: {type(e).__name__}",
                    }
                )
    merge_cost(spark, fq, ws, results)
    for table in STORAGE_TABLES:
        try:
            detail = spark.sql(f"DESCRIBE DETAIL {fq}.`{table}`").collect()[0]
            size = int(detail["sizeInBytes"])
        except Exception as e:  # noqa: BLE001 — missing table/permission is unknown, not zero bytes
            print(f"storage {table} unavailable: {e}")
            size = None
        spark.sql(
            f"""MERGE INTO {fq}.monitor_storage_daily t USING
          (SELECT :ws AS workspace_id, current_date() AS date, :table AS table_name,
            :size AS size_bytes, now() AS computed_at) s
          ON t.workspace_id = s.workspace_id AND t.date = s.date AND t.table_name = s.table_name
          WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *""",
            args={"ws": ws, "table": table, "size": size},
        )
    yesterday = [r for r in results if r["date"] == today - timedelta(days=1)]
    known = sum(float(r["usd"]) for r in yesterday if r["usd"] is not None)
    complete = all(r["usd"] is not None for r in yesterday)
    fleet = spark.sql(
        f"""SELECT sum(coalesce(dbu_usd, 0) + coalesce(ai_usd, 0)) AS usd
      FROM {fq}.costs_daily WHERE workspace_id = :ws AND name != :app
        AND date = current_date() - 1""",
        args={"ws": ws, "app": args.monitor_app},
    ).collect()[0]["usd"]
    pct = cost_share(known, float(fleet) if fleet is not None else None)
    firing = pct is not None and pct > args.cost_pct
    emit_alerts(
        spark,
        args.catalog,
        args.schema,
        [
            {
                "rule": "monitor_cost_ratio",
                "app": args.monitor_app,
                "severity": "warning",
                "value": pct,
                "message": f"monitor known cost ${known:.2f} is {pct:.1f}% of fleet billed/estimated cost "
                f"(limit {args.cost_pct:g}%; unpriced tokens excluded)",
            }
        ]
        if firing
        else [],
        owned_rules=("monitor_cost_ratio",),
        evaluated_apps={args.monitor_app} if firing or (complete and pct is not None) else set(),
    )


if __name__ == "__main__":
    import sys

    _jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
    if _jobs_dir:
        sys.path.append(_jobs_dir)
    main()
