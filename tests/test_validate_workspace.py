"""Golden inputs and corrupted evidence must lead to different validation outcomes."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_workspace", ROOT / "scripts/validate_workspace.py"
)
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)


def args_for(tmp_path):
    return SimpleNamespace(
        profile="chosen",
        catalog="cat",
        schema="monitor",
        monitor_url="https://monitor.invalid",
        conformance_url="https://fixture.invalid",
        warehouse_id="warehouse",
        report=tmp_path / "report.json",
        wait_minutes=0,
        monitor_app_name="apps-monitor",
    )


def fixture_report():
    plan = v.make_plan("unit")
    return {
        "run_id": "unit",
        "plan": plan,
        "expected": v.expected_values(plan),
        "responses": [],
        "drive_checks": [],
        "checks": [],
        "workspace_id": "123",
    }


def golden_spans():
    rows = []
    for i, p in enumerate(v.make_plan("unit")):
        attrs = {
            "session.id": p["session"],
            "user.id_hash": v.identity_hashes(p["user"], "key")[1],
            "journey.step": p["query"]["name"] if p["group"] == "step" else p["path"],
            "app.name": v.APP,
            "app.version": "test-version",
        }
        if p["group"] == "error":
            attrs["exception.fingerprint"] = "abcdef012345"
        row = {
            "span_id": f"server-{i}",
            "trace_id": f"trace-{i}",
            "name": p["path"],
            "kind": "SPAN_KIND_SERVER",
            "rid": p["rid"],
            "route": p["path"],
            "http_status": str(p["status"]),
            "traffic_kind": p["kind"],
            "failed": str(p["status"] >= 400).lower(),
            "ms": str(p["query"].get("ms", 10)),
            "attributes": attrs,
        }
        rows.append(row)
        if p["path"] in {"/c/llm", "/c/budget"}:
            attr = {
                "gen_ai.request.model": v.MODEL
                if p["path"] == "/c/llm"
                else "conformance-budget-model",
                "monitor.llm.billable": True,
                "app.client_request_id": p["rid"],
            }
            if p["group"].startswith("fail_"):
                attr["error.type"] = p["query"]["fail"]
            elif p["path"] == "/c/llm":
                attr.update({"gen_ai.usage.input_tokens": 1000, "gen_ai.usage.output_tokens": 200})
                if p["group"] == "stream":
                    attr["monitor.llm.ttft_ms"] = 10
            rows.append({**row, "span_id": f"llm-{i}", "kind": "CLIENT", "attributes": attr})
        elif p["group"] == "sql":
            rows.append(
                {
                    **row,
                    "span_id": f"sql-{i}",
                    "name": "sql.execute",
                    "kind": "CLIENT",
                    "attributes": {
                        "db.response.returned_rows": 42,
                        "db.namespace": "conformance-fake-warehouse",
                    },
                }
            )
    return rows


def test_clean_import_without_sdk(monkeypatch):
    monkeypatch.setitem(sys.modules, "databricks.sdk", None)
    module = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(module)
    assert module.make_plan("offline")


def test_exact_seeded_plan_and_contract():
    plan = v.make_plan("unit")
    assert plan == v.make_plan("unit")
    assert plan != v.make_plan("another")
    expected = v.expected_values(plan)
    assert expected["requests"] == 242
    assert expected["real_requests"] == 233
    assert expected["errors"] == 35
    assert expected["server_errors"] == 25
    assert expected["error_rate"] == 35 / 233
    assert expected["traffic"] == {"real": 233, "journey": 5, "probe": 4}
    assert expected["users"] == 5
    assert expected["sessions"] == 15
    assert expected["input_tokens"] == 12000
    assert expected["output_tokens"] == 2400
    assert expected["billable_spans"] == 18
    assert expected["routes"]["/c/ok"] == 105
    assert len({p["rid"] for p in plan}) == len(plan)
    for session in {p["session"] for p in plan}:
        steps = [
            p["query"]["name"].split(":")[-1]
            for p in plan
            if p["session"] == session and p["group"] == "event"
        ]
        assert steps in (["signup"], ["signup", "verify"], ["signup", "verify", "activate"])
    assert expected["events"] == {
        "val-unit:signup": 15,
        "val-unit:verify": 10,
        "val-unit:activate": 5,
        "val-unit:ingress": 1,
    }
    assert plan[-3]["delay_before_s"] >= 30 and plan[-2]["delay_before_s"] >= 120
    assert len(v.make_plan("a" * 32)[-1]["rid"]) <= 64


@pytest.mark.parametrize("bad", ["", "x" * 33, "bad/id", "x%", "a\nb", "é", "' OR true"])
def test_bad_run_ids(bad):
    with pytest.raises(ValueError):
        v.make_plan(bad)


@pytest.mark.parametrize(
    ("actual", "expected", "options", "passes"),
    [
        (240, 300, {"relative": 0.2, "upper_extra": 100}, True),
        (460, 300, {"relative": 0.2, "upper_extra": 100}, True),
        (461, 300, {"relative": 0.2, "upper_extra": 100}, False),
        (239, 300, {"relative": 0.2, "upper_extra": 100}, False),
        ("35", 35, {}, True),
        (None, 0, {}, False),
        (float("nan"), 1, {}, False),
        (float("inf"), 1, {}, False),
        (1.01, 1, {"absolute": 0.02}, True),
    ],
)
def test_tolerance(actual, expected, options, passes):
    assert v.within_tolerance(actual, expected, **options) is passes


def test_percentile_and_invalid_tolerance():
    values = [300] * 30 + [1500] * 10
    assert v.percentile(values, 0.5) == 300
    assert v.percentile(values, 0.95) == 1500
    with pytest.raises(ValueError):
        v.percentile([], 0.5)
    with pytest.raises(ValueError):
        v.within_tolerance(1, 1, relative=-0.1)


def test_redaction_decoded_nested_and_missing_evidence():
    needles = ("secret", "test@example.invalid", v.PAT)
    assert v.contains_leak({"nested": [None, {"x": '"\\u0073ecret"'}]}, needles)
    assert v.contains_leak({"test@example.invalid": 1}, needles)
    assert not v.contains_leak({"body": "Bearer [redacted] [email]"}, needles)
    checks = v.evaluate_logs("unit", [], [])
    assert next(c for c in checks if c["name"] == "leak log coverage")["status"] == "FAIL"
    clean = [{"body": "email=[email] Bearer [redacted] PAT=[redacted]"}] * 3
    clean += [{"body": json.dumps({"event": "feedback", "rating": 5, "comment": "[redacted]"})}]
    assert all(c["status"] == "PASS" for c in v.evaluate_logs("unit", clean, []))
    clean[0] = {"body": v.leak_values("unit")[0]}
    assert any(c["status"] == "FAIL" for c in v.evaluate_logs("unit", clean, []))


def test_hmac_must_match_known_key_and_cannot_be_plain_sha():
    email = "conformance-user-1@example.invalid"
    plain, keyed = v.identity_hashes(email, "key")
    assert not v.is_keyed_hash(plain, email)
    assert v.is_keyed_hash(keyed, email, "key")
    assert not v.is_keyed_hash(keyed, email, "wrong-key")
    assert not v.is_keyed_hash("anon", email)
    assert not v.is_keyed_hash(None, email)
    assert v.is_keyed_hash(keyed, email)  # negative control only; full proof is a separate check


def test_golden_span_evidence():
    checks = v.evaluate_spans(v.make_plan("unit"), golden_spans(), "key")
    assert {c["status"] for c in checks} == {"PASS"}, [c for c in checks if c["status"] != "PASS"]
    checks = v.evaluate_spans(v.make_plan("unit"), golden_spans())
    assert [c["name"] for c in checks if c["status"] == "SKIP"] == ["user hash equals HMAC-SHA256"]


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate",
        "missing",
        "inflation",
        "wrong_error",
        "missing_ttft",
        "sql_text",
        "synthetic_real",
        "fingerprint",
        "plain_sha",
    ],
)
def test_corrupt_span_evidence_fails(corruption):
    rows = golden_spans()
    if corruption == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif corruption == "missing":
        rows.pop(0)
    elif corruption == "inflation":
        next(r for r in rows if "gen_ai.usage.input_tokens" in r["attributes"])["attributes"][
            "gen_ai.usage.input_tokens"
        ] = 10000
    elif corruption == "wrong_error":
        next(r for r in rows if "error.type" in r["attributes"])["attributes"]["error.type"] = (
            "unknown"
        )
    elif corruption == "missing_ttft":
        next(r for r in rows if "monitor.llm.ttft_ms" in r["attributes"])["attributes"].pop(
            "monitor.llm.ttft_ms"
        )
    elif corruption == "sql_text":
        next(r for r in rows if r["name"] == "sql.execute")["attributes"]["db.statement"] = (
            "SELECT 42"
        )
    elif corruption == "synthetic_real":
        next(r for r in rows if r["traffic_kind"] == "journey")["traffic_kind"] = "real"
    elif corruption == "fingerprint":
        next(r for r in rows if "exception.fingerprint" in r["attributes"])["attributes"][
            "exception.fingerprint"
        ] = "different"
    elif corruption == "plain_sha":
        rows[0]["attributes"]["user.id_hash"] = v.identity_hashes(v.make_plan("unit")[0]["user"])[0]
    assert v.exit_code(v.evaluate_spans(v.make_plan("unit"), rows, "key")) == 1


def test_aggregate_buckets_keep_traffic_separate():
    rows = [
        {
            "time": "2026-10-30T12:00:00+00:00",
            "traffic_kind": "real",
            "failed": "false",
            "user_hash": "u",
            "session_id": "s",
        },
        {
            "time": "2026-10-30T12:00:01+00:00",
            "traffic_kind": "real",
            "failed": "true",
            "user_hash": "u",
            "session_id": "s2",
        },
        {
            "time": "2026-10-30T12:00:02+00:00",
            "traffic_kind": "journey",
            "failed": False,
            "user_hash": "u",
            "session_id": "s",
        },
    ]
    expected = v.aggregate_expectations(rows, "date")
    assert expected["2026-10-30/real"] == {"requests": 2, "errors": 1, "users": 1, "sessions": 2}
    assert expected["2026-10-30/journey"]["requests"] == 1
    actual = [
        {
            "date": "2026-10-30",
            "traffic_kind": "real",
            "requests": "2",
            "errors": "1",
            "users": "1",
            "sessions": "2",
        }
    ]
    assert v.aggregate_actual(actual, "date")["2026-10-30/real"] == expected["2026-10-30/real"]
    with pytest.raises(ValueError, match="duplicate"):
        v.aggregate_actual(actual * 2, "date")


def test_report_rendering_and_exit_codes():
    checks = [v.check("exact", 1, 1), v.pending("job", "run inventory_scan")]
    assert v.exit_code(checks) == 2
    assert "SKIP | job" in v.summary_table(checks)
    assert json.loads(v.report_json({"checks": checks}))["checks"] == checks
    checks.append(v.check("bad", 10, 11))
    assert v.exit_code(checks) == 1
    assert v.exit_code(checks[:1]) == 0
    assert v.exit_code([v.pending("browser", "use browser", "MANUAL")]) == 2


def test_sql_uses_identifiers_and_named_parameters(tmp_path):
    report = {
        **fixture_report(),
        "started_at": "2026-10-30T12:00:00+00:00",
        "finished_at": "2026-10-30T12:05:00+00:00",
    }
    params = v.query_parameters(args_for(tmp_path), report)
    assert params["spans"] == "`cat`.`monitor`.`otel_spans`"
    assert v.qualified_table("a`b", "schema; DROP X", "table") == "`a``b`.`schema; DROP X`.`table`"
    assert "IN (SELECT explode(from_json(:ids" in v.SPAN_SQL
    assert "trace_id IN (SELECT trace_id FROM roots)" in v.LOG_SQL
    assert "val-unit" not in v.SPAN_SQL


def test_drive_records_no_retries_and_health_evidence(monkeypatch, tmp_path):
    report, args = fixture_report(), args_for(tmp_path)
    client = MagicMock()
    client.api.return_value = {"series": [[9_999_999_999, 0, 503, 10]]}
    statuses = iter(p["status"] for p in report["plan"])
    client.http.side_effect = lambda *a, **kw: (next(statuses), {"boot_id": "boot"}, {})
    monkeypatch.setattr(v, "sleep_progress", lambda *a: None)
    monkeypatch.setattr(v, "browser_drive", lambda *a: {"status": "manual"})
    v.drive(client, args, report)
    assert client.http.call_count == 242
    assert report["health_seen_503"]
    assert "finished_at" in json.loads(args.report.read_text())
    assert v.exit_code(report["drive_checks"]) == 0
    sent = [call.kwargs["headers"]["x-request-id"] for call in client.http.call_args_list]
    assert sent == [p["rid"] for p in report["plan"]]


def test_partial_drive_preserves_in_flight_and_restores_health(monkeypatch, tmp_path):
    report, args = fixture_report(), args_for(tmp_path)
    report["plan"] = report["plan"][-4:]
    client = MagicMock()
    client.http.side_effect = [(200, {}, {}), OSError("lost response"), (200, {}, {})]
    monkeypatch.setattr(v, "sleep_progress", lambda *a: None)
    with pytest.raises(OSError):
        v.drive(client, args, report)
    assert report["in_flight"] == report["plan"][1]["rid"]
    assert client.http.call_args.kwargs["query"] == {"ok": 1}
    assert "finished_at" not in report


def test_statement_polling_and_pagination(monkeypatch, tmp_path):
    def item_type(**kwargs):
        return SimpleNamespace(**kwargs)

    monkeypatch.setitem(
        sys.modules,
        "databricks.sdk.service.sql",
        SimpleNamespace(StatementParameterListItem=item_type),
    )
    client = object.__new__(v.LiveClient)
    client.args = args_for(tmp_path)
    client.w = MagicMock()
    execution = client.w.statement_execution
    first = SimpleNamespace(
        status=SimpleNamespace(state=SimpleNamespace(value="PENDING")), statement_id="statement"
    )
    done = SimpleNamespace(
        status=SimpleNamespace(state=SimpleNamespace(value="SUCCEEDED")),
        statement_id="statement",
        manifest=SimpleNamespace(
            truncated=False, schema=SimpleNamespace(columns=[SimpleNamespace(name="n")])
        ),
        result=SimpleNamespace(data_array=[["1"]], next_chunk_index=1),
    )
    execution.execute_statement.return_value = first
    execution.get_statement.return_value = done
    execution.get_statement_result_chunk_n.return_value = SimpleNamespace(
        data_array=[["2"]], next_chunk_index=None
    )
    monkeypatch.setattr(v.time, "sleep", lambda _: None)
    assert client.sql("SELECT :value", value="x'; DROP") == [{"n": "1"}, {"n": "2"}]
    assert execution.execute_statement.call_args.kwargs["parameters"][0].value == "x'; DROP"
    done.manifest.truncated = True
    with pytest.raises(RuntimeError, match="truncated"):
        client.sql("SELECT 1")


def test_lifecycle_duplicates_visible():
    rows = [{"state": "firing", "muted": "true"}, {"state": "resolved", "muted": True}]
    assert v.lifecycle_counts(rows) == {"firing/muted=true": 1, "resolved/muted=true": 1}
    assert v.lifecycle_counts(rows + rows[:1])["firing/muted=true"] == 2


def test_webhook_evidence_requires_coverage_and_positive_control():
    windows = ("alert lifecycle + monitor restart", "muted lifecycle")
    report = {
        "run_id": "unit",
        "operations": {
            label: {"since": "2026-10-30T12:00:00+00:00", "until": "2026-10-30T12:10:00+00:00"}
            for label in windows
        },
    }
    evidence = {
        "run_id": "unit",
        "receiver": "receiver/export",
        "windows": {label: {**report["operations"][label], "alerts": []} for label in windows},
    }
    assert v.exit_code(v.evaluate_webhook_evidence(report, evidence)) == 1
    alerts = [
        {"app": v.APP, "rule": "app_stopped", "state": state, "muted": False}
        for state in ("firing", "resolved")
    ]
    evidence["windows"][windows[0]]["alerts"] = alerts
    assert v.exit_code(v.evaluate_webhook_evidence(report, evidence)) == 0
    evidence["windows"][windows[1]]["alerts"] = alerts
    assert v.exit_code(v.evaluate_webhook_evidence(report, evidence)) == 1
    evidence["windows"][windows[1]]["alerts"] = []
    evidence["windows"][windows[1]]["until"] = "2026-10-30T12:01:00+00:00"
    assert v.exit_code(v.evaluate_webhook_evidence(report, evidence)) == 1


def test_verify_measurements_and_missing_job_classification(monkeypatch, tmp_path):
    report = fixture_report()
    report.update(
        started_at="2026-10-30T12:00:00+00:00",
        finished_at="2026-10-30T12:05:00+00:00",
        health_seen_503=True,
        responses=[
            {"group": "health_probe_down", "body": {"boot_id": "boot", "version": "test-version"}}
        ],
    )
    args = args_for(tmp_path)
    monkeypatch.setenv("MONITOR_HASH_KEY", "key")
    spans = golden_spans()
    raw = [
        {
            "time": "2026-10-30T12:01:00+00:00",
            "traffic_kind": s["traffic_kind"],
            "failed": s["failed"],
            "user_hash": s["attributes"]["user.id_hash"],
            "session_id": s["attributes"]["session.id"],
        }
        for s in spans
        if "SERVER" in s["kind"]
    ]
    funnel = [
        {
            "step_name": v.event_name("unit", step),
            "sessions": count,
            "dropoff_pct": drop,
            "funnel": "val-unit:funnel",
        }
        for (step, count), drop in zip(v.FUNNEL, [None, 100 / 3, 50], strict=True)
    ]
    cost = [{"date": "2026-10-30", "in_t": "12000", "out_t": "2400", "ai_calls": "17"}]
    fault = {}
    calls = []

    def sql(statement, **params):
        calls.append((statement, params))
        for table, message in fault.items():
            if f"IDENTIFIER(:{table})" in statement:
                raise RuntimeError(message)
        if statement == v.SPAN_SQL:
            return spans
        if statement == v.LOG_SQL:
            return [{"body": "email=[email] Bearer [redacted] PAT=[redacted]"}] * 3 + [
                {"body": '{"event":"feedback","rating":5}'}
            ]
        if "IDENTIFIER(:otel_metrics)" in statement:
            return [
                {
                    "row": json.dumps(
                        {
                            "name": "gen_ai.client.token.usage",
                            "attributes": {"gen_ai.request.model": v.MODEL, "gen_ai.token.type": d},
                        }
                    )
                }
                for d in ("input", "output")
            ]
        if "IDENTIFIER(:logs)" in statement:
            return [
                {
                    "body": json.dumps(
                        {
                            "boot_id": "boot",
                            "packages": ["fastapi==1"],
                            "team": "conformance",
                            "cost_center": "cc-test",
                        }
                    )
                }
            ]
        if "IDENTIFIER(:v_error_groups)" in statement:
            return [{"fingerprint": "abcdef012345"}]
        if "IDENTIFIER(:v_events)" in statement:
            return [
                {"event_name": name, "n": n} for name, n in report["expected"]["events"].items()
            ]
        if "IDENTIFIER(:v_funnels)" in statement:
            return funnel
        if "AS user_hash FROM" in statement:
            return raw
        for table, period in (("agg_app_daily", "date"), ("agg_app_hourly", "hour")):
            if f"IDENTIFIER(:{table})" in statement:
                values = v.aggregate_expectations(raw, period)
                return [
                    {period: key.split("/")[0], "traffic_kind": key.split("/")[1], **counts}
                    for key, counts in values.items()
                ]
        if "sum(coalesce(variant_get" in statement or "IDENTIFIER(:costs_ai_daily)" in statement:
            return cost
        if "SELECT cast(window(time" in statement or "SELECT cast(b.bucket" in statement:
            return [{"bucket": "2026-10-30 12:00:00", "good": "196", "total": "231"}]
        if "SELECT cast(date(b.bucket)" in statement:
            return [{"bucket": "2026-10-30", "good": "196", "total": "231"}]
        raise AssertionError(statement)

    def api(path):
        if path.endswith("/events"):
            return {
                "events": [
                    {"event_name": name, "events": n}
                    for name, n in report["expected"]["events"].items()
                ]
            }
        if path.endswith("/funnels"):
            return {"steps": funnel}
        if path.endswith("/slo"):
            return {
                "series": [{"slo": "val-unit", "date": "2026-10-30", "good": "196", "total": "231"}]
            }
        raise AssertionError(path)

    client = SimpleNamespace(sql=sql, api=api)
    checks = v.verify_data(client, args, report)
    assert not [c for c in checks if c["status"] == "FAIL"]
    assert v.exit_code(checks) == 2  # Browser has not been driven.
    assert all("cat.monitor" not in sql for sql, _ in calls)
    assert all(
        set(params) == set(v.re.findall(r"(?<!:):([a-zA-Z_]\w*)", sql)) for sql, params in calls
    )
    fault["costs_ai_daily"] = "TABLE_OR_VIEW_NOT_FOUND"
    checks = v.verify_data(client, args, report)
    skipped = next(c for c in checks if c["name"] == "costs_ai_daily")
    assert skipped["status"] == "SKIP" and "bundle run cost_rollup" in skipped["detail"]
    fault["costs_ai_daily"] = "PERMISSION_DENIED"
    checks = v.verify_data(client, args, report)
    assert next(c for c in checks if c["name"] == "costs_ai_daily")["status"] == "FAIL"


def test_operational_exercises_restore_settings_and_record_transitions(monkeypatch, tmp_path):
    args, report = args_for(tmp_path), fixture_report()
    client = MagicMock()
    client.ws = "123"
    states = {v.APP: "ACTIVE", "apps-monitor": "ACTIVE"}
    transitions, writes, mutes = [], [], []

    def api(path, method="GET", body=None):
        if method == "PUT":
            writes.append(body)
            return {"ok": True}
        if method == "POST":
            mutes.append("mute-id")
            return {"id": "mute-id"}
        if method == "DELETE":
            mutes.clear()
            return {"ok": True}
        if path.endswith("product-config"):
            return {"outcome_event": "original", "token_budget_day": 90000}
        if "/policy/" in path:
            return {"throttle": "block"}
        return {"app_state": "RUNNING", "compute_state": "ACTIVE"}

    def control(method, path):
        _, name, action = path.rsplit("/", 2)
        old = states[name]
        states[name] = "STOPPED" if action == "stop" else "ACTIVE"
        if name == v.APP and states[name] != old:
            transitions.append(
                {
                    "state": "firing" if action == "stop" else "resolved",
                    "muted": bool(mutes),
                    "ts": v.utcnow(),
                }
            )

    client.api.side_effect = api
    client.w.api_client.do.side_effect = control
    client.w.apps.get.side_effect = lambda name: SimpleNamespace(
        compute_status=SimpleNamespace(state=SimpleNamespace(value=states[name]))
    )
    client.sql.side_effect = lambda sql, **p: [r for r in transitions if r["ts"] >= p["since"]]
    client.http.return_value = (429, {"error": "budget exceeded"}, {})
    monkeypatch.setattr(v, "sleep_progress", lambda *a: None)
    checks = v.exercise_operations(client, args, report)
    assert v.exit_code(checks) == 0
    assert writes == [
        {"outcome_event": "original", "token_budget_day": 1},
        {"outcome_event": "original", "token_budget_day": 90000},
    ]
    assert states == {v.APP: "ACTIVE", "apps-monitor": "ACTIVE"}
    assert not mutes
    assert len(transitions) == 4
    assert report["operations"]["product_config_restored"] is True


def test_cli_requires_explicit_profile_and_rejects_bad_urls():
    required = [
        "--profile",
        "chosen",
        "--catalog",
        "cat",
        "--schema",
        "monitor",
        "--monitor-url",
        "https://monitor.invalid",
        "--conformance-url",
        "https://fixture.invalid",
        "--warehouse-id",
        "warehouse",
    ]
    assert v.parse_args(required).wait_minutes == 15
    with pytest.raises(SystemExit):
        v.parse_args(required[2:])
    with pytest.raises(SystemExit):
        v.parse_args([*required, "--monitor-url", "https://user:secret@host/path"])
    with pytest.raises(SystemExit):
        v.parse_args([*required, "--wait-minutes", "nan"])
