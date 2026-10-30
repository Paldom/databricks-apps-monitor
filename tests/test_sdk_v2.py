"""SDK v2 contract: redaction, GenAI usage, health, RUM, policy, and the sampler."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import sys
import time
import types
from importlib.metadata import entry_points
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.sampling import Decision, Sampler
from opentelemetry.trace import (
    NonRecordingSpan,
    SpanContext,
    SpanKind,
    TraceFlags,
    set_span_in_context,
)
from starlette.requests import Request

import monitor_middleware as mm
from monitor_middleware import (
    _MAX_LOG_CHARS,
    BudgetExceeded,
    _hash,
    _TruncateLongLines,
    install,
    llm_call,
    monitor_parentbased,
    serving_ready,
    set_step,
    trace_sql,
    track,
    warehouse_ready,
)

_RID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


@pytest.fixture(autouse=True)
def _isolate_monitor_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MONITOR_URL", raising=False)
    mm._policy_cache.clear()
    mm._rum_buckets.clear()


def _with_span(app: Any) -> Any:
    async def wrapped(scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return
        with trace.get_tracer("t").start_as_current_span("test.request"):
            await app(scope, receive, send)

    return wrapped


def _named(exporter: InMemorySpanExporter, name: str) -> list[Any]:
    return [span for span in exporter.get_finished_spans() if span.name == name]


def _token_sum(reader: InMemoryMetricReader, model: str, token_type: str) -> float:
    data = reader.get_metrics_data()
    if data is None:
        return 0.0
    total = 0.0
    for resource in data.resource_metrics:
        for scope in resource.scope_metrics:
            for metric in scope.metrics:
                if metric.name != "gen_ai.client.token.usage":
                    continue
                for point in metric.data.data_points:
                    attrs = point.attributes
                    if attrs.get("gen_ai.request.model") != model:
                        continue
                    if attrs.get("gen_ai.token.type") != token_type:
                        continue
                    total += point.sum or 0
    return total


def _parent(sampled: bool) -> Context:
    flags = TraceFlags(TraceFlags.SAMPLED if sampled else 0)
    ctx = SpanContext(trace_id=0x10, span_id=0x20, is_remote=False, trace_flags=flags)
    return set_span_in_context(NonRecordingSpan(ctx))


class _Resp:
    def __init__(self, raw: bytes) -> None:
        self._raw = raw

    def read(self, size: int = -1) -> bytes:
        return self._raw

    def __enter__(self) -> _Resp:
        return self

    def __exit__(self, *_exc: object) -> bool:
        return False


class _Coded(Exception):
    def __init__(self, code: int, msg: str) -> None:
        super().__init__(msg)
        self.status_code = code


class _FromResponse(Exception):
    def __init__(self) -> None:
        super().__init__("nope")
        self.response = SimpleNamespace(status_code=429)


def test_redacts_query_and_extra_keys(
    monkeypatch: pytest.MonkeyPatch, span_exporter: InMemorySpanExporter
) -> None:
    monkeypatch.setenv("MONITOR_REDACT_EXTRA", "db.statement")
    monkeypatch.setattr(mm, "APP_NAME", "demo")
    app = install(FastAPI(), redact=True)

    @app.get("/x")
    async def handle() -> dict[str, bool]:
        return {"ok": True}

    with trace.get_tracer("redact").start_as_current_span(
        "leak",
        attributes={
            "url.full": "https://app.example/x?token=abc",
            "http.url": "https://app.example/x?token=abc",
            "http.target": "https://app.example/x?token=abc",
            "url.query": "token=abc",
            "process.command_line": "python abc",
            "db.statement": "select abc",
        },
    ):
        pass
    client = TestClient(_with_span(app))
    client.cookies.set("monitor_session", "sess-1")
    client.get(
        "/x",
        params={"token": "abc"},
        headers={"x-request-id": "fixed-id-123"},
    )
    finished = list(span_exporter.get_finished_spans())
    assert finished
    for span in finished:
        for value in (span.attributes or {}).values():
            assert "abc" not in str(value)
    leak = _named(span_exporter, "leak")[-1]
    assert leak.attributes["db.statement"] == "[redacted]"
    assert leak.attributes["url.query"] == "[redacted]"


def test_log_filter_scrubs_and_truncates_after_format() -> None:
    mm._REDACT = True
    filt = _TruncateLongLines()
    jwt = "eyJaaaaaaaa.bbbbbbbb.cccccccc"
    pat = "dapi" + ("a" * 20)
    record = logging.LogRecord(
        "t",
        logging.INFO,
        __file__,
        1,
        "user %s tok %s pat %s jwt %s",
        ("alice@example.com", "Bearer sekrit", pat, jwt),
        None,
    )
    assert filt.filter(record) is True
    assert "[email]" in record.msg
    assert "alice@example.com" not in record.msg
    assert "Bearer [redacted]" in record.msg
    assert "Bearer sekrit" not in record.msg
    assert pat not in record.msg
    assert jwt not in record.msg
    huge = logging.LogRecord(
        "t", logging.INFO, __file__, 1, "pre %s", ("z" * (_MAX_LOG_CHARS + 5000),), None
    )
    assert filt.filter(huge) is True
    assert huge.msg.startswith("pre ")
    assert not huge.msg.startswith("pre %s")
    assert len(huge.msg) < _MAX_LOG_CHARS + 100
    assert huge.msg.endswith("chars]")


def test_bad_request_ids_are_replaced() -> None:
    app = install(FastAPI())

    @app.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(app)
    bad = client.get("/ping", headers={"x-request-id": "bad id"})
    assert _RID_RE.fullmatch(bad.headers["x-request-id"])
    assert bad.headers["x-request-id"] != "bad id"
    long = client.get("/ping", headers={"x-request-id": "b" * 65})
    assert _RID_RE.fullmatch(long.headers["x-request-id"])
    assert long.headers["x-request-id"] != "b" * 65
    ok = client.get("/ping", headers={"x-request-id": "a" * 64})
    assert ok.headers["x-request-id"] == "a" * 64


def test_hash_hmac_when_key_set_else_sha256(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONITOR_HASH_KEY", "secret")
    expected = hmac.new(b"secret", b"alice@example.com", hashlib.sha256).hexdigest()[:16]
    plain = hashlib.sha256(b"alice@example.com").hexdigest()[:16]
    assert _hash("alice@example.com") == expected
    assert expected != plain
    monkeypatch.delenv("MONITOR_HASH_KEY")
    assert _hash("alice@example.com") == plain
    assert _hash("") == "anon"
    assert _hash(None) == "anon"


def test_streaming_records_last_usage_once(
    span_exporter: InMemorySpanExporter, metric_reader: InMemoryMetricReader
) -> None:
    before_in = _token_sum(metric_reader, "stream-model", "input")
    before_out = _token_sum(metric_reader, "stream-model", "output")
    with llm_call("stream-model", streaming=True) as usage:
        usage.first_token()
        usage.first_token()
        for i in range(5):
            usage.set(input_tokens=1000, output_tokens=i)
    span = _named(span_exporter, "chat stream-model")[-1]
    assert span.attributes["gen_ai.usage.input_tokens"] == 1000
    assert span.attributes["gen_ai.usage.output_tokens"] == 4
    assert span.attributes["monitor.llm.billable"] is True
    assert span.attributes["monitor.llm.streaming"] is True
    assert "monitor.llm.ttft_ms" in span.attributes
    assert span.kind is SpanKind.CLIENT
    assert _token_sum(metric_reader, "stream-model", "input") - before_in == 1000
    assert _token_sum(metric_reader, "stream-model", "output") - before_out == 4

    with llm_call("total-model") as usage:
        usage.set(total_tokens=100, output_tokens=40)
    total = _named(span_exporter, "chat total-model")[-1]
    assert total.attributes["gen_ai.usage.input_tokens"] == 60
    assert total.attributes["gen_ai.usage.output_tokens"] == 40

    with llm_call("zero-model") as usage:
        usage.set(total_tokens=0, output_tokens=0)
    zero = _named(span_exporter, "chat zero-model")[-1]
    assert zero.attributes["gen_ai.usage.input_tokens"] == 0
    assert zero.attributes["gen_ai.usage.output_tokens"] == 0


def test_llm_error_classes_and_billable(span_exporter: InMemorySpanExporter) -> None:
    cases: list[tuple[BaseException, str]] = [
        (_Coded(429, "x"), "rate_limit"),
        (Exception("rate limit"), "rate_limit"),
        (Exception("timed out"), "timeout"),
        (_Coded(400, "content filter"), "policy"),
        (Exception("schema validation"), "schema"),
        (_Coded(503, "boom"), "server"),
        (ValueError("nope"), "ValueError"),
        (_FromResponse(), "rate_limit"),
    ]
    for index, (exc, kind) in enumerate(cases):
        model = f"err-{index}"
        with pytest.raises(type(exc)), llm_call(model):
            raise exc
        span = _named(span_exporter, f"chat {model}")[-1]
        assert span.attributes["error.type"] == kind
        assert span.attributes["monitor.llm.billable"] is True


def test_fingerprint_ignores_line_numbers(monkeypatch: pytest.MonkeyPatch) -> None:
    def raiser(which: int) -> None:
        if which == 1:
            raise ValueError("one")
        raise ValueError("two")

    found: list[str] = []
    for which in (1, 2):
        try:
            raiser(which)
        except ValueError as exc:
            found.append(mm._fingerprint(exc))
    assert found[0] == found[1]

    frames = [
        SimpleNamespace(filename="/opt/site-packages/lib.py", name="lib", lineno=1),
        SimpleNamespace(filename="/app/routes.py", name="upload", lineno=10),
        SimpleNamespace(filename="/app/routes.py", name="upload", lineno=20),
    ]
    monkeypatch.setattr(mm.traceback, "extract_tb", lambda _tb: frames)
    try:
        raise ValueError("x")
    except ValueError as exc:
        got = mm._fingerprint(exc)
    raw = "ValueError|routes.py:upload|routes.py:upload"
    assert got == hashlib.sha256(raw.encode()).hexdigest()[:12]
    frames[1] = SimpleNamespace(filename="/app/routes.py", name="upload", lineno=11)
    frames[2] = SimpleNamespace(filename="/app/routes.py", name="upload", lineno=12)
    try:
        raise ValueError("y")
    except ValueError as exc:
        assert mm._fingerprint(exc) == got


def test_recording_span_skips_error_summary(
    caplog: pytest.LogCaptureFixture, span_exporter: InMemorySpanExporter
) -> None:
    app = install(FastAPI())

    @app.get("/boom")
    async def boom() -> dict[str, bool]:
        raise RuntimeError("nope")

    client = TestClient(_with_span(app), raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR, logger="monitor.errors"):
        response = client.get("/boom")
    assert response.status_code == 500
    reqs = _named(span_exporter, "test.request")
    assert len(reqs) == 1
    fp = reqs[0].attributes["exception.fingerprint"]
    assert not any(
        span.name == "monitor.error_summary" for span in span_exporter.get_finished_spans()
    )
    recs = [rec for rec in caplog.records if rec.name == "monitor.errors"]
    assert recs[-1].__dict__["exception.fingerprint"] == fp


def test_unrecorded_request_exports_error_summary(
    caplog: pytest.LogCaptureFixture, span_exporter: InMemorySpanExporter
) -> None:
    app = install(FastAPI())

    @app.get("/boom")
    async def boom() -> dict[str, bool]:
        raise RuntimeError("nope")

    client = TestClient(app, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR, logger="monitor.errors"):
        response = client.get("/boom")
    assert response.status_code == 500
    summaries = _named(span_exporter, "monitor.error_summary")
    assert len(summaries) == 1
    fp = summaries[0].attributes["exception.fingerprint"]
    recs = [rec for rec in caplog.records if rec.name == "monitor.errors"]
    assert recs[-1].__dict__["exception.fingerprint"] == fp


def test_health_ok_cache_and_degraded() -> None:
    bare = install(FastAPI())
    client = TestClient(bare)
    ok = client.get("/monitor/health")
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] == "ok"
    assert {"status", "version", "boot_id", "uptime_s", "checks"} <= set(body)
    assert body["checks"] == {}

    calls = {"n": 0}

    def down() -> bool:
        calls["n"] += 1
        return False

    app = install(FastAPI(), health_checks={"db": down})
    client = TestClient(app)
    first = client.get("/monitor/health")
    assert first.status_code == 503
    assert first.json()["status"] == "degraded"
    client.get("/monitor/health")
    assert calls["n"] == 1
    health = next(
        route.endpoint.__self__ for route in app.routes if route.path == "/monitor/health"
    )
    health.expires = 0
    client.get("/monitor/health")
    assert calls["n"] == 2


def test_health_hides_exception_text_and_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode() -> bool:
        raise RuntimeError("secret")

    app = install(FastAPI(), health_checks={"dep": explode})
    client = TestClient(app)
    response = client.get("/monitor/health")
    assert response.status_code == 503
    assert response.json()["checks"]["dep"]["error"] == "RuntimeError"
    assert "secret" not in response.text

    monkeypatch.setattr(mm, "_HEALTH_TIMEOUT", 0.05)

    def slow() -> bool:
        time.sleep(0.4)
        return True

    slow_app = install(FastAPI(), health_checks={"slow": slow})
    timed = TestClient(slow_app).get("/monitor/health")
    assert timed.status_code == 503
    assert timed.json()["checks"]["slow"]["error"] == "timeout"


def test_health_checks_run_concurrently() -> None:
    def slow() -> bool:
        time.sleep(0.2)
        return True

    app = install(FastAPI(), health_checks={"a": slow, "b": slow})
    client = TestClient(app)
    started = time.perf_counter()
    response = client.get("/monitor/health")
    assert time.perf_counter() - started < 0.5
    assert response.status_code == 200
    assert response.json()["checks"]["a"]["ok"] is True
    assert response.json()["checks"]["b"]["ok"] is True


def test_traffic_kind(span_exporter: InMemorySpanExporter) -> None:
    app = install(FastAPI())

    @app.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(_with_span(app))
    for kind in ("probe", "journey", "capacity"):
        client.get("/ping", headers={"x-monitor-synthetic": kind, "x-request-id": "fixed-id-123"})
    client.get("/ping", headers={"x-monitor-synthetic": "nope", "x-request-id": "fixed-id-123"})
    client.get("/ping", headers={"x-request-id": "fixed-id-123"})
    kinds = [span.attributes["traffic.kind"] for span in _named(span_exporter, "test.request")]
    assert kinds == ["probe", "journey", "capacity", "real", "real"]


def test_set_step_and_track(
    caplog: pytest.LogCaptureFixture, span_exporter: InMemorySpanExporter
) -> None:
    app = install(FastAPI())

    @app.get("/submit")
    async def submit(request: Request) -> dict[str, bool]:
        set_step("submit")
        track("report_generated", request, n=1, email="a@b.co", nested={"x": 1})
        return {"ok": True}

    @app.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/many")
    async def many(request: Request) -> dict[str, bool]:
        track("bulk", request, **{f"p{i}": i for i in range(21)})
        return {"ok": True}

    client = TestClient(_with_span(app))
    with caplog.at_level(logging.INFO, logger="monitor.events"):
        client.get("/submit", headers={"x-request-id": "fixed-id-123"})
        client.get("/ping", headers={"x-request-id": "fixed-id-123"})
        client.post("/many", headers={"x-request-id": "fixed-id-123"})
    reqs = _named(span_exporter, "test.request")
    assert reqs[0].attributes["journey.step"] == "submit"
    assert reqs[1].attributes["journey.step"] == "/ping"
    events = [
        json.loads(rec.getMessage()) for rec in caplog.records if rec.name == "monitor.events"
    ]
    report = events[0]
    assert report["name"] == "report_generated"
    assert report["event_id"]
    assert report["rid"]
    assert report["props"]["n"] == 1
    assert report["props"]["email"] == "[email]"
    assert "nested" not in report["props"]
    assert len(events[1]["props"]) == 20


def test_event_and_feedback_caps(caplog: pytest.LogCaptureFixture) -> None:
    app = install(FastAPI())
    client = TestClient(app)
    with caplog.at_level(logging.INFO, logger="monitor.events"):
        ok = client.post("/monitor/event", json={"name": "click", "props": {"email": "a@b.co"}})
    assert ok.json() == {"ok": True}
    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["props"]["email"] == "[email]"
    assert "a@b.co" not in caplog.records[-1].getMessage()
    too_big = client.post("/monitor/event", content=b"q" * 4097)
    assert too_big.status_code == 413

    with caplog.at_level(logging.INFO, logger="monitor.feedback"):
        oversized = client.post("/monitor/feedback", content=b"z" * 4097)
    assert oversized.json() == {"ok": True}
    feedback = json.loads(caplog.records[-1].getMessage())
    assert feedback["rating"] == 3
    assert feedback["comment"] == ""
    with caplog.at_level(logging.INFO, logger="monitor.feedback"):
        normal = client.post("/monitor/feedback", json={"rating": 4, "comment": "ping a@b.co"})
    assert normal.json() == {"ok": True}
    stored = json.loads(caplog.records[-1].getMessage())
    assert stored["comment"] == "ping [email]"
    assert len(stored["comment"]) <= 500
    assert "a@b.co" not in stored["comment"]


def test_rum_script_and_ingest(caplog: pytest.LogCaptureFixture) -> None:
    plain = TestClient(install(FastAPI()))
    assert plain.get("/monitor/rum.js").status_code == 404

    app = install(FastAPI(), rum=True, rum_sample=0.25)
    client = TestClient(app)
    script = client.get("/monitor/rum.js")
    assert script.status_code == 200
    assert script.headers["content-type"].startswith("application/javascript")
    text = script.text
    for needle in (
        "sendBeacon",
        "pushState",
        "PerformanceObserver",
        "unhandledrejection",
        "largest-contentful-paint",
        "0.25",
    ):
        assert needle in text

    evil = client.post("/monitor/rum", json={}, headers={"Origin": "https://evil.test"})
    assert evil.status_code == 403
    same = client.post("/monitor/rum", json={"events": []}, headers={"Origin": "http://testserver"})
    assert same.status_code == 200
    assert client.post("/monitor/rum", json={}).status_code == 403
    cross = client.post("/monitor/rum", json={}, headers={"sec-fetch-site": "cross-site"})
    assert cross.status_code == 403

    client.headers["origin"] = "http://testserver"
    client.cookies.clear()
    client.cookies.set("monitor_session", "sess-a")
    for _ in range(10):
        response = client.post("/monitor/rum", json={})
        assert response.status_code == 200
    limited = client.post("/monitor/rum", json={})
    assert limited.status_code == 429
    client.cookies.set("monitor_session", "sess-b")
    other = client.post("/monitor/rum", json={})
    assert other.status_code == 200

    huge = client.post(
        "/monitor/rum",
        content=b"x" * 8193,
        headers={"Origin": "http://testserver"},
    )
    assert huge.status_code == 413
    with caplog.at_level(logging.INFO, logger="monitor.rum"):
        logged = client.post(
            "/monitor/rum",
            json={"msg": "a@b.co"},
            headers={"Origin": "http://testserver"},
        )
    assert logged.status_code == 200
    message = caplog.records[-1].getMessage()
    assert "a@b.co" not in message
    assert "[email]" in message


def test_rum_allow_prunes_stale_buckets() -> None:
    old = time.monotonic() - 120
    mm._rum_buckets["old-sid"] = (0, old)
    assert mm._rum_allow("old-sid") is True
    mm._rum_buckets.clear()
    for index in range(1024):
        mm._rum_buckets[f"k{index}"] = (0, old)
    assert mm._rum_allow("fresh") is True
    assert mm._rum_buckets.keys() == {"fresh"}


def test_trace_sql_attributes_omit_statement_text(span_exporter: InMemorySpanExporter) -> None:
    with trace_sql("wh-1") as res:
        res.statement_id = "stmt-1"
        res.rows = 0
        res.sql = "select token from secrets"
    span = _named(span_exporter, "sql.execute")[-1]
    assert span.attributes["db.system.name"] == "databricks_sql"
    assert span.attributes["db.namespace"] == "wh-1"
    assert span.attributes["databricks.statement_id"] == "stmt-1"
    assert span.attributes["db.response.returned_rows"] == 0
    assert span.kind is SpanKind.CLIENT
    assert "select token" not in " ".join(str(value) for value in span.attributes.values())

    with trace_sql("wh-pg", system="postgresql"):
        pass
    pg = [
        item
        for item in span_exporter.get_finished_spans()
        if item.attributes and item.attributes.get("db.namespace") == "wh-pg"
    ][-1]
    assert pg.attributes["db.system.name"] == "postgresql"

    with pytest.raises(RuntimeError), trace_sql("wh-err"):
        raise RuntimeError("db")
    err = [
        item
        for item in span_exporter.get_finished_spans()
        if item.attributes and item.attributes.get("db.namespace") == "wh-err"
    ][-1]
    assert err.attributes["error.type"] == "RuntimeError"


def test_budget_fail_open_and_block(
    monkeypatch: pytest.MonkeyPatch, span_exporter: InMemorySpanExporter
) -> None:
    queue: list[Any] = []
    calls: list[dict[str, Any]] = []

    def fake(req: Any, timeout: float = 0) -> _Resp:
        calls.append(
            {"url": req.full_url, "auth": req.get_header("Authorization"), "timeout": timeout}
        )
        payload = queue.pop(0)
        if isinstance(payload, BaseException):
            raise payload
        return _Resp(payload)

    monkeypatch.setattr(mm, "urlopen", fake)
    monkeypatch.setattr(mm, "APP_NAME", "demo-app")
    monkeypatch.delenv("MONITOR_URL", raising=False)
    mm._policy_cache.clear()
    with llm_call("no-policy"):
        pass
    assert calls == []

    monkeypatch.setenv("MONITOR_URL", "http://monitor.example")
    monkeypatch.setenv("DATABRICKS_TOKEN", "dapi-secret")
    mm._policy_cache.clear()
    queue.append(b'{"throttle": "block"}')
    with pytest.raises(BudgetExceeded), llm_call("blocked-model"):
        raise AssertionError("body ran")
    assert calls[0]["url"] == "http://monitor.example/api/policy/demo-app"
    assert calls[0]["auth"] == "Bearer dapi-secret"
    assert calls[0]["timeout"] == 2.0
    assert not _named(span_exporter, "chat blocked-model")

    mm._policy_cache.clear()
    calls.clear()
    queue.append(b'{"throttle": "warn"}')
    with llm_call("warn-model"):
        pass
    with llm_call("warn-model"):
        pass
    assert len(calls) == 1

    for bad in (TimeoutError("t"), b"not-json", b"[1]"):
        mm._policy_cache.clear()
        calls.clear()
        queue.append(bad)
        ran = False
        with llm_call("open-model"):
            ran = True
        assert ran

    monkeypatch.delenv("DATABRICKS_TOKEN", raising=False)
    mm._policy_cache.clear()
    calls.clear()
    queue.append(b'{"throttle": "warn"}')
    with llm_call("no-token"):
        pass
    assert calls[0]["auth"] is None


def test_warehouse_and_serving_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    states = {"wh": "STOPPED"}
    updates = {"ep": "NOT_UPDATING"}

    class _Val:
        def __init__(self, value: str) -> None:
            self.value = value

    class _Warehouses:
        def get(self, warehouse_id: str) -> Any:
            return SimpleNamespace(state=_Val(states[warehouse_id]))

    class _Serving:
        def get(self, name: str) -> Any:
            return SimpleNamespace(
                state=SimpleNamespace(
                    ready=_Val("READY" if updates[name] != "UPDATE_FAILED" else "NOT_READY")
                )
            )

    class _Client:
        def __init__(self) -> None:
            self.warehouses = _Warehouses()
            self.serving_endpoints = _Serving()

    sdk = types.ModuleType("databricks.sdk")
    sdk.WorkspaceClient = _Client
    monkeypatch.setitem(sys.modules, "databricks", types.ModuleType("databricks"))
    monkeypatch.setitem(sys.modules, "databricks.sdk", sdk)
    for state in ("STOPPED", "RUNNING", "STARTING", "STOPPING"):
        states["wh"] = state
        assert warehouse_ready("wh")() is True
    states["wh"] = "ERROR"
    assert warehouse_ready("wh")() is False
    assert serving_ready("ep")() is True
    updates["ep"] = "UPDATE_FAILED"
    assert serving_ready("ep")() is False


def test_startup_log(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    mm._startup_logged = False
    monkeypatch.setenv("MONITOR_TEAM", "platform")
    monkeypatch.setenv("MONITOR_COST_CENTER", "cc-1")
    with caplog.at_level(logging.INFO, logger="monitor.lifecycle"):
        app = install(FastAPI())
    assert app is not None
    recs = [rec for rec in caplog.records if rec.name == "monitor.lifecycle"]
    assert len(recs) == 1
    payload = json.loads(recs[0].getMessage())
    assert payload["event"] == "startup"
    assert payload["team"] == "platform"
    assert payload["cost_center"] == "cc-1"
    assert payload["boot_id"] == mm.BOOT_ID
    assert payload["version"] == mm.APP_VERSION
    assert payload["app"] == mm.APP_NAME
    assert len(payload["packages"]) <= 400

    caplog.clear()
    mm._startup_logged = False

    def boom() -> None:
        raise RuntimeError("inventory down")

    monkeypatch.setattr(mm, "distributions", boom)
    with caplog.at_level(logging.INFO, logger="monitor.lifecycle"):
        again = install(FastAPI())
    assert again is not None
    recs = [rec for rec in caplog.records if rec.name == "monitor.lifecycle"]
    assert json.loads(recs[-1].getMessage())["packages"] == []


def test_cold_start_only_on_first_request(span_exporter: InMemorySpanExporter) -> None:
    mm._cold_done = False
    app = install(FastAPI())

    @app.get("/ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(_with_span(app))
    client.get("/ping")
    client.get("/ping")
    reqs = _named(span_exporter, "test.request")
    assert len(reqs) == 2
    assert "monitor.cold_start_ms" in reqs[0].attributes
    assert "monitor.cold_start_ms" not in (reqs[1].attributes or {})


def test_monitor_parentbased_keeps_error_summary() -> None:
    sampler = monitor_parentbased("0")
    assert isinstance(sampler, Sampler)
    assert sampler.should_sample(Context(), 1, "normal").decision is not Decision.RECORD_AND_SAMPLE
    kept = sampler.should_sample(Context(), 1, "monitor.error_summary")
    assert kept.decision is Decision.RECORD_AND_SAMPLE
    assert monitor_parentbased(None).get_description() == "MonitorParentBased(ratio=1.0)"
    assert monitor_parentbased("").get_description() == "MonitorParentBased(ratio=1.0)"
    assert monitor_parentbased("nope").get_description() == "MonitorParentBased(ratio=1.0)"
    assert monitor_parentbased("5").get_description() == "MonitorParentBased(ratio=1.0)"
    ratio_zero = monitor_parentbased("0")
    child = ratio_zero.should_sample(_parent(True), 1, "child")
    assert child.decision is Decision.RECORD_AND_SAMPLE
    dropped = ratio_zero.should_sample(_parent(False), 1, "child")
    assert dropped.decision is not Decision.RECORD_AND_SAMPLE
    forced = ratio_zero.should_sample(_parent(False), 1, "monitor.error_summary")
    assert forced.decision is Decision.RECORD_AND_SAMPLE


def test_sampler_entry_point() -> None:
    found = [
        item
        for item in entry_points(group="opentelemetry_traces_sampler")
        if item.name == "monitor_parentbased"
    ]
    assert found
    sampler = found[0].load()("0.5")
    assert sampler.get_description() == "MonitorParentBased(ratio=0.5)"
