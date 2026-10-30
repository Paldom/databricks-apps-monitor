"""Browser-mode synthetic smoke (optional deep check).

HTTP journeys run INSIDE the monitor app (app/main.py `run_journeys`) because only the
app's own SP OAuth is accepted by app URLs — job-runtime tokens get 401/302. This job
only attempts a real-browser page load per app with Playwright:

  - serverless: best-effort — `playwright install chromium --only-shell` may lack system
    libraries; failures are recorded as 'playwright unavailable', never job failures.
  - classic compute + Databricks Container Services: use the proven custom-container
    pattern from databricks-apps-e2e-playwright-testing-dab (Playwright pre-installed,
    M2M service-principal auth via secret scope).

Results land in synthetic_runs with kind='playwright'; per-run artifacts (result JSON +
screenshot when the browser rendered) go to the UC volume {schema}.ui_tests, and each row's
`artifact` column points at its folder there.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import time
from datetime import datetime, timezone

from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession

DDL = """
CREATE TABLE IF NOT EXISTS {fq}.synthetic_runs (
  run_ts TIMESTAMP, app STRING, journey STRING, step INT, step_name STRING,
  ok BOOLEAN, status_code INT, latency_ms DOUBLE, within_budget BOOLEAN,
  detail STRING, kind STRING, artifact STRING
) COMMENT 'Synthetic results: kind=playwright from this job (artifact = UC volume folder); live HTTP journeys run in-app'"""

VOLUME_DDL = "CREATE VOLUME IF NOT EXISTS {fq}.ui_tests COMMENT 'Browser-test artifacts: result JSON + screenshot per app per run'"


def browser_smoke(url: str, headers: dict) -> dict:
    try:
        from playwright.sync_api import sync_playwright

        t0 = time.perf_counter()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_context(
                extra_http_headers={**headers, "x-monitor-synthetic": "journey"},
                viewport={"width": 1280, "height": 800},
            ).new_page()
            resp = page.goto(url, timeout=30_000)
            page.wait_for_timeout(1500)
            title = page.title()
            shot = page.screenshot(type="png")
            browser.close()
        ms = round((time.perf_counter() - t0) * 1000, 1)
        ok = bool(resp) and resp.status < 400
        return {
            "ok": ok,
            "status_code": resp.status if resp else -1,
            "latency_ms": ms,
            "detail": f"title: {title[:80]}",
            "screenshot": shot,
        }
    except Exception as e:  # noqa: BLE001 — expected on serverless without browser deps
        return {
            "ok": False,
            "status_code": -1,
            "latency_ms": 0.0,
            "detail": f"playwright unavailable: {type(e).__name__}"[:200],
            "screenshot": None,
        }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"

    w = WorkspaceClient()
    spark = SparkSession.builder.getOrCreate()
    spark.sql(DDL.format(fq=fq))
    spark.sql(VOLUME_DDL.format(fq=fq))
    try:  # table may predate the artifact column
        spark.sql(f"ALTER TABLE {fq}.synthetic_runs ADD COLUMNS (artifact STRING)")
    except Exception:  # noqa: BLE001 — already there
        pass
    vol_root = f"/Volumes/{args.catalog}/{args.schema}/ui_tests"

    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium", "--only-shell"],
            capture_output=True,
            timeout=300,
            check=True,
        )
    except Exception as e:  # noqa: BLE001
        print(f"browser install failed (expected on serverless): {e}")

    headers = w.config.authenticate()
    ts = datetime.now(timezone.utc)
    stamp = ts.strftime("%Y%m%d-%H%M%S")
    rows = []
    for a in w.apps.list():
        if not a.url:
            continue
        r = browser_smoke(a.url, headers)
        shot = r.pop("screenshot", None)
        folder = f"{vol_root}/{a.name}/{stamp}"
        artifact = None
        try:  # artifacts to the UC volume: result JSON always, screenshot when rendered
            result = {
                "run_ts": ts.isoformat(),
                "app": a.name,
                "url": a.url,
                **r,
            }
            w.files.upload(
                f"{folder}/result.json",
                io.BytesIO(json.dumps(result, indent=1).encode()),
                overwrite=True,
            )
            if shot:
                w.files.upload(f"{folder}/screenshot.png", io.BytesIO(shot), overwrite=True)
            artifact = folder
        except Exception as e:  # noqa: BLE001 — volume write must not fail the run
            print(f"  artifact upload failed for {a.name}: {e}")
        rows.append(
            {
                "run_ts": ts,
                "app": a.name,
                "journey": "browser-smoke",
                "step": 0,
                "step_name": "browser page load",
                "within_budget": bool(r.get("ok")),
                "kind": "playwright",
                "artifact": artifact,
                **r,
            }
        )
        print(
            f"{a.name}: {'OK' if r['ok'] else 'FAIL'} {r['detail']} → {artifact or 'no artifact'}"
        )

    if rows:
        spark.createDataFrame(
            rows, schema=spark.table(f"{args.catalog}.{args.schema}.synthetic_runs").schema
        ).write.mode("append").saveAsTable(f"{args.catalog}.{args.schema}.synthetic_runs")
    print(f"done: {len(rows)} browser checks · artifacts under {vol_root}")


if __name__ == "__main__":
    main()
