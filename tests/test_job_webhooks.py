"""Job webhook delivery: pure acknowledgement rules and scheduler cadence."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from test_service_correctness import service as service

NOW = datetime(2026, 10, 26, tzinfo=UTC)


def event(offset=1, **changes):
    return {
        "ts": (NOW + timedelta(seconds=offset)).isoformat(),
        "source": "job",
        "rule": "prompt_drift",
        "app": "demo",
        "severity": "warning",
        "message": "drift",
        "value": "0.5",
        "state": "firing",
        "workspace_id": "123",
        "muted": "false",
        **changes,
    }


def test_cursor_excludes_history_and_acknowledges_equal_timestamp_batch(service):
    rows = [
        event(-1),
        event(0),
        event(1),
        event(1, state="resolved"),
        event(2, muted="true"),
        event(100, source="monitor"),
    ]
    batch = service.alerts.job_webhook_batch
    events, cursor = batch(rows, NOW)
    assert cursor == NOW
    assert [e["state"] for e in events] == ["firing", "resolved"]
    assert events[0]["value"] == 0.5 and events[0]["muted"] is False
    assert events[0]["since"] == event()["ts"]
    assert batch(rows, NOW, posted=True)[1] == NOW + timedelta(seconds=2)
    assert batch(rows, NOW + timedelta(seconds=2)) == ([], NOW + timedelta(seconds=2))


@pytest.mark.parametrize("muted", [True, "true", "TRUE"])
def test_all_muted_batches_never_post_or_advance(service, muted):
    for posted in (False, True):
        assert service.alerts.job_webhook_batch([event(muted=muted)], NOW, posted=posted) == (
            [],
            NOW,
        )


@pytest.mark.parametrize("muted", [False, "false", None])
def test_sql_booleans_and_timezone_normalization(service, muted):
    row = event(muted=muted, ts="2026-10-26 00:00:01.123456", value=None)
    events, cursor = service.alerts.job_webhook_batch([row], NOW, posted=True)
    assert events[0]["value"] is None
    assert cursor == NOW + timedelta(seconds=1, microseconds=123456)
    row["ts"] = "2026-10-25T20:00:01.123456-04:00"
    assert service.alerts.job_webhook_batch([row], NOW, posted=True)[1] == cursor


def test_webhook_reports_success_or_failure_and_preserves_payload(service, monkeypatch):
    alerts = service.alerts
    monkeypatch.setattr(alerts, "WEBHOOK", "https://webhook.invalid")
    rows = [event(muted=True), event(muted="false")]
    assert alerts.notify_webhook(rows) is True
    alerts.httpx.post.assert_called_once_with(
        alerts.WEBHOOK, json={"source": "apps-monitor", "events": [rows[1]]}, timeout=10
    )
    alerts.httpx.post.return_value.raise_for_status.side_effect = RuntimeError("HTTP 500")
    assert alerts.notify_webhook(rows) is False
    alerts.httpx.post.side_effect = TimeoutError()
    assert alerts.notify_webhook(rows) is False
    alerts.httpx.post.reset_mock()
    monkeypatch.setattr(alerts, "WEBHOOK", "")
    assert alerts.notify_webhook(rows) is False
    alerts.httpx.post.assert_not_called()


def test_forwarder_is_disabled_without_webhook_and_waits_five_minutes(service, monkeypatch):
    main = service.main
    monkeypatch.setattr(main.time, "monotonic", lambda: 1000)
    monkeypatch.setattr(main, "_last_job_alert_poll", 0)
    monkeypatch.setattr(main, "_job_alert_cursor", NOW)
    monkeypatch.setattr(service.alerts, "WEBHOOK", "")
    main.q.run = AsyncMock(return_value=[event()])
    notify = MagicMock(return_value=False)
    monkeypatch.setattr(service.alerts, "notify_webhook", notify)
    asyncio.run(main.forward_job_alerts())
    main.q.run.assert_not_called()
    monkeypatch.setattr(service.alerts, "WEBHOOK", "https://webhook.invalid")
    asyncio.run(main.forward_job_alerts())
    main.q.run.assert_awaited_once_with(main.q.JOB_ALERTS, ttl=0, ws="123", cursor=NOW.isoformat())
    assert main._job_alert_cursor == NOW
    assert main._last_job_alert_poll == 1000
    monkeypatch.setattr(main.time, "monotonic", lambda: 1299)
    asyncio.run(main.forward_job_alerts())
    assert main.q.run.await_count == 1
    monkeypatch.setattr(main.time, "monotonic", lambda: 1300)
    notify.return_value = True
    asyncio.run(main.forward_job_alerts())
    assert main.q.run.await_count == 2
    assert main._job_alert_cursor == NOW + timedelta(seconds=1)
    assert "source = 'job'" in main.q.JOB_ALERTS and "ts > :cursor::timestamp" in main.q.JOB_ALERTS


def test_query_failure_and_all_muted_leave_cursor_intact(service, monkeypatch):
    main = service.main
    monkeypatch.setattr(main.time, "monotonic", lambda: 1000)
    monkeypatch.setattr(main, "_last_job_alert_poll", 0)
    monkeypatch.setattr(main, "_job_alert_cursor", NOW)
    monkeypatch.setattr(service.alerts, "WEBHOOK", "https://webhook.invalid")
    notify = MagicMock(return_value=True)
    monkeypatch.setattr(service.alerts, "notify_webhook", notify)
    main.q.run = AsyncMock(side_effect=RuntimeError("SQL unavailable"))
    asyncio.run(main.forward_job_alerts())
    assert main._job_alert_cursor == NOW
    main.q.run = AsyncMock(return_value=[event(muted="true")])
    monkeypatch.setattr(main.time, "monotonic", lambda: 1300)
    asyncio.run(main.forward_job_alerts())
    assert main._job_alert_cursor == NOW
    notify.assert_not_called()


def test_boot_resets_cursor_before_starting_scheduler(service, monkeypatch):
    main = service.main
    monkeypatch.setattr(main, "_job_alert_cursor", NOW)
    main.q.run = AsyncMock(return_value=[])
    monkeypatch.setattr(main, "scheduler", AsyncMock())
    before = datetime.now(UTC)

    async def boot():
        async with main.lifespan(main.app):
            await asyncio.sleep(0)

    asyncio.run(boot())
    assert before <= main._job_alert_cursor <= datetime.now(UTC)


def test_all_statement_chunks_are_read_and_truncation_is_rejected(service):
    q = service.queries
    statement = q.w.statement_execution
    response = SimpleNamespace(
        statement_id="statement",
        status=SimpleNamespace(state=SimpleNamespace(value="SUCCEEDED")),
        manifest=SimpleNamespace(
            truncated=False, schema=SimpleNamespace(columns=[SimpleNamespace(name="rule")])
        ),
        result=SimpleNamespace(data_array=[["first"]], next_chunk_index=1),
    )
    statement.execute_statement.return_value = response
    statement.get_statement_result_chunk_n.side_effect = [
        SimpleNamespace(data_array=[["second"]], next_chunk_index=2),
        SimpleNamespace(data_array=[["third"]], next_chunk_index=None),
    ]
    assert q._run(q.JOB_ALERTS, {"ws": "123", "cursor": NOW.isoformat()}, 0) == [
        {"rule": "first"},
        {"rule": "second"},
        {"rule": "third"},
    ]
    assert statement.get_statement_result_chunk_n.call_count == 2
    response.manifest.truncated = True
    with pytest.raises(RuntimeError, match="truncated"):
        q._run(q.JOB_ALERTS, {"ws": "123", "cursor": NOW.isoformat()}, 0)
