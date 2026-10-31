"""S10–S13 read-only routes, composed with the monitor's existing handlers."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from reach_logic import CallerRateLimit, uptime_bars
from starlette.routing import Route

import queries as q

log = logging.getLogger("monitor.reach")
TOOL_NAMES = (
    "fleet_summary",
    "app_overview",
    "error_groups",
    "trace",
    "cost_summary",
    "open_alerts",
    "slo_status",
)


def caller(headers):
    return next(
        (
            headers.get(h)
            for h in ("x-forwarded-email", "x-forwarded-preferred-username", "x-forwarded-user")
            if headers.get(h)
        ),
        None,
    )


def authenticated(request: Request):
    # Apps ingress authenticates OAuth and injects these headers. Do not expose this
    # process directly on the internet behind a proxy that preserves caller headers.
    identity = caller(request.headers)
    if not identity:
        raise HTTPException(401, "Workspace authentication required")
    return identity


async def optional(query, **params):
    try:
        return {"available": True, "rows": await q.run(query, **params)}
    except Exception:  # noqa: BLE001 — SLO/mute objects may not have been deployed
        log.warning("optional reach data unavailable")
        return {"available": False, "rows": []}


def create_mcp(handlers, slo_status):
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

    # The authenticated Apps ingress serves the public host, not FastMCP's localhost server.
    mcp = FastMCP(
        "Apps Monitor",
        host="0.0.0.0",
        stateless_http=True,
        json_response=True,
        streamable_http_path="/mcp",
    )

    async def fleet_summary() -> dict:
        return await handlers["api_fleet"]()

    async def app_overview(app: str) -> dict:
        return await handlers["api_overview"](app)

    async def error_groups(app: str) -> dict:
        result = await handlers["api_errors"](app)
        return {"groups": result["groups"]}

    async def trace(trace_id: str) -> dict:
        return await handlers["api_trace"](trace_id)

    async def cost_summary() -> dict:
        return await handlers["api_cost_summary"]()

    async def open_alerts() -> dict:
        result = await handlers["api_alerts"]()
        return {"active": result["active"]}

    for fn in (
        fleet_summary,
        app_overview,
        error_groups,
        trace,
        cost_summary,
        open_alerts,
        slo_status,
    ):
        mcp.tool(
            annotations=ToolAnnotations(
                readOnlyHint=True, destructiveHint=False, idempotentHint=True
            )
        )(fn)
    return mcp


class MCPIngress:
    def __init__(self, app, limiter):
        self.app, self.limiter = app, limiter

    async def __call__(self, scope, receive, send):
        request = Request(scope)
        identity = caller(request.headers)
        if not identity:
            response = JSONResponse({"error": "Workspace authentication required"}, status_code=401)
        elif not self.limiter.allow(identity):
            response = JSONResponse(
                {"error": "Rate limit exceeded"}, status_code=429, headers={"Retry-After": "60"}
            )
        else:
            await self.app(scope, receive, send)
            return
        await response(scope, receive, send)


def build_router(handlers):
    async def slo_status(app: str = "") -> dict:
        return await optional(q.REACH_SLO, app=app)

    try:
        mcp = create_mcp(handlers, slo_status)
        transport = mcp.streamable_http_app()
    except ModuleNotFoundError as exc:
        if exc.name != "mcp":
            raise
        mcp = None
        log.warning("MCP unavailable: install app/requirements.txt in the app runtime")

    @asynccontextmanager
    async def lifespan(_app):
        if mcp:
            async with mcp.session_manager.run():
                yield
        else:
            yield

    router = APIRouter(lifespan=lifespan, dependencies=[Depends(authenticated)])
    if mcp:
        router.routes.append(
            Route(
                "/mcp", MCPIngress(transport, CallerRateLimit()), methods=["GET", "POST", "DELETE"]
            )
        )
    else:

        @router.api_route("/mcp", methods=["GET", "POST", "DELETE"])
        async def missing_mcp():
            raise HTTPException(503, "MCP runtime dependency is unavailable")

    @router.get("/status", include_in_schema=False)
    async def status_page():
        return FileResponse(Path(__file__).parent / "static" / "status.html")

    @router.get("/api/status")
    async def status():
        ws = str(await asyncio.to_thread(handlers["_workspace_id"]))
        incidents, maintenance, slos = await asyncio.gather(
            optional(q.REACH_INCIDENTS, ws=ws),
            optional(q.REACH_MAINTENANCE, ws=ws),
            slo_status(),
        )
        now = time.time()
        apps = []
        for name, info in sorted(handlers["fleet"].items()):
            summary = handlers["_summary"](name)
            apps.append(
                {
                    "name": name,
                    "workspace_id": ws,
                    "status": handlers["_status"](info, summary),
                    "uptime_24h": summary["uptime_24h"],
                    "bars": uptime_bars(handlers["probes"].get(name, ()), now),
                    "slos": [r for r in slos["rows"] if r["name"] == name],
                }
            )
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "apps": apps,
            "incidents": incidents["rows"],
            "maintenance": maintenance["rows"],
            "available": {
                "incidents": incidents["available"],
                "maintenance": maintenance["available"],
                "slos": slos["available"],
            },
        }

    @router.get("/api/reach/fleet")
    async def federated_fleet(workspace_id: str = ""):
        return {
            "mode": q.DEPLOYMENT_MODE,
            "apps": await q.run(q.REACH_FLEET, ws=workspace_id)
            if q.DEPLOYMENT_MODE == "hub"
            else [],
        }

    @router.get("/api/reach/slos")
    async def slos(app: str = ""):
        return await slo_status(app)

    return router
