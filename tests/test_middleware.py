"""Behavioral tests for the golden-envelope middleware (public API only)."""

from __future__ import annotations

import json
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from monitor_middleware import _MAX_LOG_CHARS, _hash, _TruncateLongLines, install


@pytest.fixture()
def client() -> TestClient:
    app = install(FastAPI())

    @app.get("/ping")
    async def ping() -> dict:
        return {"ok": True}

    return TestClient(app)


def test_install_returns_the_same_app() -> None:
    app = FastAPI()
    assert install(app) is app


def test_envelope_stamps_request_id_and_session(client: TestClient) -> None:
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.headers["x-request-id"]
    assert r.cookies.get("monitor_session")


def test_request_id_passthrough(client: TestClient) -> None:
    r = client.get("/ping", headers={"x-request-id": "fixed-id-123"})
    assert r.headers["x-request-id"] == "fixed-id-123"


def test_session_cookie_not_reissued(client: TestClient) -> None:
    first = client.get("/ping")
    sid = first.cookies["monitor_session"]
    second = client.get("/ping")  # TestClient persists cookies
    assert "set-cookie" not in second.headers
    assert client.cookies["monitor_session"] == sid


def test_hash_is_stable_and_anonymous() -> None:
    h = _hash("alice@example.com")
    assert h == _hash("alice@example.com")
    assert len(h) == 16
    assert h != "alice@example.com"
    assert _hash(None) == "anon"
    assert _hash("") == "anon"


def test_feedback_logs_clamped_payload(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="monitor.feedback"):
        r = client.post(
            "/monitor/feedback",
            json={"rating": 99, "comment": "x" * 600},
            headers={"x-forwarded-user": "bob@example.com"},
        )
    assert r.json() == {"ok": True}
    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "feedback"
    assert payload["rating"] == 5  # clamped into 1..5
    assert len(payload["comment"]) == 500  # truncated
    assert payload["user"] == _hash("bob@example.com")
    assert payload["rid"] and payload["sid"]


def test_feedback_survives_invalid_body(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="monitor.feedback"):
        r = client.post("/monitor/feedback", content=b"not json")
    assert r.json() == {"ok": True}
    payload = json.loads(caplog.records[-1].message)
    assert payload["rating"] == 3  # default when absent/invalid


def test_truncate_filter_caps_giant_log_lines() -> None:
    f = _TruncateLongLines()
    rec = logging.LogRecord("t", logging.INFO, __file__, 1, "y" * (_MAX_LOG_CHARS + 5000), (), None)
    assert f.filter(rec) is True
    assert len(rec.msg) < _MAX_LOG_CHARS + 100
    assert rec.msg.endswith("chars]")
    short = logging.LogRecord("t", logging.INFO, __file__, 1, "short %s", ("a",), None)
    assert f.filter(short) is True
    assert short.msg == "short a"
    assert short.args == ()
    assert f.filter(short) is True  # second pass is a no-op
    assert short.msg == "short a"
