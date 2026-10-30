"""Telemetry retention — keeps the monitor from torching its own storage budget.

Raw otel_* rows older than --days (default 90) are deleted and the tables VACUUMed;
gold aggregates (agg_app_*, agg_genai_daily, costs_*) are kept indefinitely.
Runs daily after a successful gold refresh in the retention job; deletes are no-ops until
data actually ages past the horizon.
"""

from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

RAW_TABLES = ["otel_logs", "otel_spans", "otel_metrics"]
EVENT_TABLES = [("synthetic_runs", "run_ts")]


def alert_retention_sql(fq: str, days: int) -> str:
    # Keep the latest transition even when it is resolved, so old firings never reappear.
    return f"""MERGE INTO {fq}.alert_events t USING (
      SELECT workspace_id, source, rule, app, max(ts) AS latest
      FROM {fq}.alert_events GROUP BY 1, 2, 3, 4) s
      ON t.workspace_id <=> s.workspace_id AND t.source = s.source
        AND t.rule = s.rule AND t.app = s.app
      WHEN MATCHED AND t.ts < s.latest AND t.ts < now() - INTERVAL {days} DAYS THEN DELETE"""


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--days", type=int, default=90)
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"
    spark = SparkSession.builder.getOrCreate()

    spark.sql(alert_retention_sql(fq, args.days))

    for tbl in RAW_TABLES:
        try:
            n = spark.sql(
                f"DELETE FROM {fq}.`{tbl}` WHERE date < current_date() - {args.days}"
            ).collect()[0][0]
            spark.sql(f"VACUUM {fq}.`{tbl}`")
            print(f"{tbl}: deleted {n} rows older than {args.days}d, vacuumed")
        except Exception as e:  # noqa: BLE001 — table may not exist yet
            print(f"{tbl}: skipped ({e})")

    for tbl, col in EVENT_TABLES:
        try:
            n = spark.sql(
                f"DELETE FROM {fq}.`{tbl}` WHERE {col} < now() - INTERVAL {args.days} DAYS"
            ).collect()[0][0]
            print(f"{tbl}: deleted {n} rows older than {args.days}d")
        except Exception as e:  # noqa: BLE001
            print(f"{tbl}: skipped ({e})")
    print("housekeeping done")


if __name__ == "__main__":
    main()
