"""Product service contracts and pure logic, with no warehouse or workspace access."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from test_service_correctness import service as service


def test_score_uses_visible_weights_and_missing_evidence(service):
    score = service.routes_product.leaderboard_score
    result = score(
        {
            "availability_pct": 100,
            "error_pct": 10,
            "p95_ms": 5000,
            "latency_budget_ms": 2500,
            "scan_score": 80,
            "review_score": 70,
            "cost_growth": 0.5,
            "users": 20,
        }
    )
    assert result["score"] == 75.5
    assert result["coverage_pct"] == 100
    assert result["components"]["latency"] == 50
    assert result["components"]["cost"] == 50
    assert score({"scan_score": "80"})["score"] == 80
    assert score({"scan_score": "80"})["coverage_pct"] == 15
    assert score({"scan_score": "NaN", "users": "inf"})["score"] is None
    assert score({"users": 5000})["score"] == 100
    assert score({"cost_growth": -1})["score"] == 100
    assert score({"cost_growth": 3})["score"] == 0


@pytest.mark.parametrize(
    "today,hour,budget,expected",
    [
        (100, 100, None, "none"),
        (100, 100, 0, "none"),
        (0, 0, 100, "none"),
        (79, 1, 100, "none"),
        (80, 0, 100, "warn"),
        (70, 30, 100, "warn"),
        (100, 0, 100, "block"),
        (101, 20, 100, "block"),
    ],
)
def test_token_policy_boundaries(service, today, hour, budget, expected):
    assert service.gold_views.token_policy(today, hour, budget) == expected


def test_policy_cache_handles_partial_rows_outages_and_expiry(service, monkeypatch):
    module = service.routes_product
    now = datetime.now(timezone.utc)
    module.q.run = AsyncMock(
        return_value=[
            {"name": "unset", "policy_updated_at": None, "throttle": None},
            {"name": "good", "policy_updated_at": now.isoformat(), "throttle": "block"},
            {
                "name": "old",
                "policy_updated_at": (now - timedelta(hours=4)).isoformat(),
                "throttle": "block",
            },
            {"name": "invalid", "policy_updated_at": now.isoformat(), "throttle": "bogus"},
        ]
    )
    asyncio.run(module.refresh_policies("123"))
    assert module.cached_policy("good") == {"throttle": "block"}
    for name in ("old", "unset", "invalid", "absent"):
        assert module.cached_policy(name) == {"throttle": "none"}
    module.q.run.side_effect = RuntimeError("warehouse asleep")
    asyncio.run(module.refresh_policies("123"))
    assert module.cached_policy("good")["throttle"] == "block"
    monkeypatch.setattr(module.time, "monotonic", lambda: module._policies_at + 301)
    assert module.cached_policy("good")["throttle"] == "none"


async def request(app, method, path, body=None, admin=False):
    sent = []
    payload = json.dumps(body).encode() if body is not None else b""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "scheme": "http",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "server": ("test", 80),
        "client": ("test", 1),
        "headers": [
            (b"content-type", b"application/json"),
            (b"x-forwarded-email", b"admin@example.com" if admin else b"viewer@example.com"),
        ],
    }

    async def receive():
        return {"type": "http.request", "body": payload, "more_body": False}

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    data = json.loads(
        b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    )
    return status, data


def product_app(service):
    service.auth.MONITOR_ADMINS.add("admin@example.com")
    api = FastAPI()
    fleet = {
        "active": {"app_state": "RUNNING", "compute_state": "ACTIVE"},
        "stopped": {"app_state": "STOPPED", "compute_state": "STOPPED"},
    }
    api.include_router(
        service.routes_product.router(
            service.main.require_admin, lambda: 123, fleet, lambda _: {"uptime_24h": 100}
        )
    )
    return api


def test_policy_endpoint_never_queries_warehouse(service):
    api = product_app(service)
    service.queries.run = AsyncMock(side_effect=AssertionError("no SQL from policy"))
    for _ in range(3):
        assert asyncio.run(request(api, "GET", "/api/policy/unknown")) == (
            200,
            {"throttle": "none"},
        )
    service.queries.run.assert_not_called()


def test_product_admin_validation_and_sql_parameters(service):
    api = product_app(service)
    service.queries.run_dml = AsyncMock()
    body = {
        "model": "model'); DROP TABLE costs_daily; --",
        "effective_from": "2026-01-01",
        "input_usd_per_mtok": 2,
        "output_usd_per_mtok": 8,
    }
    assert asyncio.run(request(api, "PUT", "/api/model-prices", body))[0] == 403
    assert (
        asyncio.run(
            request(api, "PUT", "/api/model-prices", {**body, "input_usd_per_mtok": -1}, True)
        )[0]
        == 422
    )
    service.queries.run_dml.assert_not_called()
    assert asyncio.run(request(api, "PUT", "/api/model-prices", body, True))[0] == 200
    sql = service.queries.run_dml.call_args.args[0]
    params = service.queries.run_dml.call_args.kwargs
    assert body["model"] not in sql and params["model"] == body["model"]
    assert params["ws"] == "123"
    assert (
        asyncio.run(
            request(api, "PUT", "/api/apps/active/product-config", {"token_budget_day": -1}, True)
        )[0]
        == 422
    )
    assert (
        asyncio.run(request(api, "PUT", "/api/apps/active/funnels/buy", {"steps": ["a"]}, True))[0]
        == 422
    )
    assert (
        asyncio.run(
            request(api, "PUT", "/api/apps/active/funnels/buy", {"steps": ["a", " "]}, True)
        )[0]
        == 422
    )
    assert (
        asyncio.run(
            request(api, "PUT", "/api/apps/active/funnels/buy", {"steps": ["a", "b"]}, True)
        )[0]
        == 200
    )


def test_leaderboard_filters_live_stopped_and_deleted_apps(service):
    api = product_app(service)
    service.queries.run = AsyncMock(
        return_value=[{"name": n, "scan_score": 80} for n in ("active", "stopped", "deleted")]
    )
    status, data = asyncio.run(request(api, "GET", "/api/leaderboard"))
    assert status == 200
    assert [r["name"] for r in data["apps"]] == ["active"]
    assert data["apps"][0]["coverage_pct"] == 40
    assert "formula" in data and "components" in data["apps"][0]


def test_business_event_api_binds_app_and_workspace(service):
    api = product_app(service)
    service.queries.run = AsyncMock(return_value=[{"event_name": "checkout", "events": "2"}])
    status, data = asyncio.run(request(api, "GET", "/api/apps/active/events"))
    assert status == 200 and data["events"][0]["event_name"] == "checkout"
    params = service.queries.run.call_args.kwargs
    assert params["app"] == "active" and params["ws"] == "123"


@pytest.mark.parametrize(
    "text,kind",
    [
        ("Contact jane.doe+sales@example.org now", "email"),
        ("Call +1 415 555 2671 today", "phone"),
        ("Call (415) 555-2671 today", "phone"),
        ("Call +14155552671 today", "phone"),
        ("GB82 WEST 1234 5698 7654 32", "iban"),
        ("Send to DE89 3704 0044 0532 0130 00 tomorrow", "iban"),
        ("Pay with 4111 1111 1111 1111.", "credit_card"),
    ],
)
def test_pii_findings_contain_only_hashes_and_fixed_masks(service, text, kind):
    found = service.quality_evals.detect_pii(text)
    assert any(f["kind"] == kind for f in found)
    assert all(len(f["excerpt_hash"]) == 64 and f["excerpt_masked"].startswith("[") for f in found)
    assert text not in json.dumps(found)


@pytest.mark.parametrize(
    "text",
    [
        "normal prose on 2026-01-20",
        "not@email",
        "4111 1111 1111 1112",
        "0000000000000000",
        "GB00 WEST 1234 5698 7654 32",
    ],
)
def test_pii_rejects_invalid_checksums_and_common_false_positives(service, text):
    found = service.quality_evals.detect_pii(text)
    assert not any(f["kind"] in ("credit_card", "iban", "email") for f in found)


def test_redaction_merges_overlaps_and_scrubs_judge_inputs(service):
    q = service.quality_evals
    sample = {
        "request": "Email person@example.com api_key=abcxyz",
        "response": "IBAN GB82 WEST 1234 5698 7654 32 card 4111 1111 1111 1111",
        "trace_id": "t",
    }
    response = MagicMock()
    response.json.return_value = {"choices": [{"message": {"content": '{"findings": []}'}}]}
    q.httpx.post.return_value = response
    q.judge(service.main.w, "judge", "app", [sample])
    content = q.httpx.post.call_args.kwargs["json"]["messages"][1]["content"]
    for raw in ("person@example.com", "abcxyz", "WEST", "4111"):
        assert raw not in content
    assert sample["request"].startswith("Email person@example.com")
    assert "quoted secret" not in q.redact('{"api_key": "quoted secret"}')


def test_templates_normalize_variables_and_require_baseline(service):
    q = service.quality_evals
    assert q.template_hash('Summarize "one report" for 123') == q.template_hash(
        'Summarize "another" for 999'
    )
    assert q.template_hash('Explain "one report" for 123') != q.template_hash(
        'Summarize "one report" for 123'
    )
    assert q.drifted_templates({"new": 5}, set()) == {}
    assert q.drifted_templates({"new": 4}, {"old"}) == {}
    assert q.drifted_templates({"new": 1, "old": 4}, {"old"}) == {}
    assert q.drifted_templates({"new": 2, "old": 3}, {"old"}) == {"new": 0.4}


def test_classifier_rejects_invalid_results_and_discards_excerpts(service):
    q = service.quality_evals
    samples = [{"trace_id": "trace", "request": "private words", "response": "secret"}]
    scores = {
        "findings": [
            {"sample": 0, "kind": "policy", "severity": "warning", "excerpt": "private words"}
        ]
    }
    found = q.classifier_findings(scores, samples)
    assert found[0]["trace_id"] == "trace"
    assert found[0]["excerpt_masked"] == "[POLICY]"
    assert "private words" not in json.dumps(found)
    for invalid in (
        {},
        {"findings": [{"sample": -1}]},
        {"findings": [{"sample": True}]},
        {"findings": [{"sample": 0, "kind": "made-up", "severity": "warning"}]},
    ):
        with pytest.raises(ValueError):
            q.classifier_findings(invalid, samples)


def test_daily_cap_survives_reruns_without_judge_calls(service, monkeypatch):
    q = service.quality_evals
    spark = MagicMock()
    spark.table.return_value.columns = ["workspace_id"]

    def sql_result(sql, **kwargs):
        frame = MagicMock()
        frame.collect.return_value = []
        if "SELECT trace_id FROM" in sql:
            frame.collect.return_value = [{"trace_id": "seen"}]
        return frame

    spark.sql.side_effect = sql_result
    q.SparkSession.builder.getOrCreate.return_value = spark
    q.WorkspaceClient.return_value.apps.list.return_value = [SimpleNamespace(name="app")]
    monkeypatch.setattr(q, "experiment_of", lambda *_: "1")
    sample, judge = MagicMock(), MagicMock()
    monkeypatch.setattr(q, "sample_traces", sample)
    monkeypatch.setattr(q, "judge", judge)
    monkeypatch.setattr(service.source_scan, "emit_alerts", MagicMock())
    monkeypatch.setattr(sys, "argv", ["evals", "--catalog=c", "--schema=s", "--daily-sample-cap=1"])
    q.main()
    sample.assert_not_called()
    judge.assert_not_called()


def test_product_sql_keeps_effective_prices_windows_and_workspace_keys(service):
    p = service.product_sql
    pricing = service.cost_rollup.priced_ai_sql("cat.sch", 30)
    assert "p.effective_from <= a.date" in pricing and "ORDER BY p.effective_from DESC" in pricing
    assert "THEN NULL" in pricing and "a.workspace_id = p.workspace_id" in pricing
    idle = service.cost_rollup.idle_cost_sql("cat.sch", 30)
    assert "INTERVAL 1 HOUR" in idle and "coalesce(a.requests, 0) = 0" in idle
    assert "unix_micros(least(b.finish" in idle
    usage = p.token_usage_sql("cat.sch", 1)
    assert "LEFT ANTI JOIN" in usage and "lag(total)" in usage and "start_id" in usage
    assert "s.direction = m.direction" in usage
    assert "otel_metrics" not in p.token_usage_sql("cat.sch", 1, metrics_available=False)
    views = dict(p.product_views_sql("cat.sch", "123"))
    assert "started + INTERVAL 30 MINUTES" in views["v_funnels"]
    assert "max(reached)" in views["v_funnels"]
    assert "app_version" in views["v_funnels"]
    assert "retention_pct" in views["v_cohorts"] and "LEFT JOIN retained" in views["v_cohorts"]
    assert "app_state = 'RUNNING'" in views["v_leaderboard"]
    for sql in views.values():
        assert "COMMENT" in sql and "workspace_id" in sql


def test_effective_price_query_reprices_and_preserves_unknown_totals(service):
    class CountIf:
        def __init__(self):
            self.n = 0

        def step(self, value):
            self.n += bool(value)

        def finalize(self):
            return self.n

    # This query's joins/windows/CASE are portable; replace only the Databricks date literal.
    sql = service.cost_rollup.priced_ai_sql("main", 30).replace(
        "current_date() - 30", "'2026-01-01'"
    )
    with sqlite3.connect(":memory:") as db:
        db.row_factory = sqlite3.Row
        db.create_aggregate("count_if", 1, CountIf)
        db.execute(
            "CREATE TABLE costs_ai_daily (date TEXT, name TEXT, model TEXT, ai_calls INT, in_t INT, out_t INT, workspace_id TEXT)"
        )
        db.execute(
            "CREATE TABLE model_prices (workspace_id TEXT, model TEXT, effective_from TEXT, input_usd_per_mtok REAL, output_usd_per_mtok REAL)"
        )
        db.executemany(
            "INSERT INTO model_prices VALUES (?, ?, ?, ?, ?)",
            [
                ("123", "m", "2025-12-01", 1, 2),
                ("123", "m", "2026-01-15", 2, 4),
                ("other", "m", "2026-01-01", 999, 999),
                ("123", "future", "2026-03-01", 1, 1),
            ],
        )
        db.executemany(
            "INSERT INTO costs_ai_daily VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("2026-01-01", "a", "m", 1, 1_000_000, 1_000_000, "123"),
                ("2026-01-16", "a", "m", 1, 1_000_000, 1_000_000, "123"),
                ("2026-01-16", "partial", "m", 1, 1_000_000, 0, "123"),
                ("2026-01-16", "partial", "missing", 1, 1, 0, "123"),
                ("2026-01-16", "future", "future", 1, 1, 0, "123"),
                ("2026-01-16", "zero", "missing", 1, 0, 0, "123"),
            ],
        )
        rows = {(r["name"], r["date"]): dict(r) for r in db.execute(sql, {"ws": "123"})}
    assert rows["a", "2026-01-01"]["ai_usd"] == 3
    assert rows["a", "2026-01-16"]["ai_usd"] == 6
    assert rows["partial", "2026-01-16"]["ai_usd"] is None
    assert rows["partial", "2026-01-16"]["ai_input_tokens"] == 1_000_001
    assert rows["future", "2026-01-16"]["ai_usd"] is None
    assert rows["zero", "2026-01-16"]["ai_usd"] == 0


def test_sample_reservation_deduplicates_and_limits_remaining_allowance(service, monkeypatch):
    q = service.quality_evals
    spark = MagicMock()
    spark.table.return_value.columns = ["workspace_id"]

    def sql_result(sql, **kwargs):
        frame = MagicMock()
        frame.collect.return_value = [{"trace_id": "seen"}] if "SELECT trace_id FROM" in sql else []
        return frame

    spark.sql.side_effect = sql_result
    q.SparkSession.builder.getOrCreate.return_value = spark
    q.WorkspaceClient.return_value.apps.list.return_value = [SimpleNamespace(name="app")]
    monkeypatch.setattr(q, "experiment_of", lambda *_: "1")
    monkeypatch.setattr(
        q,
        "sample_traces",
        lambda *_: [
            {"trace_id": t, "request": "person@example.com", "response": "reply"}
            for t in ("seen", "new", "new", "excess")
        ],
    )

    def judge(_client, _model, _app, samples):
        assert [s["trace_id"] for s in samples] == ["new"]
        reservations = [
            c
            for c in spark.sql.call_args_list
            if "MERGE INTO `c`.`s`.guardrail_samples" in c.args[0]
        ]
        assert len(reservations) == 1
        assert reservations[0].kwargs["args"]["tid"] == "new"
        return {"relevance": 8, "faithfulness": 8, "toxicity": 0, "findings": []}

    monkeypatch.setattr(q, "judge", judge)
    monkeypatch.setattr(q, "guardrail_alerts", lambda *_: ([], True))
    monkeypatch.setattr(service.source_scan, "emit_alerts", MagicMock())
    monkeypatch.setattr(sys, "argv", ["evals", "--catalog=c", "--schema=s", "--daily-sample-cap=2"])
    q.main()
    for call in spark.sql.call_args_list:
        assert "person@example.com" not in str(call)
    findings = [
        c for c in spark.sql.call_args_list if "MERGE INTO `c`.`s`.guardrail_findings" in c.args[0]
    ]
    assert findings[0].kwargs["args"]["excerpt_masked"] == "[EMAIL]"


def test_budget_job_resolves_only_its_evaluated_apps(service, monkeypatch):
    spark = MagicMock()
    spark.sql.return_value.collect.return_value = [
        {"name": "warn", "today": 80, "last_hour": 1, "token_budget_day": 100},
        {"name": "block", "today": 110, "last_hour": 5, "token_budget_day": 100},
        {"name": "disabled", "today": 110, "last_hour": 5, "token_budget_day": 0},
    ]
    emit = MagicMock()
    monkeypatch.setattr(service.source_scan, "emit_alerts", emit)
    service.gold_views.check_token_budgets(spark, "cat.sch", "123", "cat", "sch")
    assert [(r["rule"], r["app"]) for r in emit.call_args.args[3]] == [
        ("token_budget_warn", "warn"),
        ("token_budget_block", "block"),
    ]
    assert emit.call_args.kwargs["evaluated_apps"] == {"warn", "block", "disabled"}
    updates = [c for c in spark.sql.call_args_list if "UPDATE" in c.args[0]]
    assert [c.kwargs["args"]["state"] for c in updates] == ["warn", "block", "none"]


def test_inventory_grants_product_writes_and_policy_access(service):
    w, spark = MagicMock(), MagicMock()
    w.api_client.do.return_value = {"resources": []}
    apps = [
        SimpleNamespace(name="monitor", service_principal_client_id="monitor-sp"),
        SimpleNamespace(name="fleet-app", service_principal_client_id="fleet-sp"),
    ]
    service.inventory_scan.grant_monitor_access(w, spark, apps, "monitor", "cat", "sch")
    assert {c.kwargs["app_name"] for c in w.apps.update_permissions.call_args_list} == {
        "monitor",
        "fleet-app",
    }
    statements = [c.args[0] for c in spark.sql.call_args_list]
    for table in ("model_prices", "funnel_specs"):
        assert any(f"MODIFY ON TABLE `cat`.`sch`.`{table}`" in sql for sql in statements)
