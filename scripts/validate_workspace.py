"""Opt-in live validation. Imports and pure checks need only the standard library.

See docs/CONFORMANCE.md for prerequisites, isolation, jobs, and manual evidence.
No request is retried: an ambiguous delivery must remain visible in the report.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import os
import random
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

APP = "monitor-demo-conformance"
MODEL = "conformance-fake-model"
FAIL_CLASSES = ("rate_limit", "timeout", "policy", "schema", "server")
# built at runtime so secret scanners never see a token-shaped literal in source
PAT = "dapi" + "0123456789abcdef" * 2
# group, method, route, count, query, expected HTTP status. Funnel counts are SESSIONS.
PLAN_TABLE = (
    ("ok", "GET", "/c/ok", 100, {}, 200),
    ("error", "GET", "/c/error", 20, {}, 500),
    ("client_error", "GET", "/c/client-error", 10, {}, 404),
    ("slow_300", "GET", "/c/slow", 30, {"ms": 300}, 200),
    ("slow_1500", "GET", "/c/slow", 10, {"ms": 1500}, 200),
    ("llm", "GET", "/c/llm", 8, {"in": 1000, "out": 200, "stream": 0}, 200),
    ("stream", "GET", "/c/llm", 4, {"in": 1000, "out": 200, "stream": 1, "chunks": 10}, 200),
    *((f"fail_{fail}", "GET", "/c/llm", 1, {"fail": fail}, 502) for fail in FAIL_CLASSES),
    ("step", "GET", "/c/step", 5, {}, 200),
    ("sql", "GET", "/c/sql", 5, {"rows": 42}, 200),
    ("leak", "GET", "/c/leak", 3, {}, 200),
    ("budget", "GET", "/c/budget", 1, {}, 200),
    ("event_ingress", "POST", "/monitor/event", 1, {}, 200),
    ("feedback", "POST", "/monitor/feedback", 1, {}, 200),
    ("synthetic", "GET", "/c/ok", 5, {}, 200),
)
FUNNEL = (("signup", 15), ("verify", 10), ("activate", 5))
HEALTH_CACHE_SECONDS = 31
HEALTH_HOLD_SECONDS = 150
JOB_GOLD = "inventory_scan"  # gold_views is a task of this bundle job.


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def validate_run_id(run_id):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", run_id):
        raise ValueError("run-id must be 1-32 ASCII letters, digits, dots, underscores or hyphens")
    return run_id


def event_name(run_id, step):
    return f"val-{run_id}:{step}"


def leak_values(run_id):
    return (f"conformance-secret-{run_id}", f"leak-{run_id}@example.invalid", PAT)


def make_plan(run_id):
    """Seeded identities/order, unique bounded request IDs, ordered funnel per session."""
    validate_run_id(run_id)
    rng, plan = random.Random(run_id), []

    def add(group, method, path, query, status, session=None, kind="real", body=None, delay=0):
        sid = rng.randrange(15) if session is None else session
        plan.append(
            {
                "group": group,
                "method": method,
                "path": path,
                "query": dict(query),
                "status": status,
                "session": f"val-{run_id}-s{sid}",
                "user": f"conformance-user-{sid % 5}@example.invalid",
                "kind": kind,
                "body": body,
                "delay_before_s": delay,
            }
        )

    for group, method, path, count, query, status in PLAN_TABLE:
        for index in range(count):
            params, body = dict(query), None
            if group == "step":
                params["name"] = f"conformance-step-{index}"
            elif group == "leak":
                token, email, _ = leak_values(run_id)
                params.update(token=token, email=email)
            elif group == "feedback":
                body = {"rating": 99, "comment": f"Bearer {leak_values(run_id)[0]}"}
            elif group == "event_ingress":
                body = {"name": event_name(run_id, "ingress"), "props": {"fixture": True}}
            add(
                group,
                method,
                path,
                params,
                status,
                kind="journey" if group == "synthetic" else "real",
                body=body,
            )
    rng.shuffle(plan)
    for session in range(15):
        for step, count in FUNNEL:
            if session < count:
                add("event", "POST", "/c/event", {"name": event_name(run_id, step)}, 200, session)
    add("health_down", "POST", "/c/health-toggle", {"ok": 0}, 200, kind="probe")
    add(
        "health_probe_down",
        "GET",
        "/monitor/health",
        {},
        503,
        kind="probe",
        delay=HEALTH_CACHE_SECONDS,
    )
    add(
        "health_up",
        "POST",
        "/c/health-toggle",
        {"ok": 1},
        200,
        kind="probe",
        delay=HEALTH_HOLD_SECONDS,
    )
    add(
        "health_probe_up",
        "GET",
        "/monitor/health",
        {},
        200,
        kind="probe",
        delay=HEALTH_CACHE_SECONDS,
    )
    return [{**item, "rid": f"val-{run_id}-{n}"} for n, item in enumerate(plan, 1)]


def expected_values(plan):
    real = [p for p in plan if p["kind"] == "real"]
    success = [p for p in real if p["group"] in {"llm", "stream"}]
    errors = sum(p["status"] >= 400 for p in real)
    return {
        "requests": len(plan),
        "real_requests": len(real),
        "errors": errors,
        "error_rate": errors / len(real),
        "server_errors": sum(p["status"] >= 500 for p in real),
        "routes": dict(Counter(p["path"] for p in plan)),
        "traffic": dict(Counter(p["kind"] for p in plan)),
        "users": len({p["user"] for p in real}),
        "sessions": len({p["session"] for p in real}),
        "input_tokens": sum(p["query"]["in"] for p in success),
        "output_tokens": sum(p["query"]["out"] for p in success),
        "events": dict(
            Counter(
                p["query"]["name"] if p["group"] == "event" else p["body"]["name"]
                for p in plan
                if p["group"] in {"event", "event_ingress"}
            )
        ),
        "billable_spans": sum(p["path"] in {"/c/llm", "/c/budget"} for p in plan),
        "funnel_sessions": dict(FUNNEL),
        "funnel_dropoff_pct": [None, 100 / 3, 50.0],
    }


def within_tolerance(actual, expected, relative=0.0, absolute=0.0, upper_extra=0.0):
    try:
        actual, expected = float(actual), float(expected)
    except (TypeError, ValueError):
        return False
    if not all(math.isfinite(n) and n >= 0 for n in (relative, absolute, upper_extra)):
        raise ValueError("tolerances must be finite and nonnegative")
    delta = abs(expected) * relative + absolute
    return (
        math.isfinite(actual)
        and math.isfinite(expected)
        and expected - delta <= actual <= expected + delta + upper_extra
    )


def percentile(values, fraction):
    """Nearest rank, matching the small deterministic slow-route populations."""
    if not values or not 0 < fraction <= 1:
        raise ValueError("nonempty population and percentile in (0, 1] required")
    return sorted(float(v) for v in values)[math.ceil(len(values) * fraction) - 1]


def contains_leak(value, needles):
    """Scan decoded structures too, so JSON Unicode escapes cannot conceal a leak."""
    if isinstance(value, dict):
        return any(contains_leak(k, needles) or contains_leak(v, needles) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(contains_leak(v, needles) for v in value)
    if not isinstance(value, str):
        return False
    if any(needle and needle in value for needle in needles):
        return True
    try:
        decoded = json.loads(value)
    except (ValueError, RecursionError):
        return False
    return decoded != value and contains_leak(decoded, needles)


def identity_hashes(email, key=None):
    plain = hashlib.sha256(email.encode()).hexdigest()[:16]
    keyed = hmac.new(key.encode(), email.encode(), hashlib.sha256).hexdigest()[:16] if key else None
    return plain, keyed


def is_keyed_hash(stored, email, key=None):
    plain, keyed = identity_hashes(email, key)
    return (
        isinstance(stored, str)
        and bool(re.fullmatch(r"[0-9a-f]{16}", stored))
        and stored != plain
        and (keyed is None or hmac.compare_digest(stored, keyed))
    )


def check(name, expected, actual, *, relative=0.0, absolute=0.0, upper_extra=0.0, detail=""):
    numeric = bool(relative or absolute or upper_extra)
    passed = (
        within_tolerance(actual, expected, relative, absolute, upper_extra)
        if numeric
        else actual == expected
    )
    return {
        "name": name,
        "status": "PASS" if passed else "FAIL",
        "expected": expected,
        "actual": actual,
        "tolerance": {"relative": relative, "absolute": absolute, "upper_extra": upper_extra},
        "detail": detail,
    }


def pending(name, detail, status="SKIP"):
    return {
        "name": name,
        "status": status,
        "expected": "evidence required",
        "actual": None,
        "tolerance": {},
        "detail": detail,
    }


def report_json(report):
    return json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"


def summary_table(checks):
    def cell(value):
        return json.dumps(value, sort_keys=True, ensure_ascii=True).replace("|", "\\|")

    lines = [
        "Status | Check | Expected | Actual | Tolerance / next step",
        "--- | --- | --- | --- | ---",
    ]
    for item in checks:
        lines.append(
            " | ".join(
                [
                    item["status"],
                    item["name"],
                    cell(item["expected"]),
                    cell(item["actual"]),
                    cell(item["tolerance"]) + " " + item["detail"],
                ]
            )
        )
    return "\n".join(lines)


def exit_code(checks):
    if any(c["status"] == "FAIL" for c in checks):
        return 1
    return 2 if any(c["status"] in {"SKIP", "MANUAL"} for c in checks) else 0


def qualified_table(catalog, schema, table):
    # IDENTIFIER receives this as a bound parameter, including escaped identifier delimiters.
    return ".".join(f"`{part.replace('`', '``')}`" for part in (catalog, schema, table))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LiveClient:
    def __init__(self, args):
        from databricks.sdk import WorkspaceClient

        self.w = WorkspaceClient(profile=args.profile)
        self.args = args
        self.ws = str(self.w.get_workspace_id())

    def http(self, base, path, *, method="GET", query=None, headers=None, body=None):
        url = base.rstrip("/") + path
        if query:
            url += "?" + urlencode(query)
        auth = self.w.config.authenticate()  # Refresh OAuth for every request.
        auth.update(headers or {})
        data = None
        if body is not None:
            auth["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        request = Request(url, data=data, method=method, headers=auth)
        try:
            response = build_opener(NoRedirect()).open(request, timeout=45)
        except HTTPError as exc:
            response = exc
        with response:
            raw = response.read()  # Consume the whole stream before the next request.
            try:
                payload = json.loads(raw)
            except ValueError:
                payload = None
            return response.code, payload, dict(response.headers)

    def api(self, path, *, method="GET", body=None):
        status, data, _ = self.http(self.args.monitor_url, path, method=method, body=body)
        if status != 200 or not isinstance(data, dict):
            raise RuntimeError(f"monitor API {path}: HTTP {status}, expected JSON object")
        return data

    def sql(self, statement, **params):
        from databricks.sdk.service.sql import StatementParameterListItem

        execution = self.w.statement_execution
        response = execution.execute_statement(
            warehouse_id=self.args.warehouse_id,
            statement=statement,
            wait_timeout="30s",
            parameters=[
                StatementParameterListItem(name=k, value=str(v)) for k, v in params.items()
            ],
        )
        deadline = time.monotonic() + 180
        while response.status.state.value in {"PENDING", "RUNNING"}:
            if time.monotonic() >= deadline:
                execution.cancel_execution(response.statement_id)
                raise TimeoutError("statement execution exceeded 180 seconds")
            time.sleep(2)
            response = execution.get_statement(response.statement_id)
        if response.status.state.value != "SUCCEEDED":
            error = response.status.error
            raise RuntimeError(error.message if error else response.status.state.value)
        if response.manifest.truncated:
            raise RuntimeError("statement result truncated; refusing partial evidence")
        columns = [c.name for c in response.manifest.schema.columns]
        rows, chunk = [], response.result
        while chunk is not None:
            rows.extend(dict(zip(columns, row, strict=True)) for row in chunk.data_array or [])
            if chunk.next_chunk_index is None:
                break
            chunk = execution.get_statement_result_chunk_n(
                response.statement_id, chunk.next_chunk_index
            )
        return rows


def vg(key, typ="string"):
    return f"variant_get(attributes, '$[\"{key}\"]', '{typ}')"


RID = vg("app.client_request_id")
HTTP_STATUS = f"coalesce({vg('http.response.status_code', 'int')}, {vg('http.status_code', 'int')})"
ROUTE = f"coalesce({vg('http.route')}, name)"
KIND = f"coalesce({vg('traffic.kind')}, 'real')"
ERROR = f"(coalesce({HTTP_STATUS} >= 400, false) OR coalesce(status.code, '') ILIKE '%error%')"
RUN_CTE = f"""WITH roots AS (
  SELECT * FROM IDENTIFIER(:spans) WHERE service_name = :app AND kind ILIKE '%server%'
    AND {RID} IN (SELECT explode(from_json(:ids, 'ARRAY<STRING>')))
), run_spans AS (
  SELECT * FROM IDENTIFIER(:spans) WHERE service_name = :app
    AND trace_id IN (SELECT trace_id FROM roots)
)"""
SPAN_SQL = (
    RUN_CTE
    + f""" SELECT span_id, trace_id, name, kind, cast(time AS STRING) AS time,
  cast(date AS STRING) AS date, to_json(attributes) AS attributes, {RID} AS rid,
  {ROUTE} AS route, {HTTP_STATUS} AS http_status, {KIND} AS traffic_kind,
  {ERROR} AS failed, (end_time_unix_nano - start_time_unix_nano) / 1e6 AS ms
  FROM run_spans"""
)
LOG_SQL = (
    RUN_CTE
    + """ SELECT cast(body AS STRING) AS body, to_json(attributes) AS attributes,
  trace_id FROM IDENTIFIER(:logs) WHERE service_name = :app AND (
    trace_id IN (SELECT trace_id FROM roots)
    OR get_json_object(cast(body AS STRING), '$.rid') IN
       (SELECT explode(from_json(:ids, 'ARRAY<STRING>'))))"""
)


def attributes(row):
    value = row.get("attributes") or {}
    return json.loads(value) if isinstance(value, str) else value


def truth(value):
    return value is True or str(value).lower() == "true"


def evaluate_spans(plan, rows, hash_key=None):
    """Independent golden expectations, including missing, duplicate, and extra spans."""
    expected = expected_values(plan)
    by_id = {p["rid"]: p for p in plan}
    roots = [r for r in rows if "server" in r["kind"].lower() and r["rid"] in by_id]
    checks = [
        check(
            "server span request IDs (exactly once)",
            dict.fromkeys(by_id, 1),
            dict(Counter(r["rid"] for r in roots)),
        ),
        check(
            "span counts per route", expected["routes"], dict(Counter(r["route"] for r in roots))
        ),
        check(
            "traffic kinds", expected["traffic"], dict(Counter(r["traffic_kind"] for r in roots))
        ),
    ]
    real = [r for r in roots if r["traffic_kind"] == "real"]
    errors = sum(truth(r["failed"]) for r in real)
    checks.append(
        check(
            "default and overridden journey steps",
            {p["rid"]: p["query"]["name"] if p["group"] == "step" else p["path"] for p in plan},
            {r["rid"]: attributes(r).get("journey.step") for r in roots},
        )
    )
    checks.append(
        check(
            "app.name envelope", len(plan), sum(attributes(r).get("app.name") == APP for r in roots)
        )
    )
    checks += [
        check("error count (4xx included)", expected["errors"], errors),
        check("error rate", expected["error_rate"], errors / len(real) if real else None),
        check(
            "HTTP 5xx count",
            expected["server_errors"],
            sum(int(r["http_status"] or 0) >= 500 for r in real),
        ),
        check(
            "status per request",
            {p["rid"]: p["status"] for p in plan},
            {r["rid"]: int(r["http_status"] or 0) for r in roots},
        ),
        check(
            "session per request",
            {p["rid"]: p["session"] for p in plan},
            {r["rid"]: attributes(r).get("session.id") for r in roots},
        ),
        check(
            "real DAU", expected["users"], len({attributes(r).get("user.id_hash") for r in real})
        ),
        check(
            "real sessions",
            expected["sessions"],
            len({attributes(r).get("session.id") for r in real}),
        ),
        check(
            "user hash differs from plain SHA256",
            len(roots),
            sum(
                is_keyed_hash(attributes(r).get("user.id_hash"), by_id[r["rid"]]["user"])
                for r in roots
            ),
        ),
    ]
    if hash_key:
        checks.append(
            check(
                "user hash equals HMAC-SHA256",
                len(plan),
                sum(
                    is_keyed_hash(
                        attributes(r).get("user.id_hash"), by_id[r["rid"]]["user"], hash_key
                    )
                    for r in roots
                ),
            )
        )
    else:
        checks.append(
            pending(
                "user hash equals HMAC-SHA256",
                "Set local MONITOR_HASH_KEY to the app's secret; inequality alone does not prove HMAC.",
            )
        )
    for group, ms in (("slow_300", 300), ("slow_1500", 1500)):
        values = [float(r["ms"]) for r in roots if by_id[r["rid"]]["group"] == group]
        for p in (0.5, 0.95):
            checks.append(
                check(
                    f"{group} p{int(p * 100)} ms",
                    ms,
                    percentile(values, p) if values else None,
                    relative=0.2,
                    upper_extra=100,
                )
            )
    slow = [float(r["ms"]) for r in roots if by_id[r["rid"]]["path"] == "/c/slow"]
    for p, ms in ((0.5, 300), (0.95, 1500)):
        checks.append(
            check(
                f"slow route p{int(p * 100)} ms",
                ms,
                percentile(slow, p) if slow else None,
                relative=0.2,
                upper_extra=100,
            )
        )
    llm = [
        r
        for r in rows
        if attributes(r).get("gen_ai.request.model") in {MODEL, "conformance-budget-model"}
    ]
    marked = [r for r in rows if truth(attributes(r).get("monitor.llm.billable"))]
    checks.append(
        check(
            "billable on exactly LLM spans",
            sorted(r["span_id"] for r in llm),
            sorted(r["span_id"] for r in marked),
        )
    )
    checks.append(check("LLM span count", expected["billable_spans"], len(llm)))
    for p in plan:
        if p["path"] not in {"/c/llm", "/c/budget"}:
            continue
        calls = [r for r in llm if attributes(r).get("app.client_request_id") == p["rid"]]
        checks.append(check(f"LLM call {p['rid']}", 1, len(calls)))
        for r in calls:
            attr = attributes(r)
            fail = p["query"].get("fail", "none")
            checks.append(
                check(
                    f"LLM error.type {p['rid']}",
                    None if fail == "none" else fail,
                    attr.get("error.type"),
                )
            )
            if p["group"] in {"llm", "stream"}:
                checks.append(
                    check(
                        f"LLM final tokens {p['rid']}",
                        [1000, 200],
                        [
                            attr.get("gen_ai.usage.input_tokens"),
                            attr.get("gen_ai.usage.output_tokens"),
                        ],
                    )
                )
            if p["group"] == "stream":
                ttft = attr.get("monitor.llm.ttft_ms")
                checks.append(
                    check(
                        f"stream TTFT {p['rid']}",
                        True,
                        isinstance(ttft, (float, int)) and math.isfinite(ttft) and ttft > 0,
                    )
                )
    successful = [
        attributes(r)
        for r in llm
        if attributes(r).get("app.client_request_id")
        in {p["rid"] for p in plan if p["group"] in {"llm", "stream"}}
    ]
    for direction in ("input", "output"):
        checks.append(
            check(
                f"successful {direction} tokens",
                expected[f"{direction}_tokens"],
                sum(a.get(f"gen_ai.usage.{direction}_tokens", 0) for a in successful),
            )
        )
    fps = [
        attributes(r).get("exception.fingerprint")
        for r in roots
        if by_id[r["rid"]]["group"] == "error"
    ]
    checks += [
        check(
            "20 stable exception fingerprints",
            True,
            len(fps) == 20 and len(set(fps)) == 1 and bool(fps[0]),
        ),
        check(
            "journey.step overrides",
            {p["rid"]: p["query"]["name"] for p in plan if p["group"] == "step"},
            {
                r["rid"]: attributes(r).get("journey.step")
                for r in roots
                if by_id[r["rid"]]["group"] == "step"
            },
        ),
    ]
    sql_spans = [r for r in rows if r["name"] == "sql.execute"]
    sql_traces = {r["trace_id"] for r in roots if by_id[r["rid"]]["group"] == "sql"}
    checks += [
        check(
            "SQL spans per request",
            dict.fromkeys(sql_traces, 1),
            dict(Counter(r["trace_id"] for r in sql_spans)),
        ),
        check(
            "SQL row counts and no text attributes",
            5,
            sum(
                attributes(r).get("db.response.returned_rows") == 42
                and attributes(r).get("db.namespace") == "conformance-fake-warehouse"
                and not {"db.statement", "db.query.text"}.intersection(attributes(r))
                for r in sql_spans
            ),
        ),
    ]
    return checks


def aggregate_expectations(rows, period):
    """Full raw buckets include other runs; golden run counts are checked separately."""
    groups = defaultdict(list)
    for row in rows:
        stamp = datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
        stamp = stamp.replace(tzinfo=stamp.tzinfo or timezone.utc)
        bucket = (
            stamp.date().isoformat()
            if period == "date"
            else stamp.replace(minute=0, second=0, microsecond=0).isoformat()
        )
        groups[(bucket, row["traffic_kind"])].append(row)
    result = {}
    for (bucket, kind), spans in groups.items():
        result[f"{bucket}/{kind}"] = {
            "requests": len(spans),
            "errors": sum(truth(s["failed"]) for s in spans),
            "users": len({s["user_hash"] for s in spans if s["user_hash"] is not None}),
            "sessions": len({s["session_id"] for s in spans if s["session_id"] is not None}),
        }
    return result


def aggregate_actual(rows, period):
    result = {}
    for row in rows:
        bucket = row[period]
        if period == "hour":
            stamp = datetime.fromisoformat(bucket.replace("Z", "+00:00"))
            bucket = stamp.replace(tzinfo=stamp.tzinfo or timezone.utc).isoformat()
        key = f"{bucket}/{row['traffic_kind']}"
        if key in result:
            raise ValueError(f"duplicate aggregate key: {key}")
        # AI-only groups can legitimately have zero SERVER spans.
        if int(row["requests"]):
            result[key] = {f: int(row[f]) for f in ("requests", "errors", "users", "sessions")}
    return result


def evaluate_logs(run_id, logs, spans):
    needles = leak_values(run_id)
    leak_logs = [r for r in logs if "PAT=" in r["body"] and "email=" in r["body"]]
    feedback = []
    for row in logs:
        try:
            body = json.loads(row["body"])
        except ValueError:
            continue
        if isinstance(body, dict) and body.get("event") == "feedback":
            feedback.append(body)
    return [
        check("leak log coverage", 3, len(leak_logs)),
        check(
            "redaction: span attributes",
            0,
            sum(contains_leak(r["attributes"], needles) for r in spans),
        ),
        check("redaction: log bodies", 0, sum(contains_leak(r["body"], needles) for r in logs)),
        check("feedback clamp and scrub", [5], [b.get("rating") for b in feedback]),
        check("feedback contains no secret", False, contains_leak(feedback, needles)),
    ]


def job_hint(job, args):
    return f"Run from repo root: databricks bundle run {job} -t <target> --profile {args.profile}; then repeat --phase verify."


def query_parameters(args, report):
    tables = (
        "otel_spans",
        "otel_logs",
        "otel_metrics",
        "v_events",
        "v_error_groups",
        "v_funnels",
        "agg_app_daily",
        "agg_app_hourly",
        "costs_ai_daily",
        "sli_5m",
        "slo_specs",
        "v_rum_daily",
        "alert_events",
    )
    params = {name: qualified_table(args.catalog, args.schema, name) for name in tables}
    params.update(
        spans=params["otel_spans"],
        logs=params["otel_logs"],
        app=APP,
        ids=json.dumps([p["rid"] for p in report["plan"]]),
        start=report["started_at"],
        end=report["finished_at"],
        ws=report["workspace_id"],
        model=MODEL,
        funnel=event_name(report["run_id"], "funnel"),
        slo=f"val-{report['run_id']}",
    )
    start = datetime.fromisoformat(report["started_at"])
    end = datetime.fromisoformat(report["finished_at"])
    params["bucket_start"] = start.replace(
        minute=start.minute // 5 * 5, second=0, microsecond=0
    ).isoformat()
    params["bucket_end"] = (
        end.replace(minute=end.minute // 5 * 5, second=0, microsecond=0) + timedelta(minutes=5)
    ).isoformat()
    return params


def verify_data(client, args, report):
    params = query_parameters(args, report)
    checks = []

    def query(statement, **extra):
        values = {**params, **extra}
        names = set(re.findall(r"(?<!:):([a-zA-Z_]\w*)", statement))
        return client.sql(statement, **{key: values[key] for key in names})

    def optional(name, statement, evaluate, job=JOB_GOLD, **extra):
        try:
            rows = query(statement, **extra)
            if not rows:
                checks.append(pending(name, "No materialized data yet. " + job_hint(job, args)))
            else:
                checks.extend(evaluate(rows))
        except Exception as exc:  # noqa: BLE001 — each check must survive independent query failures
            message = str(exc)
            if "TABLE_OR_VIEW_NOT_FOUND" in message or "TABLE_NOT_FOUND" in message:
                checks.append(pending(name, job_hint(job, args)))
            else:
                checks.append(check(name, "query succeeds", type(exc).__name__, detail=message))

    spans = query(SPAN_SQL)
    checks.extend(evaluate_spans(report["plan"], spans, os.getenv("MONITOR_HASH_KEY")))
    logs = query(LOG_SQL)
    checks.extend(evaluate_logs(report["run_id"], logs, spans))
    # Metrics have no request ID. App/model/time are the strongest available scope.
    metric_rows = query("""SELECT to_json(struct(*)) AS row FROM IDENTIFIER(:otel_metrics)
      WHERE service_name = :app AND time >= :start::timestamp AND time <= :end::timestamp + INTERVAL 20 MINUTES""")
    metrics = [json.loads(r["row"]) for r in metric_rows]
    directions = {
        attributes(r).get("gen_ai.token.type")
        for r in metrics
        if (r.get("name") or r.get("metric_name")) == "gen_ai.client.token.usage"
        and attributes(r).get("gen_ai.request.model") == MODEL
    }
    checks.append(
        check(
            "GenAI metric rows (input + output)", ["input", "output"], sorted(directions - {None})
        )
    )
    boot_ids = {
        r["body"]["boot_id"]
        for r in report["responses"]
        if r.get("body") and r["group"] in {"health_probe_down", "health_probe_up"}
    }
    versions = {
        r["body"].get("version")
        for r in report["responses"]
        if r.get("body") and r["group"] in {"health_probe_down", "health_probe_up"}
    }
    roots = [r for r in spans if "server" in r["kind"].lower()]
    checks.append(
        check(
            "span version matches health contract",
            True,
            len(versions) == 1
            and None not in versions
            and all(attributes(r).get("app.version") in versions for r in roots),
        )
    )
    startup = query(
        """SELECT cast(body AS STRING) AS body FROM IDENTIFIER(:logs)
      WHERE service_name = :app AND get_json_object(cast(body AS STRING), '$.event') = 'startup'
        AND get_json_object(cast(body AS STRING), '$.boot_id') IN
          (SELECT explode(from_json(:boots, 'ARRAY<STRING>')))""",
        boots=json.dumps(sorted(boot_ids)),
    )
    startup_bodies = [json.loads(r["body"]) for r in startup]
    checks.append(
        check(
            "startup packages, team, cost center for observed boot",
            True,
            bool(boot_ids)
            and boot_ids == {b.get("boot_id") for b in startup_bodies}
            and all(
                b.get("packages")
                and b.get("team") == "conformance"
                and b.get("cost_center") == "cc-test"
                for b in startup_bodies
            ),
        )
    )
    fingerprints = sorted(
        {
            attributes(r)["exception.fingerprint"]
            for r in spans
            if attributes(r).get("exception.fingerprint")
        }
    )
    optional(
        "v_error_groups fingerprint",
        """SELECT fingerprint FROM IDENTIFIER(:v_error_groups)
      WHERE name = :app AND fingerprint IN (SELECT explode(from_json(:fps, 'ARRAY<STRING>')))""",
        lambda rows: [
            check(
                "v_error_groups fingerprint", fingerprints, sorted({r["fingerprint"] for r in rows})
            )
        ],
        fps=json.dumps(fingerprints),
    )
    optional(
        "v_events exact counts",
        """SELECT event_name, count(*) AS n FROM IDENTIFIER(:v_events)
      WHERE name = :app AND workspace_id = :ws AND event_source = 'event'
        AND request_id IN (SELECT explode(from_json(:ids, 'ARRAY<STRING>'))) GROUP BY event_name""",
        lambda rows: [
            check(
                "v_events exact counts",
                report["expected"]["events"],
                {r["event_name"]: int(r["n"]) for r in rows},
            )
        ],
    )

    def funnel_checks(rows):
        counts, drops = {}, {}
        for row in rows:
            step = row["step_name"]
            if step in counts:
                raise ValueError("funnel spans multiple app versions; keep one version per run")
            counts[step] = int(row["sessions"])
            drops[step] = None if row["dropoff_pct"] is None else float(row["dropoff_pct"])
        result = [
            check(
                "funnel session counts",
                {event_name(report["run_id"], s): n for s, n in FUNNEL},
                counts,
            )
        ]
        for (step, _), expected in zip(FUNNEL, [None, 100 / 3, 50], strict=True):
            result.append(
                check(
                    f"funnel {step} dropoff %",
                    expected,
                    drops.get(event_name(report["run_id"], step)),
                    absolute=0.001 if expected is not None else 0,
                )
            )
        return result

    optional(
        "v_funnels",
        """SELECT step_name, sessions, dropoff_pct FROM IDENTIFIER(:v_funnels)
      WHERE name = :app AND workspace_id = :ws AND funnel = :funnel""",
        funnel_checks,
    )
    raw_daily = query(f"""SELECT cast(time AS STRING) AS time, {KIND} AS traffic_kind, {ERROR} AS failed,
      {vg("session.id")} AS session_id, {vg("user.id_hash")} AS user_hash FROM IDENTIFIER(:spans)
      WHERE service_name = :app AND kind ILIKE '%server%'
        AND date BETWEEN date(:start::timestamp) AND date(:end::timestamp)""")
    for table, period in (("agg_app_daily", "date"), ("agg_app_hourly", "hour")):
        optional(
            table,
            f"""SELECT cast({period} AS STRING) AS {period}, traffic_kind, requests, errors, users, sessions
          FROM IDENTIFIER(:{table}) WHERE name = :app AND workspace_id = :ws
            AND date({period}) BETWEEN date(:start::timestamp) AND date(:end::timestamp)""",
            lambda rows, period=period, table=table: [
                check(
                    f"{table} counts by kind (synthetics excluded from real)",
                    aggregate_expectations(raw_daily, period),
                    aggregate_actual(rows, period),
                )
            ],
        )
    expected_costs = query(f"""SELECT cast(date AS STRING) AS date,
      sum(coalesce({vg("gen_ai.usage.input_tokens", "long")}, 0)) AS in_t,
      sum(coalesce({vg("gen_ai.usage.output_tokens", "long")}, 0)) AS out_t, count(*) AS ai_calls
      FROM IDENTIFIER(:spans) WHERE service_name = :app AND {vg("gen_ai.request.model")} = :model
        AND {vg("monitor.llm.billable", "boolean")} = true
        AND date BETWEEN date(:start::timestamp) AND date(:end::timestamp) GROUP BY date""")

    def cost_values(rows):
        values = {}
        for row in rows:
            if row["date"] in values:
                raise ValueError("duplicate costs_ai_daily key")
            values[row["date"]] = [int(row[k]) for k in ("in_t", "out_t", "ai_calls")]
        return values

    optional(
        "costs_ai_daily",
        """SELECT cast(date AS STRING) AS date, in_t, out_t, ai_calls
      FROM IDENTIFIER(:costs_ai_daily) WHERE name = :app AND workspace_id = :ws AND model = :model
        AND date BETWEEN date(:start::timestamp) AND date(:end::timestamp)""",
        lambda rows: [
            check(
                "costs_ai_daily tokens and calls",
                cost_values(expected_costs),
                cost_values(rows),
                detail="Full-day raw expectation includes prior runs; this run separately requires 12000/2400 tokens.",
            )
        ],
        job="cost_rollup",
    )
    # Use complete buckets, including other requests, because sli_5m has no run dimension.
    slo_expected = query(f"""SELECT cast(window(time, '5 minutes').start AS STRING) AS bucket,
      count(*) AS total, count_if(NOT {ERROR}) AS good FROM IDENTIFIER(:spans)
      WHERE service_name = :app AND kind ILIKE '%server%' AND {KIND} = 'real' AND {ROUTE} LIKE '/c/%'
        AND time >= :bucket_start::timestamp
        AND time < :bucket_end::timestamp GROUP BY 1""")

    def bucket_values(rows):
        result = {}
        for row in rows:
            if row["bucket"] in result:
                raise ValueError("duplicate SLI bucket or revision")
            result[row["bucket"]] = [int(row["good"]), int(row["total"])]
        return result

    optional(
        "sli_5m",
        """SELECT cast(b.bucket AS STRING) AS bucket, b.good, b.total
      FROM IDENTIFIER(:sli_5m) b JOIN IDENTIFIER(:slo_specs) s USING (workspace_id, name, slo, revision)
      WHERE b.workspace_id = :ws AND b.name = :app AND b.slo = :slo
        AND b.bucket >= :bucket_start::timestamp
        AND b.bucket < :bucket_end::timestamp""",
        lambda rows: [
            check("SLI good/total per bucket", bucket_values(slo_expected), bucket_values(rows))
        ],
        job="slo_eval",
    )
    for product, prerequisite, job in (
        ("events", "v_events exact counts", JOB_GOLD),
        ("funnels", "v_funnels", JOB_GOLD),
        ("slo", "sli_5m", "slo_eval"),
    ):
        if any(c["name"] == prerequisite and c["status"] == "SKIP" for c in checks):
            checks.append(pending(f"monitor API {product}", job_hint(job, args)))
            continue
        try:
            data = client.api(f"/api/apps/{APP}/{product}")
            if product == "events":
                actual = Counter()
                for row in data["events"]:
                    if row["event_name"] in report["expected"]["events"]:
                        actual[row["event_name"]] += int(row["events"])
                checks.append(
                    check("monitor API event counts", report["expected"]["events"], dict(actual))
                )
            elif product == "funnels":
                checks.extend(
                    {**c, "name": "monitor API " + c["name"]}
                    for c in funnel_checks(
                        [r for r in data["steps"] if r["funnel"] == params["funnel"]]
                    )
                )
            else:
                totals = query("""SELECT cast(date(b.bucket) AS STRING) AS bucket,
                  sum(b.good) AS good, sum(b.total) AS total FROM IDENTIFIER(:sli_5m) b
                  JOIN IDENTIFIER(:slo_specs) s USING (workspace_id, name, slo, revision)
                  WHERE b.workspace_id = :ws AND b.name = :app AND b.slo = :slo
                    AND b.bucket >= timestampadd(DAY, -s.window_days, now()) GROUP BY 1""")
                rows = [
                    {**r, "bucket": r["date"]} for r in data["series"] if r["slo"] == params["slo"]
                ]
                checks.append(
                    check(
                        "monitor API SLI daily good/total",
                        bucket_values(totals),
                        bucket_values(rows),
                    )
                )
        except Exception as exc:  # noqa: BLE001 — retain failures from each independent API
            checks.append(
                check(
                    f"monitor API {product}",
                    "valid measurements",
                    type(exc).__name__,
                    detail=str(exc),
                )
            )
    checks.append(
        check(
            "monitor observed health 503 window",
            True,
            report.get("health_seen_503", False),
            detail="Requires /monitor/health probing; /healthz is intercepted by the platform.",
        )
    )
    browser = report.get("browser", {})
    if browser.get("status") == "driven":
        optional(
            "browser RUM daily",
            """SELECT sum(page_views) AS views, sum(js_errors) AS errors
          FROM IDENTIFIER(:v_rum_daily) WHERE name = :app AND workspace_id = :ws
            AND route = :route AND date BETWEEN date(:start::timestamp) AND date(:end::timestamp)
          HAVING sum(page_views) > 0 OR sum(js_errors) > 0""",
            lambda rows: [
                check(
                    "browser pushState view and JS error",
                    True,
                    int(rows[0]["views"] or 0) >= 1 and int(rows[0]["errors"] or 0) >= 1,
                )
            ],
            route=browser["route"],
        )
    else:
        checks.append(
            pending(
                "browser RUM",
                browser.get(
                    "detail", "Open the app in a real browser; follow docs/CONFORMANCE.md."
                ),
                "MANUAL",
            )
        )
    return checks


def save_report(path, report):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(report_json(report))
    temporary.replace(path)


def sleep_progress(seconds, message):
    deadline = time.monotonic() + seconds
    while (remaining := deadline - time.monotonic()) > 0:
        print(f"{message}: {math.ceil(remaining)}s remaining", flush=True)
        time.sleep(min(30, remaining))


def browser_drive(client, run_id):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "status": "manual",
            "detail": "Playwright unavailable. Follow the browser RUM procedure in docs/CONFORMANCE.md; do not substitute an HTTP POST.",
        }
    route = f"/conformance-route/{run_id}"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            context = browser.new_context()
            # Bind credentials only to this origin; never send them to redirect targets.
            origin = client.args.conformance_url.rstrip("/")

            def authenticate(route_request):
                request = route_request.request
                if request.url.startswith(origin + "/"):
                    route_request.continue_(
                        headers={**request.headers, **client.w.config.authenticate()}
                    )
                else:
                    route_request.abort()

            context.route("**/*", authenticate)
            page = context.new_page()
            page.goto(origin + "/?" + urlencode({"run": run_id}), wait_until="networkidle")
            page.wait_for_timeout(12000)
            page.goto("about:blank")  # pagehide flushes the browser's pending events.
            context.close()
        finally:
            browser.close()
    return {"status": "driven", "route": route}


def drive(client, args, report):
    run_id = report["run_id"]
    client.api(
        f"/api/apps/{APP}/funnels/{event_name(run_id, 'funnel')}",
        method="PUT",
        body={"steps": [event_name(run_id, step) for step, _ in FUNNEL]},
    )
    client.api(
        f"/api/apps/{APP}/slo",
        method="PUT",
        body={
            "slo": f"val-{run_id}",
            "sli": "availability",
            "target": 0.99,
            "route_filter": "/c/%",
        },
    )
    report["started_at"] = utcnow()
    save_report(args.report, report)

    health_down = False
    try:
        for item in report["plan"]:
            sleep_progress(item["delay_before_s"], f"Waiting before {item['group']}")
            if item["group"] == "health_up":
                series = client.api(f"/api/apps/{APP}").get("series", [])
                down_since = next(
                    r["at"] for r in report["responses"] if r["group"] == "health_probe_down"
                )
                since = datetime.fromisoformat(down_since).timestamp()
                report["health_seen_503"] = any(
                    p[0] >= since and not p[1] and int(p[2]) == 503 for p in series
                )
            headers = {
                "x-request-id": item["rid"],
                "x-forwarded-email": item["user"],
                "Cookie": f"monitor_session={item['session']}",
            }
            if item["kind"] != "real":
                headers["x-monitor-synthetic"] = item["kind"]
            # Record intention before sending: a lost response must not cause replay.
            report["in_flight"] = item["rid"]
            save_report(args.report, report)
            if item["group"] == "health_down":
                health_down = True
            started = time.perf_counter()
            status, body, _ = client.http(
                args.conformance_url,
                item["path"],
                method=item["method"],
                query=item["query"],
                body=item["body"],
                headers=headers,
            )
            record = {
                "rid": item["rid"],
                "group": item["group"],
                "status": status,
                "at": utcnow(),
                "ms": round((time.perf_counter() - started) * 1000, 3),
            }
            if item["group"] in {"health_probe_down", "health_probe_up"}:
                record["body"] = body
            report["responses"].append(record)
            report["drive_checks"].append(check(f"HTTP {item['rid']}", item["status"], status))
            report.pop("in_flight")
            if item["group"] == "health_up" and status == 200:
                health_down = False
            save_report(args.report, report)
        report["finished_at"] = utcnow()
    finally:
        if health_down:
            client.http(
                args.conformance_url,
                "/c/health-toggle",
                method="POST",
                query={"ok": 1},
                headers={"x-monitor-synthetic": "probe", "x-request-id": f"cleanup-{run_id}"},
            )
    try:
        report["browser"] = browser_drive(client, run_id)
    except Exception as exc:  # noqa: BLE001 — missing browser binaries are an explicit manual check
        report["browser"] = {
            "status": "manual",
            "detail": f"Browser unavailable ({type(exc).__name__}); follow docs/CONFORMANCE.md.",
        }
    save_report(args.report, report)


def poll_until(fn, seconds, description):
    deadline = time.monotonic() + seconds
    while True:
        value = fn()
        if value:
            return value
        if time.monotonic() >= deadline:
            return None
        print(f"Waiting for {description}", flush=True)
        time.sleep(min(15, max(0, deadline - time.monotonic())))


def lifecycle_counts(rows):
    return dict(Counter(f"{r['state']}/muted={str(truth(r['muted'])).lower()}" for r in rows))


def evaluate_webhook_evidence(report, evidence):
    """Receiver export supplies coverage as well as deliveries: an empty file proves nothing."""
    checks = [
        check("webhook evidence run", report["run_id"], evidence.get("run_id")),
        check("webhook receiver identified", True, bool(evidence.get("receiver"))),
    ]
    windows = evidence.get("windows", {})
    for label, muted in (("alert lifecycle + monitor restart", False), ("muted lifecycle", True)):
        operation = report.get("operations", {}).get(label, {})
        observed = windows.get(label, {})
        coverage = False
        try:
            coverage = datetime.fromisoformat(observed["since"]) <= datetime.fromisoformat(
                operation["since"]
            ) and datetime.fromisoformat(observed["until"]) >= datetime.fromisoformat(
                operation["until"]
            )
        except (ValueError, KeyError, TypeError):
            pass
        deliveries = observed.get("alerts")
        checks.append(
            check(f"webhook {label} coverage", True, coverage and isinstance(deliveries, list))
        )
        rows = [
            r for r in deliveries or [] if r.get("app") == APP and r.get("rule") == "app_stopped"
        ]
        checks.append(
            check(
                f"webhook {label} deliveries",
                {} if muted else {"firing/muted=false": 1, "resolved/muted=false": 1},
                lifecycle_counts(rows),
            )
        )
    return checks


def exercise_operations(client, args, report):
    """Explicitly selected disruptive checks; recovery intent is persisted before each change."""
    checks, timeout = [], max(180, args.wait_minutes * 60)
    config_path = f"/api/apps/{APP}/product-config"
    original = client.api(config_path)
    restore = {
        "outcome_event": original.get("outcome_event") or "",
        "token_budget_day": int(original.get("token_budget_day") or 0),
    }
    report["operations"] = {"restore_product_config": restore, "started_at": utcnow()}
    save_report(args.report, report)
    try:
        client.api(config_path, method="PUT", body={**restore, "token_budget_day": 1})
        print("Tiny token budget set. " + job_hint(JOB_GOLD, args), flush=True)
        blocked = poll_until(
            lambda: client.api(f"/api/policy/{APP}").get("throttle") == "block",
            timeout,
            "hourly token evaluation and monitor policy refresh",
        )
        if blocked:
            started = time.monotonic()
            attempts = report["operations"]["policy_attempts"] = []

            def budget_rejected():
                rid = f"policy-{report['run_id']}-{len(attempts) + 1}"
                code, body, _ = client.http(
                    args.conformance_url,
                    "/c/budget",
                    headers={
                        "x-monitor-synthetic": "journey",
                        "x-request-id": rid,
                    },
                )
                attempts.append({"rid": rid, "status": code, "at": utcnow()})
                save_report(args.report, report)
                return code == 429 and body == {"error": "budget exceeded"}

            rejected = poll_until(budget_rejected, 75, "SDK policy cache (60s)")
            checks.append(
                check(
                    "K7 policy block returns 429 within refresh window",
                    True,
                    bool(rejected),
                    detail=f"Observed after {time.monotonic() - started:.1f}s; allowance 75s.",
                )
            )
        else:
            checks.append(
                pending("K7 policy block", "No block policy yet. " + job_hint(JOB_GOLD, args))
            )
    finally:
        client.api(config_path, method="PUT", body=restore)
        report["operations"]["product_config_restored"] = True
        save_report(args.report, report)
        print(
            "Budget setting restored; rerun inventory_scan to recompute the cached throttle.",
            flush=True,
        )

    table = qualified_table(args.catalog, args.schema, "alert_events")

    def transitions(since):
        return client.sql(
            """SELECT state, muted FROM IDENTIFIER(:table)
          WHERE workspace_id = :ws AND app = :app AND rule = 'app_stopped' AND source = 'monitor'
            AND ts >= :since::timestamp ORDER BY ts""",
            table=table,
            ws=client.ws,
            app=APP,
            since=since,
        )

    def control(name, action):
        client.w.api_client.do("POST", f"/api/2.0/apps/{name}/{action}")

    def compute_state(name):
        status = client.w.apps.get(name).compute_status
        return status.state.value if status and status.state else None

    def ensure_started(name):
        if compute_state(name) == "STOPPING" and not poll_until(
            lambda: compute_state(name) == "STOPPED", timeout, name + " shutdown"
        ):
            raise TimeoutError(f"{name} did not stop; recovery start required")
        if compute_state(name) not in {"ACTIVE", "STARTING"}:
            control(name, "start")

    def healthy(name):
        info = client.api(f"/api/apps/{name}")
        return info.get("app_state") == "RUNNING" and info.get("compute_state") == "ACTIVE"

    if not healthy(APP):
        checks.append(check("alert lifecycle precondition", "RUNNING/ACTIVE", "app is not running"))
        return checks
    for muted in (False, True):
        mute_id, since = None, utcnow()
        label = "muted lifecycle" if muted else "alert lifecycle + monitor restart"
        report["operations"][label] = {
            "since": since,
            "recover": f"start {APP} and {args.monitor_app_name}",
        }
        save_report(args.report, report)
        try:
            if muted:
                ends = datetime.now(timezone.utc) + timedelta(seconds=3 * timeout + 600)
                mute_id = client.api(
                    "/api/actions/mute",
                    method="POST",
                    body={
                        "app": APP,
                        "rule": "app_stopped",
                        "ends_at": ends.isoformat(),
                        "reason": f"conformance {report['run_id']}",
                    },
                )["id"]
                report["operations"][label]["mute_id"] = mute_id
                save_report(args.report, report)
            control(APP, "stop")
            fired = poll_until(
                lambda since=since: any(r["state"] == "firing" for r in transitions(since)),
                timeout,
                label + " firing",
            )
            if not fired:
                checks.append(check(label, "one firing", "timeout"))
                continue
            if not muted:
                try:
                    control(args.monitor_app_name, "stop")
                    if not poll_until(
                        lambda: compute_state(args.monitor_app_name) == "STOPPED",
                        timeout,
                        "monitor shutdown",
                    ):
                        raise TimeoutError("monitor did not stop")
                finally:
                    ensure_started(args.monitor_app_name)

                def monitor_ready():
                    try:
                        return bool(client.api("/api/fleet"))
                    except (RuntimeError, OSError):
                        return False

                if not poll_until(monitor_ready, timeout, "monitor restart"):
                    checks.append(check("monitor restart", "reachable", "timeout"))
                    continue
                sleep_progress(150, "Observe stopped state after monitor restart")
                checks.append(
                    check(
                        "no duplicate firing after monitor restart",
                        {"firing/muted=false": 1},
                        lifecycle_counts(transitions(since)),
                    )
                )
            control(APP, "start")
            poll_until(
                lambda since=since: any(r["state"] == "resolved" for r in transitions(since)),
                timeout,
                label + " resolution",
            )
            sleep_progress(150, "Observe stable resolved state")
            rows = transitions(since)
            checks.append(
                check(
                    label,
                    {
                        f"firing/muted={str(muted).lower()}": 1,
                        f"resolved/muted={str(muted).lower()}": 1,
                    },
                    lifecycle_counts(rows),
                )
            )
            report["operations"][label]["until"] = utcnow()
            report["operations"][label]["transitions"] = rows
        finally:
            try:
                ensure_started(APP)
            finally:
                try:
                    if mute_id:
                        client.api(f"/api/actions/mute/{mute_id}", method="DELETE")
                finally:
                    save_report(args.report, report)
    return checks


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("profile", "catalog", "schema", "monitor-url", "conformance-url", "warehouse-id"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument(
        "--run-id", help="1-32 safe characters; default UTC timestamp (or saved report for verify)"
    )
    parser.add_argument("--phase", choices=("drive", "verify", "all"), default="all")
    parser.add_argument("--wait-minutes", type=float, default=15)
    parser.add_argument("--report", type=Path, default=Path("out.json"))
    parser.add_argument(
        "--exercise-ops",
        action="store_true",
        help="Temporarily set a token budget, stop/start the fixture, restart the monitor and exercise a mute",
    )
    parser.add_argument("--monitor-app-name", default="apps-monitor")
    parser.add_argument(
        "--webhook-evidence",
        type=Path,
        help="Receiver export with coverage windows and alert payloads; see CONFORMANCE.md",
    )
    args = parser.parse_args(argv)
    if not math.isfinite(args.wait_minutes) or args.wait_minutes < 0:
        parser.error("wait-minutes must be finite and nonnegative")
    for url in (args.monitor_url, args.conformance_url):
        parts = urlsplit(url)
        if (
            parts.scheme != "https"
            or not parts.netloc
            or parts.username
            or parts.password
            or parts.query
            or parts.fragment
            or parts.path not in {"", "/"}
        ):
            parser.error(
                "app URLs must be HTTPS origins without credentials, paths, query or fragment"
            )
    if not re.fullmatch(r"[a-z0-9-]{1,30}", args.monitor_app_name):
        parser.error("invalid monitor app name")
    if args.run_id:
        validate_run_id(args.run_id)
    return args


def main(argv=None):
    args = parse_args(argv)
    target = {
        key: getattr(args, key)
        for key in (
            "profile",
            "catalog",
            "schema",
            "monitor_url",
            "conformance_url",
            "warehouse_id",
        )
    }
    if args.phase == "verify":
        report = json.loads(args.report.read_text())
        if target != report["target"] or (args.run_id and args.run_id != report["run_id"]):
            raise ValueError("report target/run-id mismatch; refusing to mix workspaces or runs")
        if "finished_at" not in report or len(report["responses"]) != len(report["plan"]):
            raise ValueError("drive was incomplete; keep its evidence and use a new run-id/report")
        if report["plan"] != make_plan(report["run_id"]) or report["expected"] != expected_values(
            report["plan"]
        ):
            raise ValueError("saved plan/expectations differ from this validator version")
    else:
        if args.report.exists():
            raise ValueError("report already exists; use --phase verify or a new report and run-id")
        run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        plan = make_plan(run_id)
        report = {
            "version": 1,
            "run_id": run_id,
            "target": target,
            "plan": plan,
            "expected": expected_values(plan),
            "responses": [],
            "drive_checks": [],
            "checks": [],
        }
    try:
        client = LiveClient(args)
        if args.phase == "verify" and client.ws != report["workspace_id"]:
            raise ValueError("profile now points to a different workspace")
        report["workspace_id"] = client.ws
        if args.phase != "verify":
            existing = client.sql(
                f"""SELECT count(*) AS n FROM IDENTIFIER(:spans)
              WHERE service_name = :app AND {RID} IN (SELECT explode(from_json(:ids, 'ARRAY<STRING>')))""",
                spans=qualified_table(args.catalog, args.schema, "otel_spans"),
                app=APP,
                ids=json.dumps([p["rid"] for p in report["plan"]]),
            )
            if int(existing[0]["n"]):
                raise ValueError("run-id already has telemetry; never replay a plan")
            if client.api(f"/api/policy/{APP}").get("throttle") == "block":
                raise ValueError(
                    "clear the existing budget policy before driving deterministic LLM calls"
                )
            drive(client, args, report)
        if args.phase != "drive":
            elapsed = (
                datetime.now(timezone.utc).timestamp()
                - datetime.fromisoformat(report["finished_at"]).timestamp()
            )
            sleep_progress(max(0, args.wait_minutes * 60 - elapsed), "Telemetry landing window")
            report["checks"] = verify_data(client, args, report)
            if args.exercise_ops:
                report["operations_checks"] = exercise_operations(client, args, report)
            if report.get("operations_checks"):
                report["checks"].extend(report["operations_checks"])
                if args.webhook_evidence:
                    report["checks"].extend(
                        evaluate_webhook_evidence(
                            report, json.loads(args.webhook_evidence.read_text())
                        )
                    )
                else:
                    report["checks"].append(
                        pending(
                            "mute webhook suppression",
                            "Export receiver coverage and deliveries for the operations windows; pass --webhook-evidence FILE on the next verify. See docs/CONFORMANCE.md.",
                            "MANUAL",
                        )
                    )
            else:
                for name in (
                    "K7 policy block",
                    "alert lifecycle + restart dedup",
                    "mute persistence and webhook suppression",
                ):
                    report["checks"].append(
                        pending(
                            name,
                            "Run --phase verify --exercise-ops in an isolated validation workspace; see docs/CONFORMANCE.md.",
                        )
                    )
    except Exception as exc:  # noqa: BLE001 — preserve partial evidence and return nonzero
        report.setdefault("checks", []).append(
            check("harness execution", "completed", type(exc).__name__, detail=str(exc))
        )
    all_checks = report["drive_checks"] + report["checks"]
    report["status"] = (
        "failed"
        if exit_code(all_checks) == 1
        else "driven"
        if args.phase == "drive"
        else "incomplete"
        if exit_code(all_checks) == 2
        else "passed"
    )
    save_report(args.report, report)
    print(summary_table(all_checks))
    print(f"Report: {args.report} ({report['status']})")
    return exit_code(all_checks)


if __name__ == "__main__":
    raise SystemExit(main())
