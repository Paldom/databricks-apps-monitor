"""Exercise the actual fixture endpoints with in-memory telemetry; no workspace clients."""

from __future__ import annotations

import importlib.util
import json
import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from opentelemetry import trace

import monitor_middleware as mm


@pytest.fixture
def fixture_app(monkeypatch):
    monkeypatch.delenv("MONITOR_URL", raising=False)
    path = Path(__file__).resolve().parents[1] / "example-apps/conformance/main.py"
    spec = importlib.util.spec_from_file_location("conformance_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixture_statuses_steps_sql(fixture_app, span_exporter):
    with TestClient(fixture_app.app, raise_server_exceptions=False) as client:
        assert client.get("/c/ok").status_code == 200
        assert client.get("/c/client-error").status_code == 404
        assert client.get("/c/slow?ms=0").json() == {"slept_ms": 0}
        with trace.get_tracer("fixture-test").start_as_current_span("step-request"):
            assert client.get("/c/step?name=checkout").status_code == 200
        assert client.get("/c/sql?rows=42").json() == {"rows": 42}
        for _ in range(2):
            with trace.get_tracer("fixture-test").start_as_current_span("error-request"):
                assert client.get("/c/error").status_code == 500
    spans = span_exporter.get_finished_spans()
    assert (
        next(s for s in spans if s.name == "step-request").attributes["journey.step"] == "checkout"
    )
    sql = next(s for s in spans if s.name == "sql.execute")
    assert sql.attributes["db.response.returned_rows"] == 42
    assert "db.statement" not in sql.attributes and "db.query.text" not in sql.attributes
    fps = [s.attributes["exception.fingerprint"] for s in spans if s.name == "error-request"]
    assert len(fps) == 2 and len(set(fps)) == 1


@pytest.mark.parametrize("stream", [0, 1])
def test_fixture_llm_final_usage(fixture_app, span_exporter, metric_reader, stream):
    with TestClient(fixture_app.app) as client:
        response = client.get(f"/c/llm?in=1000&out=200&stream={stream}&chunks=10")
        assert response.status_code == 200
        if stream:
            assert response.text.count("data:") == 10
    spans = [
        s for s in span_exporter.get_finished_spans() if s.name == "chat conformance-fake-model"
    ]
    assert len(spans) == 1
    attrs = spans[0].attributes
    assert attrs["gen_ai.usage.input_tokens"] == 1000
    assert attrs["gen_ai.usage.output_tokens"] == 200
    assert attrs["monitor.llm.billable"] is True
    assert ("monitor.llm.ttft_ms" in attrs) is bool(stream)
    data = metric_reader.get_metrics_data()
    assert any(
        m.name == "gen_ai.client.token.usage"
        for r in data.resource_metrics
        for s in r.scope_metrics
        for m in s.metrics
    )


@pytest.mark.parametrize("failure", ["rate_limit", "timeout", "policy", "schema", "server"])
def test_fixture_provider_taxonomy(fixture_app, span_exporter, failure):
    with TestClient(fixture_app.app) as client:
        response = client.get(f"/c/llm?fail={failure}&stream=1")
    assert response.status_code == 502
    span = next(
        s for s in span_exporter.get_finished_spans() if s.name == "chat conformance-fake-model"
    )
    assert span.attributes["error.type"] == failure
    assert "gen_ai.usage.input_tokens" not in span.attributes


def test_fixture_events_redaction_and_html(fixture_app, caplog):
    caplog.set_level(logging.INFO)
    with TestClient(fixture_app.app) as client:
        headers = {"x-request-id": "val-test-1", "cookie": "monitor_session=session-1"}
        assert client.post("/c/event?name=signup", headers=headers).json() == {"event": "signup"}
        assert (
            client.get("/c/leak?token=DELIBERATE_SECRET&email=leak@example.invalid").status_code
            == 200
        )
        html = client.get("/?run=unit").text
        assert (
            "/monitor/rum.js" in html and "pushState" in html and "/conformance-route/unit" in html
        )
        assert "throw new Error" in html
        assert client.get("/monitor/rum.js").status_code == 200
    event = next(json.loads(r.getMessage()) for r in caplog.records if r.name == "monitor.events")
    assert event["rid"] == "val-test-1" and event["sid"] == "session-1"
    leak = next(r.getMessage() for r in caplog.records if r.name == "conformance.leak")
    assert (
        "DELIBERATE_SECRET" not in leak
        and "leak@example.invalid" not in leak
        and fixture_app.PAT not in leak
    )


def test_fixture_health_cache_and_budget(fixture_app, monkeypatch):
    now = [100.0]
    monkeypatch.setattr(mm.time, "monotonic", lambda: now[0])
    with TestClient(fixture_app.app) as client:
        assert client.get("/monitor/health").status_code == 200
        assert client.post("/c/health-toggle?ok=0").status_code == 200
        assert client.get("/monitor/health").status_code == 200
        now[0] += 31
        down = client.get("/monitor/health")
        assert down.status_code == 503
        assert down.json()["checks"]["always_ok"]["ok"] is True
        client.post("/c/health-toggle?ok=1")
        now[0] += 31
        assert client.get("/monitor/health").status_code == 200
        assert client.get("/c/budget").status_code == 200
        monkeypatch.setattr(mm, "_policy", lambda: {"throttle": "block"})
        assert client.get("/c/budget").status_code == 429
