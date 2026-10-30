"""Phase 2 behavior with pure logic and fake warehouse / workspace clients."""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from fastapi.testclient import TestClient
from test_service_correctness import ROOT, alert_spark, firing
from test_service_correctness import service as service

NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)


def mute_window(**overrides):
    return {
        "app": "demo-*",
        "rule": "app_*",
        "starts_at": NOW,
        "ends_at": NOW + timedelta(hours=1),
        **overrides,
    }


@pytest.mark.parametrize(
    "app,rule,minute,expected",
    [
        ("demo-api", "app_down", 0, True),
        ("demo-api", "app_down", 59, True),
        ("demo-api", "app_down", 60, False),
        ("demo-api", "app_down", -1, False),
        ("demo-api", "slo_fast_burn", 1, False),
        ("other-api", "app_down", 1, False),
        ("DEMO-api", "app_down", 1, False),
    ],
)
def test_mute_globs_and_half_open_window(service, app, rule, minute, expected):
    assert (
        service.mutes.is_muted(app, rule, [mute_window()], NOW + timedelta(minutes=minute))
        is expected
    )


def test_mutes_accept_sql_strings_naive_utc_and_offsets(service):
    row = mute_window(
        app="*", rule="*", starts_at="2026-10-29 12:00:00", ends_at="2026-10-29T15:00:00+02:00"
    )
    assert service.mutes.is_muted("any", "any", [row], NOW)
    assert not service.mutes.is_muted("any", "any", [row], NOW + timedelta(hours=1))
    assert not service.mutes.is_muted("any", "any", [{"starts_at": "bad"}], NOW)


def test_monitor_evaluates_persists_and_resolves_muted_alert(service, monkeypatch):
    a = service.alerts
    now = datetime.now(timezone.utc)
    a.set_mutes(
        [
            mute_window(
                app="demo", starts_at=now - timedelta(seconds=1), ends_at=now + timedelta(hours=1)
            )
        ]
    )
    events = a.evaluate({"demo": {"app_state": "STOPPED"}}, {}, lambda _: {})
    assert len(events) == 1 and events[0]["muted"] is True
    monkeypatch.setattr(a, "WEBHOOK", "https://webhook.invalid")
    a.notify_webhook(events)
    a.httpx.post.assert_not_called()
    service.main.q.run_dml = AsyncMock()
    asyncio.run(service.main._persist_alerts(events))
    assert service.main.q.run_dml.call_args.kwargs["muted"] == "true"
    resolved = a.evaluate({"demo": {"app_state": "RUNNING"}}, {}, lambda _: {})
    assert resolved[0]["state"] == "resolved" and resolved[0]["muted"]
    a.set_mutes([])
    events = a.evaluate({"demo": {"app_state": "STOPPED"}}, {}, lambda _: {})
    a.notify_webhook(events)
    assert a.httpx.post.call_args.kwargs["json"]["events"][0]["muted"] is False


def test_job_emitter_marks_firing_and_resolved_events_muted(service):
    spark = alert_spark({("app_down", "demo")})
    base = spark.sql.side_effect
    now = datetime.now(timezone.utc)

    def result(sql, **kwargs):
        frame = base(sql, **kwargs)
        if "alert_mutes" in sql:
            frame.collect.return_value = [
                mute_window(
                    app="*",
                    rule="*",
                    starts_at=now - timedelta(hours=1),
                    ends_at=now + timedelta(hours=1),
                )
            ]
        return frame

    spark.sql.side_effect = result
    service.source_scan.emit_alerts(
        spark, "cat", "sch", [firing("app_down", "new")], owned_rules=("app_down",)
    )
    rows = spark.createDataFrame.call_args.args[0]
    assert {r["state"] for r in rows} == {"firing", "resolved"}
    assert all(r["muted"] for r in rows)


def test_fleet_refresh_keeps_cache_on_sql_failure(service):
    main = service.main
    main.w.apps.list.return_value = []
    service.alerts.set_mutes([mute_window()])
    main.q.run = AsyncMock(side_effect=RuntimeError("offline"))
    asyncio.run(main.refresh_fleet())
    assert service.alerts._mutes == [mute_window()]
    main.q.run = AsyncMock(return_value=[])
    asyncio.run(main.refresh_fleet())
    assert service.alerts._mutes == []


@pytest.mark.parametrize(
    "long,short,expected",
    [
        ((80, 100), (80, 100), True),
        ((80, 100), (100, 100), False),
        ((100, 100), (80, 100), False),
        ((0, 0), (80, 100), None),
        ((80, 100), (0, 0), None),
        ((856, 1000), (856, 1000), True),
    ],
)
def test_burn_requires_both_windows_and_zero_is_unknown(service, long, short, expected):
    assert service.slo_eval.both_windows(long, short, 0.99, 14.4) is expected
    assert service.slo_eval.burn_rate(0, 0, 0.995) is None
    assert service.slo_eval.burn_rate(99, 100, 0.995) == pytest.approx(2)


@pytest.mark.parametrize(
    "good,total,target", [(2, 1, 0.99), (-1, 10, 0.99), (1, 1, 1), (1, 1, float("nan"))]
)
def test_invalid_sli_counts_rejected(service, good, total, target):
    with pytest.raises(ValueError):
        service.slo_eval.burn_rate(good, total, target)


def slo_row(slo="uptime", good=80, total=100, **kw):
    return {
        "name": "demo",
        "slo": slo,
        "target": 0.99,
        "app_state": "RUNNING",
        "updated_at": NOW - timedelta(days=1),
        **{f"good_{n}": good for n in (5, 30, 60, 360, 4320)},
        **{f"total_{n}": total for n in (5, 30, 60, 360, 4320)},
        **kw,
    }


def test_slo_specs_coalesce_per_app_and_no_data_has_grace(service):
    alerts = service.slo_eval.slo_alerts([slo_row(), slo_row("latency")], NOW)
    assert {r["rule"] for r in alerts} == {"slo_fast_burn", "slo_slow_burn", "slo_ticket"}
    assert all("uptime:" in r["message"] and "latency:" in r["message"] for r in alerts)
    no_data = slo_row(good=0, total=0)
    assert service.slo_eval.slo_alerts([no_data], NOW)[0]["rule"] == "slo_no_data"
    assert service.slo_eval.slo_alerts([{**no_data, "app_state": "STOPPED"}], NOW) == []
    assert service.slo_eval.slo_alerts([{**no_data, "updated_at": NOW}], NOW) == []


def test_orphan_alert_requires_six_hours_without_gaps(service):
    samples = [{"bucket": NOW - timedelta(minutes=15 * i), "orphan_ratio": 0.21} for i in range(25)]
    check = service.telemetry_health.sustained_orphans
    assert check(samples, NOW) is True
    assert check(samples[:-1], NOW) is None
    assert check([{**s, "orphan_ratio": 0.2} for s in samples], NOW) is False
    assert check([*samples[:10], {**samples[10], "orphan_ratio": 0.1}, *samples[11:]], NOW) is False
    assert check(samples, NOW + timedelta(minutes=30)) is None
    assert check([{**samples[0], "orphan_ratio": 0.1}], NOW) is False


def test_sampler_ratio_unknown_stays_unknown(service):
    ratio = service.telemetry_health.sampler_ratio
    assert ratio(None) is None
    assert ratio({"env": [{"name": "OTEL_TRACES_SAMPLER", "value": "always_on"}]}) == 1
    for value, expected in [("0.2", 0.2), ("nan", None), ("1.2", None), (None, None)]:
        assert ratio({"env": [{"name": "OTEL_TRACES_SAMPLER_ARG", "value": value}]}) == expected


def test_night_start_tracks_timezone_and_dst(service):
    start = service.app_stopper.scheduled_start
    assert start(datetime(2026, 10, 25, 0, tzinfo=timezone.utc), "Europe/Budapest") == datetime(
        2026, 10, 25, 5, 5, tzinfo=timezone.utc
    )
    assert start(datetime(2026, 3, 29, 0, tzinfo=timezone.utc), "Europe/Budapest") == datetime(
        2026, 3, 29, 4, 5, tzinfo=timezone.utc
    )


def test_night_mutes_only_stop_rules(service):
    spark = MagicMock()
    service.app_stopper.night_mute(spark, "cat.sch", "123", "demo", NOW, "UTC")
    args = [c.kwargs["args"] for c in spark.sql.call_args_list]
    assert {a["rule"] for a in args} == {"app_down", "app_stopped"}
    assert all(a["end"] > a["start"] and a["ws"] == "123" for a in args)


def test_ops_routes_authorization_validation_parameters_and_audit(service):
    client = TestClient(service.main.app)
    q = service.queries
    q.run_dml = AsyncMock()
    q.run = AsyncMock(return_value=[])
    spec = {"slo": "uptime", "sli": "availability", "target": 0.995}
    assert client.post("/api/apps/demo/slo", json=spec).status_code == 403
    assert client.delete("/api/actions/mute/a").status_code == 403
    service.auth.MONITOR_ADMINS.add("admin@example.invalid")
    headers = {"x-forwarded-email": "admin@example.invalid"}
    assert (
        client.post("/api/apps/demo/slo", json={**spec, "target": 1}, headers=headers).status_code
        == 422
    )
    assert (
        client.post(
            "/api/apps/demo/slo", json={**spec, "sli": "latency"}, headers=headers
        ).status_code
        == 422
    )
    assert client.post("/api/apps/demo/slo", json=spec, headers=headers).status_code == 200
    write, audit = q.run_dml.call_args_list
    assert write.args[0] == q.SLO_UPSERT and write.kwargs["ws"] == "123"
    assert audit.args[0] == q.OPS_AUDIT and audit.kwargs["actor"] == headers["x-forwarded-email"]
    q.run_dml.reset_mock()
    response = client.post(
        "/api/actions/mute",
        headers=headers,
        json={
            "app": "demo' OR true --",
            "rule": "*",
            "reason": "release",
            "ends_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        },
    )
    assert response.status_code == 200
    write = q.run_dml.call_args_list[0]
    assert "demo'" not in write.args[0] and write.kwargs["app"] == "demo' OR true --"
    assert client.delete("/api/actions/mute/missing", headers=headers).status_code == 404
    q.run.side_effect = [[{"app": "demo"}], []]
    assert client.delete("/api/actions/mute?id=existing", headers=headers).status_code == 200
    assert q.run_dml.call_args_list[-1].kwargs["action"] == "unmute"


def test_slo_and_health_read_apis_preserve_unknown_values(service):
    client = TestClient(service.main.app)
    service.queries.run = AsyncMock(
        side_effect=[[{"slo": "a", "budget_remaining_pct": None}], [], []]
    )
    response = client.get("/api/apps/demo/slo")
    assert (
        response.status_code == 200 and response.json()["specs"][0]["budget_remaining_pct"] is None
    )
    assert client.get("/api/apps/demo/telemetry-health").json() == {"health": None}


def test_slo_job_uses_completed_buckets_and_resolves_empty_specs(service, monkeypatch):
    spark = MagicMock()

    def result(sql, **_kwargs):
        frame = MagicMock()
        frame.collect.return_value = (
            [{"ts": NOW.replace(tzinfo=None)}] if "SELECT window(now()" in sql else []
        )
        return frame

    spark.sql.side_effect = result
    sys.modules["pyspark.sql"].SparkSession.builder.getOrCreate.return_value = spark
    emit, health = MagicMock(), MagicMock()
    monkeypatch.setattr(service.source_scan, "emit_alerts", emit)
    monkeypatch.setattr(service.telemetry_health, "check_telemetry", health)
    monkeypatch.setattr(sys, "argv", ["slo", "--catalog=cat", "--schema=sch"])
    service.slo_eval.main()
    emit.assert_called_once_with(
        spark, "cat", "sch", [], owned_rules=service.slo_eval.OWNED_RULES, unknown_keys=set()
    )
    rollup = next(c for c in spark.sql.call_args_list if "MERGE INTO" in c.args[0])
    assert rollup.kwargs["args"]["end"] == NOW.replace(tzinfo=None)
    assert "time < :end" in rollup.args[0] and "date >= current_date() - 1" in rollup.args[0]
    assert service.telemetry_sql.NOT_PROBE in rollup.args[0]
    assert "t.revision = s.revision" in rollup.args[0]
    health.assert_called_once()


def test_meter_uses_workspace_sp_and_separate_unknown_model_cost(service):
    meter = service.self_meter
    assert meter.cost_share(10, 50) == 20
    assert meter.cost_share(10, 0) is None
    assert meter.cost_share(None, 100) is None
    assert "workspace_id = :ws" in meter.billing_sql()
    assert "executed_by_user_id" in meter.warehouse_sql()
    assert "d.monitor_ms / nullif(d.total_ms, 0)" in meter.warehouse_sql()
    assert "cast(NULL AS DOUBLE)" in meter.model_sql("cat.sch", False)
    assert "p.effective_from <= date(u.ts)" in meter.model_sql("cat.sch", True)
    spark = MagicMock()
    service.model_usage.record_usage(
        spark, "cat.sch", "123", "review", "model", {"prompt_tokens": 7, "completion_tokens": 4}
    )
    assert spark.sql.call_args.kwargs["args"]["input"] == 7


def test_ops_tables_are_scoped_and_mutations_granted(service):
    spark = MagicMock()
    service.ops_tables.ensure_ops_tables(spark, "cat.sch")
    assert all(
        "CREATE TABLE IF NOT EXISTS" in c.args[0]
        and "workspace_id STRING" in c.args[0]
        and "COMMENT" in c.args[0]
        for c in spark.sql.call_args_list
    )
    spark.reset_mock()
    monitor = SimpleNamespace(name="apps-monitor", service_principal_client_id="monitor-sp")
    service.inventory_scan.grant_monitor_access(
        MagicMock(), spark, [monitor], "apps-monitor", "cat", "sch"
    )
    grants = "\n".join(c.args[0] for c in spark.sql.call_args_list)
    for table in ("alert_mutes", "slo_specs", "monitor_audit"):
        assert f"GRANT MODIFY ON TABLE `cat`.`sch`.`{table}`" in grants
    assert "GRANT SELECT ON SCHEMA" in grants


def test_unknown_slo_windows_do_not_resolve_but_deleted_specs_do(service):
    unknown = service.slo_eval.unknown_slo_keys([slo_row(good=0, total=0)])
    assert ("slo_fast_burn", "demo") in unknown
    spark = alert_spark({("slo_fast_burn", "demo")})
    service.source_scan.emit_alerts(
        spark, "cat", "sch", [], owned_rules=service.slo_eval.OWNED_RULES, unknown_keys=unknown
    )
    spark.createDataFrame.assert_not_called()
    service.source_scan.emit_alerts(
        spark, "cat", "sch", [], owned_rules=service.slo_eval.OWNED_RULES, unknown_keys=set()
    )
    assert spark.createDataFrame.call_args.args[0][0]["state"] == "resolved"


class Row(dict):
    def asDict(self):
        return dict(self)


@pytest.mark.parametrize("warehouse_unavailable,monitor_usd", [(False, 5), (False, 20), (True, 5)])
def test_self_meter_resolves_only_known_cost_and_preserves_gaps(
    service, monkeypatch, warehouse_unavailable, monitor_usd
):
    spark = MagicMock()
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)

    def result(sql, **_kwargs):
        frame = MagicMock()
        rows = []
        if "WITH priced AS" in sql and "system.billing.usage" in sql:
            rows = [Row(date=yesterday, component="app", usd=monitor_usd, basis="billing")]
        elif "WITH durations AS" in sql and warehouse_unavailable:
            raise RuntimeError("no query history privilege")
        elif sql.startswith("DESCRIBE DETAIL"):
            rows = [Row(sizeInBytes=123)]
        elif "SELECT sum(coalesce(dbu_usd" in sql:
            rows = [Row(usd=100)]
        frame.collect.return_value = rows
        return frame

    spark.sql.side_effect = result
    spark.catalog.tableExists.return_value = False
    sys.modules["pyspark.sql"].SparkSession.builder.getOrCreate.return_value = spark
    sys.modules[
        "databricks.sdk"
    ].WorkspaceClient.return_value.apps.get.return_value = SimpleNamespace(
        service_principal_client_id="monitor-sp", service_principal_id=42
    )
    emit = MagicMock()
    monkeypatch.setattr(service.source_scan, "emit_alerts", emit)
    monkeypatch.setattr(
        sys, "argv", ["meter", "--catalog=cat", "--schema=sch", "--job-ids=1,2", "--cost-pct=10"]
    )
    service.self_meter.main()
    rows = spark.createDataFrame.call_args.args[0]
    costs = {r["component"]: r for r in rows if r["date"] == yesterday}
    assert costs["warehouse"]["usd"] == (None if warehouse_unavailable else 0.0)
    if warehouse_unavailable:
        assert "unavailable" in costs["warehouse"]["basis"]
        assert emit.call_args.kwargs["evaluated_apps"] == set()
    else:
        assert emit.call_args.kwargs["evaluated_apps"] == {"apps-monitor"}
        assert bool(emit.call_args.args[3]) == (monitor_usd > 10)
    assert all(r["workspace_id"] == "123" for r in rows)
    merges = [
        c
        for c in spark.sql.call_args_list
        if "MERGE INTO `cat`.`sch`.monitor_cost_daily" in c.args[0]
    ]
    assert len(merges) == 1


def test_orphan_emitter_scopes_unknown_apps_and_resolves_recovery(service, monkeypatch):
    now = datetime.now(timezone.utc)
    end = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0)
    samples = [
        Row(name="bad", bucket=end - timedelta(minutes=15 * i), orphan_ratio=0.25)
        for i in range(25)
    ]
    samples += [
        Row(name="ok", bucket=end, orphan_ratio=0.1),
        Row(name="unknown", bucket=end, orphan_ratio=None),
    ]
    spark = MagicMock()
    spark.sql.return_value.collect.return_value = samples
    emit = MagicMock()
    monkeypatch.setattr(service.source_scan, "emit_alerts", emit)
    service.telemetry_health.check_telemetry(spark, "cat.sch", "123", "cat", "sch")
    assert [a["app"] for a in emit.call_args.args[3]] == ["bad"]
    assert emit.call_args.kwargs["evaluated_apps"] == {"bad", "ok"}
    assert emit.call_args.kwargs["owned_rules"] == ("telemetry_orphans",)


def test_job_bundle_wires_meter_and_quarter_hour_serverless():
    slo = yaml.safe_load((ROOT / "resources/slo.job.yml").read_text())["resources"]["jobs"][
        "slo_eval"
    ]
    assert slo["schedule"]["quartz_cron_expression"] == "0 0/15 * * * ?"
    assert slo["performance_target"] == "PERFORMANCE_OPTIMIZED"
    assert "new_cluster" not in str(slo)
    cost = yaml.safe_load((ROOT / "resources/cost.job.yml").read_text())["resources"]["jobs"][
        "cost_rollup"
    ]
    meter = next(t for t in cost["tasks"] if t["task_key"] == "self_meter")
    assert meter["depends_on"] == [{"task_key": "rollup"}]
    assert meter["run_if"] == "ALL_DONE"
    assert "{{job.id}}" in str(meter) and "${resources.jobs.cost_rollup.id}" not in str(meter)
