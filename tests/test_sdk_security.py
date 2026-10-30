"""Security and failure-mode regressions for the copy-in SDK."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request as UrlRequest

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk._configuration import _import_sampler
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Status, StatusCode
from starlette.requests import Request

import monitor_middleware as mm


@pytest.fixture(autouse=True)
def isolate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MONITOR_URL", raising=False)
    monkeypatch.delenv("MONITOR_HASH_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "databricks.sdk", None)
    mm._policy_cache.clear()
    mm._rum_buckets.clear()


def test_late_attributes_events_and_shared_mlflow_provider_are_scrubbed(
    monkeypatch: pytest.MonkeyPatch, span_exporter: InMemorySpanExporter
) -> None:
    monkeypatch.setenv("MLFLOW_ENABLE_DUAL_EXPORT", "true")
    monkeypatch.setenv("MLFLOW_TRACE_ENABLE_OTLP_DUAL_EXPORT", "true")
    mm.install(FastAPI())
    with trace.get_tracer("mlflow").start_as_current_span("Bearer start-secret") as span:
        span.set_attribute("url.full", "https://user:pass@host/x?token=abc#secret")
        span.set_attributes({"url.query": "token=abc", "db.query.text": "SELECT secret"})
        span.add_event(
            "Bearer event-secret", {"email": "alice@example.com", "db.statement": "SELECT secret"}
        )
        span.record_exception(RuntimeError("Bearer exception-secret alice@example.com"))
        span.set_status(Status(StatusCode.ERROR, "Bearer status-secret"))
        span.update_name("Bearer name-secret")
    rendered = str(span_exporter.get_finished_spans()[-1].to_json())
    for secret in (
        "user:pass",
        "abc",
        "#secret",
        "SELECT secret",
        "alice@example.com",
        "exception-secret",
        "status-secret",
        "name-secret",
        "event-secret",
    ):
        assert secret not in rendered


def test_log_extra_stack_and_exception_scrub(caplog: pytest.LogCaptureFixture) -> None:
    mm.install(FastAPI())
    try:
        raise ValueError("alice@example.com Bearer secret")
    except ValueError:
        with caplog.at_level(logging.ERROR):
            logging.getLogger("app.child").exception(
                "bad %s",
                "alice@example.com",
                extra={"nested": {"authorization": "Bearer extra-secret"}},
                stack_info=True,
            )
    record = caplog.records[-1]
    assert "alice@example.com" not in record.getMessage()
    assert record.nested == {"authorization": "Bearer [redacted]"}
    assert record.exc_info is None
    assert "extra-secret" not in caplog.text
    bad = logging.LogRecord("x", 20, __file__, 1, "%d", ("bad",), None)
    assert mm._SafeLog().filter(bad)


def test_redaction_of_long_plain_log_is_bounded() -> None:
    import time

    mm.install(FastAPI())
    record = logging.LogRecord("x", 20, __file__, 1, "%s", ("x" * 200_000,), None)
    start = time.monotonic()
    mm._SafeLog().filter(record)
    assert time.monotonic() - start < 2
    assert len(record.msg) < mm._MAX_LOG_CHARS + 100


@pytest.mark.parametrize("rid", ["", "bad\nid", "x\r", "x" * 65, "bad id"])
def test_invalid_ids_and_cookies_are_replaced(rid: str) -> None:
    client = TestClient(mm.install(FastAPI()))
    client.cookies.set("monitor_session", "invalid@private.example")
    response = client.get("/monitor/health", headers={"x-request-id": rid})
    assert mm._RID.fullmatch(response.headers["x-request-id"])
    assert "invalid" not in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]


@pytest.mark.parametrize(
    "origin",
    [
        "https://testserver",
        "http://testserver:81",
        "null",
        "http://user@testserver",
        "http://testserver/",
        "http://testserver?x=1",
        "http://[broken",
        "http://testserver:bad",
    ],
)
def test_rum_rejects_wrong_or_malformed_origin(origin: str) -> None:
    client = TestClient(mm.install(FastAPI(), rum=True))
    assert client.post("/monitor/rum", headers={"origin": origin}, json={}).status_code == 403


def test_rum_origin_default_port_metadata_and_unicode_scrub(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = TestClient(mm.install(FastAPI(), rum=True))
    assert client.post("/monitor/rum", json={}).status_code == 403
    assert (
        client.post("/monitor/rum", headers={"sec-fetch-site": "same-origin"}, json={}).status_code
        == 200
    )
    with caplog.at_level(logging.INFO, logger="monitor.rum"):
        response = client.post(
            "/monitor/rum",
            headers={"origin": "http://testserver:80"},
            content=b'{"email":"alice\\u0040example.com", "source":"https://host/x?anything=private"}',
        )
    assert response.status_code == 200
    logged = json.loads(caplog.records[-1].getMessage())
    assert "alice" not in logged["body"] and "private" not in logged["body"]
    assert logged["sid"] == client.cookies["monitor_session"]
    assert logged["rid"] == response.headers["x-request-id"]


def test_streaming_body_cap_stops_reading_and_accepts_boundary() -> None:
    async def run() -> None:
        chunks = iter([b"x" * 2048, b"y" * 2049])
        calls = 0

        async def receive() -> dict:
            nonlocal calls
            calls += 1
            return {"type": "http.request", "body": next(chunks), "more_body": True}

        request = Request({"type": "http", "headers": [(b"content-length", b"1")]}, receive)
        assert await mm._body(request, 4096) is None
        assert calls == 2

    asyncio.run(run())
    client = TestClient(mm.install(FastAPI()))
    assert client.post("/monitor/event", content=b" " * 4094 + b"{}").status_code == 200
    assert client.post("/monitor/event", content=b"[" * 2000).status_code == 200
    assert client.post("/monitor/event", content=b"\xff").status_code == 200
    assert (
        client.post("/monitor/event", json={"props": {"name": "x", "request": 1}}).status_code
        == 200
    )
    assert mm._safe(float("nan")) is None
    assert client.post("/monitor/feedback", content=b'{"rating":1e999}').status_code == 200


def test_bucket_refills_is_bounded_and_cookieless_clients_share_bucket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [100.0]
    monkeypatch.setattr(mm.time, "monotonic", lambda: now[0])
    for _ in range(10):
        assert mm._rum_allow("s")
    assert not mm._rum_allow("s")
    now[0] += 6
    assert mm._rum_allow("s")
    assert not mm._rum_allow("s")
    for i in range(1023):
        assert mm._rum_allow(str(i))
    assert not mm._rum_allow("overflow")
    assert len(mm._rum_buckets) == 1024
    now[0] += 61
    assert mm._rum_allow("overflow")
    mm._rum_buckets.clear()
    client = TestClient(mm.install(FastAPI(), rum=True))
    for _ in range(10):
        client.cookies.clear()
        assert (
            client.post(
                "/monitor/rum", json={}, headers={"origin": "http://testserver"}
            ).status_code
            == 200
        )
    client.cookies.clear()
    assert (
        client.post("/monitor/rum", json={}, headers={"origin": "http://testserver"}).status_code
        == 429
    )


def test_events_remain_json_and_scrub_keys(caplog: pytest.LogCaptureFixture) -> None:
    mm.install(FastAPI())
    with caplog.at_level(logging.INFO, logger="monitor.events"):
        mm.track("long", **{f"alice{i}@example.com": "λ" * 3000 for i in range(20)})
        mm.track("numbers", nested={}, nan=float("nan"))
    payload = json.loads(caplog.records[-2].getMessage())
    assert "alice" not in str(payload)
    assert json.loads(caplog.records[-1].getMessage())["props"] == {}
    cyclic = []
    cyclic.append(cyclic)
    assert "[redacted]" in str(mm._safe(cyclic))


def test_sql_failure_does_not_export_exception_text(span_exporter: InMemorySpanExporter) -> None:
    with pytest.raises(ValueError, match="SELECT"), mm.trace_sql("wh"):
        raise ValueError("SELECT salary FROM employee")
    span = span_exporter.get_finished_spans()[-1]
    assert span.status.status_code is StatusCode.ERROR
    assert "SELECT" not in span.to_json()
    assert not span.events


def test_policy_expiry_url_key_and_bounded_response(monkeypatch: pytest.MonkeyPatch) -> None:
    now = [100.0]
    monkeypatch.setattr(mm.time, "monotonic", lambda: now[0])
    monkeypatch.setenv("MONITOR_URL", "https://monitor")
    monkeypatch.setattr(mm, "APP_NAME", "a/b")
    payloads = [b'{"throttle":"block"}', TimeoutError(), b'{"throttle":"warn"}', b" " * 8193]
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, size):
            assert size == 8193
            value = payloads.pop(0)
            if isinstance(value, Exception):
                raise value
            return value

    def fetch(request, timeout):
        calls.append(request.full_url)
        assert timeout == 2
        return Response()

    monkeypatch.setattr(mm, "urlopen", fetch)
    assert mm._policy()["throttle"] == "block"
    assert mm._policy()["throttle"] == "block"
    assert calls == ["https://monitor/api/policy/a%2Fb"]
    now[0] += 60
    assert mm._policy() == {}
    monkeypatch.setenv("MONITOR_URL", "https://other")
    assert mm._policy()["throttle"] == "warn"
    now[0] += 60
    assert mm._policy() == {}


def test_policy_redirect_never_forwards_bearer() -> None:
    request = UrlRequest("https://monitor/policy", headers={"Authorization": "Bearer secret"})
    handler = mm._NoRedirect()
    assert (
        handler.http_error_302(
            request, SimpleNamespace(), 302, "Found", {"location": "https://other/path"}
        )
        is None
    )


def test_health_does_not_block_loop_or_duplicate_hung_workers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release = threading.Event()
    calls = []

    def slow() -> bool:
        calls.append(1)
        release.wait(5)
        return True

    async def run() -> None:
        monkeypatch.setattr(mm, "_HEALTH_TIMEOUT", 0.02)
        health = mm._Health({"slow": slow})
        first = asyncio.create_task(health.get())
        await asyncio.sleep(0.005)
        assert not first.done()
        assert (await first).status_code == 503
        health.expires = 0
        assert (await health.get()).status_code == 503
        assert len(calls) == 1
        release.set()
        await asyncio.wrap_future(health.pending["slow"])
        health.expires = 0
        assert (await health.get()).status_code == 200

    try:
        asyncio.run(run())
    finally:
        release.set()


def test_step_context_isolated_under_concurrent_requests() -> None:
    async def run() -> None:
        app = mm.install(FastAPI())
        barrier = asyncio.Event()
        seen = []

        @app.get("/{name}")
        async def handler(name: str):
            mm.set_step(name)
            seen.append(mm._step.get())
            if len(seen) == 2:
                barrier.set()
            await barrier.wait()
            return {"step": mm._step.get()["name"]}

        import httpx2

        async with httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app), base_url="http://app"
        ) as client:
            a, b = await asyncio.gather(client.get("/a"), client.get("/b"))
        assert a.json()["step"] == "a" and b.json()["step"] == "b"
        assert seen[0] is not seen[1]

    asyncio.run(run())


def test_actual_sampler_loader_and_unsampled_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OTEL_TRACES_SAMPLER_ARG", "0")
    sampler = _import_sampler("monitor_parentbased")
    assert sampler.get_description() == "MonitorParentBased(ratio=0.0)"
    provider = TracerProvider(sampler=sampler)
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(mm.trace, "get_tracer_provider", lambda: provider)
    app = mm.install(FastAPI())

    @app.get("/fail")
    async def fail():
        raise RuntimeError("Bearer secret")

    async def wrapped(scope, receive, send):
        with provider.get_tracer("test").start_as_current_span("dropped"):
            await app(scope, receive, send)

    try:
        assert TestClient(wrapped, raise_server_exceptions=False).get("/fail").status_code == 500
        spans = exporter.get_finished_spans()
        assert [s.name for s in spans] == ["monitor.error_summary"]
        assert spans[0].attributes["exception.fingerprint"]
    finally:
        provider.shutdown()


def test_api_only_copy_in_and_redact_false_in_fresh_process() -> None:
    code = """
import importlib.abc, importlib.util, sys
class NoSDK(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname == "opentelemetry.sdk" or fullname.startswith("opentelemetry.sdk."):
            raise ImportError("SDK intentionally unavailable")
sys.meta_path.insert(0, NoSDK())
spec = importlib.util.spec_from_file_location("copy_in", sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from fastapi import FastAPI
from fastapi.testclient import TestClient
m.install(FastAPI(), redact=False)
assert not m._REDACT
client = TestClient(m.install(FastAPI(), rum=True))
assert client.get("/monitor/health").status_code == 200
with m.llm_call("model") as usage:
    usage.set(input_tokens=1, output_tokens=2)
with m.trace_sql("wh"):
    pass
m.track("event")
assert not any(k.startswith("opentelemetry.sdk") for k in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(Path(mm.__file__))],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
