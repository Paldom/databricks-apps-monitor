"""External OAuth M2M checks; stdlib HTTP/SQL client, optional Playwright journeys.

Run with uv run scripts/external_synthetics.py. Credentials are read only from env;
failed auth/SQL delivery exits nonzero and leaves a sanitized local result artifact.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(url, method="GET", headers=None, data=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        with exc:
            return exc.code, exc.read(), dict(exc.headers)


def https_url(value):
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Expected an HTTPS URL without credentials or query")
    return value.rstrip("/")


def relative_url(base, path):
    parsed = urllib.parse.urlsplit(path)
    if (
        not path.startswith("/")
        or path.startswith("//")
        or parsed.netloc
        or parsed.scheme
        or "\\" in path
        or any(ord(c) < 32 for c in path)
    ):
        raise ValueError("Journey paths must be app-relative")
    if urllib.parse.unquote(parsed.path).rstrip("/").lower() == "/healthz":
        raise ValueError("Use an app route: the Apps proxy intercepts /healthz")
    return https_url(base) + path


def token(host, client_id, client_secret):
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    code, body, _ = request(
        host + "/oidc/v1/token",
        "POST",
        {"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
        b"grant_type=client_credentials&scope=all-apis",
    )
    if code != 200:
        raise RuntimeError(f"OAuth failed (HTTP {code})")
    return json.loads(body)["access_token"]


class Workspace:
    def __init__(self, host, access_token, warehouse):
        self.host, self.warehouse = host, warehouse
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def api(self, path, payload=None):
        code, body, _ = request(
            self.host + path,
            "POST" if payload is not None else "GET",
            {**self.headers, "Content-Type": "application/json"},
            json.dumps(payload).encode() if payload is not None else None,
            timeout=60,  # Statement Execution can wait up to 50 seconds before returning.
        )
        if code < 200 or code >= 300:
            raise RuntimeError(f"Workspace API failed (HTTP {code})")
        return json.loads(body)

    def apps(self):
        apps, path = [], "/api/2.0/apps"
        while path:
            result = self.api(path)
            apps.extend(result.get("apps", []))
            page = result.get("next_page_token")
            path = "/api/2.0/apps?" + urllib.parse.urlencode({"page_token": page}) if page else None
        return apps

    def sql(self, statement, parameters):
        result = self.api(
            "/api/2.0/sql/statements",
            {
                "warehouse_id": self.warehouse,
                "statement": statement,
                "wait_timeout": "50s",
                "parameters": [
                    {"name": k, "value": str(v).lower() if isinstance(v, bool) else str(v)}
                    for k, v in parameters.items()
                ],
            },
        )
        deadline = time.monotonic() + 180
        while result["status"]["state"] in ("PENDING", "RUNNING") and time.monotonic() < deadline:
            time.sleep(2)
            result = self.api("/api/2.0/sql/statements/" + result["statement_id"])
        if result["status"]["state"] != "SUCCEEDED":
            # Do not print SQL error messages: they can contain parameter values.
            raise RuntimeError("SQL result delivery did not succeed")

    def artifact(self, path, data):
        directory = path.rsplit("/", 1)[0]
        code, _, _ = request(
            self.host + "/api/2.0/fs/directories" + urllib.parse.quote(directory, safe="/"),
            "PUT",
            self.headers,
        )
        if code not in (200, 201, 204):
            raise RuntimeError(f"Artifact directory creation failed (HTTP {code})")
        code, _, _ = request(
            self.host
            + "/api/2.0/fs/files"
            + urllib.parse.quote(path, safe="/")
            + "?overwrite=true",
            "PUT",
            {**self.headers, "Content-Type": "application/octet-stream"},
            data,
        )
        if code not in (200, 201, 204):
            raise RuntimeError(f"Artifact upload failed (HTTP {code})")


INSERT = """
MERGE INTO IDENTIFIER(:table) t USING (
  SELECT :workspace_id AS workspace_id, :run_id AS run_id, :app AS app,
         :journey AS journey, :step::int AS step, 'external' AS vantage) s
ON t.workspace_id = s.workspace_id AND t.run_id = s.run_id AND t.app = s.app
 AND t.journey = s.journey AND t.step = s.step AND t.vantage = s.vantage
WHEN NOT MATCHED THEN INSERT
 (workspace_id, run_id, app, journey, step, vantage, run_ts, step_name, ok, status_code,
  latency_ms, within_budget, detail, kind, artifact, failure_stage)
VALUES (s.workspace_id, s.run_id, s.app, s.journey, s.step, s.vantage, :run_ts::timestamp,
 :step_name, :ok::boolean, :status_code::int, :latency_ms::double, :within_budget::boolean,
 :detail, :kind, nullif(:artifact, ''), nullif(:failure_stage, ''))
"""


def failure_stage(exc):
    cause = exc
    while cause:
        if isinstance(cause, socket.gaierror):
            return "dns"
        cause = getattr(cause, "reason", None) or cause.__cause__
        if cause is not None and not isinstance(cause, BaseException):
            break
    return "http"


def http_step(base, step, headers, timeout):
    code, body, _ = request(
        relative_url(base, step["path"]),
        step.get("method", "GET"),
        headers,
        json.dumps(step["json"]).encode() if "json" in step else None,
        timeout,
    )
    if code in (301, 302, 303, 307, 308, 401, 403):
        return code, "auth"
    if code != step.get("expect_status", 200):
        return code, "http"
    if step.get("expect_contains") and step["expect_contains"] not in body.decode(errors="replace"):
        return code, "assertion"
    return code, ""


def browser_steps(base, journey, headers, timeout, screenshot):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        origin = urllib.parse.urlsplit(base)

        def authorize(route):
            req = route.request
            target = urllib.parse.urlsplit(req.url)
            clean = {k: v for k, v in req.headers.items() if k.lower() != "authorization"}
            if (target.scheme, target.netloc) != (origin.scheme, origin.netloc):
                route.continue_(headers=clean)
                return
            # Header overrides on continue_ propagate through redirects. Fetch without
            # following redirects so an OAuth token can never reach a login/asset host.
            response = route.fetch(headers={**clean, **headers}, max_redirects=0)
            if 300 <= response.status < 400:
                route.fulfill(status=401, body="Synthetic authentication redirect")
            else:
                route.fulfill(response=response)

        context.route("**/*", authorize)
        page = context.new_page()
        page.set_default_timeout(timeout * 1000)
        for step in journey["steps"]:
            code, stage, start = 200, "", time.perf_counter()
            operation_stage = "assertion"
            try:
                if "path" in step:
                    operation_stage = "http"
                    response = page.goto(relative_url(base, step["path"]))
                    code = response.status if response else -1
                    stage = (
                        "auth"
                        if urllib.parse.urlsplit(page.url).netloc != origin.netloc
                        or code in (401, 403)
                        else "http"
                        if code != step.get("expect_status", 200)
                        else ""
                    )
                operation_stage = "assertion"
                if not stage and step.get("fill"):
                    page.locator(step["selector"]).fill(step["fill"])
                if not stage and step.get("click"):
                    page.locator(step["click"]).click()
                if not stage and step.get("expect_selector"):
                    page.locator(step["expect_selector"]).wait_for(state="visible")
                if (
                    not stage
                    and step.get("expect_contains")
                    and step["expect_contains"] not in page.content()
                ):
                    stage = "assertion"
            except Exception as exc:  # noqa: BLE001 — one failed journey must not stop the fleet
                stage = "dns" if "ERR_NAME_NOT_RESOLVED" in str(exc) else operation_stage
            yield code, stage, round((time.perf_counter() - start) * 1000, 1)
            if stage:
                break
        try:
            page.screenshot(path=str(screenshot))
        except Exception:  # noqa: BLE001 — artifacts must not discard functional results
            print("Browser screenshot unavailable")
        finally:
            browser.close()


def sanitize_status(data, public_apps):
    """Explicit public labels are the allowlist; never copy internal message fields."""
    apps = []
    allowed_status = {"ok", "down", "degraded", "stopped", "pending"}
    for app in data.get("apps", []):
        if app["name"] not in public_apps:
            continue
        bars = [
            {
                "ts": int(b["ts"]),
                "uptime": float(b["uptime"]) if b.get("uptime") is not None else None,
            }
            for b in app.get("bars", [])
        ]
        apps.append(
            {
                "name": public_apps[app["name"]],
                "status": app.get("status") if app.get("status") in allowed_status else "pending",
                "bars": bars,
            }
        )
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "apps": apps}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--journeys", default="app/journeys.json")
    parser.add_argument("--output", default="external-results")
    parser.add_argument("--playwright", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    phase = "auth"
    try:
        host = https_url(os.environ["DATABRICKS_HOST"])
        access_token = token(
            host, os.environ["DATABRICKS_CLIENT_ID"], os.environ["DATABRICKS_CLIENT_SECRET"]
        )
        phase = "http"
        workspace = Workspace(host, access_token, os.environ["DATABRICKS_WAREHOUSE_ID"])
        ws = os.environ["DATABRICKS_WORKSPACE_ID"]
        catalog, schema = (
            os.environ["MONITOR_CATALOG"],
            os.environ.get("MONITOR_SCHEMA") or "monitor",
        )
        table = ".".join(
            "`" + s.replace("`", "``") + "`" for s in (catalog, schema, "synthetic_runs")
        )
        inventory = {a["name"]: a for a in workspace.apps()}
        config = json.loads(Path(args.journeys).read_text())
        keys = [(j["app"], j["name"]) for j in config["journeys"]]
        if len(keys) != len(set(keys)) or any(not j["steps"] for j in config["journeys"]):
            raise ValueError("Journeys require unique app/name pairs and at least one step")
        defaults = config.get("defaults", {})
        run_id = str(uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        headers = {
            **workspace.headers,
            "x-monitor-synthetic": "journey",
            "Content-Type": "application/json",
        }
        for journey in config["journeys"]:
            browser = journey.get("kind") == "playwright"
            if browser and not args.playwright:
                continue
            app = inventory.get(journey["app"], {})
            timeout = journey.get("timeout_s", defaults.get("timeout_s", 20))
            budget = journey.get("latency_budget_ms", defaults.get("latency_budget_ms", 3000))
            folder = output / str(len(rows))
            folder.mkdir(exist_ok=True)
            iterator = (
                browser_steps(app["url"], journey, headers, timeout, folder / "screen.png")
                if browser and app.get("url")
                else None
            )
            for index, step in enumerate(journey["steps"]):
                start, code, stage = time.perf_counter(), -1, ""
                try:
                    if iterator:
                        code, stage, ms = next(iterator)
                    else:
                        code, stage = http_step(app["url"], step, headers, timeout)
                        ms = round((time.perf_counter() - start) * 1000, 1)
                except Exception as exc:  # noqa: BLE001 — persist failed checks, never exception text/secrets
                    stage, ms = failure_stage(exc), round((time.perf_counter() - start) * 1000, 1)
                rows.append(
                    {
                        "workspace_id": ws,
                        "run_id": run_id,
                        "run_ts": ts,
                        "app": journey["app"],
                        "journey": journey["name"],
                        "step": index,
                        "step_name": step.get("name", f"step {index + 1}"),
                        "ok": not stage,
                        "status_code": code,
                        "latency_ms": ms,
                        "within_budget": ms <= budget,
                        "detail": stage,
                        "kind": "playwright" if browser else "http",
                        "failure_stage": stage,
                        "artifact": "",
                    }
                )
                if stage:
                    break
            if iterator:
                try:
                    next(iterator, None)  # finish screenshot and browser cleanup
                finally:
                    iterator.close()
            journey_rows = [
                r for r in rows if r["app"] == journey["app"] and r["journey"] == journey["name"]
            ]
            failed = next((r for r in journey_rows if not r["ok"]), None)
            # Only this last row participates in corroboration, after all steps arrive.
            rows.append(
                {
                    **(failed or journey_rows[-1]),
                    "step": -1,
                    "step_name": "journey complete",
                    "ok": failed is None,
                    "latency_ms": sum(r["latency_ms"] for r in journey_rows),
                    "within_budget": all(r["within_budget"] for r in journey_rows),
                }
            )
            volume = (
                os.environ.get("SYNTHETIC_ARTIFACT_VOLUME")
                or f"/Volumes/{catalog}/{schema}/ui_tests"
            )
            if volume:
                artifact = volume.rstrip("/") + f"/{run_id}/{folder.name}"
                journey_rows = [
                    r
                    for r in rows
                    if r["app"] == journey["app"] and r["journey"] == journey["name"]
                ]
                try:
                    workspace.artifact(artifact + "/result.json", json.dumps(journey_rows).encode())
                    if (folder / "screen.png").exists():
                        workspace.artifact(
                            artifact + "/screen.png", (folder / "screen.png").read_bytes()
                        )
                    for row in journey_rows:
                        row["artifact"] = artifact
                except Exception:  # noqa: BLE001 — SQL evidence is more important than screenshots
                    print("UC artifact upload unavailable; persisting check results")
        (output / "results.json").write_text(json.dumps(rows, indent=2))
        for row in rows:
            workspace.sql(INSERT, {"table": table, **row})
        if args.status:
            monitor = https_url(os.environ["MONITOR_URL"])
            code, body, _ = request(monitor + "/api/status", headers=workspace.headers)
            if code != 200:
                raise RuntimeError("Status snapshot unavailable")
            public = output / "public"
            public.mkdir(exist_ok=True)
            public.joinpath("status.json").write_text(
                json.dumps(
                    sanitize_status(
                        json.loads(body), json.loads(os.environ.get("PUBLIC_STATUS_APPS") or "{}")
                    )
                )
            )
            public.joinpath("index.html").write_text(
                Path("app/static/status.html")
                .read_text()
                .replace('data-source="/api/status"', 'data-source="status.json"')
            )
    except Exception as exc:  # noqa: BLE001 — credentials must never appear in Actions logs
        (output / "results.json").write_text(json.dumps(rows, indent=2))
        (output / "runner.json").write_text(
            json.dumps(
                {
                    "completed": False,
                    "failure_stage": phase if phase == "auth" else failure_stage(exc),
                    "error_type": type(exc).__name__,
                }
            )
        )
        print(
            f"External synthetics failed: {type(exc).__name__}; no credentials or response bodies logged"
        )
        return 1
    return int(any(not r["ok"] for r in rows))


if __name__ == "__main__":
    raise SystemExit(main())
