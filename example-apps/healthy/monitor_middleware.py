"""Golden-envelope middleware for Databricks Apps — copy this file into your app.

Every request's server span gets the correlation envelope (request id, session id,
hashed user, app name/version, journey step), so OTel logs/spans/metrics from every
fleet app can be joined in the monitor schema. Pair with:
  - `opentelemetry-instrument` in your app command (auto spans for FastAPI/httpx/requests)
  - `telemetry_export_destinations` on the app resource (ships telemetry to UC)
See docs/INSTRUMENTATION.md in the databricks-apps-monitor repo for the full contract.

Usage:
    from monitor_middleware import install
    app = install(FastAPI())
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from opentelemetry import trace
from starlette.requests import Request  # fastapi dependency; module-level so the
from starlette.responses import Response

# stringified annotation (from __future__ import annotations) resolves for FastAPI

AppT = TypeVar("AppT")

APP_NAME = os.environ.get("DATABRICKS_APP_NAME") or os.environ.get("OTEL_SERVICE_NAME", "app")
APP_VERSION = os.environ.get("APP_VERSION", "0.1.0")

# Zerobus silently drops log lines > 1 MB — stay far under so nothing vanishes.
_MAX_LOG_CHARS = 60_000


class _TruncateLongLines(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str) and len(record.msg) > _MAX_LOG_CHARS:
            record.msg = record.msg[:_MAX_LOG_CHARS] + f"…[truncated, was {len(record.msg)} chars]"
            record.args = ()
        return True


def _hash(value: str | None) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16] if value else "anon"


def install(app: AppT) -> AppT:
    root = logging.getLogger()
    root.addFilter(_TruncateLongLines())
    for h in root.handlers:  # the OTel log handler sits on root — guard it too
        h.addFilter(_TruncateLongLines())
    fastapi_app: Any = app  # duck-typed: anything with .post()/.middleware() (FastAPI)

    @fastapi_app.post("/monitor/feedback")  # type: ignore[untyped-decorator]  # duck-typed FastAPI
    async def monitor_feedback(
        request: Request,
    ) -> dict[str, bool]:  # user feedback → otel_logs (native pipeline, no extra infra)
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
        env = getattr(request.state, "monitor", {})
        logging.getLogger("monitor.feedback").info(
            json.dumps(
                {
                    "event": "feedback",
                    "rating": max(1, min(5, int(body.get("rating") or 0) or 3)),
                    "comment": str(body.get("comment") or "")[:500],
                    "rid": env.get("rid"),
                    "sid": env.get("sid"),
                    "user": env.get("user"),
                }
            )
        )
        return {"ok": True}

    @fastapi_app.middleware("http")  # type: ignore[untyped-decorator]  # duck-typed FastAPI
    async def golden_envelope(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        sid = request.cookies.get("monitor_session") or uuid.uuid4().hex[:12]
        user = _hash(
            request.headers.get("x-forwarded-user") or request.headers.get("x-forwarded-email")
        )
        # handlers read the envelope here (e.g. to tag MLflow traces / gateway calls)
        request.state.monitor = {"rid": rid, "sid": sid, "user": user}

        span = trace.get_current_span()
        span.set_attribute("app.client_request_id", rid)
        span.set_attribute("session.id", sid)
        span.set_attribute("user.id_hash", user)
        span.set_attribute("app.name", APP_NAME)
        span.set_attribute("app.version", APP_VERSION)

        response = await call_next(request)

        # journey step = route template (low cardinality), known only after routing
        route = request.scope.get("route")
        span.set_attribute("journey.step", getattr(route, "path", request.url.path))

        response.headers["x-request-id"] = rid
        if "monitor_session" not in request.cookies:
            response.set_cookie("monitor_session", sid, httponly=True)
        return response

    return app
