"""Console contracts and pure mappings; no warehouse or Databricks credentials."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from test_service_correctness import ROOT
from test_service_correctness import service as service

NOW = datetime(2026, 10, 30, 9, 30, tzinfo=timezone.utc)


def live(**overrides):
    return {
        "workspace": "local",
        "workspace_id": "123",
        "last_collection": NOW,
        "fleet": {"demo": {"app_state": "RUNNING", "compute_state": "ACTIVE"}},
        "summaries": {"demo": {"last": {"ok": True}, "uptime_24h": 100}},
        **overrides,
    }


@pytest.mark.parametrize(
    "info,summary,detail,points,requests,expected",
    [
        ({"app_state": "STOPPED"}, {}, {}, [], None, "stopped"),
        ({"compute_state": "STOPPED"}, {}, {}, [], None, "stopped"),
        ({"app_state": "FAILED"}, {}, {}, [], None, "down"),
        ({"app_state": "RUNNING"}, {}, {}, [], None, None),
        ({}, {"last": {"ok": False}}, {}, [(1, False)], None, "degraded"),
        ({}, {"last": {"ok": False}}, {}, [(1, False), (2, False)], None, "down"),
        ({}, {"last": {"ok": True}}, {"status": "degraded"}, [], 10, "degraded"),
        ({}, {"last": {"ok": True}, "error_rate_1h": "6"}, {}, [], 10, "degraded"),
        ({}, {"last": {"ok": True}}, {}, [], 0, "idle"),
        ({}, {"last": {"ok": True}}, {}, [], None, "healthy"),
    ],
)
def test_health(service, info, summary, detail, points, requests, expected):
    assert service.console.health(info, summary, detail, points, requests) == expected


def test_hourly_utc_buckets_and_gaps(service):
    result = service.console.hourly_series(
        [
            {"hour": "2026-10-30T10:00:00+02:00", "requests": "10", "errors": "2", "p95_ms": "125"},
            {"hour": "2026-10-30 09:00:00", "requests": "0", "errors": "0", "p95_ms": None},
            {"hour": "2026-10-29 09:00:00", "requests": "999"},
        ],
        NOW,
    )
    assert len(result["hours"]) == 24
    assert result["hours"][0] == "2026-10-29T10:00:00Z"
    assert result["requests"][-2:] == [10, 0]
    assert result["error_rate_pct"][-2:] == [20, None]
    assert result["p95_ms"][-2:] == [125, None]
    assert all(x is None for x in result["requests"][:-2])
    invalid = service.console.hourly_series(
        [{"hour": NOW, "requests": 1, "errors": 2, "p95_ms": "NaN"}], NOW
    )
    assert invalid["error_rate_pct"][-1] is None
    assert invalid["p95_ms"][-1] is None


def test_snapshot_sparse_and_partial_sources(service):
    result = service.console.build_snapshot(live(), {}, {"costs": "error", "slos": "missing"}, NOW)
    a = result["apps"][0]
    assert a["health"] == "healthy"
    assert a["last24h"]["p95_ms"] is None  # Probe latency must not become request latency.
    assert a["cost"]["mtd_usd"] is None
    assert a["security"]["cve"]["critical"] is None
    assert a["slo"]["availability_target"] is None
    assert result["trace_example"] is None
    assert result["sources"] == {"costs": "error", "slos": "missing"}
    json.dumps(result, allow_nan=False)
    empty = service.console.build_snapshot(live(fleet={}), {}, {}, NOW)
    assert empty["apps"] == []
    stale = service.console.build_snapshot(
        live(last_collection=NOW - timedelta(hours=3)), {}, {}, NOW
    )
    assert stale["workspaces"][0]["status"] == "STALE"


def test_real_mapping_types_units_and_costs(service):
    result = service.console.build_snapshot(
        live(),
        {
            "performance": [
                {
                    "name": "demo",
                    "requests_24h": "100",
                    "errors_24h": "2",
                    "real_p95_ms": "430",
                    "active_users": "3",
                }
            ],
            "configs": [
                {"name": "demo", "tags_json": '{"team":"Engineering"}', "budget_usd_month": "90"}
            ],
            "unit_economics": [{"name": "demo", "total_usd": "15", "dbu_usd": "10", "ai_usd": "5"}],
            "telemetry": [
                {
                    "name": "demo",
                    "envelope_coverage": ".8",
                    "orphan_ratio_24h": ".02",
                    "last_span_at": "2026-10-30 09:29:00",
                }
            ],
            "slos": [
                {
                    "name": "demo",
                    "sli": "availability",
                    "window_days": "28",
                    "target": ".999",
                    "total": "10000",
                    "good": "9980",
                    "budget_remaining_pct": "-100",
                }
            ],
        },
        {"performance": "ok"},
        NOW,
    )
    a = result["apps"][0]
    assert a["last24h"]["error_rate_pct"] == 2
    assert a["cost"]["mtd_usd"] == 15
    assert a["telemetry"]["envelope_coverage_pct"] == 80
    assert a["telemetry"]["last_span_age_s"] == 60
    assert a["slo"]["availability_target"] == pytest.approx(99.9)
    assert a["slo"]["attainment_28d"] == 99.8
    assert a["slo"]["error_budget_remaining_pct"] == -100
    assert a["team"] == "Engineering"
    assert not a["governance"]["tags_complete"]


def test_slo_does_not_relabel_seven_day_or_route_filtered_objectives(service):
    assert (
        service.console.shape_slo([{"sli": "availability", "window_days": 7, "target": 0.99}])[
            "availability_target"
        ]
        is None
    )
    assert (
        service.console.shape_slo(
            [{"sli": "availability", "window_days": 28, "route_filter": "/api"}]
        )["attainment_28d"]
        is None
    )


def test_federated_names_do_not_join_local_metrics(service):
    result = service.console.build_snapshot(
        live(),
        {
            "performance": [{"name": "demo", "requests_24h": "100"}],
            "federation": [
                {
                    "name": "demo",
                    "workspace_name": "remote",
                    "workspace_id": "456",
                    "snapshot_ts": "2026-10-30 06:00:00",
                    "app_state": "RUNNING",
                    "requests_7d": "44",
                }
            ],
            "federation_alerts": [
                {"app": "demo", "workspace_id": "456", "rule": "app_down", "ts": NOW}
            ],
        },
        {},
        NOW,
    )
    a, b = result["apps"]
    assert a["id"] != b["id"]
    assert b["last24h"]["requests"] is None
    assert b["health"] is None
    assert b["usage_7d"]["requests"] == 44
    assert result["workspaces"][-1]["status"] == "STALE"
    assert result["alerts"][0]["app"] == b["id"]


def test_trace_orphans_offsets_and_attributes(service):
    start = int(NOW.timestamp() * 1e9)
    rows = [
        {
            "span_id": "root",
            "name": "GET /",
            "service_name": "demo",
            "kind": "SERVER",
            "start_time_unix_nano": str(start),
            "end_time_unix_nano": str(start + 100_000_000),
            "attributes": '{"session.id":"s1"}',
            "status": "ok",
        },
        {
            "span_id": "child",
            "parent_span_id": "missing",
            "start_time_unix_nano": str(start + 10_000_000),
            "end_time_unix_nano": str(start + 20_000_000),
            "attributes": "not json",
            "status": "error",
        },
    ]
    result = service.console.shape_trace(
        "aabb",
        rows,
        [{"time": NOW + timedelta(milliseconds=50), "service_name": "demo", "body": "message"}],
    )
    assert result["duration_ms"] == 100
    assert result["status"] == "error"
    assert result["session_id"] == "s1"
    assert result["spans"][1]["parent"] is None
    assert result["spans"][1]["attrs"]["monitor.orphan_parent"] == "missing"
    assert result["spans"][1]["start_ms"] == 10
    assert result["logs"][0]["ts_ms"] == pytest.approx(50, abs=0.001)
    assert service.console.shape_trace("aabb", [], []) is None
    json.dumps(
        service.console.shape_trace("aabb", [{"span_id": "x", "attributes": None}], []),
        allow_nan=False,
    )


@pytest.mark.parametrize(
    "trace_id,code",
    [
        ("abcDEF0123", 404),
        ("a" * 64, 404),
        ("a" * 65, 422),
        ("not-a-trace", 422),
        ("' OR 1=1", 422),
    ],
)
def test_trace_route_validates_before_query(service, monkeypatch, trace_id, code):
    run = AsyncMock(return_value=[])
    monkeypatch.setattr(service.queries, "run", run)
    response = TestClient(service.main.app).get(f"/api/console/trace/{trace_id}")
    assert response.status_code == code
    assert run.await_count == (2 if code == 404 else 0)
    if code == 404:
        assert run.call_args.kwargs["tid"] == trace_id


def test_trace_partial_logs_and_query_failure(service, monkeypatch):
    async def run(sql, **_params):
        if sql == service.queries.TRACE_LOGS:
            raise RuntimeError("TABLE_OR_VIEW_NOT_FOUND")
        return [{"span_id": "1", "name": "root", "attributes": "{}"}]

    monkeypatch.setattr(service.queries, "run", run)
    client = TestClient(service.main.app)
    response = client.get("/api/console/trace/abc")
    assert response.status_code == 200
    assert response.json()["sources"]["logs"] == "missing"
    monkeypatch.setattr(
        service.queries, "run", AsyncMock(side_effect=RuntimeError("warehouse failed"))
    )
    assert client.get("/api/console/trace/abc").status_code == 503


def test_shell_and_classic_routes(service):
    client = TestClient(service.main.app)
    root = client.get("/")
    assert root.status_code == 200 and "boot.js" in root.text
    classic = client.get("/classic")
    assert classic.status_code == 200
    assert classic.text == (ROOT / "app/static/index.html").read_text()
    assert client.get("/console/boot.js").status_code == 200
    assert client.get("/console/tokens.css").status_code == 200


def test_demo_has_snapshot_keys(service):
    data = (ROOT / "app/static/console/demo-data.js").read_text()
    demo = json.loads(data.removeprefix("window.MOCK = ").strip().removesuffix(";"))
    snapshot = service.console.build_snapshot(live(), {}, {}, NOW)
    assert set(demo) == set(snapshot)
    assert len(demo["apps"]) == 12
    assert demo["trace_example"]["spans"]
    assert set(demo["apps"][0]) == set(snapshot["apps"][0])
    for key in ("topology", "fleet_measures"):
        assert set(snapshot[key]) <= set(demo[key])


def test_concurrent_optional_sources_cache_and_live_overlay(service, monkeypatch):
    main, console = service.main, service.console
    main.fleet["demo"] = {"name": "demo", "app_state": "RUNNING"}
    main._last_fleet_refresh = NOW.timestamp()
    main._last_probe_ts = NOW.timestamp()
    main._ws_id = 123
    main.probes["demo"] = [(NOW.timestamp(), True, 200, 10)]
    calls = []

    async def run(sql, **params):
        calls.append(sql)
        await asyncio.sleep(0.01)
        if sql == service.queries.CONSOLE_SLOS:
            raise RuntimeError("TABLE_OR_VIEW_NOT_FOUND")
        if sql == service.queries.REAL_PERF_FLEET:
            return [{"name": "demo", "requests_24h": "25"}]
        return []

    monkeypatch.setattr(service.queries, "run", run)
    endpoint = next(
        r.endpoint
        for r in console.build_router(vars(main)).routes
        if getattr(r, "path", "") == "/api/console/snapshot"
    )

    async def exercise():
        first, second = await asyncio.gather(endpoint(), endpoint())
        assert first["sources"]["slos"] == "missing"
        assert first["apps"][0]["last24h"]["requests"] == 25
        count = len(calls)
        assert count == len(console.query_plan("123", NOW))
        main.probes["demo"].extend([(NOW.timestamp(), False, 503, 5)] * 2)
        third = await endpoint()
        assert len(calls) == count
        assert third["apps"][0]["health"] == "down"
        assert second["apps"][0]["health"] == "healthy"
        main.fleet.clear()
        assert not (await endpoint())["apps"]

    asyncio.run(exercise())


def test_slow_warehouse_does_not_block_live_inventory(service, monkeypatch):
    async def run(*_args, **_kwargs):
        await asyncio.sleep(10)
        return []

    monkeypatch.setattr(service.queries, "run", run)
    endpoint = next(
        r.endpoint
        for r in service.console.build_router(vars(service.main)).routes
        if getattr(r, "path", "") == "/api/console/snapshot"
    )

    async def exercise():
        result = await asyncio.wait_for(endpoint(), 0.3)
        assert result["notes"]["collecting"]
        assert "inventory" in result["sources"]

    asyncio.run(exercise())


def test_lazy_app_errors_parameterized(service, monkeypatch):
    service.main.fleet["demo"] = {"name": "demo"}
    run = AsyncMock(
        return_value=[
            {"name": "demo", "fingerprint": "fp", "count_24h": "2", "sample_trace_id": "abc"}
        ]
    )
    monkeypatch.setattr(service.queries, "run", run)
    client = TestClient(service.main.app)
    assert client.get("/api/console/apps/missing/errors").status_code == 404
    response = client.get("/api/console/apps/demo/errors")
    assert response.json()["error_groups"][0]["count_24h"] == 2
    assert run.call_args.kwargs["app"] == "demo"


def test_synthetics_and_alert_boolean_strings(service):
    checks = service.console.shape_synthetics(
        [
            {
                "app": "demo",
                "journey": "journey",
                "vantage": "internal",
                "ok": "true",
                "run_ts": NOW - timedelta(minutes=1),
            },
            {
                "app": "demo",
                "journey": "journey",
                "vantage": "internal",
                "ok": "false",
                "run_ts": NOW,
            },
        ]
    )
    assert checks[0]["history"] == [True, False]
    alerts = service.console.shape_alerts(
        [
            {"app": "demo", "rule": "down", "state": "firing", "muted": "false", "ts": NOW},
            {
                "app": "demo",
                "rule": "down",
                "state": "resolved",
                "muted": "true",
                "ts": NOW + timedelta(minutes=1),
            },
        ]
    )
    assert len(alerts) == 1 and alerts[0]["state"] == "resolved" and alerts[0]["muted"]


def test_cost_series_and_totals_do_not_fill_gaps_with_zero(service):
    console = service.console
    rows = [
        {"date": "2026-10-28", "dbu_usd": "2", "total_usd": "3"},
        {"date": "2026-10-29", "dbu_usd": None, "total_usd": "4"},
    ]
    assert console.daily_cost_series(rows, ["2026-10-28", "2026-10-29", "2026-10-30"]) == [
        3,
        None,
        None,
    ]
    assert console.total([None, 3]) is None
    assert console.total([0, 3]) == 3
    assert console.total([]) is None
    assert "count_if(dbu_usd IS NULL)" in service.queries.CONSOLE_UNIT_ECONOMICS


def test_usage_shapes_configured_steps_and_cohort_gaps(service):
    funnel, cohort = service.console.shape_usage(
        [
            {
                "name": "demo",
                "funnel": "checkout",
                "app_version": "v1",
                "step_name": "cart",
                "sessions": "10",
            },
            {
                "name": "demo",
                "funnel": "checkout",
                "app_version": "v1",
                "step_name": "purchase",
                "sessions": "3",
            },
        ],
        [
            {
                "name": "demo",
                "cohort_week": "2026-10-19",
                "week_number": "0",
                "cohort_size": "10",
                "retention_pct": "100",
            },
            {
                "name": "demo",
                "cohort_week": "2026-10-19",
                "week_number": "1",
                "cohort_size": "10",
                "retention_pct": "30",
            },
            {
                "name": "demo",
                "cohort_week": "2026-10-26",
                "week_number": "0",
                "cohort_size": "20",
                "retention_pct": "100",
            },
        ],
    )
    assert funnel["by_version"]["v1"][-1] == {"step": "purchase", "sessions": 3}
    assert cohort["retention_pct"] == [[100, 30], [100, None]]
    assert cohort["sizes"] == [10, 20]


def test_optional_read_deadline_degrades_one_source(service, monkeypatch):
    async def slow(*_args, **_kwargs):
        await asyncio.sleep(1)

    monkeypatch.setattr(service.queries, "run", slow)
    monkeypatch.setattr(service.console, "QUERY_TIMEOUT", 0.01)
    assert asyncio.run(service.console.optional_read("query", {})) == ([], "error")


def test_gold_genai_and_live_sdk_signals_keep_their_periods(service):
    result = service.console.build_snapshot(
        live(),
        {
            "genai": [
                {
                    "name": "demo",
                    "model": "model",
                    "calls": "12",
                    "input_tokens": "100",
                    "output_tokens": "50",
                }
            ],
            "genai_signals": [{"name": "demo", "ttft_p95_ms": "80", "rate_limit": "2"}],
            "packages": [
                {"name": "demo", "deps_json": '[{"behind":"minor"},{"behind":"current"}]'}
            ],
            "health_detail": [],
        },
        {},
        NOW,
    )
    a = result["apps"][0]
    assert a["genai"]["period"] == "Previous UTC day"
    assert a["genai"]["calls_24h"] == 12
    assert a["genai"]["ttft_p95_ms"] == 80
    assert a["genai"]["error_classes_24h"]["rate_limit"] == 2
    assert a["security"]["outdated_packages"] == 1


def test_idle_requires_observed_export_and_successful_traffic_read(service):
    data = {"telemetry": [{"name": "demo", "last_span_at": NOW}]}
    observed = service.console.build_snapshot(live(), data, {"performance": "ok"}, NOW)["apps"][0]
    assert observed["health"] == "idle" and observed["last24h"]["requests"] == 0
    missing = service.console.build_snapshot(live(), data, {"performance": "error"}, NOW)["apps"][0]
    assert missing["health"] == "healthy" and missing["last24h"]["requests"] is None
    uninstrumented = service.console.build_snapshot(live(), {}, {"performance": "ok"}, NOW)["apps"][
        0
    ]
    assert uninstrumented["last24h"]["requests"] is None


@pytest.mark.parametrize("value", [None, "not json", "{}", {}, [None, "wrong"]])
def test_invalid_resource_json_is_not_a_binding(service, value):
    assert service.console_topology.resources(value) == []


def test_resources_fall_back_to_inventory_and_live_declarations_win(service):
    resource = {"name": "warehouse", "sql_warehouse": {"id": "wh"}}
    data = {"inventory_resources": [{"name": "demo", "resources_json": json.dumps([resource])}]}
    result = service.console.build_snapshot(live(), data, {}, NOW)
    assert result["apps"][0]["resources"] == [resource]
    assert result["topology"]["edges"][0]["declared"]
    result = service.console.build_snapshot(live(fleet={"demo": {"resources": []}}), data, {}, NOW)
    assert result["apps"][0]["resources"] == []
    assert result["topology"]["edges"] == []


def test_graph_merges_typed_runtime_peers_and_qualifies_workspaces(service):
    def app(ws, name, bindings):
        return {
            "id": f"{ws}:{name}",
            "name": name,
            "workspace_id": ws,
            "url": f"https://{name}-{ws}.apps.invalid",
            "resources": bindings,
        }

    bindings = [
        {"name": "warehouse", "sql_warehouse": {"id": "shared"}},
        {"name": "model", "serving_endpoint": {"name": "shared"}},
        {"name": "peer", "app": {"name": "target"}},
        {"name": "database", "postgres": {"database": "orders"}},
    ]
    apps = [
        app("1", "source", bindings),
        app("1", "target", bindings[:1]),
        app("2", "source", bindings),
    ]
    observed = [
        {
            "dependency": "databricks_sql/shared",
            "calls": "10",
            "errors": "1",
            "avg_ms": "10",
            "p95_ms": "100",
        },
        {"dependency": "databricks/shared", "calls": 30, "errors": 1, "avg_ms": 30, "p95_ms": 90},
        {
            "dependency": "https://workspace/serving-endpoints/shared/invocations",
            "calls": 2,
            "errors": 0,
        },
        {"dependency": "https://target-1.apps.invalid/api", "calls": 3, "errors": 0},
        {"dependency": "postgresql/orders", "calls": 1, "errors": 0},
        {"dependency": "external.invalid", "calls": 9, "errors": 2},
    ]
    result = service.console_topology.graph(
        apps, [{"workspace_id": "1", "name": "source", **r} for r in observed]
    )
    edges = {e["target"]: e for e in result["edges"] if e["source"] == "app:1:source"}
    wh = edges["resource:1:sql_warehouse:shared"]
    assert wh["declared"] and wh["observed"]
    assert (wh["calls"], wh["errors"], wh["avg_ms"], wh["p95_ms"], wh["error_pct"]) == (
        40,
        2,
        25,
        100,
        5,
    )
    assert edges["resource:1:serving_endpoint:shared"]["calls"] == 2
    assert edges["app:1:target"]["declared"] and edges["app:1:target"]["observed"]
    assert edges["resource:1:postgres:orders"]["observed"]
    assert not edges["resource:1:external:external.invalid"]["declared"]
    assert not any(e["observed"] for e in result["edges"] if e["source"] == "app:2:source")
    nodes = {n["id"]: n for n in result["nodes"]}
    assert nodes["resource:1:sql_warehouse:shared"]["dependents"] == [
        "app:1:source",
        "app:1:target",
    ]
    assert nodes["resource:1:sql_warehouse:shared"]["health"] is None
    assert "not a combined" in result["latency_basis"]


def test_graph_partial_metrics_and_invalid_sources_stay_unknown(service):
    apps = [{"id": "a", "name": "a", "workspace_id": "1", "resources": []}]
    rows = [
        {
            "workspace_id": "1",
            "name": "a",
            "dependency": "peer",
            "calls": 10,
            "errors": 1,
            "avg_ms": 10,
        },
        {"workspace_id": "1", "name": "a", "dependency": "https://peer/path", "calls": 5},
        {"workspace_id": "other", "name": "a", "dependency": "peer", "calls": 100},
        {"workspace_id": "1", "name": "missing", "dependency": "peer", "calls": 100},
    ]
    result = service.console_topology.graph(apps, rows)
    assert len(result["edges"]) == 1
    edge = result["edges"][0]
    assert edge["calls"] == 15
    assert edge["avg_ms"] is edge["errors"] is edge["error_pct"] is None
    assert edge["p95_ms"] is None


def test_each_declared_binding_type_has_a_stable_target(service):
    fixtures = json.loads(
        (ROOT / "app/static/console/demo-fixtures.js")
        .read_text()
        .removeprefix("window.CONSOLE_FIXTURES = ")
        .strip()
        .removesuffix(";")
    )
    # Use the actual Apps API binding shapes from the demo contract.
    bindings = fixtures["api/apps/claims-assistant/ops"]["resources"]
    pairs = dict(service.console_topology.binding(r) for r in bindings)
    assert pairs == {
        "sql_warehouse": "wh-7d1a",
        "serving_endpoint": "claims-model",
        "job": "101",
        "experiment": "201",
        "database": "risk-db",
        "postgres": "claims-db",
        "uc_securable": "demo.claims.documents",
        "secret": "app-secrets",
        "genie_space": "genie-demo",
        "app": "doc-intake",
    }


def test_identity_is_per_request_and_writes_still_require_admin(service, monkeypatch):
    monkeypatch.setattr(service.auth, "MONITOR_ADMINS", {"operator@example.test"})
    monkeypatch.setenv("STOPPER_JOB_ID", "42")
    service.main.w.jobs.run_now.return_value = MagicMock(run_id=123)
    client = TestClient(service.main.app)
    for actor, allowed in [("OPERATOR@example.test", True), ("viewer@example.test", False)]:
        headers = {"x-forwarded-email": actor}
        identity = client.get("/api/console/identity", headers=headers).json()
        assert identity["admin"] is allowed
        assert bool(identity["reason"]) is not allowed
        response = client.post("/api/actions/appctl/demo/restart", headers=headers)
        assert response.status_code == (200 if allowed else 403)
    service.main.w.jobs.run_now.assert_called_once_with(
        job_id=42, job_parameters={"app": "demo", "action": "restart"}
    )
    assert not client.get("/api/console/identity").json()["admin"]
    assert (
        client.post(
            "/api/actions/appctl/apps-monitor/restart",
            headers={"x-forwarded-email": "operator@example.test"},
        ).status_code
        == 400
    )


def test_restart_waits_for_stop_and_failure_never_starts(service):
    client = MagicMock()
    service.app_stopper.manual_control(client, "demo", "restart")
    client.apps.stop_and_wait.assert_called_once_with("demo", timeout=timedelta(minutes=10))
    client.api_client.do.assert_called_once_with("POST", "/api/2.0/apps/demo/start")
    client.reset_mock()
    client.apps.stop_and_wait.side_effect = TimeoutError("stop not complete")
    with pytest.raises(TimeoutError):
        service.app_stopper.manual_control(client, "demo", "restart")
    client.api_client.do.assert_not_called()
    with pytest.raises(ValueError, match="protected"):
        service.app_stopper.manual_control(client, "apps-monitor", "restart")


def test_graph_query_is_fleet_wide_and_parameterized(service):
    query, params = service.console.query_plan("ws-with-'", NOW)["dependencies"]
    assert params == {"ws": "ws-with-'"}
    assert ":ws" in query and ":app" not in query and "ws-with-'" not in query
    assert "sum(avg_ms * calls)" in query and "max(p95_ms)" in query
    assert ":ws" in service.queries.CONSOLE_RESOURCES


@pytest.mark.parametrize(
    "path,label",
    [("ops", "App configuration"), ("cost", "Cost forecast"), ("genai", "LLM error taxonomy")],
)
def test_optional_deep_failures_are_reported_without_discarding_evidence(
    service, monkeypatch, path, label
):
    async def run(sql, **_params):
        if sql in {
            service.queries.COST_APP,
            service.queries.GENAI_DAILY,
            service.queries.GENAI_TOP,
        }:
            return [{"date": "2026-10-30", "calls": 3}]
        raise RuntimeError("warehouse unavailable")

    monkeypatch.setattr(service.queries, "run", run)
    result = TestClient(service.main.app).get(f"/api/apps/demo/{path}")
    assert result.status_code == 200
    assert label in result.json()["_source_errors"]
    if path in {"cost", "genai"}:
        assert result.json()["daily"][0]["calls"] == 3


def test_policy_apply_requires_available_config_and_matching_preview(service, monkeypatch):
    monkeypatch.setattr(service.auth, "MONITOR_ADMINS", {"operator@example.test"})
    service.main.fleet["demo"] = {"name": "demo"}
    run = AsyncMock(side_effect=RuntimeError("warehouse unavailable"))
    write = AsyncMock()
    monkeypatch.setattr(service.queries, "run", run)
    monkeypatch.setattr(service.queries, "run_dml", write)
    client = TestClient(service.main.app)
    headers = {"x-forwarded-email": "operator@example.test"}
    path = "/api/actions/autostop-policy"
    assert client.post(path, headers=headers, json={"dry_run": True}).status_code == 503
    run.side_effect = None
    run.return_value = []
    assert client.post(path, headers=headers, json={"dry_run": True}).json()["targets"] == ["demo"]
    assert client.post(path, headers=headers, json={"expected_targets": ["old"]}).status_code == 409
    write.assert_not_called()


def test_browser_history_uses_the_requested_window_and_artifact_fields(service, monkeypatch):
    run = AsyncMock(return_value=[])
    monkeypatch.setattr(service.queries, "run", run)
    response = TestClient(service.main.app).get("/api/apps/demo/synthetics?hours=168")
    assert response.status_code == 200
    assert run.call_args.args[0] == service.queries.SYNTH_BROWSER
    assert run.call_args.kwargs["app"] == "demo"
    assert "since" in run.call_args.kwargs
    assert "failure_stage" in service.queries.SYNTH_BROWSER


def test_probe_percentile_uses_raw_successful_probes_not_percentiles(service):
    assert (
        service.console.probe_percentile(
            {
                "probes": {
                    "a": [(1, True, 200, 10)] * 99,
                    "b": [(1, True, 200, 1000), (1, False, 503, 2000)],
                }
            }
        )
        == 10
    )
    assert service.console.probe_percentile({}) is None


def test_graph_app_name_precedes_host_and_never_merges_cross_workspace_names(service):
    apps = [
        {
            "id": "1:caller",
            "name": "caller",
            "workspace_id": "1",
            "workspace": "prod-eu",
            "resources": [
                {"app": {"name": "target", "url": "https://target-2.apps.invalid/api"}},
                {"app": {"name": "uncollected"}},
            ],
        },
        {
            "id": "1:target",
            "name": "target",
            "workspace_id": "1",
            "health": "healthy",
            "url": "https://target-1.apps.invalid",
        },
        {
            "id": "2:target",
            "name": "target",
            "workspace_id": "2",
            "health": "down",
            "url": "https://target-2.apps.invalid",
        },
        {"id": "2:uncollected", "name": "uncollected", "workspace_id": "2"},
    ]
    result = service.console_topology.graph(apps, [])
    assert {e["target"] for e in result["edges"]} == {
        "app:1:target",
        "resource:1:app:uncollected",
    }
    nodes = {n["id"]: n for n in result["nodes"]}
    assert nodes["app:1:target"]["health"] == "healthy"
    assert nodes["resource:1:app:uncollected"]["health"] is None
    assert nodes["resource:1:app:uncollected"]["workspace"] == "prod-eu"


@pytest.mark.parametrize(
    "reference",
    [
        {"name": "target", "url": "https://TARGET.apps.invalid:443/api"},
        {"url": "https://target.apps.invalid/api"},
        {"host": "target.apps.invalid"},
        {"name": "target", "workspace_id": "2"},
    ],
)
def test_graph_app_reference_uses_unique_host_or_explicit_workspace(service, reference):
    binding = {"name": "dependency", "app": reference}
    apps = [
        {"id": "1:caller", "name": "caller", "workspace_id": "1", "resources": [binding, binding]},
        {
            "id": "2:target",
            "name": "target",
            "workspace_id": "2",
            "workspace": "prod-us",
            "url": "https://target.apps.invalid",
            "health": "degraded",
        },
    ]
    observed = [
        {
            "workspace_id": "1",
            "name": "caller",
            "dependency": peer,
            "calls": 2,
            "errors": 1,
            "avg_ms": 10,
        }
        for peer in ["https://target.apps.invalid/path", "target.apps.invalid"]
    ]
    result = service.console_topology.graph(apps, observed)
    assert len(result["nodes"]) == 2
    assert len(result["edges"]) == 1
    edge = result["edges"][0]
    assert edge["target"] == "app:2:target"
    assert edge["declared"] and edge["observed"]
    assert edge["calls"] == 4
    assert edge["avg_ms"] == 10
    assert edge["bindings"] == [binding]
    target = next(n for n in result["nodes"] if n["id"] == edge["target"])
    assert target["health"] == "degraded"
    assert target["workspace"] == "prod-us"
    assert target["dependents"] == ["app:1:caller"]


def test_graph_ambiguous_host_does_not_guess_an_application(service):
    apps = [
        {
            "id": "1:caller",
            "name": "caller",
            "workspace_id": "1",
            "resources": [{"app": {"url": "https://shared.apps.invalid/path"}}],
        },
        *[
            {
                "id": f"{ws}:target",
                "name": "target",
                "workspace_id": ws,
                "url": "https://shared.apps.invalid",
            }
            for ws in ["2", "3"]
        ],
    ]
    result = service.console_topology.graph(apps, [])
    assert result["edges"][0]["target"].startswith("resource:1:app:")
    assert result["nodes"][-1]["health"] is None


def test_demo_graph_and_leaderboard_preserve_identity_and_evidence(service):
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "demo_generator", ROOT / "scripts/generate_console_demo.py"
    )
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    data = json.loads(
        (ROOT / "app/static/console/demo-data.js")
        .read_text()
        .removeprefix("window.MOCK = ")
        .strip()
        .removesuffix(";")
    )
    fixtures = json.loads(
        (ROOT / "app/static/console/demo-fixtures.js")
        .read_text()
        .removeprefix("window.CONSOLE_FIXTURES = ")
        .strip()
        .removesuffix(";")
    )
    nodes = data["topology"]["nodes"]
    assert len([n for n in nodes if n["label"] == "doc-intake"]) == 1
    warehouses = [n for n in nodes if n["label"] == "wh-7d1a"]
    assert len(warehouses) == 3
    assert len({n["workspace"] for n in warehouses}) == 3
    scores = {r["name"]: r for r in fixtures["api/leaderboard"]["apps"]}
    assert "legacy-reports" not in scores
    assert len({r["score"] for r in scores.values()}) > 8
    assert scores["fraud-triage"]["score"] < scores["pricing-api"]["score"]
    for app in data["apps"]:
        if app["health"] == "stopped":
            continue
        row = {
            "availability_pct": app["probe"]["uptime_24h"],
            "error_pct": app["last24h"]["error_rate_pct"],
            "p95_ms": app["last24h"]["p95_ms"],
            "latency_budget_ms": 2500,
            "scan_score": app["scan"]["quality_score"],
            "review_score": app["review"]["score_overall"] * 10,
            "cost_growth": generator.weekly_growth(app["cost"]["daily_30d"]),
            "users": app["last24h"]["active_users"],
        }
        expected = service.routes_product.leaderboard_score(row)
        assert generator.leaderboard_score(row) == expected
        assert {k: scores[app["name"]][k] for k in expected} == expected
    assert generator.weekly_growth([1, None]) is None
    assert generator.weekly_growth([0] * 14) is None
