"""Fleet inventory snapshot (runs hourly on serverless, as the deploying user).

1. Lists every Databricks App into <catalog>.<schema>.apps_inventory (append-only,
   `v_apps_latest` view exposes the newest snapshot per app).
2. Grants the monitor app's service principal what it can't grant itself:
   CAN_USE on every app (so it can probe their URLs) and read access on the
   monitoring schema (so the dashboard can query history).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.apps import AppAccessControlRequest, AppPermissionLevel
from pyspark.sql import SparkSession

ALERT_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.alert_events (
  ts TIMESTAMP, rule STRING, app STRING, severity STRING,
  message STRING, value DOUBLE, state STRING, source STRING,
  workspace_id STRING, muted BOOLEAN, incident_id STRING
) COMMENT 'Alert state transitions from the monitor app (probe rules) and jobs (deep rules)'
"""

INVENTORY_DDL = """
CREATE TABLE IF NOT EXISTS {fq}.apps_inventory (
  snapshot_ts TIMESTAMP,
  name STRING,
  app_id STRING,
  url STRING,
  app_state STRING,
  app_message STRING,
  compute_state STRING,
  compute_message STRING,
  creator STRING,
  description STRING,
  create_time STRING,
  update_time STRING,
  sp_client_id STRING,
  source_code_path STRING,
  deployment_id STRING,
  resources_json STRING, workspace_id STRING, sampler_ratio DOUBLE
) COMMENT 'Hourly snapshot of every Databricks App in the workspace (monitor-inventory-scan job)'
"""


def app_row(a, ts: datetime, workspace_id: str) -> dict:
    dep = a.active_deployment
    return {
        "snapshot_ts": ts,
        "workspace_id": workspace_id,
        "name": a.name,
        "app_id": getattr(a, "id", None) or getattr(a, "service_principal_client_id", None),
        "url": a.url,
        "app_state": a.app_status.state.value if a.app_status and a.app_status.state else None,
        "app_message": a.app_status.message if a.app_status else None,
        "compute_state": a.compute_status.state.value
        if a.compute_status and a.compute_status.state
        else None,
        "compute_message": a.compute_status.message if a.compute_status else None,
        "creator": a.creator,
        "description": a.description,
        "create_time": a.create_time,
        "update_time": a.update_time,
        "sp_client_id": a.service_principal_client_id,
        "source_code_path": dep.source_code_path if dep else None,
        "deployment_id": dep.deployment_id if dep else None,
        "resources_json": json.dumps([r.as_dict() for r in (a.resources or [])]),
        "sampler_ratio": None,
    }


def grant_monitor_access(
    w: WorkspaceClient,
    spark,
    apps,
    monitor_name: str,
    catalog: str,
    schema: str,
    external_sp: str = "",
) -> None:
    monitor = next((a for a in apps if a.name == monitor_name), None)
    if not monitor or not monitor.service_principal_client_id:
        print(f"monitor app '{monitor_name}' not found — skipping grants")
        return
    sp = monitor.service_principal_client_id

    for stmt in (
        f"GRANT USE CATALOG ON CATALOG `{catalog}` TO `{sp}`",
        f"GRANT USE SCHEMA ON SCHEMA `{catalog}`.`{schema}` TO `{sp}`",
        # Inherited SELECT covers product tables/views as they appear after the gold task.
        f"GRANT SELECT ON SCHEMA `{catalog}`.`{schema}` TO `{sp}`",
        # the monitor appends its probe-rule alert transitions itself
        f"GRANT MODIFY ON TABLE `{catalog}`.`{schema}`.`alert_events` TO `{sp}`",
        f"GRANT MODIFY ON TABLE `{catalog}`.`{schema}`.`app_config` TO `{sp}`",
        f"GRANT MODIFY ON TABLE `{catalog}`.`{schema}`.`alert_mutes` TO `{sp}`",
        f"GRANT MODIFY ON TABLE `{catalog}`.`{schema}`.`slo_specs` TO `{sp}`",
        f"GRANT MODIFY ON TABLE `{catalog}`.`{schema}`.`monitor_audit` TO `{sp}`",
        f"GRANT MODIFY ON TABLE `{catalog}`.`{schema}`.`model_prices` TO `{sp}`",
        f"GRANT MODIFY ON TABLE `{catalog}`.`{schema}`.`funnel_specs` TO `{sp}`",
        f"GRANT MODIFY ON TABLE `{catalog}`.`{schema}`.`synthetic_runs` TO `{sp}`",
    ):
        try:
            spark.sql(stmt)
        except Exception as e:  # noqa: BLE001 — grant failures must not kill the snapshot
            print(f"grant failed ({stmt}): {e}")

    if external_sp and external_sp != "unset":
        from federation import identifier

        principal = identifier(external_sp)
        for stmt in (
            f"GRANT USE CATALOG ON CATALOG `{catalog}` TO {principal}",
            f"GRANT USE SCHEMA ON SCHEMA `{catalog}`.`{schema}` TO {principal}",
            f"GRANT SELECT, MODIFY ON TABLE `{catalog}`.`{schema}`.`synthetic_runs` TO {principal}",
            f"GRANT READ VOLUME, WRITE VOLUME ON VOLUME `{catalog}`.`{schema}`.`ui_tests` TO {principal}",
        ):
            spark.sql(stmt)
        for a in apps:
            w.apps.update_permissions(
                app_name=a.name,
                access_control_list=[
                    AppAccessControlRequest(
                        service_principal_name=external_sp,
                        permission_level=AppPermissionLevel.CAN_USE,
                    )
                ],
            )

    for a in apps:
        if a.name == monitor_name:
            continue
        if a.service_principal_client_id:
            try:
                # CAN_USE covers every viewer endpoint on the monitor, not only /api/policy.
                w.apps.update_permissions(
                    app_name=monitor_name,
                    access_control_list=[
                        AppAccessControlRequest(
                            service_principal_name=a.service_principal_client_id,
                            permission_level=AppPermissionLevel.CAN_USE,
                        )
                    ],
                )
            except Exception as e:  # noqa: BLE001 — one grant must not stop the fleet scan
                print(f"policy CAN_USE grant for {a.name} failed: {e}")
        try:
            w.apps.update_permissions(
                app_name=a.name,
                access_control_list=[
                    AppAccessControlRequest(
                        service_principal_name=sp,
                        permission_level=AppPermissionLevel.CAN_USE,
                    )
                ],
            )
        except Exception as e:  # noqa: BLE001
            print(f"CAN_USE grant on app {a.name} failed: {e}")

    # monitor reads MLflow traces of apps that bind an experiment (unified trace view).
    # Raw REST (not the App model) — older preinstalled SDKs drop unknown fields silently.
    for a in apps:
        try:
            raw = w.api_client.do("GET", f"/api/2.0/apps/{a.name}")
            exp_ids = [
                r["experiment"]["experiment_id"]
                for r in raw.get("resources", [])
                if r.get("experiment")
            ]
        except Exception as e:  # noqa: BLE001
            print(f"resource lookup for {a.name} failed: {e}")
            continue
        for exp_id in exp_ids:
            try:
                w.api_client.do(
                    "PATCH",
                    f"/api/2.0/permissions/experiments/{exp_id}",
                    body={
                        "access_control_list": [
                            {"service_principal_name": sp, "permission_level": "CAN_READ"}
                        ]
                    },
                )
                print(f"experiment READ granted for {a.name} ({exp_id})")
            except Exception as e:  # noqa: BLE001
                print(f"experiment grant for {a.name} failed: {e}")


def main() -> None:
    from federation import arguments, destination, publish
    from ops_tables import ensure_ops_tables
    from product_sql import FUNNEL_DDL, MODEL_PRICES_DDL
    from schema_utils import ensure_columns, workspace_column
    from synthetics import ensure_tables
    from telemetry_health import sampler_ratio

    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--jobs-dir", default="")
    p.add_argument("--monitor-app", default="apps-monitor")
    p.add_argument("--external-sp", default="")
    arguments(p)
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"

    w = WorkspaceClient()
    spark = SparkSession.builder.getOrCreate()
    ts = datetime.now(timezone.utc)
    args.snapshot_ts = ts
    destination(args, w)

    apps = list(w.apps.list())
    print(f"{len(apps)} apps found")

    spark.sql(INVENTORY_DDL.format(fq=fq))
    spark.sql(ALERT_DDL.format(fq=fq))
    ensure_ops_tables(spark, fq)
    workspace_column(spark, f"{fq}.monitor_audit", str(w.get_workspace_id()))
    # Create writable product tables before granting; the gold task runs afterwards.
    spark.sql(MODEL_PRICES_DDL.format(fq=fq))
    spark.sql(FUNNEL_DDL.format(fq=fq))
    ensure_columns(spark, f"{fq}.alert_events", {"muted": "BOOLEAN", "incident_id": "STRING"})
    workspace_column(spark, f"{fq}.alert_events", str(w.get_workspace_id()))
    ws = str(w.get_workspace_id())
    ensure_tables(spark, fq, ws)
    workspace_column(spark, f"{fq}.apps_inventory", ws)
    ensure_columns(spark, f"{fq}.apps_inventory", {"sampler_ratio": "DOUBLE"})
    rows = [app_row(a, ts, ws) for a in apps]
    for row in rows:
        try:
            raw = w.api_client.do("GET", f"/api/2.0/apps/{row['name']}")
            row["sampler_ratio"] = sampler_ratio(raw.get("config"))
        except Exception as e:  # noqa: BLE001 — config may not be exposed by the Apps API
            print(f"sampler config unavailable for {row['name']}: {type(e).__name__}")
    if rows:
        df = spark.createDataFrame(
            rows, schema=spark.table(f"{args.catalog}.{args.schema}.apps_inventory").schema
        )
        df.write.mode("append").saveAsTable(f"{args.catalog}.{args.schema}.apps_inventory")

    spark.sql(
        f"""CREATE OR REPLACE VIEW {fq}.v_apps_latest
            COMMENT 'Latest inventory snapshot per Databricks App'
            AS SELECT * FROM (
              SELECT *, ROW_NUMBER() OVER (PARTITION BY name ORDER BY snapshot_ts DESC) rn
              FROM {fq}.apps_inventory
            ) WHERE rn = 1"""
    )

    grant_monitor_access(
        w, spark, apps, args.monitor_app, args.catalog, args.schema, args.external_sp
    )
    publish(spark, args, w, ("apps_inventory",))
    print("inventory scan done")


if __name__ == "__main__":
    import sys

    # Serverless script tasks do not set __file__; the bundle provides the helper path.
    _jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
    if _jobs_dir:
        sys.path.append(_jobs_dir)
    main()
