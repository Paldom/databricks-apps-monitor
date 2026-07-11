"""Provision a new, properly-tagged Databricks App from the monitor UI.

DAB-style flow executed as the deployer: template files (templates/basic-app, shipped
with the bundle) → workspace folder → app created with telemetry export to the shared
monitoring tables → deployment started → governance tags recorded in app_config.
The new app is born fully observable (probes, telemetry, scans, reviews, cost) on the
next inventory cycle.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import re
import time
from datetime import datetime, timezone

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ExportFormat, ImportFormat
from pyspark.sql import SparkSession


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--app-name", required=True)
    p.add_argument("--team", default="unassigned")
    p.add_argument("--cost-center", default="unassigned")
    p.add_argument("--env", default="dev")
    p.add_argument("--description", default="")
    p.add_argument("--templates-dir", required=True, help="workspace path of templates/")
    p.add_argument("--jobs-dir", default="")
    args = p.parse_args()

    name = args.app_name.lower()
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,25}", name):
        raise SystemExit(f"invalid app name '{name}' (lowercase, digits, hyphens, ≤26 chars)")

    w = WorkspaceClient()
    spark = SparkSession.builder.getOrCreate()
    fq = f"`{args.catalog}`.`{args.schema}`"
    tags = {
        "team": args.team,
        "cost_center": args.cost_center,
        "env": args.env,
        "provisioned_by": "apps-monitoring",
        "provisioned_at": datetime.now(timezone.utc).isoformat(),
    }

    # 1) template files → /Workspace/Shared/monitor-apps/<name>
    target = f"/Workspace/Shared/monitor-apps/{name}"
    w.workspace.mkdirs(target)
    tpl = f"{args.templates_dir}/basic-app"
    for obj in w.workspace.list(tpl):
        fname = obj.path.rsplit("/", 1)[-1]
        content = base64.b64decode(
            w.workspace.export(obj.path, format=ExportFormat.SOURCE).content or b""
        )
        text = content.decode("utf-8").replace("__APP_NAME__", name)
        w.workspace.upload(
            f"{target}/{fname}", io.BytesIO(text.encode()), overwrite=True, format=ImportFormat.AUTO
        )
        print(f"  {fname} → {target}")

    # 2) create the app with telemetry export into the shared monitoring tables
    body = {
        "name": name,
        "description": args.description
        or f"Provisioned via apps-monitoring · team={args.team} · cc={args.cost_center} · env={args.env}",
        "telemetry_export_destinations": [
            {
                "unity_catalog": {
                    "logs_table": f"{args.catalog}.{args.schema}.otel_logs",
                    "traces_table": f"{args.catalog}.{args.schema}.otel_spans",
                    "metrics_table": f"{args.catalog}.{args.schema}.otel_metrics",
                }
            }
        ],
    }
    try:
        w.api_client.do("POST", "/api/2.0/apps", body=body)
        print(f"app {name} created")
    except Exception as e:
        if "already exists" in str(e):
            # fail closed (review P0.1): provisioning must never redeploy over an existing app
            raise SystemExit(f"app {name} already exists — refusing to overwrite") from e
        raise

    # 3) wait for compute, then deploy the source
    for _ in range(60):
        a = w.api_client.do("GET", f"/api/2.0/apps/{name}")
        state = (a.get("compute_status") or {}).get("state")
        if state == "ACTIVE":
            break
        if state in ("ERROR", "DELETING"):
            raise SystemExit(f"app compute state {state}")
        print(f"  compute {state}…")
        time.sleep(10)
    w.api_client.do(
        "POST",
        f"/api/2.0/apps/{name}/deployments",
        body={"source_code_path": target, "mode": "SNAPSHOT"},
    )
    print("deployment started")

    # 4) governance tags → app_config (chargeback picks them up immediately)
    tags_sql = json.dumps(tags).replace("'", "''")  # escape for SQL string literal
    spark.sql(f"""
      MERGE INTO {fq}.app_config t
      USING (SELECT '{name}' AS name) s ON t.name = s.name
      WHEN MATCHED THEN UPDATE SET tags_json = '{tags_sql}', updated_at = current_timestamp(), updated_by = 'provision-job'
      WHEN NOT MATCHED THEN INSERT (name, tags_json, budget_usd_month, auto_stop, idle_hours, updated_at, updated_by)
      VALUES ('{name}', '{tags_sql}', NULL, 'none', 24, current_timestamp(), 'provision-job')""")

    from source_scan import emit_alerts

    emit_alerts(
        spark,
        args.catalog,
        args.schema,
        [
            {
                "rule": "app_provisioned",
                "app": name,
                "severity": "info",
                "message": f"provisioned by monitoring toolkit · team={args.team} cc={args.cost_center} env={args.env}",
                "value": 0,
            }
        ],
    )
    print(f"done — app '{name}' provisioned, tagged, telemetry-wired")


if __name__ == "__main__":
    import sys

    _jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
    if _jobs_dir:
        sys.path.append(_jobs_dir)
    main()
