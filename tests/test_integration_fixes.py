"""Cross-component regressions using emitted SDK payloads and local SQL/runtime fakes."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import sqlite3
import sys
from contextlib import closing
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_product import request
from test_service_correctness import service as service

import monitor_middleware as mm


@pytest.mark.parametrize("failed", [[], ["b"], ["a", "b"]])
def test_bulk_autostop_binds_all_parameters_and_reports_failures(service, failed):
    main, q = service.main, service.queries
    service.auth.MONITOR_ADMINS.add("admin@example.com")
    main.fleet.update({name: {} for name in ("a", "b", "prod", "apps-monitor")})
    q.run = AsyncMock(return_value=[{"name": "prod", "tags_json": '{"env":"prod"}'}])

    async def write(sql, **params):
        assert set(re.findall(r"(?<!:):(\w+)", sql)) == params.keys()
        assert params["ws"] == "123" and params["capacity_path"] == ""
        if params["app"] in failed:
            raise RuntimeError("warehouse write failed")

    q.run_dml = AsyncMock(side_effect=write)
    status, body = asyncio.run(request(main.app, "POST", "/api/actions/autostop-policy", {}, True))
    assert status == (502 if failed else 200)
    result = body["detail"] if failed else body
    assert result["applied"] == [n for n in ("a", "b") if n not in failed]
    if failed:
        assert result["failed"] == failed
    assert q.run_dml.await_count == 2
    q.run_dml.reset_mock()
    status, body = asyncio.run(
        request(main.app, "POST", "/api/actions/autostop-policy", {"dry_run": True}, True)
    )
    assert status == 200 and body["targets"] == ["a", "b"]
    q.run_dml.assert_not_called()


def json_value(body, path, _type=None):
    value = json.loads(body)
    key = json.loads(path[1:])[0] if path.startswith("$[") else path[2:]
    value = value.get(key)
    return json.dumps(value) if isinstance(value, (dict, list)) else value


@pytest.mark.parametrize("shape", ["sdk", "batch", "single"])
def test_rum_view_decodes_sdk_body_and_counts_views(service, caplog, shape):
    events = [
        {"type": "view", "path": "/page", "rid": "backend-rid"},
        {"type": "error", "message": "failure 123", "path": "/page", "rid": "backend-rid"},
        {"name": "LCP", "value": 1200, "path": "/page", "rid": "backend-rid"},
    ]
    if shape == "sdk":
        mm._rum_buckets.clear()
        with TestClient(mm.install(FastAPI(), rum=True)) as client, caplog.at_level(logging.INFO):
            response = client.post(
                "/monitor/rum",
                json={"events": events},
                headers={"origin": "http://testserver", "x-request-id": "ingestion-rid"},
            )
        assert response.status_code == 200
        body = next(r.message for r in caplog.records if r.name == "monitor.rum")
        assert isinstance(json.loads(body)["body"], str)
    else:
        body = json.dumps({"events": events} if shape == "batch" else events[0])
    sql = service.product_sql.rum_view_sql("cat.sch", "123", "logger")
    # Execute the view's normalization expression; Spark's typed explode is tested by shape.
    payload_cte = re.search(r"payloads AS \((.*?)\), events AS", sql, re.S).group(1)
    with closing(sqlite3.connect(":memory:")) as db:
        db.create_function("get_json_object", 2, json_value)
        db.execute("CREATE TABLE logs (body TEXT)")
        db.execute("INSERT INTO logs VALUES (?)", (body,))
        payload = json.loads(db.execute(payload_cte).fetchone()[1])
        decoded = payload.get("events", [payload])
        view_condition = re.search(r"count_if\((kind IN \(.*?\))\) AS page_views", sql).group(1)
        db.execute("CREATE TABLE events (kind TEXT)")
        db.executemany("INSERT INTO events VALUES (?)", [(e.get("type"),) for e in decoded])
        assert db.execute(f"SELECT sum({view_condition}) FROM events").fetchone()[0] == 1
    assert decoded == (events[:1] if shape == "single" else events)
    assert "get_json_object(payload, '$.events')" in sql and "array(from_json(payload," in sql
    assert "coalesce(event.rid, envelope_rid)" in sql


class CostSchemaSpark:
    """Reject dependent reads until the legacy table has all required columns."""

    required = frozenset({"workspace_id", "ai_tokens_gateway", "idle_usd"})

    def __init__(self):
        self.columns = {
            "date",
            "name",
            "dbus",
            "dbu_usd",
            "ai_calls",
            "ai_input_tokens",
            "ai_output_tokens",
            "ai_usd",
            "computed_at",
        }
        self.rows = [
            {"workspace_id": None, "dbu_usd": 12.5},
            {"workspace_id": "other", "dbu_usd": 4.0},
        ]
        self.statements = []
        self.conf = MagicMock()
        self.catalog = MagicMock()

    def table(self, name):
        return SimpleNamespace(
            columns=list(self.columns) if name.endswith("costs_daily") else ["workspace_id"]
        )

    def sql(self, sql, args=None):
        self.statements.append(sql)
        if "costs_daily" in sql:
            if sql.startswith("ALTER TABLE"):
                columns = sql.split("ADD COLUMNS (")[1].rstrip(")").split(", ")
                self.columns.update(c.split()[0] for c in columns)
            elif sql.startswith("UPDATE"):
                for row in self.rows:
                    if row["workspace_id"] is None:
                        row["workspace_id"] = args["ws"]
            elif "CREATE TABLE IF NOT EXISTS" not in sql:
                assert self.required <= self.columns, "dependent query before cost migration"
        frame = MagicMock()
        frame.collect.return_value = [{"c": 2}] if "SELECT count(*) c" in sql else []
        return frame


@pytest.mark.parametrize("entry", ["gold", "cost", "telemetry"])
def test_cost_migration_precedes_each_independent_reader_or_writer(service, monkeypatch, entry):
    spark = CostSchemaSpark()
    monkeypatch.setattr(service.source_scan, "emit_alerts", MagicMock())
    monkeypatch.setattr(service.federation, "publish", MagicMock())
    if entry == "telemetry":
        service.telemetry_health.check_telemetry(spark, "`cat`.`sch`", "123", "cat", "sch")
    else:
        module = service.gold_views if entry == "gold" else service.cost_rollup
        module.SparkSession.builder.getOrCreate.return_value = spark
        service.main.w.apps.list.return_value = []
        if entry == "gold":
            for method in (
                "materialize_aggregates",
                "snapshot_permissions",
                "snapshot_deployments",
                "detect_anomalies",
                "check_budgets",
                "check_token_budgets",
            ):
                monkeypatch.setattr(module, method, MagicMock())
        monkeypatch.setattr(sys, "argv", [entry, "--catalog=cat", "--schema=sch"])
        module.main()
    assert spark.required <= spark.columns
    assert spark.rows == [
        {"workspace_id": "123", "dbu_usd": 12.5},
        {"workspace_id": "other", "dbu_usd": 4.0},
    ]
    service.schema_utils.ensure_costs_table(spark, "`cat`.`sch`", "123")
    alters = [s for s in spark.statements if s.startswith("ALTER TABLE") and "costs_daily" in s]
    assert len(alters) == 1


def test_reach_slo_attainment_uses_current_revision_and_preserves_unknown(service):
    q = service.queries
    sql = q.REACH_SLO.replace(q.t("slo_specs"), "slo_specs").replace(q.t("sli_5m"), "sli_5m")
    sql = sql.replace("timestampadd(DAY, -s.window_days, current_timestamp())", "'2026-01-01'")
    with closing(sqlite3.connect(":memory:")) as db:
        db.execute(
            "CREATE TABLE slo_specs (name, slo, sli, target, window_days, workspace_id, revision)"
        )
        db.execute(
            "CREATE TABLE sli_5m (name, slo, workspace_id, revision, bucket, good REAL, total REAL)"
        )
        db.executemany(
            "INSERT INTO slo_specs VALUES (?, 'uptime', 'availability', .99, 28, '123', 'new')",
            [("app",), ("no-current-data",)],
        )
        db.executemany(
            "INSERT INTO sli_5m VALUES (?, 'uptime', ?, ?, '2026-01-20', ?, ?)",
            [
                ("app", "123", "old", 0, 100),
                ("app", "123", "new", 100, 100),
                ("app", "other", "new", 0, 100),
                ("no-current-data", "123", "old", 100, 100),
            ],
        )
        rows = {r[0]: r for r in db.execute(sql, {"app": ""})}
    assert rows["app"][-2:] == (1.0, 100)
    assert rows["no-current-data"][-2:] == (None, None)


@pytest.mark.parametrize("classified", [None, False, True])
def test_guardrail_resolution_requires_daily_evidence(service, monkeypatch, classified):
    q, spark = service.quality_evals, MagicMock()
    spark.table.return_value.columns = ["workspace_id"]
    daily = (
        []
        if classified is None
        else [{"trace_id": "existing", "template_hash": "known", "classified": classified}]
    )

    def result(sql, **kwargs):
        rows = (
            daily
            if (
                "SELECT trace_id FROM" in sql or "SELECT trace_id, template_hash, classified" in sql
            )
            else []
        )
        return SimpleNamespace(collect=lambda: rows)

    spark.sql.side_effect = result
    q.SparkSession.builder.getOrCreate.return_value = spark
    q.WorkspaceClient.return_value.apps.list.return_value = [SimpleNamespace(name="app")]
    monkeypatch.setattr(q, "experiment_of", lambda *_: "1")
    monkeypatch.setattr(q, "sample_traces", lambda *_: [])
    judge, emit = MagicMock(), MagicMock()
    monkeypatch.setattr(q, "judge", judge)
    monkeypatch.setattr(service.source_scan, "emit_alerts", emit)
    monkeypatch.setattr(sys, "argv", ["evals", "--catalog=cat", "--schema=sch"])
    q.main()
    judge.assert_not_called()
    scopes = {c.kwargs["owned_rules"][0]: c.kwargs["evaluated_apps"] for c in emit.call_args_list}
    assert scopes["guardrail_pii_rate"] == (set() if classified is None else {"app"})
    assert scopes["guardrail_policy_rate"] == ({"app"} if classified is True else set())
    for call in emit.call_args_list:
        rules = call.kwargs["owned_rules"]
        resolved = service.alert_state.resolving_keys(
            {(rule, "app") for rule in rules}, set(), rules, call.kwargs["evaluated_apps"]
        )
        assert bool(resolved) == bool(call.kwargs["evaluated_apps"])


@pytest.mark.parametrize(
    "attrs,expected",
    [
        ({"db.system.name": "databricks_sql", "db.namespace": "wh-1"}, "databricks_sql/wh-1"),
        ({"db.system.name": "databricks_sql", "db.namespace": "wh-2"}, "databricks_sql/wh-2"),
        (
            {"db.system.name": "postgresql", "db.namespace": "lakebase", "server.address": "host"},
            "postgresql/lakebase",
        ),
        ({"db.system.name": "new", "db.system": "legacy"}, "new"),
        ({"db.system": "postgresql"}, "postgresql"),
        ({"server.address": "api.example"}, "api.example"),
        ({"net.peer.name": "legacy.example"}, "legacy.example"),
        ({}, "sql.execute"),
    ],
)
def test_dependency_identity_preserves_database_and_warehouse(service, attrs, expected):
    sql = dict(service.gold_views.views_sql("cat.sch"))["v_dependencies"]
    expression = re.search(r"(coalesce\(.*?) AS dependency", sql, re.S).group(1)
    with closing(sqlite3.connect(":memory:")) as db:
        db.create_function("variant_get", 3, json_value)
        db.create_function(
            "concat_ws", -1, lambda sep, *items: sep.join(i for i in items if i is not None)
        )
        actual = db.execute(
            f"SELECT {expression} FROM (SELECT ? AS attributes, 'sql.execute' AS name)",
            (json.dumps(attrs),),
        ).fetchone()[0]
    assert actual == expected


@pytest.mark.parametrize(
    "error_type,message,expected",
    [
        ("policy", None, "content_policy"),
        ("policy", "", "content_policy"),
        ("policy", "429 misleading text", "content_policy"),
        ("rate_limit", None, "rate_limit"),
        ("timeout", None, "timeout"),
        ("schema", None, "schema_validation"),
        ("server", None, "server"),
        ("SomeException", "content filter", "content_policy"),
        (None, "rate limit", "rate_limit"),
        (None, "deadline exceeded", "timeout"),
        (None, "json validation", "schema_validation"),
        ("SomeException", "unrecognized", "other"),
    ],
)
def test_genai_taxonomy_prefers_canonical_error_types(service, error_type, message, expected):
    q = service.queries
    sql = q.GENAI_ERRORS.replace(q.t("otel_spans"), "otel_spans")
    sql = sql.replace("status.message", "status_message").replace("status.code", "status_code")
    sql = (
        sql.replace("ILIKE", "LIKE")
        .replace("RLIKE", "REGEXP")
        .replace("now() - INTERVAL 7 DAYS", "'2026-01-01'")
    )
    sql = sql.replace("any_value(", "min(")
    with closing(sqlite3.connect(":memory:")) as db:
        db.create_function("variant_get", 3, json_value)
        db.create_function("regexp", 2, lambda pattern, text: bool(re.search(pattern, text)))
        db.execute(
            "CREATE TABLE otel_spans (time, service_name, attributes, status_message, status_code)"
        )
        db.execute(
            "INSERT INTO otel_spans VALUES ('2026-01-20', 'app', ?, ?, 'ERROR')",
            (json.dumps({"gen_ai.request.model": "m", "error.type": error_type}), message),
        )
        row = db.execute(sql, {"app": "app"}).fetchone()
    assert row[0] == expected and row[1] == 1
