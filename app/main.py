"""apps-monitor — Application Insights for Databricks Apps.

Live fleet board: Apps API inventory + periodic HTTP probes authenticated with the
app's own service principal OAuth (same mechanism as the playwright monitoring DAB).

Design (docs/PLAN.md): warm data stays in memory; durable history rides the platform
OTel export (probe calls are auto-instrumented httpx client spans + a custom
histogram metric) into UC. The SQL warehouse is only queried on demand.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import httpx
import uvicorn
from auth import require_admin
from databricks.sdk import WorkspaceClient
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from opentelemetry import metrics, trace
from routes_ops import router as ops_router
from synthetic import capacity_path, capacity_url, synthetic_headers

import alerts
import mlflow_traces as mt
import queries as q

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger("monitor")

PROBE_INTERVAL = int(os.environ.get("PROBE_INTERVAL_SECONDS", "60"))
FLEET_REFRESH = int(os.environ.get("FLEET_REFRESH_SECONDS", "120"))
SYNTH_INTERVAL = int(os.environ.get("SYNTH_INTERVAL_SECONDS", "1800"))
HISTORY_POINTS = max(1, 24 * 60 * 60 // PROBE_INTERVAL)  # 24 h ring buffer
STATIC_DIR = Path(__file__).parent / "static"

w = WorkspaceClient()

# Genie space iframe (docs.databricks.com/aws/en/genie/embed) — app domain is on the
# workspace approved-embedding-domains list; users auth via their own workspace session.
_genie_space = os.environ.get("MONITOR_GENIE_SPACE_ID", "")
if _genie_space.lower() == "unset":
    _genie_space = ""
GENIE_EMBED_URL = (
    f"https://{w.config.host.removeprefix('https://')}/embed/genie/rooms/{_genie_space}"
    if _genie_space
    else ""
)

meter = metrics.get_meter("monitor")
probe_latency = meter.create_histogram(
    "monitor.probe.latency_ms", unit="ms", description="Fleet probe round-trip latency"
)
probe_checks = meter.create_counter("monitor.probe.checks", description="Fleet probe results")

fleet: dict[str, dict] = {}  # app name -> inventory info
_bg_tasks: set = set()  # keep create_task references alive
probes: dict[str, deque] = {}  # app name -> deque[(epoch, ok, http_code, ms)]
ttfbs: dict[str, deque] = {}  # app name -> deque[ms to first byte] (successful probes)
capacity: dict[str, dict] = {}  # app name -> last in-app capacity-ramp result
_capacity_lock = asyncio.Lock()
_ws_id: int | None = None


def _workspace_id() -> int:
    global _ws_id
    if _ws_id is None:
        _ws_id = w.get_workspace_id()
    return _ws_id


_last_fleet_refresh = 0.0
_last_probe_ts = 0.0


def _app_info(a) -> dict:
    return {
        "name": a.name,
        "url": a.url,
        "app_state": a.app_status.state.value if a.app_status and a.app_status.state else None,
        "app_message": a.app_status.message if a.app_status else None,
        "compute_state": a.compute_status.state.value
        if a.compute_status and a.compute_status.state
        else None,
        "creator": a.creator,
        "description": a.description,
        "update_time": a.update_time,
        "resources": [r.as_dict() for r in (getattr(a, "resources", None) or [])],
    }


def _experiment_of(name: str) -> str | None:
    for r in fleet.get(name, {}).get("resources", []):
        if r.get("experiment"):
            return str(r["experiment"].get("experiment_id"))
    return None


async def refresh_fleet() -> None:
    global _last_fleet_refresh
    try:
        apps = await asyncio.to_thread(lambda: list(w.apps.list()))
    except Exception:
        log.exception("apps.list failed")
        return
    names = set()
    for a in apps:
        names.add(a.name)
        fleet[a.name] = _app_info(a)
        probes.setdefault(a.name, deque(maxlen=HISTORY_POINTS))
    for gone in set(fleet) - names:
        fleet.pop(gone, None)
        probes.pop(gone, None)
    _last_fleet_refresh = time.time()
    try:
        ws = str(await asyncio.to_thread(_workspace_id))
        alerts.set_mutes(await q.run(q.ACTIVE_MUTES, ttl=0, ws=ws))
    except Exception:  # noqa: BLE001 — retain cached windows during a warehouse outage
        log.warning("mute refresh failed", exc_info=True)
    log.info("fleet refreshed: %d apps visible", len(fleet))


async def _probe_one(client: httpx.AsyncClient, name: str, url: str, headers: dict) -> None:
    headers = synthetic_headers(headers, "probe")
    code, placeholder, ttfb = -1, False, None
    start = time.perf_counter()
    try:
        # stream so time-to-first-byte (headers received) is observable separately —
        # the streaming SLO the p95 total hides (article: track TTFT, not just p95)
        async with client.stream("GET", f"{url}/healthz", headers=headers) as r:
            ttfb = round((time.perf_counter() - start) * 1000, 1)
            await r.aread()
        # a STOPPED app's URL serves an HTML placeholder with HTTP 200 — an HTML
        # answer to /healthz (that isn't a 404 fallback) means the app isn't running
        placeholder = r.status_code == 200 and "text/html" in r.headers.get("content-type", "")
        if r.status_code in (404, 405):
            r = await client.get(url + "/", headers=headers)
            placeholder = False
        code = r.status_code
    except Exception as e:  # noqa: BLE001 — a dead app must not kill the round
        log.warning("probe %s: %s", name, type(e).__name__)
    ms = round((time.perf_counter() - start) * 1000, 1)
    ok = 200 <= code < 400 and not placeholder
    probes.setdefault(name, deque(maxlen=HISTORY_POINTS)).append((time.time(), ok, code, ms))
    if ok and ttfb is not None:
        ttfbs.setdefault(name, deque(maxlen=60)).append(ttfb)
    attrs = {"probe.app": name, "probe.ok": str(ok).lower()}
    probe_latency.record(ms, attrs)
    probe_checks.add(1, attrs)


async def probe_round() -> None:
    global _last_probe_ts
    targets = [(n, i["url"]) for n, i in fleet.items() if i.get("url")]
    if not targets:
        return
    try:
        headers = await asyncio.to_thread(w.config.authenticate)
    except Exception:
        log.exception("SP token refresh failed")
        return
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
        await asyncio.gather(*(_probe_one(client, n, u, headers) for n, u in targets))
    _last_probe_ts = time.time()


# --------------------------------------------------------------- synthetics
# journeys run in-app: only the app's SP OAuth is accepted by app URLs
# (job-runtime tokens get 401/302 — see BUILDLOG). Results: memory + custom
# OTel spans (history lands in otel_spans via the telemetry pipeline).

JOURNEYS = json.loads((Path(__file__).parent / "journeys.json").read_text())
tracer = trace.get_tracer("monitor")
synth: dict[str, dict] = {}  # app name -> latest journey result
_last_synth = 0.0


async def run_journeys() -> None:
    global _last_synth
    defaults = JOURNEYS.get("defaults", {})
    auto = JOURNEYS.get("auto_journey")
    by_app = {j["app"]: j for j in JOURNEYS.get("journeys", [])}
    try:
        headers = await asyncio.to_thread(w.config.authenticate)
    except Exception:
        log.exception("synthetics token refresh failed")
        return
    async with httpx.AsyncClient(
        timeout=defaults.get("timeout_s", 20), follow_redirects=False
    ) as client:
        headers = synthetic_headers(headers, "journey")
        for name, info in list(fleet.items()):
            url = info.get("url")
            jn = by_app.get(name) or ({**auto, "app": name} if auto else None)
            if not url or not jn:
                continue
            budget = jn.get("latency_budget_ms", defaults.get("latency_budget_ms", 3000))
            steps = []
            with tracer.start_as_current_span("synthetic.journey") as span:
                span.set_attribute("journey.app", name)
                span.set_attribute("journey.name", jn["name"])
                for i, step in enumerate(jn["steps"]):
                    t0 = time.perf_counter()
                    ok, code, detail = False, -1, ""
                    try:
                        r = await client.request(
                            step.get("method", "GET"), url + step["path"], headers=headers
                        )
                        code = r.status_code
                        ok = code == step.get("expect_status", 200)
                        if (
                            ok
                            and "text/html" in r.headers.get("content-type", "")
                            and step["path"] != "/"
                        ):
                            ok, detail = False, "stopped-app placeholder page"
                        elif (
                            ok
                            and step.get("expect_contains")
                            and step["expect_contains"] not in r.text
                        ):
                            ok, detail = False, f"body missing '{step['expect_contains']}'"
                        elif not ok:
                            detail = f"expected {step.get('expect_status', 200)}, got {code}"
                    except Exception as e:  # noqa: BLE001
                        detail = type(e).__name__
                    ms = round((time.perf_counter() - t0) * 1000, 1)
                    steps.append(
                        {
                            "step": i,
                            "name": f"{step.get('method', 'GET')} {step['path']}",
                            "ok": ok,
                            "code": code,
                            "ms": ms,
                            "detail": detail,
                        }
                    )
                    if not ok:
                        break
                ok_all = all(s["ok"] for s in steps)
                span.set_attribute("journey.ok", ok_all)
                span.set_attribute("journey.steps", len(steps))
            synth[name] = {
                "journey": jn["name"],
                "ts": time.time(),
                "ok": ok_all,
                "steps": steps,
                "budget_ms": budget,
                "within_budget": all(s["ms"] <= budget for s in steps),
            }
    _last_synth = time.time()
    log.info(
        "synthetics: %d journeys, %d failing", len(synth), sum(not s["ok"] for s in synth.values())
    )


async def _persist_alerts(events: list[dict]) -> None:
    for e in events:
        try:
            await q.run_dml(
                q.INSERT_ALERT,
                ts=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                rule=e["rule"],
                app=e["app"],
                severity=e["severity"],
                message=e["message"],
                value=e["value"] if e["value"] is not None else 0,
                state=e["state"],
                muted=str(e.get("muted", False)).lower(),
                ws=str(await asyncio.to_thread(_workspace_id)),
            )
        except Exception:  # noqa: BLE001 — table appears after first inventory run
            log.warning("alert persist failed (alert_events table missing yet?)")


async def scheduler() -> None:
    while True:
        try:
            if time.time() - _last_fleet_refresh > FLEET_REFRESH:
                await refresh_fleet()
            await probe_round()
            if time.time() - _last_synth > SYNTH_INTERVAL:
                await run_journeys()
            events = alerts.evaluate(fleet, probes, _summary, synth)
            if events:
                await asyncio.to_thread(alerts.notify_webhook, events)
                task = asyncio.create_task(_persist_alerts(events))
                _bg_tasks.add(task)
                task.add_done_callback(_bg_tasks.discard)
        except Exception:
            log.exception("scheduler round failed")
        await asyncio.sleep(PROBE_INTERVAL)


# ---------------------------------------------------------------- aggregation


def _p95(vals: list[float]) -> float | None:
    if not vals:
        return None
    vs = sorted(vals)
    return vs[min(len(vs) - 1, int(0.95 * len(vs)))]


def _summary(name: str) -> dict:
    pts = list(probes.get(name, ()))
    last = pts[-1] if pts else None
    ok_lat = [p[3] for p in pts if p[1]]
    hour = [p for p in pts if p[0] > time.time() - 3600]
    return {
        "checks_24h": len(pts),
        "uptime_24h": round(100 * sum(p[1] for p in pts) / len(pts), 2) if pts else None,
        "p95_ms": round(_p95(ok_lat), 1) if ok_lat else None,
        "error_rate_1h": round(100 * sum(not p[1] for p in hour) / len(hour), 2) if hour else None,
        "last": {"ts": last[0], "ok": last[1], "code": last[2], "ms": last[3]} if last else None,
        "spark": [[1 if p[1] else 0, p[3]] for p in pts[-60:]],
    }


def _status(info: dict, s: dict) -> str:
    if info.get("app_state") not in ("RUNNING", None) or info.get("compute_state") not in (
        "ACTIVE",
        None,
    ):
        return "stopped"
    last = s.get("last")
    if not last:
        return "pending"
    pts = list(probes.get(info["name"], ()))
    if not last["ok"]:
        return "down" if len(pts) >= 2 and not pts[-2][1] else "degraded"
    if (s.get("error_rate_1h") or 0) > 5 or (s.get("p95_ms") or 0) > 2500:
        return "degraded"
    return "ok"


# ------------------------------------------------------------------- FastAPI


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        ws = str(await asyncio.to_thread(_workspace_id))
        alerts.rehydrate(await q.run(q.OPEN_ALERTS, ttl=0, ws=ws))
    except Exception:  # noqa: BLE001 — the table may not exist on the first deployment
        log.warning("alert rehydrate skipped", exc_info=True)
    task = asyncio.create_task(scheduler())
    yield
    task.cancel()


app = FastAPI(title="apps-monitor", lifespan=lifespan, docs_url=None, redoc_url=None)
app.include_router(ops_router)

# ---- workspace federation: each workspace runs its own monitor; the selector links them.
WORKSPACE_NAME = w.config.host.removeprefix("https://").split(".")[0]
try:
    WORKSPACES = json.loads(os.environ.get("MONITOR_WORKSPACES", "[]"))  # [{name, url}]
except Exception:  # noqa: BLE001
    WORKSPACES = []
if not any(x.get("name") == WORKSPACE_NAME for x in WORKSPACES):
    WORKSPACES.insert(0, {"name": WORKSPACE_NAME, "url": ""})  # "" = this one


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "apps_tracked": len(fleet), "last_probe": _last_probe_ts}


@app.get("/api/fleet")
async def api_fleet() -> dict:
    apps_payload = []
    for name in sorted(fleet):
        s = _summary(name)
        apps_payload.append({**fleet[name], **s, "status": _status(fleet[name], s)})
    statuses = [a["status"] for a in apps_payload]
    all_ok_lat = [p[3] for d in probes.values() for p in d if p[1]]
    up = [a["uptime_24h"] for a in apps_payload if a["uptime_24h"] is not None]
    err = [a["error_rate_1h"] for a in apps_payload if a["error_rate_1h"] is not None]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "probe_interval": PROBE_INTERVAL,
        "genie_url": GENIE_EMBED_URL,
        "workspace": WORKSPACE_NAME,
        "workspaces": WORKSPACES,
        "kpis": {
            "apps_total": len(apps_payload),
            "apps_ok": sum(s == "ok" for s in statuses),
            "apps_down": sum(s == "down" for s in statuses),
            "availability_24h": round(sum(up) / len(up), 2) if up else None,
            "p95_ms": round(_p95(all_ok_lat), 1) if all_ok_lat else None,
            "error_rate_1h": round(sum(err) / len(err), 2) if err else None,
            "cost_today_usd": None,  # iteration 5
            "critical_findings": None,  # iteration 3
        },
        "attention": [a for a in apps_payload if a["status"] in ("down", "degraded", "stopped")],
        "apps": apps_payload,
    }


@app.get("/api/apps/{name}")
async def api_app(name: str) -> dict:
    if name not in fleet:
        raise HTTPException(404, f"unknown app: {name}")
    pts = list(probes.get(name, ()))
    tf = list(ttfbs.get(name, ()))
    return {
        **fleet[name],
        **_summary(name),
        "series": [[round(p[0]), 1 if p[1] else 0, p[2], p[3]] for p in pts],
        "ttfb_ms": round(sum(tf) / len(tf), 1) if tf else None,
        "ttfb_last_ms": tf[-1] if tf else None,
    }


# ------------------------------------------------- telemetry pages (UC otel_*)


async def _q(coro):
    try:
        return await coro
    except Exception as e:
        raise HTTPException(502, f"telemetry query failed: {e}") from e


@app.get("/api/apps/{name}/requests")
async def api_requests(name: str, hours: float = 24) -> dict:
    hours = min(hours, 168)
    return {
        "timeline": await _q(q.run(q.requests_timeline(hours), app=name, since=q.since(hours))),
        "routes": await _q(q.run(q.ROUTES, app=name, since=q.since(hours))),
    }


@app.get("/api/apps/{name}/errors")
async def api_errors(name: str, hours: float = 24) -> dict:
    hours = min(hours, 168)
    groups: list = []
    try:
        groups = await q.run(q.ERROR_GROUPS, ttl=300, app=name)
    except Exception:  # noqa: BLE001 — view appears after first gold run
        pass
    return {
        "failed_requests": await _q(q.run(q.ERROR_SPANS, app=name, since=q.since(hours))),
        "error_logs": await _q(q.run(q.ERROR_LOGS, app=name, since=q.since(hours))),
        "groups": groups,
    }


@app.get("/api/apps/{name}/logs")
async def api_logs(name: str, hours: float = 1) -> dict:
    return {"logs": await _q(q.run(q.LOGS_TAIL, ttl=15, app=name, since=q.since(min(hours, 48))))}


@app.get("/api/apps/{name}/traces")
async def api_traces(name: str, hours: float = 1) -> dict:
    return {"traces": await _q(q.run(q.TRACES, app=name, since=q.since(min(hours, 48))))}


@app.get("/api/traces/{tid}")
async def api_trace(tid: str) -> dict:
    return {
        "spans": await _q(q.run(q.TRACE_SPANS, tid=tid)),
        "logs": await _q(q.run(q.TRACE_LOGS, tid=tid)),
    }


@app.get("/api/apps/{name}/security")
async def api_security(name: str) -> dict:
    scan = await _q(q.run(q.SCAN_LATEST, ttl=300, app=name))
    findings = await _q(q.run(q.FINDINGS_LATEST, ttl=300, app=name)) if scan else []
    return {"scan": scan[0] if scan else None, "findings": findings}


@app.get("/api/security/summary")
async def api_security_summary() -> dict:
    rows = await _q(q.run(q.SECURITY_SUMMARY, ttl=600))
    return rows[0] if rows else {}


@app.get("/api/apps/{name}/overview")
async def api_overview(name: str) -> dict:
    """The tech-lead scorecard: one call composes reliability, quality, cost, adoption
    and recent activity from already-cached queries (partial data beats a 502)."""

    async def safe(query, **kw):
        try:
            return await q.run(query, **kw)
        except Exception:  # noqa: BLE001
            return []

    scan = await safe(q.SEC_BY_APP, ttl=600)
    review = await safe(q.REVIEW_BY_APP, ttl=600)
    cost7 = await safe(q.COST_FLEET, ttl=900)
    mtd = await safe(q.MTD_BY_APP, ttl=900)
    usage = await safe(q.USAGE_FLEET, ttl=600)
    forecast = await safe(q.FORECAST, ttl=900, app=name)
    cfg = await safe(q.CONFIG_GET, ttl=120, app=name)
    events = (await safe(q.ALERTS_APP, ttl=120, app=name))[:6]
    pick = lambda rows: next((r for r in rows if r.get("name") == name), None)  # noqa: E731
    return {
        "scan": pick(scan),
        "review": pick(review),
        "cost_7d": pick(cost7),
        "mtd": pick(mtd),
        "usage": pick(usage),
        "forecast": forecast[0] if forecast else None,
        "config": cfg[0] if cfg else None,
        "events": events,
        "synth": synth.get(name),
    }


@app.get("/api/apps/{name}/analytics")
async def api_analytics(name: str) -> dict:
    daily = await _q(q.run(q.USAGE_DAILY, ttl=300, app=name))
    users = await _q(q.run(q.USERS_TOP, ttl=300, app=name))
    mtd = []
    try:
        mtd = await q.run(q.MTD_BY_APP, ttl=900)
    except Exception:  # noqa: BLE001
        pass
    return {
        "daily": daily,
        "users": users,
        "mtd_usd": next((r["mtd_usd"] for r in mtd if r["name"] == name), None),
    }


@app.get("/api/apps/{name}/genai")
async def api_genai(name: str) -> dict:
    async def safe(query, **kw):
        try:
            return await q.run(query, **kw)
        except Exception:  # noqa: BLE001 — views appear as jobs run
            return []

    return {
        "daily": await _q(q.run(q.GENAI_DAILY, ttl=300, app=name)),
        "top": await _q(q.run(q.GENAI_TOP, ttl=300, app=name)),
        "error_taxonomy": await safe(q.GENAI_ERRORS, ttl=300, app=name),
        "agent_steps": await safe(q.AGENT_STEPS, ttl=300, app=name),
        "quality": await safe(q.QUALITY_APP, ttl=600, app=name),
        "feedback": await safe(q.FEEDBACK_APP, ttl=300, app=name),
        "feedback_recent": await safe(q.FEEDBACK_RECENT, ttl=300, app=name),
    }


@app.get("/api/apps/{name}/deps")
async def api_deps(name: str) -> dict:
    return {"deps": await _q(q.run(q.DEPS_7D, ttl=300, app=name))}


@app.get("/api/apps/{name}/timeline")
async def api_timeline(name: str) -> dict:
    events: list[dict] = []
    try:
        for r in await q.run(q.ALERTS_APP, ttl=120, app=name):
            events.append({"ts": r["ts"], "type": "alert", **r})
    except Exception:  # noqa: BLE001
        pass
    try:
        for r in await q.run(q.DEPLOYMENTS, ttl=300, app=name):
            events.append(
                {
                    "ts": r["create_time"],
                    "type": "deploy",
                    "message": f"deployment {(r['deployment_id'] or '')[:8]} · {r['state']}",
                    "state": r["state"],
                    "rule": "deployment",
                    "severity": "info",
                }
            )
    except Exception:  # noqa: BLE001
        pass
    releases = []
    try:
        releases = await q.run(q.RELEASES, ttl=300, app=name)
    except Exception:  # noqa: BLE001
        pass
    events.sort(key=lambda e: str(e["ts"]), reverse=True)
    return {"events": events[:120], "releases": releases}


@app.get("/api/apps/{name}/ops")
async def api_ops(name: str) -> dict:
    async def safe(query, **kw):
        try:
            return await q.run(query, **kw)
        except Exception:  # noqa: BLE001 — tables appear as jobs run
            return []

    cfg = await safe(q.CONFIG_GET, ttl=30, app=name)
    resources = fleet.get(name, {}).get("resources", [])
    job_ids = sorted(
        {
            int(j)
            for r in resources
            for j in [((r.get("job") or {}).get("id"))]
            if j and str(j).isdigit()
        }
    )
    job_health = []
    if job_ids:
        ws = await asyncio.to_thread(_workspace_id)
        job_health = await safe(
            q.JOB_HEALTH.format(ids=",".join(map(str, job_ids))), ttl=600, ws=str(ws)
        )
    return {
        "resources": resources,
        "deployments": await safe(q.DEPLOYMENTS, ttl=300, app=name),
        "permissions": await safe(q.PERMS_APP, ttl=600, app=name),
        "audit": await safe(q.AUDIT_APP, ttl=600, app=name),
        "releases": await safe(q.RELEASES, ttl=300, app=name),
        "config": cfg[0] if cfg else None,
        "telemetry_volume": await safe(q.TELEMETRY_VOLUME, ttl=600, app=name),
        "job_health": job_health,
        "capacity": capacity.get(name),
    }


@app.post("/api/apps/{name}/config")
async def api_config_save(name: str, body: dict, actor: str = Depends(require_admin)) -> dict:
    try:
        path = capacity_path(body.get("capacity_path"))
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    auto_stop = body.get("auto_stop", "none")
    if auto_stop not in ("none", "idle", "night", "budget"):
        raise HTTPException(400, "auto_stop must be none|idle|night|budget")
    tags_json = json.dumps(body.get("tags", {}))
    if len(tags_json) > 2000:
        raise HTTPException(400, "tags too large (max 2000 chars serialized)")
    try:
        await q.run_dml(
            q.CONFIG_UPSERT,
            app=name,
            tags=tags_json,
            budget=float(body.get("budget_usd_month") or 0) or 0,
            auto_stop=auto_stop,
            idle=int(body.get("idle_hours") or 24),
            who=actor,
            capacity_path=path if "capacity_path" in body else "",
            ws=str(await asyncio.to_thread(_workspace_id)),
        )
    except Exception as e:
        raise HTTPException(502, f"config save failed (has the inventory job run?): {e}") from e
    return {"ok": True}


@app.post("/api/actions/capacity/{name}")
async def api_capacity(name: str, actor: str = Depends(require_admin)) -> dict:
    """In-app step-ramp capacity probe (job tokens are rejected by app URLs, so this
    must run here with the monitor SP's OAuth). Bounded: 4 levels × 8 s, ≤8 concurrent."""
    info = fleet.get(name)
    if not info or not info.get("url"):
        raise HTTPException(404, f"unknown app: {name}")
    if _capacity_lock.locked():
        raise HTTPException(409, "a capacity run is already in progress")
    async with _capacity_lock:
        headers = synthetic_headers(await asyncio.to_thread(w.config.authenticate), "capacity")
        try:
            config = await q.run(q.CONFIG_GET, app=name)
        except Exception:  # noqa: BLE001 — capacity probing also works before gold creates config
            log.warning("capacity config unavailable; using default fallback")
            config = []
        fallback = config[0].get("capacity_path") if config else None
        levels, results = [1, 2, 4, 8], []
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
            url = await capacity_url(client, info["url"], fallback, headers)
            for c in levels:
                lat: list[float] = []
                errs = 0
                stop_at = time.perf_counter() + 8.0

                async def worker(stop_at: float = stop_at, lat: list[float] = lat):
                    nonlocal errs
                    while time.perf_counter() < stop_at:
                        t0 = time.perf_counter()
                        try:
                            r = await client.get(url, headers=headers)
                            if not 200 <= r.status_code < 300:
                                errs += 1
                            else:
                                lat.append((time.perf_counter() - t0) * 1000)
                        except Exception:  # noqa: BLE001
                            errs += 1

                with tracer.start_as_current_span("capacity.ramp") as span:
                    span.set_attribute("capacity.app", name)
                    span.set_attribute("capacity.concurrency", c)
                    await asyncio.gather(*(worker() for _ in range(c)))
                lat.sort()
                p95 = round(lat[int(len(lat) * 0.95)], 1) if lat else None
                qps = round(len(lat) / 8.0, 1)
                results.append(
                    {
                        "concurrency": c,
                        "qps": qps,
                        "p95_ms": p95,
                        "errors": errs,
                        "requests": len(lat),
                    }
                )
                if errs > len(lat) * 0.2 or (p95 and p95 > 5000):
                    break  # saturated — stop ramping
        base_p95 = results[0]["p95_ms"] or 1
        knee = max(
            (r for r in results if (r["p95_ms"] or 9e9) < 2 * base_p95 and not r["errors"]),
            key=lambda r: r["qps"],
            default=results[0],
        )
        capacity[name] = {
            "path": url.removeprefix(info["url"].rstrip("/")),
            "ts": time.time(),
            "levels": results,
            "max_healthy_qps": knee["qps"],
            "at_concurrency": knee["concurrency"],
            # article: operate at 60–70% of measured peak — latency rises non-linearly near saturation
            "recommended_qps": round(knee["qps"] * 0.65, 1),
        }
        return capacity[name]


@app.post("/api/actions/appctl/{name}/{action}")
async def api_appctl(name: str, action: str, actor: str = Depends(require_admin)) -> dict:
    if action not in ("stop", "start"):
        raise HTTPException(400, "action must be stop|start")
    job_id = os.environ.get("STOPPER_JOB_ID")
    if not job_id:
        raise HTTPException(500, "STOPPER_JOB_ID not configured")
    run = await asyncio.to_thread(
        lambda: w.jobs.run_now(job_id=int(job_id), job_parameters={"action": action, "app": name})
    )
    return {"run_id": run.run_id}


@app.post("/api/actions/provision")
async def api_provision(body: dict, actor: str = Depends(require_admin)) -> dict:
    app_name = (body.get("app_name") or "").strip().lower()
    if not app_name:
        raise HTTPException(400, "app_name required")
    job_id = os.environ.get("PROVISION_JOB_ID")
    if not job_id:
        raise HTTPException(500, "PROVISION_JOB_ID not configured")
    run = await asyncio.to_thread(
        lambda: w.jobs.run_now(
            job_id=int(job_id),
            job_parameters={
                "app_name": app_name,
                "team": body.get("team") or "unassigned",
                "cost_center": body.get("cost_center") or "unassigned",
                "env": body.get("env") or "dev",
            },
        )
    )
    return {"run_id": run.run_id, "app_name": app_name}


@app.get("/api/governance")
async def api_governance() -> dict:
    async def safe(query, **kw):
        try:
            return await q.run(query, **kw)
        except Exception:  # noqa: BLE001
            return []

    return {
        "chargeback": await safe(q.CHARGEBACK, ttl=600),
        "configs": await safe(q.CONFIGS_ALL, ttl=120),
        "mtd": await safe(q.MTD_BY_APP, ttl=900),
        "usage": await safe(q.USAGE_FLEET, ttl=600),
        "telemetry_active": [r["name"] for r in await safe(q.TELEMETRY_ACTIVE, ttl=600)],
        "audit": await safe(q.AUDIT_FLEET, ttl=600),
    }


@app.get("/api/fleet/enrich")
async def api_fleet_enrich() -> dict:
    """Per-app cost / scan / review for the fleet cards — partial data beats a 502."""
    out: dict = {
        "security": {},
        "reviews": {},
        "cost": {},
        "config": {},
        "mtd": {},
        "perf": {},
        "usage": {},
    }
    for key, query, ttl in (
        ("security", q.SEC_BY_APP, 600),
        ("reviews", q.REVIEW_BY_APP, 600),
        ("cost", q.COST_FLEET, 900),
        ("config", q.CONFIGS_ALL, 120),
        ("mtd", q.MTD_BY_APP, 900),
        ("perf", q.REAL_PERF_FLEET, 300),  # real-traffic p95 (probe RTT isn't user latency)
        ("usage", q.USAGE_FLEET, 600),
    ):
        try:
            for r in await q.run(query, ttl=ttl):
                out[key][r["name"]] = r
        except Exception:  # noqa: BLE001 — tables appear as the jobs run
            log.warning("enrich %s unavailable", key)
    try:
        rows = await q.run(q.REAL_P95_FLEETWIDE, ttl=300)
        out["real_fleet"] = rows[0] if rows else None
    except Exception:  # noqa: BLE001
        out["real_fleet"] = None
    return out


@app.get("/api/apps/{name}/review")
async def api_review(name: str) -> dict:
    rows = await _q(q.run(q.REVIEW_LATEST, ttl=300, app=name))
    overview = None
    try:  # overview_json lands with the first post-update review run
        ov = await q.run(q.REVIEW_OVERVIEW, ttl=300, app=name)
        if ov and ov[0].get("overview_json"):
            overview = json.loads(ov[0]["overview_json"])
    except Exception:  # noqa: BLE001
        pass
    return {"review": rows[0] if rows else None, "overview": overview}


@app.get("/api/apps/{name}/cost")
async def api_cost(name: str) -> dict:
    async def safe(query, **kw):
        try:
            return await q.run(query, **kw)
        except Exception:  # noqa: BLE001
            return []

    forecast = await safe(q.FORECAST, ttl=900, app=name)
    cfg = await safe(q.CONFIG_GET, ttl=120, app=name)
    mtd = await safe(q.MTD_BY_APP, ttl=900)
    return {
        "daily": await _q(q.run(q.COST_APP, ttl=600, app=name)),
        "forecast": forecast[0] if forecast else None,
        "budget": (cfg[0] if cfg else {}).get("budget_usd_month") if cfg else None,
        "mtd_usd": next((r["mtd_usd"] for r in mtd if r["name"] == name), None),
    }


@app.get("/api/cost/summary")
async def api_cost_summary() -> dict:
    rows = await _q(q.run(q.COST_SUMMARY, ttl=900))
    fleet_rows = await _q(q.run(q.COST_FLEET, ttl=900))
    return {**(rows[0] if rows else {}), "by_app": fleet_rows}


@app.get("/api/apps/{name}/agent-traces")
async def api_agent_traces(name: str) -> dict:
    exp = _experiment_of(name)
    if not exp:
        return {"experiment": None, "traces": []}
    try:
        traces = await asyncio.to_thread(mt.search, exp)
    except Exception as e:
        raise HTTPException(502, f"MLflow search failed (experiment {exp}): {e}") from e
    return {"experiment": exp, "traces": traces}


@app.get("/api/apps/{name}/agent-traces/{tid}")
async def api_agent_trace(name: str, tid: str) -> dict:
    exp = _experiment_of(name)
    try:
        data = await asyncio.to_thread(mt.get, tid)
    except Exception as e:
        raise HTTPException(502, f"MLflow get_trace failed: {e}") from e
    crid = data["info"].get("client_request_id")
    otel_spans, logs = [], []
    try:
        # span detail lives in otel_spans (dual export) — joined by MLflow trace id,
        # falling back to the golden-envelope client_request_id
        otel_spans = await q.run(q.OTEL_BY_MLFLOW, ttl=60, tid=tid, rid=crid or "-")
        tids = sorted({r["trace_id"] for r in otel_spans})
        if tids:
            logs = await q.run(q.TRACE_LOGS, ttl=60, tid=tids[0])
    except Exception:
        log.exception("otel correlation lookup failed")
    return {
        "mlflow": data,
        "otel_spans": otel_spans,
        "logs": logs,
        "client_request_id": crid,
        "mlflow_url": f"{w.config.host}/ml/experiments/{exp}/traces?selectedTraceId={tid}"
        if exp
        else None,
    }


@app.get("/api/alerts")
async def api_alerts() -> dict:
    recent: list = []
    try:
        recent = await q.run(q.RECENT_ALERTS, ttl=60)
    except Exception:  # noqa: BLE001 — table appears after first inventory run
        pass
    job_alerts = []
    try:
        job_alerts = await q.run(
            q.OPEN_JOB_ALERTS, ttl=60, ws=str(await asyncio.to_thread(_workspace_id))
        )
    except Exception:  # noqa: BLE001 — gold views may not exist on first deployment
        log.warning("open job alerts unavailable")
    return {"active": alerts.active() + job_alerts, "recent": recent}


@app.get("/api/apps/{name}/synthetics")
async def api_synthetics(name: str, hours: float = 24) -> dict:
    browser: list = []
    try:  # browser-mode job rows (with volume artifact path), if that job has ever run
        browser = await q.run(q.SYNTH_BROWSER, ttl=300, app=name)
    except Exception:  # noqa: BLE001 — artifact column appears after the job's first run
        try:
            browser = await q.run(q.SYNTH_RUNS, ttl=300, app=name, since=q.since(min(hours, 168)))
        except Exception:  # noqa: BLE001
            pass
    return {"live": synth.get(name), "interval_s": SYNTH_INTERVAL, "browser": browser}


@app.post("/api/actions/autostop-policy")
async def autostop_policy(body: dict, actor: str = Depends(require_admin)) -> dict:
    """Governance rule: apply an auto-stop mode fleet-wide. Scope 'all' skips the monitor
    itself and apps tagged env=prod; dry_run returns the target list without writing."""
    mode = body.get("auto_stop", "idle")
    if mode not in ("none", "idle", "night"):
        raise HTTPException(400, "auto_stop must be none|idle|night")
    idle_hours = max(1, int(body.get("idle_hours") or 24))
    dry = bool(body.get("dry_run"))
    cfgs: dict[str, dict] = {}
    tags: dict[str, dict] = {}
    try:
        for r in await q.run(q.CONFIGS_ALL, ttl=0):
            cfgs[r["name"]] = r
            try:
                tags[r["name"]] = json.loads(r.get("tags_json") or "{}")
            except Exception:  # noqa: BLE001
                tags[r["name"]] = {}
    except Exception:  # noqa: BLE001
        pass
    targets = [
        n for n in sorted(fleet) if n != "apps-monitor" and tags.get(n, {}).get("env") != "prod"
    ]
    if dry:
        return {"targets": targets, "mode": mode, "idle_hours": idle_hours, "dry_run": True}
    applied = []
    for n in targets:
        try:
            await q.run_dml(
                q.CONFIG_UPSERT,
                app=n,
                tags=json.dumps(tags.get(n, {})),
                budget=float(cfgs.get(n, {}).get("budget_usd_month") or 0) or 0,
                auto_stop=mode,
                idle=idle_hours,
                who=actor,
            )
            applied.append(n)
        except Exception as e:  # noqa: BLE001
            log.warning("autostop policy failed for %s: %s", n, e)
    return {"applied": applied, "mode": mode, "idle_hours": idle_hours}


@app.post("/api/actions/run-journeys")
async def trigger_journeys(actor: str = Depends(require_admin)) -> dict:
    await run_journeys()
    return {"ok": True, "failing": sum(not s["ok"] for s in synth.values())}


@app.post("/api/actions/review/{name}")
async def request_review(name: str, actor: str = Depends(require_admin)) -> dict:
    job_id = os.environ.get("REVIEW_JOB_ID")
    if not job_id:
        raise HTTPException(500, "REVIEW_JOB_ID not configured")
    run = await asyncio.to_thread(
        lambda: w.jobs.run_now(job_id=int(job_id), job_parameters={"only_app": name})
    )
    return {"run_id": run.run_id}


@app.post("/api/actions/refresh-inventory")
async def refresh_inventory(actor: str = Depends(require_admin)) -> dict:
    job_id = os.environ.get("INVENTORY_JOB_ID")
    if not job_id:
        raise HTTPException(500, "INVENTORY_JOB_ID not configured")
    run = await asyncio.to_thread(lambda: w.jobs.run_now(job_id=int(job_id)))
    await refresh_fleet()
    return {"run_id": run.run_id}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/icon.svg")
async def icon() -> FileResponse:
    return FileResponse(STATIC_DIR / "icon.svg", media_type="image/svg+xml")


# Alternative UI concepts under evaluation (same APIs, different UX visions).
# Served as static files so their shared _common.js module import resolves:
#   /ui/<concept>.html  →  fetches ../api/*  →  /api/*
if (STATIC_DIR / "ui").is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/ui", StaticFiles(directory=str(STATIC_DIR / "ui"), html=True), name="ui")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("DATABRICKS_APP_PORT", 8000)))
