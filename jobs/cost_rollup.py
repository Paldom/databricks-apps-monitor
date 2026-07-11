"""Daily cost rollup per app.

Sources, in order of exactness:
  - App compute $: system.billing.usage (billing_origin_product='APPS', this workspace)
    × system.billing.list_prices  → exact DBUs and USD per app per day.
  - AI usage: gen_ai.* span attributes from our own otel_spans (exact tokens per app),
    plus system.ai_gateway.usage rows when the endpoint has usage tracking enabled.
AI USD stays unset unless gateway usage rows exist (pay-per-token FMAPI endpoints don't
log to ai_gateway.usage by default and their $ can't be attributed per app honestly).
"""

from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

DDL = """
CREATE TABLE IF NOT EXISTS {fq}.costs_daily (
  date DATE, name STRING,
  dbus DOUBLE, dbu_usd DOUBLE,
  ai_calls LONG, ai_input_tokens LONG, ai_output_tokens LONG, ai_usd DOUBLE,
  computed_at TIMESTAMP
) COMMENT 'Per-app daily cost: exact app-compute DBUs/$ from billing + AI tokens from telemetry'"""


def main() -> None:
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

    ws_id = str(WorkspaceClient().get_workspace_id())
    print(f"workspace_id={ws_id}, window={args.days}d")

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

    # exact per-app AI tokens from our own telemetry (gen_ai.* span attributes)
    spark.sql(f"""
      CREATE OR REPLACE TEMP VIEW app_ai AS
      SELECT date, service_name AS name,
             count(*) AS ai_calls,
             sum(coalesce(variant_get(attributes, '$["gen_ai.usage.input_tokens"]', 'long'), 0)) AS ai_input_tokens,
             sum(coalesce(variant_get(attributes, '$["gen_ai.usage.output_tokens"]', 'long'), 0)) AS ai_output_tokens
      FROM {fq}.otel_spans
      WHERE variant_get(attributes, '$["gen_ai.request.model"]', 'string') IS NOT NULL
        AND date >= current_date() - {args.days}
      GROUP BY 1, 2""")

    # gateway usage (exact $ impossible without per-token price; keep tokens if rows exist)
    spark.sql(f"""
      CREATE OR REPLACE TEMP VIEW app_gw AS
      SELECT date(event_time) AS date,
             coalesce(request_tags['app'], requester) AS name,
             count(*) AS calls, sum(input_tokens) AS in_t, sum(output_tokens) AS out_t
      FROM system.ai_gateway.usage
      WHERE workspace_id = '{ws_id}' AND event_time >= current_timestamp() - INTERVAL {args.days} DAYS
      GROUP BY 1, 2""")

    spark.sql(f"""
      MERGE INTO {fq}.costs_daily t
      USING (
        SELECT coalesce(d.date, a.date, g.date) AS date,
               coalesce(d.name, a.name, g.name) AS name,
               d.dbus, d.dbu_usd,
               greatest(coalesce(a.ai_calls, 0), coalesce(g.calls, 0)) AS ai_calls,
               greatest(coalesce(a.ai_input_tokens, 0), coalesce(g.in_t, 0)) AS ai_input_tokens,
               greatest(coalesce(a.ai_output_tokens, 0), coalesce(g.out_t, 0)) AS ai_output_tokens,
               CAST(NULL AS DOUBLE) AS ai_usd,
               current_timestamp() AS computed_at
        FROM app_dbu d
        FULL OUTER JOIN app_ai a ON d.date = a.date AND d.name = a.name
        FULL OUTER JOIN app_gw g ON coalesce(d.date, a.date) = g.date AND coalesce(d.name, a.name) = g.name
      ) s
      ON t.date = s.date AND t.name = s.name
      WHEN MATCHED THEN UPDATE SET *
      WHEN NOT MATCHED THEN INSERT *""")

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
    if spikes:
        import sys as _sys

        _jobs_dir = next((a.split("=", 1)[1] for a in _sys.argv if a.startswith("--jobs-dir=")), "")
        if _jobs_dir:
            _sys.path.append(_jobs_dir)
        try:
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
            )
        except Exception as e:  # noqa: BLE001
            print(f"spike alert emit failed: {e}")
    spark.sql(f"""CREATE OR REPLACE VIEW {fq}.v_cost_summary
        COMMENT 'Fleet cost KPIs: today + last 7 days' AS
        SELECT sum(CASE WHEN date = current_date() THEN dbu_usd END) AS usd_today,
               sum(CASE WHEN date >= current_date() - 7 THEN dbu_usd END) AS usd_7d,
               sum(CASE WHEN date = current_date() THEN ai_input_tokens + ai_output_tokens END) AS tokens_today,
               sum(CASE WHEN date >= current_date() - 7 THEN ai_input_tokens + ai_output_tokens END) AS tokens_7d
        FROM {fq}.costs_daily""")
    print("done")


if __name__ == "__main__":
    main()
