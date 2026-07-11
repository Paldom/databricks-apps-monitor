"""Telemetry retention — keeps the monitor from torching its own storage budget.

Raw otel_* rows older than --days (default 90) are deleted and the tables VACUUMed;
gold views/aggregates (costs_daily, code_scans, llm_reviews, monitor_quality) are kept
indefinitely. Runs daily as the second task of the cost job; deletes are no-ops until
data actually ages past the horizon.
"""

from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

RAW_TABLES = ["otel_logs", "otel_spans", "otel_metrics"]
EVENT_TABLES = [("alert_events", "ts"), ("synthetic_runs", "run_ts")]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--days", type=int, default=90)
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"
    spark = SparkSession.builder.getOrCreate()

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
