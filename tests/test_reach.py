"""Reach behavior with fake transports and Spark; no network or Databricks required."""

import asyncio
import importlib.util
import json
import re
import socket
import sys
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from fastapi import FastAPI, HTTPException
from starlette.requests import Request

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


logic = load("app/reach_logic.py", "reach_logic")
external = load("scripts/external_synthetics.py", "external_synthetics")
federation = load("jobs/federation.py", "federation")


@pytest.fixture
def routes(monkeypatch):
    monkeypatch.setitem(sys.modules, "reach_logic", logic)
    monkeypatch.setitem(sys.modules, "queries", MagicMock())
    return load("app/routes_reach.py", "routes_reach")


def test_rate_limit_is_per_caller_expires_and_bounds_memory():
    clock = [0]
    limiter = logic.CallerRateLimit(limit=2, max_callers=2, clock=lambda: clock[0])
    assert limiter.allow("a") and limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")
    assert not limiter.allow("c")
    clock[0] = 60
    assert limiter.allow("c") and limiter.allow("a")
    assert len(limiter.calls) == 2


def runs():
    return [
        {
            "app": "demo",
            "journey": "checkout",
            "vantage": vantage,
            "run_id": str(i),
            "run_ts": 100 + i,
            "ok": "false",
        }
        for vantage in ("internal", "external")
        for i in (0, 1)
    ]


def test_two_consecutive_failures_from_each_vantage():
    rows = runs()
    assert logic.vantage_decisions(rows, 102) == {"demo": True}
    assert logic.vantage_decisions(rows[:2], 102) == {}
    assert logic.vantage_decisions(rows[:-1], 102) == {}
    assert logic.vantage_decisions(rows * 3, 102) == {"demo": True}
    # Many failed steps from one run cannot satisfy the two-run requirement.
    assert logic.vantage_decisions([rows[0], rows[0], rows[2], rows[2]], 102) == {}
    assert logic.vantage_decisions(rows, 10000) == {}
    assert logic.vantage_decisions(rows, 99) == {}
    rows[-1]["ok"] = "true"
    assert logic.vantage_decisions(rows, 102) == {"demo": False}


def test_vantages_compare_same_journey_and_recovery_waits_for_all():
    rows = runs()
    rows[-1]["journey"] = "other"
    assert logic.vantage_decisions(rows, 102) == {}
    rows = runs()
    rows[0]["ok"] = True
    assert logic.vantage_decisions(rows, 102, expected=[("demo", "missing")]) == {}
    rows.append({**rows[0], "journey": "incomplete"})
    assert logic.vantage_decisions(rows, 102) == {}


def test_uptime_bars_do_not_invent_data_on_restart():
    bars = logic.uptime_bars([(7200, True), (7201, False), (10801, True)], 10800, hours=3)
    assert [b["uptime"] for b in bars] == [None, 50, None]
    assert sum(b["checks"] for b in bars) == 2


def test_authenticated_route_rejects_anonymous(routes):
    with pytest.raises(HTTPException) as exc:
        routes.authenticated(Request({"type": "http", "headers": []}))
    assert exc.value.status_code == 401
    assert (
        routes.authenticated(
            Request({"type": "http", "headers": [(b"x-forwarded-user", b"sp-id")]})
        )
        == "sp-id"
    )


def test_mcp_ingress_checks_auth_and_rate_before_transport(routes):
    transport = AsyncMock()
    ingress = routes.MCPIngress(transport, logic.CallerRateLimit(limit=1))

    async def send_request(headers):
        send = AsyncMock()
        await ingress({"type": "http", "headers": headers}, AsyncMock(), send)
        return send

    anonymous = asyncio.run(send_request([]))
    assert anonymous.call_args_list[0].args[0]["status"] == 401
    headers = [(b"x-forwarded-user", b"caller")]
    asyncio.run(send_request(headers))
    denied = asyncio.run(send_request(headers))
    assert denied.call_args_list[0].args[0]["status"] == 429
    assert transport.await_count == 1


def test_mcp_registry_read_only_and_delegates(routes):
    pytest.importorskip("mcp", reason="MCP is an app runtime dependency, not an SDK dev dependency")
    handlers = {
        key: AsyncMock(return_value={"groups": [], "active": []})
        for key in (
            "api_fleet",
            "api_overview",
            "api_errors",
            "api_trace",
            "api_cost_summary",
            "api_alerts",
        )
    }

    async def slo_status(app: str = "") -> dict:
        return {"available": False, "rows": []}

    mcp = routes.create_mcp(handlers, slo_status)
    tools = asyncio.run(mcp.list_tools())
    assert {t.name for t in tools} == set(routes.TOOL_NAMES)
    assert all(t.annotations.readOnlyHint and not t.annotations.destructiveHint for t in tools)
    asyncio.run(mcp.call_tool("trace", {"trace_id": "trace-123"}))
    handlers["api_trace"].assert_awaited_once_with("trace-123")


def test_status_optional_tables_and_probe_history(routes, monkeypatch):
    def unavailable(*_):
        raise ModuleNotFoundError("MCP missing", name="mcp")

    monkeypatch.setattr(routes, "create_mcp", unavailable)
    routes.q.run = AsyncMock(side_effect=RuntimeError("missing table"))
    handlers = {
        "_workspace_id": lambda: 123,
        "fleet": {"demo": {"name": "demo"}},
        "_summary": lambda _: {"uptime_24h": 50},
        "_status": lambda *_: "degraded",
        "probes": {"demo": [(0, True, 200, 1)]},
    }
    router = routes.build_router(handlers)
    status = next(r.endpoint for r in router.routes if r.path == "/api/status")
    result = asyncio.run(status())
    assert result["apps"][0]["workspace_id"] == "123"
    assert len(result["apps"][0]["bars"]) == 24
    assert result["available"] == {"incidents": False, "maintenance": False, "slos": False}
    assert result["incidents"] == result["maintenance"] == []
    assert all(r.dependencies for r in router.routes)


def test_mcp_route_survives_router_inclusion(routes, monkeypatch):
    manager = MagicMock()
    transport = AsyncMock()
    manager.streamable_http_app.return_value = transport
    monkeypatch.setattr(routes, "create_mcp", lambda *_: manager)
    app = FastAPI()
    app.include_router(routes.build_router({}))

    async def invoke():
        send = AsyncMock()
        await app(
            {
                "type": "http",
                "method": "POST",
                "path": "/mcp",
                "root_path": "",
                "query_string": b"",
                "headers": [(b"x-forwarded-user", b"caller")],
                "scheme": "https",
                "server": ("monitor", 443),
            },
            AsyncMock(),
            send,
        )

    asyncio.run(invoke())
    transport.assert_awaited_once()


def test_official_mcp_streamable_http_lifespan_and_registry(routes):
    pytest.importorskip("mcp", reason="MCP is only an app runtime dependency")
    httpx = pytest.importorskip("httpx")
    app = FastAPI()
    app.include_router(routes.build_router({}))

    async def exercise():
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="https://monitor.databricksapps.com",
            ) as client,
        ):
            headers = {
                "x-forwarded-user": "test-sp",
                "Accept": "application/json, text/event-stream",
            }
            response = await client.post(
                "/mcp",
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                },
            )
            assert response.status_code == 200, response.text
            response = await client.post(
                "/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
            )
            assert response.status_code == 200, response.text
            assert {t["name"] for t in response.json()["result"]["tools"]} == set(routes.TOOL_NAMES)
            anonymous = await client.post("/mcp", json={})
            assert anonymous.status_code == 401

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "path", ["https://evil.invalid/", "//evil.invalid/", "/\\evil", "/healthz", "/%68ealthz/"]
)
def test_external_paths_do_not_leak_tokens_or_probe_proxy(path):
    with pytest.raises(ValueError):
        external.relative_url("https://app.invalid", path)


def test_external_oauth_and_sql_parameters(monkeypatch):
    http = MagicMock(return_value=(200, b'{"access_token":"token"}', {}))
    monkeypatch.setattr(external, "request", http)
    assert external.token("https://workspace.invalid", "client", "secret") == "token"
    assert http.call_args.args[0].endswith("/oidc/v1/token")
    assert b"grant_type=client_credentials" in http.call_args.args[3]
    ws = external.Workspace("https://workspace.invalid", "token", "warehouse")
    ws.api = MagicMock(return_value={"status": {"state": "SUCCEEDED"}})
    ws.sql(
        external.INSERT,
        {"table": "catalog.monitor.synthetic_runs", "app": "' ; DROP TABLE x", "ok": False},
    )
    payload = ws.api.call_args.args[1]
    assert "DROP TABLE" not in payload["statement"]
    assert {"name": "app", "value": "' ; DROP TABLE x"} in payload["parameters"]
    assert {"name": "ok", "value": "false"} in payload["parameters"]
    assert "MERGE INTO IDENTIFIER(:table)" in payload["statement"]


def test_external_checks_classify_auth_dns_http_assertions(monkeypatch):
    assert external.failure_stage(urllib.error.URLError(socket.gaierror("DNS"))) == "dns"
    assert external.failure_stage(TimeoutError()) == "http"
    for code, body, expected in [
        (302, b"", "auth"),
        (401, b"", "auth"),
        (503, b"", "http"),
        (200, b"no", "assertion"),
        (200, b"yes", ""),
    ]:
        monkeypatch.setattr(external, "request", lambda *_, c=code, b=body: (c, b, {}))
        assert external.http_step(
            "https://app.invalid", {"path": "/", "expect_contains": "yes"}, {}, 10
        ) == (code, expected)


def test_statement_api_polls_and_rejects_failed_delivery(monkeypatch):
    ws = external.Workspace("https://workspace.invalid", "token", "warehouse")
    monkeypatch.setattr(external.time, "sleep", lambda _: None)
    ws.api = MagicMock(
        side_effect=[
            {"status": {"state": "RUNNING"}, "statement_id": "1"},
            {"status": {"state": "SUCCEEDED"}},
        ]
    )
    ws.sql("SELECT :value", {"value": "ok"})
    assert ws.api.call_count == 2
    ws.api = MagicMock(return_value={"status": {"state": "FAILED", "error": "secret"}})
    with pytest.raises(RuntimeError, match="delivery did not succeed"):
        ws.sql("SELECT :value", {"value": "ok"})


def test_public_snapshot_is_explicit_allowlist_not_copy_of_internal_status():
    internal = {
        "apps": [
            {
                "name": "secret-app",
                "status": "ok",
                "url": "https://private.invalid",
                "creator": "private@example.com",
                "bars": [{"ts": 0, "uptime": 100, "checks": 20}],
                "slos": [{"secret": True}],
            },
            {"name": "not-public", "status": "down"},
        ],
        "incidents": [{"message": "access token"}],
        "maintenance": [{"reason": "private reason"}],
    }
    result = external.sanitize_status(internal, {"secret-app": "Public service"})
    text = json.dumps(result)
    assert "Public service" in text
    for secret in ("secret-app", "not-public", "private", "token", "slos", "checks"):
        assert secret not in text
    assert external.sanitize_status(internal, {})["apps"] == []


def test_federation_names_and_union_preserve_workspace_identity():
    assert federation.feeder_schema("West EU", "123") == "af_west_eu__123"
    assert federation.feeder_schema("West EU", "456") != federation.feeder_schema("West EU", "123")
    with pytest.raises(ValueError):
        federation.identifier("evil`; DROP SCHEMA x")
    with pytest.raises(ValueError):
        federation.feeder_schema("west", "123' OR true")
    sql = federation.union_sql("hub", ["af_east__1", "af_west__2", "af_east__1"], "apps_current")
    assert sql.count("UNION ALL") == 1
    assert "af_east__1" in sql and "af_west__2" in sql


def test_feeder_current_replaces_and_history_merges_workspace_keys():
    spark, client = MagicMock(), MagicMock()
    client.get_workspace_id.return_value = 123
    args = SimpleNamespace(
        deployment_mode="feeder",
        hub_catalog="hub",
        catalog="local",
        schema="monitor",
        workspace_name="east",
        snapshot_ts="2026-01-01",
    )
    federation.publish(
        spark, args, client, ("apps_inventory", "costs_daily", "agg_app_daily", "alert_events")
    )
    statements = [c.args[0] for c in spark.sql.call_args_list]
    assert any("INSERT OVERWRITE `hub`.`af_east__123`.apps_current" in s for s in statements)
    history = next(s for s in statements if "MERGE INTO" in s and ".apps_history" in s)
    assert "t.workspace_id <=> s.workspace_id" in history
    assert "t.snapshot_ts <=> s.snapshot_ts" in history
    cost_source = next(s for s in statements if "FROM `local`.`monitor`.costs_daily" in s)
    assert "dbus" in cost_source and "usd" not in cost_source and "ai_" not in cost_source
    args.deployment_mode = "standalone"
    spark.reset_mock()
    federation.publish(spark, args, client, ("apps_inventory",))
    spark.sql.assert_not_called()


def test_hub_rediscovers_feeders_and_prices_account_billing_once():
    spark = MagicMock()
    spark.sql.return_value.collect.return_value = [
        {"table_schema": s, "table_name": t}
        for s in ("af_east__1", "af_west__2")
        for t in ("apps_current", "costs_daily", "agg_app_daily", "alert_events")
    ]
    args = SimpleNamespace(
        deployment_mode="hub", hub_catalog="hub", catalog="local", schema="monitor"
    )
    federation.hub_views(spark, args)
    sql = "\n".join(c.args[0] for c in spark.sql.call_args_list)
    assert "UNION ALL" in sql and "af_east__1" in sql and "af_west__2" in sql
    assert sql.count("system.billing.usage") == 1
    assert "c.workspace_id = p.workspace_id" in sql
    assert "PARTITION BY workspace_id, source, rule, app" in sql
    spark.reset_mock()
    spark.sql.return_value.collect.return_value = []
    federation.hub_views(spark, args)
    assert any("WHERE false" in c.args[0] for c in spark.sql.call_args_list)


def test_external_workflow_has_pinned_actions_and_opt_in_pages():
    workflow = yaml.safe_load((ROOT / ".github/workflows/synthetics-external.yml").read_text())
    assert workflow["permissions"] == {"contents": "read"}
    assert "public_ready" in workflow["jobs"]["publish"]["if"]
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            if "uses" in step:
                assert re.fullmatch(r"[^@]+@[a-f0-9]{40}", step["uses"])


@pytest.mark.parametrize("code,expected,stage", [(200, 0, ""), (401, 1, "auth"), (503, 1, "http")])
def test_external_runner_persists_results_even_if_artifact_upload_fails(
    tmp_path, monkeypatch, code, expected, stage
):
    config = tmp_path / "journeys.json"
    config.write_text(
        json.dumps(
            {"journeys": [{"app": "demo", "name": "flow", "steps": [{"path": "/api/ready"}]}]}
        )
    )
    output = tmp_path / "results"
    monkeypatch.setattr(
        sys, "argv", ["external_synthetics.py", "--journeys", str(config), "--output", str(output)]
    )
    for key, value in {
        "DATABRICKS_HOST": "https://workspace.invalid",
        "DATABRICKS_CLIENT_ID": "id",
        "DATABRICKS_CLIENT_SECRET": "secret",
        "DATABRICKS_WAREHOUSE_ID": "warehouse",
        "DATABRICKS_WORKSPACE_ID": "123",
        "MONITOR_CATALOG": "catalog",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(external, "token", lambda *_: "token")
    monkeypatch.setattr(external, "request", lambda *_: (code, b"ready", {}))
    client = MagicMock()
    client.headers = {"Authorization": "Bearer token"}
    client.apps.return_value = [{"name": "demo", "url": "https://app.invalid"}]
    client.artifact.side_effect = RuntimeError("upload unavailable")
    monkeypatch.setattr(external, "Workspace", lambda *_: client)
    assert external.main() == expected
    rows = json.loads((output / "results.json").read_text())
    assert len(rows) == 2 and rows[0]["failure_stage"] == stage
    assert rows[-1]["step"] == -1 and rows[-1]["ok"] is (code == 200)
    assert rows[0]["workspace_id"] == "123" and rows[0]["run_id"]
    assert client.sql.call_count == 2
    assert client.sql.call_args.args[1]["ok"] is (code == 200)
    assert "secret" not in (output / "results.json").read_text()


def test_external_auth_failure_leaves_sanitized_diagnostic(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["external_synthetics.py", "--output", str(tmp_path)])
    for key in ("DATABRICKS_HOST", "DATABRICKS_CLIENT_ID", "DATABRICKS_CLIENT_SECRET"):
        monkeypatch.setenv(
            key, "https://workspace.invalid" if key == "DATABRICKS_HOST" else "secret"
        )

    def denied(*_):
        raise RuntimeError("secret token response")

    monkeypatch.setattr(external, "token", denied)
    assert external.main() == 1
    assert json.loads((tmp_path / "runner.json").read_text())["failure_stage"] == "auth"
    assert "secret token" not in capsys.readouterr().out
