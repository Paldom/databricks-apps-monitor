"""Copy-in Databricks Apps telemetry. See docs/INSTRUMENTATION.md for the v2 contract."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import importlib
import json
import logging
import math
import os
import platform
import re
import threading
import time
import traceback
import uuid
from collections.abc import Callable, Iterator, Mapping
from concurrent.futures import Future
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from importlib.metadata import distributions
from types import SimpleNamespace
from typing import Any, TypeVar
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, build_opener
from urllib.request import Request as UrlRequest

from opentelemetry import metrics, trace
from opentelemetry.trace import SpanKind, Status, StatusCode
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

AppT = TypeVar("AppT")
APP_NAME = os.getenv("DATABRICKS_APP_NAME") or os.environ.get("OTEL_SERVICE_NAME", "app")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
BOOT_ID, _BOOT = uuid.uuid4().hex, time.perf_counter()
_MAX_LOG_CHARS, _HEALTH_TIMEOUT = 60_000, 2.0
_ERROR_SPAN = "monitor.error_summary"
_RID = re.compile(r"[A-Za-z0-9._:-]{1,64}")
_DROP = {
    "process.command_line",
    "process.command_args",
    "db.statement",
    "db.query.text",
    "url.query",
}
_SCRUBS = (
    (r"Bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [redacted]"),
    (r"\beyJ[\w-]*\.[\w-]+\.[\w-]+", "[redacted]"),
    (r"\bdapi[a-z0-9]+", "[redacted]"),
    (r"[a-z0-9._%+-]{1,64}@[a-z0-9.-]{1,253}\.[a-z]{2,63}", "[email]"),
    (
        r"([?&](?:access_token|refresh_token|token|password|secret|code)=)[^&\s\"'<>]*",
        r"\1[redacted]",
    ),
)
_PATTERNS = [(re.compile(p, re.I), replacement) for p, replacement in _SCRUBS]
_REDACT, _cold_done, _startup_logged = False, False, False
_step: ContextVar[dict[str, str]] = ContextVar("monitor_step")
_policy_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_rum_buckets: dict[str, tuple[float, float]] = {}
_token_hist: Any = None


def _scrub(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe(value: Any, key: str = "", depth: int = 0) -> Any:
    if depth > 8:
        return "[redacted]"
    if isinstance(value, Status):
        return Status(value.status_code, _scrub(value.description) if value.description else None)
    extra = os.getenv("MONITOR_REDACT_EXTRA", "").replace(" ", "").split(",")
    if key in _DROP or (key and key in extra):
        return "[redacted]"
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, str):
        if key in {"url.full", "http.url", "http.target", "source"}:
            value = value.split("?", 1)[0].split("#", 1)[0]
            value = re.sub(r"(https?://)[^/]*@", r"\1[redacted]@", value)
        return _scrub(value)
    if isinstance(value, Mapping):
        return {_scrub(str(k)): _safe(v, str(k), depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v, key, depth + 1) for v in value]
    return value


class _SafeLog(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except (TypeError, ValueError):
            message = str(record.msg)
        if _REDACT:
            if record.exc_info:
                message += "\n" + logging.Formatter().formatException(record.exc_info)
            record.exc_info = None
            record.__dict__.update(
                _safe({k: v for k, v in record.__dict__.items() if k not in {"msg", "args"}})
            )
            record.exc_text = None
            message = _scrub(message)
        record.msg = message[:_MAX_LOG_CHARS]
        if len(message) > _MAX_LOG_CHARS:
            record.msg += f"…[truncated, was {len(message)} chars]"
        record.args = ()
        return True


_TruncateLongLines = _SafeLog


class _Redactor:
    # Wrap public mutation methods: on_start alone misses late auto-instrumentation attributes.
    def on_start(self, span: Any, parent_context: Any = None) -> None:
        span.set_attributes(_safe(span.attributes or {}))
        span.update_name(_scrub(span.name))
        setter = span.set_attribute
        span.set_attribute = lambda key, value: setter(key, _safe(value, key))
        for method in ("set_attributes", "add_event", "update_name", "set_status"):

            def wrap(original: Any) -> Any:
                return lambda *args, **kwargs: original(*_safe(args), **_safe(kwargs))

            setattr(span, method, wrap(getattr(span, method)))

    def on_end(self, span: Any) -> None:
        pass

    _on_ending = on_end

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


def _hash(value: str | None) -> str:
    key = os.getenv("MONITOR_HASH_KEY")
    return (
        hmac.new(key.encode(), value.encode(), hashlib.sha256).hexdigest()[:16]
        if key and value
        else hashlib.sha256(value.encode()).hexdigest()[:16]
        if value
        else "anon"
    )


def _fingerprint(exc: BaseException) -> str:
    frames = [
        f"{f.filename.replace(chr(92), '/').rsplit('/', 1)[-1]}:{f.name}"
        for f in traceback.extract_tb(exc.__traceback__)
        if "site-packages" not in f.filename
    ][-5:]
    return hashlib.sha256(f"{type(exc).__qualname__}|{'|'.join(frames)}".encode()).hexdigest()[:12]


def monitor_parentbased(sampler_arg: str | None = None) -> Any:
    sampling: Any = importlib.import_module("opentelemetry.sdk.trace.sampling")
    try:
        ratio = min(1.0, max(0.0, float(sampler_arg or "1")))
    except ValueError:
        ratio = 1.0
    inner = sampling.ParentBased(root=sampling.TraceIdRatioBased(ratio))

    class ErrorBiased(sampling.Sampler):  # type: ignore[misc]
        def should_sample(
            self, parent_context: Any, trace_id: int, name: str, *args: Any, **kwargs: Any
        ) -> Any:
            if name == _ERROR_SPAN:
                return sampling.SamplingResult(sampling.Decision.RECORD_AND_SAMPLE)
            return inner.should_sample(parent_context, trace_id, name, *args, **kwargs)

        def get_description(self) -> str:
            return f"MonitorParentBased(ratio={ratio})"

    return ErrorBiased()


class BudgetExceeded(Exception):
    """The monitor's cached policy blocks new LLM calls."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None  # Never forward the policy bearer token to a login or another host.


urlopen = build_opener(_NoRedirect()).open


def _policy() -> dict[str, Any]:
    base = os.getenv("MONITOR_URL", "").rstrip("/")
    if not base:
        return {}
    url = f"{base}/api/policy/{quote(APP_NAME, safe='')}"
    now = time.monotonic()
    if url not in _policy_cache or now - _policy_cache[url][0] >= 60:
        try:
            headers = (
                {"Authorization": f"Bearer {os.environ['DATABRICKS_TOKEN']}"}
                if os.getenv("DATABRICKS_TOKEN")
                else {}
            )
            with urlopen(UrlRequest(url, headers=headers), timeout=2) as response:
                raw = response.read(8193)
                data = json.loads(raw) if len(raw) <= 8192 else {}
            if not isinstance(data, dict):
                data = {}
        except Exception:  # noqa: BLE001 — a monitor failure must not block the app
            data = {}
        _policy_cache.clear()
        _policy_cache[url] = (now, data)
    return _policy_cache[url][1]


def _llm_error_class(exc: BaseException) -> str:
    code = getattr(exc, "status_code", None) or getattr(
        getattr(exc, "response", None), "status_code", None
    )
    text = f"{type(exc).__name__} {exc}".lower()
    if str(code) == "429" or "rate limit" in text or "ratelimit" in text:
        return "rate_limit"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if str(code) == "400" and any(w in text for w in ("safety", "policy", "content filter")):
        return "policy"
    if any(w in text for w in ("json", "schema", "validation")):
        return "schema"
    return "server" if re.fullmatch(r"5\d\d", str(code)) else type(exc).__name__


@contextmanager
def _span(name: str, **attrs: Any) -> Iterator[Any]:
    with trace.get_tracer("monitor_middleware").start_as_current_span(
        name,
        kind=SpanKind.CLIENT,
        attributes=attrs,
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        try:
            yield span
        except Exception as exc:
            span.set_attribute(
                "error.type", _llm_error_class(exc) if name != "sql.execute" else type(exc).__name__
            )
            span.set_status(Status(StatusCode.ERROR))
            raise


class _Usage:
    def __init__(self, span: Any) -> None:
        self.span, self.started = span, time.perf_counter()
        self.ttft: float | None = None
        self.tokens: tuple[int, int] | None = None

    def first_token(self) -> None:
        if self.ttft is None:
            self.ttft = (time.perf_counter() - self.started) * 1000

    def set(
        self,
        *,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> None:
        out = max(output_tokens or 0, 0)
        inp = max(total_tokens - out if total_tokens is not None else input_tokens or 0, 0)
        self.tokens = (inp, out)
        self.span.set_attributes(
            {"gen_ai.usage.input_tokens": inp, "gen_ai.usage.output_tokens": out}
        )


@contextmanager
def llm_call(model: str, *, streaming: bool = False, operation: str = "chat") -> Iterator[_Usage]:
    """One billable call; set() overwrites usage, and metrics emit once on exit."""
    global _token_hist
    if _policy().get("throttle") == "block":
        raise BudgetExceeded(APP_NAME)
    attrs: dict[str, str | bool] = {
        "gen_ai.request.model": model,
        "gen_ai.operation.name": operation,
    }
    attrs.update({"monitor.llm.billable": True, "monitor.llm.streaming": streaming})
    with _span(f"{operation} {model}", **attrs) as span:
        usage = _Usage(span)
        try:
            yield usage
        finally:
            if usage.ttft is not None:
                span.set_attribute("monitor.llm.ttft_ms", round(usage.ttft, 1))
            if usage.tokens is not None:
                if _token_hist is None:
                    _token_hist = metrics.get_meter("monitor_middleware").create_histogram(
                        "gen_ai.client.token.usage", unit="{token}"
                    )
                for direction, count in zip(("input", "output"), usage.tokens, strict=True):
                    _token_hist.record(
                        count, {"gen_ai.token.type": direction, "gen_ai.request.model": model}
                    )


@contextmanager
def trace_sql(warehouse_id: str, *, system: str = "databricks_sql") -> Iterator[SimpleNamespace]:
    """Record identifiers and row counts only, including on failure."""
    with _span("sql.execute", **{"db.system.name": system, "db.namespace": warehouse_id}) as span:
        result = SimpleNamespace(statement_id=None, rows=None)
        try:
            yield result
        finally:
            if result.statement_id:
                span.set_attribute("databricks.statement_id", str(result.statement_id))
            if isinstance(result.rows, int) and not isinstance(result.rows, bool):
                span.set_attribute("db.response.returned_rows", result.rows)


def _event(logger: str, request: Request | None = None, **body: Any) -> None:
    env = getattr(request.state, "monitor", {}) if request else {}
    logging.getLogger(f"monitor.{logger}").info(
        json.dumps(_safe({**body, **env}), ensure_ascii=False)
    )


def track(name: str, request: Request | None = None, **props: Any) -> None:
    values = {
        str(k)[:64]: _scrub(v)[:256] if isinstance(v, str) else v
        for k, v in list(props.items())[:20]
        if isinstance(v, (str, int, float, bool))
        and not (isinstance(v, float) and not math.isfinite(v))
    }
    _event(
        "events",
        request,
        event="custom",
        name=_scrub(name)[:64],
        event_id=uuid.uuid4().hex,
        props=values,
    )


def set_step(name: str) -> None:
    _step.get()["name"] = _scrub(name)[:64]


class _Health:
    def __init__(self, checks: Mapping[str, Callable[[], Any]]) -> None:
        self.checks, self.expires = checks, 0.0
        self.results: dict[str, Any] = {}
        self.pending: dict[str, Future[Any]] = {}
        self.lock = asyncio.Lock()

    def run(self, name: str, fn: Callable[[], Any]) -> None:
        started = time.perf_counter()
        try:
            ok, error = bool(fn()), None
        except Exception as exc:  # noqa: BLE001 — dependency failure is a health result
            ok, error = False, type(exc).__name__
        self.pending[name].set_result(
            {"ok": ok, "error": error, "ms": round((time.perf_counter() - started) * 1000, 1)}
        )

    async def get(self) -> JSONResponse:
        async with self.lock:
            if time.monotonic() >= self.expires:
                for name, fn in self.checks.items():
                    if name not in self.pending or self.pending[name].done():
                        self.pending[name] = Future()
                        threading.Thread(target=self.run, args=(name, fn), daemon=True).start()
                if self.pending:
                    await asyncio.wait(
                        [asyncio.wrap_future(f) for f in self.pending.values()],
                        timeout=_HEALTH_TIMEOUT,
                    )
                self.results = {
                    name: f.result()
                    if f.done()
                    else {"ok": False, "error": "timeout", "ms": _HEALTH_TIMEOUT * 1000}
                    for name, f in self.pending.items()
                }
                self.expires = time.monotonic() + 30
        ok = all(item["ok"] for item in self.results.values())
        body = {
            "status": "ok" if ok else "degraded",
            "version": APP_VERSION,
            "boot_id": BOOT_ID,
            "uptime_s": round(time.perf_counter() - _BOOT, 3),
            "checks": self.results,
        }
        return JSONResponse(body, status_code=200 if ok else 503)


def warehouse_ready(warehouse_id: str) -> Callable[[], bool]:
    def check() -> bool:
        client = importlib.import_module("databricks.sdk").WorkspaceClient()
        state = client.warehouses.get(warehouse_id).state
        return str(getattr(state, "value", state)) in {"RUNNING", "STOPPED", "STARTING", "STOPPING"}

    return check


def serving_ready(name: str) -> Callable[[], bool]:
    def check() -> bool:
        client = importlib.import_module("databricks.sdk").WorkspaceClient()
        state = client.serving_endpoints.get(name).state
        ready = getattr(state, "ready", None)
        return str(getattr(ready, "value", ready)) == "READY"

    return check


async def _body(request: Request, cap: int) -> dict[str, Any] | None:
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > cap:
            return None
        raw.extend(chunk)
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except (ValueError, RecursionError):
        return {}


def _same_origin(request: Request) -> bool:
    origin = request.headers.get("origin")
    if not origin:
        return request.headers.get("sec-fetch-site") == "same-origin"
    try:
        parsed, expected = urlsplit(origin), request.url
        port = 443 if parsed.scheme == "https" else 80
        return (
            parsed.scheme in {"http", "https"}
            and parsed.scheme == expected.scheme
            and parsed.hostname == expected.hostname
            and (parsed.port or port) == (expected.port or port)
            and not (
                parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment
            )
        )
    except ValueError:
        return False


def _rum_allow(sid: str) -> bool:
    now = time.monotonic()
    if len(_rum_buckets) >= 1024:
        for key, (_, last) in list(_rum_buckets.items()):
            if now - last >= 60:
                del _rum_buckets[key]
        if sid not in _rum_buckets and len(_rum_buckets) >= 1024:
            return False
    tokens, last = _rum_buckets.get(sid, (10.0, now))
    tokens = min(10.0, tokens + (now - last) / 6)
    _rum_buckets[sid] = (tokens - 1 if tokens >= 1 else tokens, now)
    return tokens >= 1


_RUM_JS = """\
(() => {
  const sample = Number(document.currentScript?.dataset.sample ?? '__SAMPLE__');
  if (!(sample > 0 && sample <= 1) || Math.random() >= sample) return;
  let q = [], rid = '';
  const path = value => { try { return new URL(value, location.href).pathname.slice(0, 128); } catch { return ''; } };
  const flush = () => {
    if (!q.length) return;
    const body = JSON.stringify({events: q.splice(0)});
    navigator.sendBeacon('/monitor/rum', new Blob([body], {type: 'application/json'}));
  };
  const push = ev => { q.push({...ev, path: path(location.href), rid, ts: Date.now()}); if (q.length >= 2) flush(); };
  addEventListener('error', e => push({type: 'error', message: String(e.message).slice(0, 400), source: path(e.filename), line: e.lineno}));
  addEventListener('unhandledrejection', e => push({type: 'unhandledrejection', message: String(e.reason?.message ?? e.reason).slice(0, 400)}));
  const view = () => push({type: 'view'});
  for (const method of ['pushState', 'replaceState']) {
    const original = history[method];
    history[method] = function (...args) { const result = original.apply(this, args); view(); return result; };
  }
  addEventListener('popstate', view); view();
  const fetch = window.fetch;
  window.fetch = async function (...args) {
    const response = await fetch.apply(this, args);
    if (new URL(response.url, location.href).origin === location.origin) rid = response.headers.get('x-request-id')?.slice(0, 64) || rid;
    return response;
  };
  let lcp = 0, cls = 0, windowCls = 0, firstShift = 0, lastShift = 0;
  const interactions = new Map();
  for (const type of ['largest-contentful-paint', 'layout-shift', 'event']) {
    try {
      new PerformanceObserver(list => list.getEntries().forEach(e => {
        if (type === 'largest-contentful-paint') lcp = e.startTime;
        if (type === 'layout-shift' && !e.hadRecentInput) {
          if (e.startTime - lastShift > 1000 || e.startTime - firstShift > 5000) { windowCls = 0; firstShift = e.startTime; }
          windowCls += e.value; lastShift = e.startTime; cls = Math.max(cls, windowCls);
        }
        if (type === 'event' && e.interactionId) {
          interactions.set(e.interactionId, Math.max(interactions.get(e.interactionId) || 0, e.duration));
          if (interactions.size > 200) interactions.delete([...interactions].sort((a, b) => a[1] - b[1])[0][0]);
        }
      })).observe({type, buffered: true, durationThreshold: 40});
    } catch {}
  }
  addEventListener('visibilitychange', () => {
    if (document.visibilityState !== 'hidden') return;
    const durations = [...interactions.values()].sort((a, b) => b - a);
    const inp = durations[Math.min(durations.length - 1, Math.floor((performance.interactionCount || interactions.size) / 50))] || 0;
    for (const [name, value] of Object.entries({LCP: lcp, CLS: cls, INP: inp})) push({type: 'vital', name, value});
    flush();
  });
  addEventListener('pagehide', flush); setInterval(flush, 10000);
})();
"""


def install(
    app: AppT,
    *,
    redact: bool = True,
    health_checks: Mapping[str, Callable[[], Any]] | None = None,
    rum: bool = False,
    rum_sample: float = 0.1,
) -> AppT:
    global _REDACT, _startup_logged
    _REDACT |= redact  # Redaction is process-wide; another app cannot disable it.
    root = logging.getLogger()
    for target in [root, *root.handlers]:
        if not any(isinstance(f, _SafeLog) for f in target.filters):
            target.addFilter(_SafeLog())
    provider: Any = trace.get_tracer_provider()
    if (
        redact
        and hasattr(provider, "add_span_processor")
        and not getattr(provider, "_monitor_redactor", False)
    ):
        provider.add_span_processor(_Redactor())
        provider._monitor_redactor = True
    health = _Health(health_checks or {})
    api: Any = app
    api.add_api_route("/monitor/health", health.get, methods=["GET"])

    async def ingest(request: Request) -> JSONResponse:
        kind = request.url.path.rsplit("/", 1)[-1]
        if kind == "rum" and not _same_origin(request):
            return JSONResponse({"error": "origin"}, status_code=403)
        body = await _body(request, 8192 if kind == "rum" else 4096)
        if body is None and kind != "feedback":
            return JSONResponse({"error": "too_large"}, status_code=413)
        body = body or {}
        if kind == "rum":
            sid = request.cookies.get("monitor_session", "")
            bucket = (
                sid
                if _RID.fullmatch(sid)
                else _hash(request.client.host if request.client else "unknown")
            )
            if not _rum_allow(bucket):
                return JSONResponse({"error": "rate_limited"}, status_code=429)
            _event("rum", request, event="rum", body=json.dumps(_safe(body)))
        elif kind == "event":
            props = body.get("props", {})
            props = (
                {k: v for k, v in props.items() if k not in {"name", "request"}}
                if isinstance(props, dict)
                else {}
            )
            track(
                str(body.get("name") or "event"),
                request,
                **props,
            )
        else:
            try:
                rating = max(1, min(5, int(body.get("rating") or 3)))
            except (ValueError, TypeError, OverflowError):
                rating = 3
            _event(
                "feedback",
                request,
                event="feedback",
                rating=rating,
                comment=_scrub(str(body.get("comment") or ""))[:500],
            )
        return JSONResponse({"ok": True})

    for kind in ("feedback", "event", "rum") if rum else ("feedback", "event"):
        api.add_api_route(f"/monitor/{kind}", ingest, methods=["POST"])
    if rum:

        async def script() -> Response:
            sample = rum_sample if math.isfinite(rum_sample) and 0 <= rum_sample <= 1 else 0.1
            return Response(
                _RUM_JS.replace("__SAMPLE__", str(sample)), media_type="application/javascript"
            )

        api.add_api_route("/monitor/rum.js", script, methods=["GET"])

    @api.middleware("http")  # type: ignore[untyped-decorator]
    async def envelope(request: Request, call_next: Any) -> Response:
        global _cold_done
        rid, cookie = (
            request.headers.get("x-request-id", ""),
            request.cookies.get("monitor_session", ""),
        )
        rid = rid if _RID.fullmatch(rid) else uuid.uuid4().hex
        sid = cookie if _RID.fullmatch(cookie) else uuid.uuid4().hex[:12]
        user = _hash(
            request.headers.get("x-forwarded-user") or request.headers.get("x-forwarded-email")
        )
        request.state.monitor = {"rid": rid, "sid": sid, "user": user}
        span = trace.get_current_span()
        box: dict[str, str] = {}
        span.set_attribute("app.client_request_id", rid)
        span.set_attribute("session.id", sid)
        span.set_attribute("user.id_hash", user)
        span.set_attribute("app.name", APP_NAME)
        span.set_attribute("app.version", APP_VERSION)
        kind = request.headers.get("x-monitor-synthetic", "real")
        span.set_attribute(
            "traffic.kind", kind if kind in {"probe", "journey", "capacity"} else "real"
        )
        token = _step.set(box)
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            fp = _fingerprint(exc)
            span.set_attribute("exception.fingerprint", fp)
            with (
                trace.get_tracer("monitor_middleware").start_as_current_span(_ERROR_SPAN)
                if not span.is_recording()
                else nullcontext(span) as error_span
            ):
                fields = {"exception.fingerprint": fp, "error.type": type(exc).__name__}
                error_span.set_attributes(fields)
                error_span.set_attribute("app.name", APP_NAME)
                error_span.set_status(Status(StatusCode.ERROR))
                log = logging.getLogger("monitor.errors")
                log.error("unhandled %s", type(exc).__name__, exc_info=exc, extra=fields)

            raise
        finally:
            span.set_attribute(
                "journey.step",
                box.get("name")
                or str(getattr(request.scope.get("route"), "path", request.url.path)),
            )
            _step.reset(token)
            if not _cold_done:
                _cold_done = True
                span.set_attribute(
                    "monitor.cold_start_ms", round((time.perf_counter() - _BOOT) * 1000, 1)
                )
        response.headers["x-request-id"] = rid
        if cookie != sid:
            response.set_cookie(
                "monitor_session", sid, httponly=True, secure=request.url.scheme == "https"
            )
        return response

    if not _startup_logged:
        _startup_logged = True
        try:
            packages = sorted(f"{d.metadata['Name']}=={d.version}"[:100] for d in distributions())[
                :400
            ]
        except Exception:  # noqa: BLE001 — inventory must not prevent startup
            packages = []
        _event(
            "lifecycle",
            event="startup",
            app=APP_NAME,
            boot_id=BOOT_ID,
            version=APP_VERSION,
            team=os.getenv("MONITOR_TEAM"),
            cost_center=os.getenv("MONITOR_COST_CENTER"),
            python=platform.python_version(),
            packages=packages,
        )
    return app
