"""Daily cost rollup per app.

Sources, in order of exactness:
  - App compute $: system.billing.usage (billing_origin_product='APPS', this workspace)
    × system.billing.list_prices  → exact DBUs and USD per app per day.
  - AI usage: gen_ai.* span attributes from our own otel_spans (exact tokens per app),
    plus system.ai_gateway.usage rows when the endpoint has usage tracking enabled.
Gateway tokens are a separate reconciliation signal, never added to span usage.
AI USD stays unset until model pricing is configured.
"""

from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

DDL = """
CREATE TABLE IF NOT EXISTS {fq}.costs_daily (
  date DATE, name STRING,
  dbus DOUBLE, dbu_usd DOUBLE,
  ai_calls LONG, ai_input_tokens LONG, ai_output_tokens LONG, ai_usd DOUBLE,
  computed_at TIMESTAMP, workspace_id STRING, ai_tokens_gateway LONG
) COMMENT 'Per-app daily cost: exact app-compute DBUs/$ from billing + AI tokens from telemetry'"""


AI_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.costs_ai_daily (
  date DATE, name STRING, model STRING, ai_calls LONG, in_t LONG, out_t LONG,
  workspace_id STRING
) CLUSTER BY (name, date)
COMMENT 'Billable model calls and tokens per app/model/day; retained for later model pricing'"""


def ai_daily_sql(fq: str, days: int) -> str:
    from telemetry_sql import BILLABLE, IN_TOK, OUT_TOK, enriched_spans

    return f"""{enriched_spans(fq, f"date >= current_date() - {days}")}
      SELECT date, service_name AS name, coalesce(model, '(unknown)') AS model,
             count(*) AS ai_calls, sum({IN_TOK}) AS in_t, sum({OUT_TOK}) AS out_t,
             :ws AS workspace_id
      FROM marked WHERE (model IS NOT NULL OR billable = true) AND {BILLABLE}
      GROUP BY 1, 2, 3"""


def main() -> None:
    from schema_utils import ensure_columns, workspace_column

    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--jobs-dir", default="", help="workspace path of the jobs dir (import path)")
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"

    spark = SparkSession.builder.getOrCreate()
    spark.sql(DDL.format(fq=fq))
    from databricks.sdk import WorkspaceClient

    ws_id = str(int(WorkspaceClient().get_workspace_id()))
    print(f"workspace_id={ws_id}, window={args.days}d")
    ensure_columns(spark, f"{fq}.costs_daily", {"ai_tokens_gateway": "LONG"})
    workspace_column(spark, f"{fq}.costs_daily", ws_id)
    spark.sql(AI_DDL.format(fq=fq))

    spark.sql(f"""
      CREATE OR REPLACE TEMP VIEW app_dbu AS
      SELECT u.usage_date AS date,
             u.usage_metadata.app_name AS name,
             sum(u.usage_quantity) AS dbus,
             sum(u.usage_quantity * coalesce(p.pricing.effective_list.default, p.pricing.default)) AS dbu_usd
      FROM system.billing.usage u
      LEFT JOIN system.billing.list_prices p
        ON u.sku_name = p.sku_name AND u.cloud = p.cloud AND p.currency_code = 'USD'
       AND u.usage_end_time >= p.price_start_time
       AND (p.price_end_time IS NULL OR u.usage_end_time < p.price_end_time)
      WHERE u.billing_origin_product = 'APPS'
        AND u.workspace_id = '{ws_id}'
        AND u.usage_date >= current_date() - {args.days}
        AND u.usage_metadata.app_name IS NOT NULL
      GROUP BY 1, 2""")

    spark.sql(
        f"""MERGE INTO {fq}.costs_ai_daily t USING ({ai_daily_sql(fq, args.days)}) s
        ON t.date = s.date AND t.name = s.name AND t.model = s.model
          AND t.workspace_id = s.workspace_id
        WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *
        WHEN NOT MATCHED BY SOURCE AND t.workspace_id = :ws
          AND t.date >= current_date() - {args.days} THEN DELETE""",
        args={"ws": ws_id},
    )
    spark.sql(f"""
      CREATE OR REPLACE TEMP VIEW app_ai AS
      SELECT date, name, sum(ai_calls) AS ai_calls, sum(in_t) AS ai_input_tokens,
             sum(out_t) AS ai_output_tokens
      FROM {fq}.costs_ai_daily
      WHERE workspace_id = '{ws_id}' AND date >= current_date() - {args.days}
      GROUP BY 1, 2""")

    # Resolve requester IDs against a deduplicated inventory; never store requester text.
    spark.sql(f"""
      CREATE OR REPLACE TEMP VIEW app_gw AS
      WITH principals AS (
        SELECT sp_client_id, max_by(name, snapshot_ts) AS name
        FROM {fq}.apps_inventory WHERE sp_client_id IS NOT NULL GROUP BY sp_client_id)
      SELECT date(g.event_time) AS date,
             coalesce(nullif(g.request_tags['app'], ''), p.name, '(untagged)') AS name,
             sum(coalesce(g.input_tokens, 0) + coalesce(g.output_tokens, 0)) AS ai_tokens_gateway
      FROM system.ai_gateway.usage g LEFT JOIN principals p ON g.requester = p.sp_client_id
      WHERE g.workspace_id = '{ws_id}' AND date(g.event_time) >= current_date() - {args.days}
      GROUP BY 1, 2""")

    spark.sql(
        f"""
      MERGE INTO {fq}.costs_daily t
      USING (
        SELECT coalesce(d.date, a.date, g.date) AS date,
               coalesce(d.name, a.name, g.name) AS name,
               d.dbus, d.dbu_usd,
               coalesce(a.ai_calls, 0) AS ai_calls,
               coalesce(a.ai_input_tokens, 0) AS ai_input_tokens,
               coalesce(a.ai_output_tokens, 0) AS ai_output_tokens,
               CAST(NULL AS DOUBLE) AS ai_usd,
               current_timestamp() AS computed_at, :ws AS workspace_id,
               g.ai_tokens_gateway
        FROM app_dbu d
        FULL OUTER JOIN app_ai a ON d.date = a.date AND d.name = a.name
        FULL OUTER JOIN app_gw g ON coalesce(d.date, a.date) = g.date AND coalesce(d.name, a.name) = g.name
      ) s
      ON t.date = s.date AND t.name = s.name AND t.workspace_id = s.workspace_id
      WHEN MATCHED THEN UPDATE SET *
      WHEN NOT MATCHED THEN INSERT *
      WHEN NOT MATCHED BY SOURCE AND t.workspace_id = :ws
        AND t.date >= current_date() - {args.days} THEN DELETE""",
        args={"ws": ws_id},
    )

    n = spark.sql(f"SELECT count(*) c FROM {fq}.costs_daily").collect()[0]["c"]
    print(f"costs_daily rows: {n}")

    # cost spike: yesterday's $ more than 2× the prior-week median and above $1
    spikes = spark.sql(f"""
      WITH base AS (SELECT name, date, dbu_usd FROM {fq}.costs_daily WHERE dbu_usd IS NOT NULL)
      SELECT b.name, b.dbu_usd, m.med
      FROM base b
      JOIN (SELECT name, percentile_approx(dbu_usd, 0.5) med FROM base
            WHERE date BETWEEN current_date() - 8 AND current_date() - 2 GROUP BY name) m
        ON b.name = m.name
      WHERE b.date = current_date() - 1 AND b.dbu_usd > 1 AND b.dbu_usd > 2 * m.med""").collect()
    from source_scan import emit_alerts

    emit_alerts(
        spark,
        args.catalog,
        args.schema,
        [
            {
                "rule": "cost_spike",
                "app": r["name"],
                "severity": "warning",
                "message": f"daily compute ${r['dbu_usd']:.2f} vs prior-week median ${r['med']:.2f}",
                "value": r["dbu_usd"],
            }
            for r in spikes
        ],
        owned_rules=("cost_spike",),
    )
    spark.sql(f"""CREATE OR REPLACE VIEW {fq}.v_cost_summary
        COMMENT 'Fleet cost KPIs: today + last 7 days' AS
        SELECT sum(CASE WHEN date = current_date() THEN dbu_usd END) AS usd_today,
               sum(CASE WHEN date >= current_date() - 7 THEN dbu_usd END) AS usd_7d,
               sum(CASE WHEN date = current_date() THEN ai_input_tokens + ai_output_tokens END) AS tokens_today,
               sum(CASE WHEN date >= current_date() - 7 THEN ai_input_tokens + ai_output_tokens END) AS tokens_7d
        FROM {fq}.costs_daily""")
    print("done")


if __name__ == "__main__":
    import sys

    _jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
    if _jobs_dir:
        sys.path.append(_jobs_dir)
    main()
