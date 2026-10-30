"""Service regressions with fake runtime clients; no Databricks connection is needed."""

from __future__ import annotations

import asyncio
import importlib.util
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def service(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT))
    # These are deployment dependencies, deliberately absent from the SDK's dev environment.
    for name in (
        "httpx",
        "uvicorn",
        "databricks",
        "databricks.sdk",
        "databricks.sdk.service",
        "databricks.sdk.service.sql",
        "databricks.sdk.service.apps",
        "databricks.sdk.service.workspace",
        "pyspark",
        "pyspark.sql",
    ):
        monkeypatch.setitem(sys.modules, name, MagicMock())
    client = sys.modules["databricks.sdk"].WorkspaceClient.return_value
    client.get_workspace_id.return_value = 123
    client.config.host = "https://workspace.invalid"
    client.config.authenticate.return_value = {"Authorization": "Bearer test"}
    loaded = {}
    for name, directory in (
        ("federation", "jobs"),
        ("schema_utils", "jobs"),
        ("alert_state", "jobs"),
        ("ops_tables", "jobs"),
        ("telemetry_sql", "jobs"),
        ("telemetry_health", "jobs"),
        ("slo_eval", "jobs"),
        ("self_meter", "jobs"),
        ("model_usage", "jobs"),
        ("app_stopper", "jobs"),
        ("inventory_scan", "jobs"),
        ("product_sql", "jobs"),
        ("source_scan", "jobs"),
        ("llm_review", "jobs"),
        ("gold_views", "jobs"),
        ("cost_rollup", "jobs"),
        ("quality_evals", "jobs"),
        ("prompt_drift", "jobs"),
        ("housekeeping", "jobs"),
        ("mutes", "app"),
        ("auth", "app"),
        ("reach_logic", "app"),
        ("alerts", "app"),
        ("queries", "app"),
        ("routes_ops", "app"),
        ("routes_product", "app"),
        ("routes_reach", "app"),
        ("synthetic", "app"),
        ("mlflow_traces", "app"),
        ("console_topology", "app"),
        ("console", "app"),
        ("main", "app"),
    ):
        spec = importlib.util.spec_from_file_location(name, ROOT / directory / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, name, module)
        spec.loader.exec_module(module)
        loaded[name] = module
    return SimpleNamespace(**loaded)


def firing(rule="app_stopped", app="demo"):
    return {
        "rule": rule,
        "app": app,
        "severity": "warning",
        "message": "stopped",
        "value": 0,
        "since": datetime(2020, 1, 1, tzinfo=timezone.utc),
    }


def test_restart_does_not_refire_and_preserves_since(service):
    a = service.alerts
    a.rehydrate([firing()])
    fleet = {"demo": {"app_state": "STOPPED"}}
    assert a.evaluate(fleet, {}, lambda _: {}) == []
    assert a.active()[0]["since"] == str(firing()["since"])
    events = a.evaluate({"demo": {"app_state": "RUNNING"}}, {}, lambda _: {})
    assert [e["state"] for e in events] == ["resolved"]
    assert a.active() == []


def test_restart_waits_for_consecutive_probe_evidence(service):
    a = service.alerts
    a.rehydrate([firing("app_down")])
    fleet = {"demo": {"app_state": "RUNNING"}}
    failed = (0, False, 503, 1)
    assert a.evaluate(fleet, {"demo": [failed]}, lambda _: {}) == []
    assert a.evaluate(fleet, {"demo": [failed, failed]}, lambda _: {}) == []
    assert (
        a.evaluate(fleet, {"demo": [failed, (1, True, 200, 1)]}, lambda _: {})[0]["state"]
        == "resolved"
    )


def test_journey_incident_requires_two_vantages_and_survives_missing_evidence(service):
    a = service.alerts
    fleet = {"demo": {"app_state": "RUNNING"}}
    now = datetime.now(timezone.utc).timestamp()
    rows = [
        {
            "app": "demo",
            "journey": "checkout",
            "vantage": v,
            "run_id": str(i),
            "run_ts": now - i,
            "ok": False,
        }
        for v in ("internal", "external")
        for i in (1, 2)
    ]
    assert a.evaluate(fleet, {}, lambda _: {}, vantage_rows=rows[:2]) == []
    assert [e["state"] for e in a.evaluate(fleet, {}, lambda _: {}, vantage_rows=rows)] == [
        "firing"
    ]
    assert a.evaluate(fleet, {}, lambda _: {}, vantage_rows=rows) == []
    assert a.evaluate(fleet, {}, lambda _: {}, vantage_rows=None) == []
    rows[2]["ok"] = True
    assert [e["state"] for e in a.evaluate(fleet, {}, lambda _: {}, vantage_rows=rows)] == [
        "resolved"
    ]


def test_rehydrate_precedes_scheduler(service, monkeypatch):
    main = service.main
    main.q.run = AsyncMock(return_value=[firing()])
    seen = []

    async def scheduler():
        seen.extend(main.alerts.active())

    monkeypatch.setattr(main, "scheduler", scheduler)

    async def run():
        async with main.lifespan(main.app):
            await asyncio.sleep(0)

    asyncio.run(run())
    assert seen[0]["rule"] == "app_stopped"
    main.q.run.assert_awaited_once_with(main.q.OPEN_ALERTS, ttl=0, ws="123")
    assert "INTERVAL" not in main.q.OPEN_ALERTS


def test_resolutions_respect_rule_and_successful_app_scope(service):
    resolve = service.alert_state.resolving_keys
    opened = {("scan", "a"), ("scan", "b"), ("cost", "a")}
    assert resolve(opened, {("scan", "a")}, ("scan",)) == {("scan", "b")}
    assert resolve(opened, set(), ("scan",), {"a"}) == {("scan", "a")}
    assert resolve(opened, set(), ("scan",), set()) == set()
    assert resolve(opened, set(), ()) == set()


def alert_spark(opened):
    spark = MagicMock()
    spark.table.return_value.columns = ["workspace_id", "muted", "incident_id"]

    def result(sql, **_kwargs):
        frame = MagicMock()
        frame.collect.return_value = (
            [] if "alert_mutes" in sql else [{"rule": r, "app": a} for r, a in opened]
        )
        return frame

    spark.sql.side_effect = result
    return spark


def test_job_emitter_resolves_empty_batch_and_deduplicates(service):
    spark = alert_spark({("cost_spike", "a")})
    service.source_scan.emit_alerts(spark, "cat", "sch", [], owned_rules=("cost_spike",))
    rows = spark.createDataFrame.call_args.args[0]
    assert [(r["rule"], r["app"], r["state"], r["workspace_id"]) for r in rows] == [
        ("cost_spike", "a", "resolved", "123")
    ]
    spark.createDataFrame.reset_mock()
    service.source_scan.emit_alerts(
        spark, "cat", "sch", [firing("cost_spike", "a")], owned_rules=("cost_spike",)
    )
    spark.createDataFrame.assert_not_called()


def test_job_emitter_partial_failure_and_new_app(service):
    spark = alert_spark({("critical_findings", "a")})
    service.source_scan.emit_alerts(
        spark,
        "cat",
        "sch",
        [firing("critical_findings", "b")],
        owned_rules=("critical_findings",),
        evaluated_apps={"b"},
    )
    rows = spark.createDataFrame.call_args.args[0]
    assert len(rows) == 1 and rows[0]["app"] == "b" and rows[0]["state"] == "firing"
    assert rows[0]["muted"] is False and rows[0]["incident_id"] is None


def test_schema_migration_adds_only_missing_columns(service):
    spark = MagicMock()
    spark.table.return_value.columns = ["muted"]
    service.schema_utils.ensure_columns(
        spark, "alerts", {"muted": "BOOLEAN", "incident_id": "STRING"}
    )
    spark.sql.assert_called_once_with("ALTER TABLE alerts ADD COLUMNS (incident_id STRING)")
    spark.sql.reset_mock()
    spark.table.return_value.columns = ["muted", "incident_id"]
    service.schema_utils.ensure_columns(
        spark, "alerts", {"muted": "BOOLEAN", "incident_id": "STRING"}
    )
    spark.sql.assert_not_called()


def test_billable_selection_handles_parents_legacy_and_explicit_false(service):
    with sqlite3.connect(":memory:") as db:
        db.execute(
            "CREATE TABLE spans (id TEXT, app_has_markers BOOL, billable BOOL, span_type TEXT, trace_has_llm BOOL)"
        )
        db.executemany(
            "INSERT INTO spans VALUES (?, ?, ?, ?, ?)",
            [
                ("marked-child", 1, 1, "LLM", 1),
                ("marked-parent", 1, None, "AGENT", 1),
                ("explicit-false", 1, 0, "LLM", 1),
                ("unmarked-sibling", 1, None, "LLM", 1),
                ("old-child", 0, None, "CHAT_MODEL", 1),
                ("old-agent", 0, None, "AGENT", 1),
                ("old-http-parent", 0, None, None, 1),
                ("legacy-untyped", 0, None, None, 0),
            ],
        )
        ids = {
            r[0] for r in db.execute(f"SELECT id FROM spans WHERE {service.telemetry_sql.BILLABLE}")
        }
    assert ids == {"marked-child", "old-child", "legacy-untyped"}


def test_aggregates_bootstrap_then_incremental_and_keep_retained_rows(service):
    spark = MagicMock()
    spark.sql.return_value.collect.return_value = []
    service.gold_views.materialize_aggregates(spark, "cat.sch", "123")
    merges = [c.args[0] for c in spark.sql.call_args_list if c.args[0].startswith("MERGE")]
    assert len(merges) == 3 and all("WHERE true" in q for q in merges)
    assert all("DELETE" not in q for q in merges)
    assert "hll_sketch_agg" in merges[0] and "users_hll" in merges[0]
    assert all("t.workspace_id = s.workspace_id" in q for q in merges)
    spark.reset_mock()
    spark.sql.return_value.collect.return_value = [1]
    service.gold_views.materialize_aggregates(spark, "cat.sch", "123")
    merges = [c.args[0] for c in spark.sql.call_args_list if c.args[0].startswith("MERGE")]
    assert all("WHERE date >= current_date() - 2" in q for q in merges)
    views = dict(service.gold_views.views_sql("cat.sch"))
    assert "cat.sch.agg_app_daily" in views["v_usage_daily"]
    assert "cat.sch.agg_genai_daily" in views["v_genai_daily"]


def test_semconv_and_synthetic_expressions_agree(service):
    assert service.queries.HTTP_STATUS == service.telemetry_sql.HTTP_STATUS
    assert service.queries.HTTP_ROUTE == service.telemetry_sql.HTTP_ROUTE
    assert service.queries.NOT_PROBE == service.telemetry_sql.NOT_PROBE
    assert service.queries.HTTP_STATUS in service.queries.ERROR_SPANS
    assert (
        "exception.fingerprint" in dict(service.gold_views.views_sql("cat.sch"))["v_error_groups"]
    )


@pytest.mark.parametrize(
    "status,content_type,path",
    [
        (200, "application/json", "/monitor/health"),
        (503, "application/json", "/monitor/health"),
        (404, "application/json", "/ready"),
        (405, "", "/ready"),
        (200, "text/html", "/ready"),
    ],
)
def test_capacity_route_discovery(service, status, content_type, path):
    client = SimpleNamespace(
        get=AsyncMock(
            return_value=SimpleNamespace(status_code=status, headers={"content-type": content_type})
        )
    )
    url = asyncio.run(
        service.synthetic.capacity_url(
            client, "https://app.invalid/", "/ready", {"Authorization": "test"}
        )
    )
    assert url == "https://app.invalid" + path
    assert client.get.call_args.kwargs["headers"]["x-monitor-synthetic"] == "capacity"


@pytest.mark.parametrize(
    "path",
    ["https://elsewhere/", "//elsewhere/", "/healthz", "/healthz/", "/%68ealthz", "/\\elsewhere"],
)
def test_capacity_path_stays_on_app_and_avoids_proxy(service, path):
    with pytest.raises(ValueError):
        service.synthetic.capacity_path(path)
    assert service.synthetic.capacity_path(None) == "/"


def test_probe_fallback_and_journeys_are_tagged(service):
    main = service.main
    response = SimpleNamespace(status_code=404, headers={}, aread=AsyncMock())
    stream = MagicMock()
    stream.__aenter__ = AsyncMock(return_value=response)
    stream.__aexit__ = AsyncMock(return_value=None)
    client = SimpleNamespace(
        stream=MagicMock(return_value=stream),
        get=AsyncMock(return_value=SimpleNamespace(status_code=200)),
    )
    headers = {"Authorization": "test"}
    asyncio.run(main._probe_one(client, "demo", "https://app.invalid", headers))
    assert client.stream.call_args.kwargs["headers"]["x-monitor-synthetic"] == "probe"
    assert client.get.call_args.kwargs["headers"]["x-monitor-synthetic"] == "probe"
    assert "x-monitor-synthetic" not in headers
    journey_client = MagicMock()
    journey_client.__aenter__ = AsyncMock(return_value=journey_client)
    journey_client.__aexit__ = AsyncMock(return_value=None)
    journey_client.request = AsyncMock(return_value=SimpleNamespace(status_code=200, headers={}))
    main.httpx.AsyncClient.return_value = journey_client
    main.fleet = {"demo": {"url": "https://app.invalid"}}
    main.JOURNEYS = {"auto_journey": {"name": "check", "steps": [{"path": "/ready"}]}}
    asyncio.run(main.run_journeys())
    assert journey_client.request.call_args.kwargs["headers"]["x-monitor-synthetic"] == "journey"


def test_retention_depends_on_gold_and_preserves_latest_alert(service):
    jobs = yaml.safe_load((ROOT / "resources/lifecycle.job.yml").read_text())["resources"]["jobs"]
    tasks = {t["task_key"]: t for t in jobs["telemetry_retention"]["tasks"]}
    assert tasks["gold"]["run_job_task"]["job_id"] == "${resources.jobs.inventory_scan.id}"
    assert tasks["housekeeping"]["depends_on"] == [{"task_key": "gold"}]
    assert tasks["housekeeping"]["run_if"] == "ALL_SUCCESS"
    assert "t.ts < s.latest" in service.housekeeping.alert_retention_sql("cat.sch", 1)


def test_cost_rollup_keeps_gateway_separate_and_resolves_empty_batch(service, monkeypatch):
    spark = MagicMock()
    spark.table.return_value.columns = ["workspace_id", "ai_tokens_gateway"]
    spark.sql.return_value.collect.return_value = []

    def result(sql, **_kwargs):
        frame = MagicMock()
        frame.collect.return_value = [{"c": 1}] if "SELECT count(*) c" in sql else []
        return frame

    spark.sql.side_effect = result
    service.cost_rollup.SparkSession.builder.getOrCreate.return_value = spark
    emit = MagicMock()
    monkeypatch.setattr(service.source_scan, "emit_alerts", emit)
    monkeypatch.setattr(sys, "argv", ["cost_rollup", "--catalog=cat", "--schema=sch"])
    service.cost_rollup.main()
    statements = [c.args[0] for c in spark.sql.call_args_list]
    gateway = next(sql for sql in statements if "TEMP VIEW app_gw" in sql)
    assert "g.requester = p.sp_client_id" in gateway and "'(untagged)'" in gateway
    assert "GROUP BY sp_client_id" in gateway
    assert "coalesce(request_tags['app'], requester)" not in gateway
    totals = next(sql for sql in statements if "MERGE INTO `cat`.`sch`.costs_daily" in sql)
    assert "greatest(" not in totals
    assert "g.ai_tokens_gateway" in totals
    assert "coalesce(a.ai_input_tokens, 0) AS ai_input_tokens" in totals
    assert "t.workspace_id = s.workspace_id" in totals
    emit.assert_called_once_with(spark, "cat", "sch", [], owned_rules=("cost_spike",))


def test_anomaly_and_budget_checks_clear_conditions_without_findings(service, monkeypatch):
    spark = MagicMock()
    spark.sql.return_value.collect.return_value = []
    emit = MagicMock()
    monkeypatch.setattr(service.source_scan, "emit_alerts", emit)
    service.gold_views.detect_anomalies(spark, "`cat`.`sch`")
    emit.assert_called_once_with(
        spark, "cat", "sch", [], owned_rules=("anomaly_traffic", "anomaly_latency")
    )
    emit.reset_mock()
    service.gold_views.check_budgets(spark, "`cat`.`sch`")
    emit.assert_called_once_with(spark, "cat", "sch", [], owned_rules=("budget_burn",))


def _probe_client(responses):
    """Stream responses keyed by path suffix; unknown paths 404."""

    def stream(method, url, headers):
        status, ctype, body = responses.get(url.rsplit("/", 1)[-1], (404, "", b""))
        r = SimpleNamespace(
            status_code=status, headers={"content-type": ctype}, aread=AsyncMock(return_value=body)
        )
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=r)
        ctx.__aexit__ = AsyncMock(return_value=None)
        return ctx

    return SimpleNamespace(
        stream=MagicMock(side_effect=stream),
        get=AsyncMock(return_value=SimpleNamespace(status_code=200)),
    )


def test_probe_prefers_sdk_health_and_sees_degraded_dependencies(service):
    main = service.main
    main.probes.clear()
    body = b'{"status": "degraded", "checks": {"db": {"ok": false}}}'
    client = _probe_client({"health": (503, "application/json", body)})
    asyncio.run(main._probe_one(client, "v2", "https://app.invalid", {}))
    _, ok, code, _ = main.probes["v2"][-1]
    assert (ok, code) == (False, 503)
    assert main.health_detail["v2"]["checks"]["db"]["ok"] is False
    assert client.stream.call_args_list[0].args[1].endswith("/monitor/health")
    assert client.stream.call_count == 1


def test_probe_falls_back_to_healthz_for_v1_apps_and_flags_placeholders(service):
    main = service.main
    main.probes.clear()
    client = _probe_client({"healthz": (200, "application/json", b"{}")})
    asyncio.run(main._probe_one(client, "v1", "https://app.invalid", {}))
    assert main.probes["v1"][-1][1:3] == (True, 200)
    assert [c.args[1].rsplit("/", 1)[-1] for c in client.stream.call_args_list] == [
        "health",
        "healthz",
    ]
    stopped = _probe_client({"health": (200, "text/html", b"<html>")})
    asyncio.run(main._probe_one(stopped, "stopped", "https://app.invalid", {}))
    assert main.probes["stopped"][-1][1] is False
