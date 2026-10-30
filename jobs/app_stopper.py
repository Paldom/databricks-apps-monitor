"""Cost guardrail: stop apps per their auto-stop config (runs hourly, as the deployer).

Modes (app_config.auto_stop):
  night  — stop during the night window (00:00–05:59 in --tz), started again by hand
  idle   — stop when no real request (server span, non-probe) for idle_hours (default 24)
  budget — HARD budget enforcement: stop when month-to-date compute $ ≥ budget_usd_month
           (article: "hard budget limits enforced from the first deployment, not retrofitted")
Manual one-off: run with action=stop|start and app=<name> job parameters (the monitor's
Ops tab triggers this — the monitor SP itself only holds CAN_USE).
The monitor and currently-deploying apps are never touched. Every action → alert_events.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession

PROTECTED = {"apps-monitor"}


def emit(spark, cat, sch, rows):
    from source_scan import emit_alerts

    # Actions are completed audit events, not ongoing conditions.
    emit_alerts(
        spark,
        cat,
        sch,
        [{**r, "state": "resolved"} for r in rows],
        owned_rules=("manual_stop", "manual_start", "auto_stopped", "budget_stopped"),
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--tz", default="Europe/Budapest")
    p.add_argument("--action", default="", help="manual: stop|start")
    p.add_argument("--app", default="", help="manual target app")
    p.add_argument("--jobs-dir", default="")
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"

    w = WorkspaceClient()
    spark = SparkSession.builder.getOrCreate()

    if args.action and args.app:  # manual one-off from the monitor UI
        if args.action == "stop" and args.app in PROTECTED:
            raise SystemExit(f"{args.app} is protected — refusing manual stop")
        if args.action == "stop":
            w.api_client.do("POST", f"/api/2.0/apps/{args.app}/stop")
        elif args.action == "start":
            w.api_client.do("POST", f"/api/2.0/apps/{args.app}/start")
        emit(
            spark,
            args.catalog,
            args.schema,
            [
                {
                    "rule": "manual_" + args.action,
                    "app": args.app,
                    "severity": "info",
                    "message": f"{args.action} requested from the monitor UI",
                    "value": 0,
                }
            ],
        )
        print(f"manual {args.action} {args.app} done")
        return

    cfg = {
        r["name"]: r
        for r in spark.sql(
            f"SELECT name, auto_stop, coalesce(idle_hours, 24) AS idle_hours, "
            f"coalesce(budget_usd_month, 0) AS budget FROM {fq}.app_config "
            f"WHERE auto_stop IN ('night', 'idle', 'budget')"
        ).collect()
    }
    if not cfg:
        emit(spark, args.catalog, args.schema, [])
        print("no apps opted into auto-stop")
        return

    from telemetry_sql import NOT_PROBE, SERVER

    last_seen = {
        r["name"]: r["last_ts"]
        for r in spark.sql(f"""
        SELECT service_name AS name, max(time) AS last_ts FROM {fq}.otel_spans
        WHERE {SERVER} AND {NOT_PROBE}
          AND time >= now() - INTERVAL 7 DAYS GROUP BY 1""").collect()
    }

    mtd = {
        r["name"]: r["mtd"]
        for r in spark.sql(f"""
        SELECT name, sum(dbu_usd) AS mtd FROM {fq}.costs_daily
        WHERE date >= date_trunc('MONTH', current_date()) GROUP BY 1""").collect()
    }

    hour_local = datetime.now(ZoneInfo(args.tz)).hour
    now = datetime.now(timezone.utc)
    actions = []
    for a in w.apps.list():
        c = cfg.get(a.name)
        if not c or a.name in PROTECTED:
            continue
        if not a.compute_status or a.compute_status.state.value != "ACTIVE":
            continue  # already stopped/stopping
        reason, rule, sev = None, "auto_stopped", "info"
        if c["auto_stop"] == "night" and hour_local < 6:
            reason = f"night window ({args.tz} {hour_local:02d}h)"
        elif c["auto_stop"] == "idle":
            seen = last_seen.get(a.name)
            if seen is None:
                # fail safe (review P0.4): no telemetry evidence must never mean "idle" —
                # uninstrumented apps, outages and permission gaps all look identical
                print(f"{a.name}: idle mode but no request evidence — skipping (fail-safe)")
                continue
            idle_h = (now - seen.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if idle_h >= c["idle_hours"]:
                reason = f"idle {idle_h:.0f}h ≥ {c['idle_hours']}h (no real requests)"
        elif c["auto_stop"] == "budget" and c["budget"] > 0:
            spent = mtd.get(a.name, 0) or 0
            if spent >= c["budget"]:
                reason = f"hard budget: MTD ${spent:.2f} ≥ ${c['budget']:.2f}"
                rule, sev = "budget_stopped", "critical"
        if reason:
            try:
                w.api_client.do("POST", f"/api/2.0/apps/{a.name}/stop")
                actions.append(
                    {
                        "rule": rule,
                        "app": a.name,
                        "severity": sev,
                        "message": f"stopped: {reason} · ~0.5 DBU/h saved while down",
                        "value": 0,
                    }
                )
                print(f"stopped {a.name}: {reason}")
            except Exception as e:  # noqa: BLE001
                print(f"stop {a.name} failed: {e}")
    emit(spark, args.catalog, args.schema, actions)
    print(f"done: {len(actions)} apps stopped")


if __name__ == "__main__":
    import sys

    _jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
    if _jobs_dir:
        sys.path.append(_jobs_dir)
    main()
