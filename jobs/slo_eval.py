"""Quarter-hour SLI rollup, multi-window burn rules and telemetry-health checks."""

from __future__ import annotations

import argparse
import math

RULES = (
    ("slo_fast_burn", 60, 5, 14.4, "critical"),
    ("slo_slow_burn", 360, 30, 6.0, "high"),
    ("slo_ticket", 4320, 360, 1.0, "warning"),
)
OWNED_RULES = (*tuple(r[0] for r in RULES), "slo_no_data")


def burn_rate(good: int, total: int, target: float) -> float | None:
    if not math.isfinite(target) or not 0 < target < 1 or not 0 <= good <= total:
        raise ValueError("invalid SLI counts or target")
    return (total - good) / total / (1 - target) if total else None


def both_windows(
    long: tuple[int, int], short: tuple[int, int], target: float, threshold: float
) -> bool | None:
    rates = [burn_rate(*counts, target) for counts in (long, short)]
    if any(rate is None for rate in rates):
        return None
    return all(rate >= threshold or math.isclose(rate, threshold) for rate in rates)


def sli_sql(fq: str) -> str:
    from telemetry_sql import DUR, ERR, HTTP_ROUTE, NOT_PROBE, SERVER

    # Qualify before the spec join: both raw spans and specs contain a name column.
    return f"""MERGE INTO {fq}.sli_5m t USING (
      WITH requests AS (
        SELECT service_name, time, {HTTP_ROUTE} AS route, {DUR} AS ms, {ERR} AS failed
        FROM {fq}.otel_spans
        WHERE {SERVER} AND {NOT_PROBE} AND date >= current_date() - 1
          AND time >= :end - INTERVAL 2 HOURS AND time < :end)
      SELECT s.workspace_id, s.name, s.slo, s.revision,
        window(o.time, '5 minutes').start AS bucket,
        sum(CASE WHEN s.sli = 'availability' AND NOT o.failed THEN 1
                 WHEN s.sli = 'latency' AND o.ms <= s.threshold_ms THEN 1 ELSE 0 END) AS good,
        count(*) AS total
      FROM requests o JOIN {fq}.slo_specs s ON o.service_name = s.name
      WHERE s.workspace_id = :ws AND (s.route_filter IS NULL OR o.route LIKE s.route_filter)
      GROUP BY ALL) s
      ON t.workspace_id = s.workspace_id AND t.name = s.name AND t.slo = s.slo
        AND t.revision = s.revision AND t.bucket = s.bucket
      WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *
      WHEN NOT MATCHED BY SOURCE AND t.workspace_id = :ws
        AND t.bucket >= :end - INTERVAL 2 HOURS AND t.bucket < :end THEN DELETE"""


def counts_sql(fq: str) -> str:
    windows = sorted({5, 30, 60, 360, 4320})
    counts = ", ".join(
        f"coalesce(sum(CASE WHEN b.bucket >= :end - INTERVAL {mins} MINUTES "
        f"THEN b.{field} END), 0) AS {field}_{mins}"
        for mins in windows
        for field in ("good", "total")
    )
    return f"""SELECT s.name, s.slo, s.target, s.updated_at, a.app_state, {counts}
      FROM {fq}.slo_specs s LEFT JOIN {fq}.sli_5m b
        ON b.workspace_id = s.workspace_id AND b.name = s.name AND b.slo = s.slo
        AND b.revision = s.revision AND b.bucket >= :end - INTERVAL 3 DAYS AND b.bucket < :end
      LEFT JOIN {fq}.v_apps_latest a ON a.name = s.name AND a.workspace_id = s.workspace_id
      WHERE s.workspace_id = :ws GROUP BY ALL"""


def slo_alerts(rows: list[dict], end) -> list[dict]:
    # Alert keys are (rule, app); combine failing specs so one cannot resolve another.
    from datetime import timedelta, timezone

    desired: dict[tuple[str, str], dict] = {}
    for row in rows:
        for rule, long, short, threshold, severity in RULES:
            lc = (int(row[f"good_{long}"]), int(row[f"total_{long}"]))
            sc = (int(row[f"good_{short}"]), int(row[f"total_{short}"]))
            if both_windows(lc, sc, float(row["target"]), threshold):
                value = burn_rate(*lc, float(row["target"]))
                key = (rule, row["name"])
                message = f"{row['slo']}: burn {value:.2f}x ({long}m and {short}m >= {threshold}x)"
                if key in desired:
                    desired[key]["message"] += "; " + message
                    desired[key]["value"] = max(desired[key]["value"], value)
                else:
                    desired[key] = {
                        "rule": rule,
                        "app": row["name"],
                        "severity": severity,
                        "message": message,
                        "value": value,
                    }
        updated = row["updated_at"]
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        if (
            row["app_state"] == "RUNNING"
            and not row["total_30"]
            and updated <= end - timedelta(minutes=30)
        ):
            key = ("slo_no_data", row["name"])
            message = f"{row['slo']}: no real request samples for 30m while RUNNING (SLI unknown)"
            if key in desired:
                desired[key]["message"] += "; " + message
            else:
                desired[key] = {
                    "rule": key[0],
                    "app": key[1],
                    "severity": "warning",
                    "message": message,
                    "value": 0,
                }
    return list(desired.values())


def unknown_slo_keys(rows: list[dict]) -> set[tuple[str, str]]:
    # A missing window cannot establish recovery. Any firing sibling still wins.
    unknown = set()
    for row in rows:
        for rule, long, short, _threshold, _severity in RULES:
            if not row[f"total_{long}"] or not row[f"total_{short}"]:
                unknown.add((rule, row["name"]))
        if row["app_state"] is None:
            unknown.add(("slo_no_data", row["name"]))
    return unknown


def main() -> None:
    from databricks.sdk import WorkspaceClient
    from ops_tables import ensure_ops_tables
    from pyspark.sql import SparkSession
    from telemetry_health import check_telemetry

    from source_scan import emit_alerts

    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--jobs-dir", default="")
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"
    spark = SparkSession.builder.getOrCreate()
    ws = str(WorkspaceClient().get_workspace_id())
    ensure_ops_tables(spark, fq)
    # Completed buckets only. One common boundary prevents rollup/evaluation skew.
    end = spark.sql("SELECT window(now(), '5 minutes').start AS ts").collect()[0]["ts"]
    spark.sql(sli_sql(fq), args={"ws": ws, "end": end})
    rows = [r.asDict() for r in spark.sql(counts_sql(fq), args={"ws": ws, "end": end}).collect()]
    from datetime import timezone

    emit_alerts(
        spark,
        args.catalog,
        args.schema,
        slo_alerts(rows, end.replace(tzinfo=timezone.utc)),
        owned_rules=OWNED_RULES,
        unknown_keys=unknown_slo_keys(rows),
    )
    check_telemetry(spark, fq, ws, args.catalog, args.schema)


if __name__ == "__main__":
    import sys

    _jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
    if _jobs_dir:
        sys.path.append(_jobs_dir)
    main()
