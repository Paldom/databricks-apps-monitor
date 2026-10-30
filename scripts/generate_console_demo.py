"""Extend the approved V1 fixture deterministically; keep deep data outside the snapshot."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app/static/console"


def leaderboard_score(row):
    """Offline equivalent of the service formula, checked against it in tests."""
    weights = {
        "availability": 25,
        "errors": 20,
        "latency": 15,
        "scan": 15,
        "review": 10,
        "cost": 10,
        "adoption": 5,
    }
    raw = {
        "availability": row["availability_pct"],
        "errors": 100 - row["error_pct"] if row["error_pct"] is not None else None,
        "latency": 100 * row["latency_budget_ms"] / row["p95_ms"] if row["p95_ms"] else None,
        "scan": row["scan_score"],
        "review": row["review_score"],
        "cost": 100 * (1 - row["cost_growth"]) if row["cost_growth"] is not None else None,
        "adoption": row["users"],
    }
    components = {k: max(0, min(100, v)) if v is not None else None for k, v in raw.items()}
    coverage = sum(weights[k] for k, v in components.items() if v is not None)
    score = sum(weights[k] * v for k, v in components.items() if v is not None)
    return {
        "score": round(score / coverage, 2) if coverage else None,
        "coverage_pct": coverage,
        "components": components,
    }


def weekly_growth(daily):
    if len(daily) < 14 or any(v is None for v in daily[-14:]):
        return None
    previous = sum(daily[-14:-7])
    return sum(daily[-7:]) / previous - 1 if previous else None


def main():
    spec = importlib.util.spec_from_file_location("topology", ROOT / "app/console_topology.py")
    topology = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(topology)
    data = json.loads(
        (STATIC / "demo-data.js")
        .read_text()
        .removeprefix("window.MOCK = ")
        .strip()
        .removesuffix(";")
    )
    fixtures, observed = {}, []
    date = "2026-10-30T09:27:00Z"
    all_resources = [
        {"name": "warehouse", "sql_warehouse": {"id": "wh-7d1a", "permission": "CAN_USE"}},
        {"name": "model", "serving_endpoint": {"name": "claims-model", "permission": "CAN_QUERY"}},
        {"name": "refresh", "job": {"id": "101", "permission": "CAN_MANAGE_RUN"}},
        {"name": "traces", "experiment": {"experiment_id": "201", "permission": "CAN_EDIT"}},
        {
            "name": "risk-store",
            "database": {"instance_name": "risk-db", "permission": "CAN_CONNECT_AND_CREATE"},
        },
        {"name": "claims-store", "postgres": {"database": "claims-db", "branch": "production"}},
        {
            "name": "documents",
            "uc_securable": {
                "securable_full_name": "demo.claims.documents",
                "securable_type": "TABLE",
            },
        },
        {"name": "credentials", "secret": {"scope": "app-secrets", "key": "api-key"}},
        {"name": "analytics", "genie_space": {"id": "genie-demo"}},
        {
            "name": "intake",
            "app": {
                "name": "doc-intake",
                "url": next(a["url"] for a in data["apps"] if a["name"] == "doc-intake"),
                "permission": "CAN_USE",
            },
        },
    ]
    for i, a in enumerate(data["apps"]):
        name = a["name"]
        base = "api/apps/" + name
        stopped = a["health"] == "stopped"
        a["workspace_id"] = next(w["id"] for w in data["workspaces"] if w["name"] == a["workspace"])
        a["description"] = "Demo " + a["kind"] + " for " + a["team"] + "."
        a["tags"] = (
            {}
            if name == "label-studio-lite"
            else {
                "team": a["team"],
                "cost_center": a["cost_center"],
                "env": "prod" if i < 9 else "dev",
                "tier": "t1",
            }
        )
        a["resources"] = (
            all_resources
            if i == 0
            else [all_resources[0], all_resources[4]]
            if i == 3
            else [all_resources[i % len(all_resources)]]
        )
        a["probe"] = {
            "uptime_24h": a["last24h"]["uptime_pct"],
            "p95_ms": None if stopped else 180 + i * 9,
            "error_rate_1h": None if stopped else 100 if i == 3 else 0,
            "checks_24h": 0 if stopped else 1440,
        }
        a["usage_7d"] = {
            "peak_dau": a["last24h"]["active_users"],
            "requests_7d": a["last24h"]["requests"] * 7,
            "sessions_7d": a["last24h"]["active_users"] * 12,
        }
        a["cost_7d"] = {
            "usd_7d": round(a["cost"]["dbu_usd"] * 7 / 30, 2),
            "ai_calls_7d": (a["genai"] or {}).get("calls_24h", 0) * 7,
            "tokens_7d": (a["genai"] or {}).get("input_tokens_24h", 0) * 7,
        }
        packages = [
            {
                "name": "example-python",
                "eco": "pypi",
                "version": "1.0.0",
                "latest": "2.0.0",
                "behind": "major",
                "vulns": ["DEMO-CVE-001"] if i == 3 else [],
            },
            {
                "name": "example-web",
                "eco": "npm",
                "version": "3.1.0",
                "latest": "3.1.1",
                "behind": "patch",
                "vulns": [],
            },
        ]
        a["scan"] = {
            "name": name,
            "quality_score": a["security"]["quality_score"],
            "findings_critical": a["security"]["cve"]["critical"],
            "findings_high": a["security"]["cve"]["high"],
            "findings_medium": 2,
            "findings_low": 1,
            "files": 14 + i,
            "py_loc": 1200 + i * 100,
            "deps": 12,
            "deps_pinned": 10,
            "freshness_score": 76,
            "has_tests": True,
            "has_readme": True,
            "scanned_at": date,
            "deployment_id": "demo-deploy-" + str(i),
            "deps_json": json.dumps(packages),
            "policy_violations": 0,
        }
        a["review"] = {
            "name": name,
            "verdict": a["security"]["review_verdict"],
            "score_overall": a.get("review", {}).get(
                "score_overall", round(a["security"]["review_score"] / 10, 1)
            ),
            "summary": "Demo advisory: review dependency freshness and retry limits.",
            "model": "demo-reviewer",
            "reviewed_at": date,
            "files_reviewed": 14,
            "input_tokens": 1200,
            "output_tokens": 240,
            "strengths_json": '["Clear request boundaries", "Tested business logic"]',
            "findings_json": '[{"severity":"medium","area":"reliability","title":"Bound retries","recommendation":"Set a retry budget."}]',
            **dict.fromkeys(
                [
                    "score_security",
                    "score_reliability",
                    "score_maintainability",
                    "score_cost",
                    "score_monitoring",
                ],
                8,
            ),
        }
        a["security"]["review_score"] = a["review"]["score_overall"]
        tid = (
            "0af7651916cd43dd8448eb211c80319c"
            if i == 0
            else "4bf92f3577b34da6a3ce929d0e0e4736"
            if i == 3
            else f"{i + 100:032x}"
        )
        trace = json.loads(json.dumps(data["trace_example"]))
        if i != 0:
            trace.update(trace_id=tid, app=name, root="GET /api/report")
            for span in trace["spans"]:
                span["service"] = name
        fixtures["api/console/trace/" + tid] = trace
        trace_rows = (
            []
            if stopped
            else [
                {
                    "trace_id": tid,
                    "name": trace["root"],
                    "route": "/api/report",
                    "duration_ms": trace["duration_ms"],
                    "status": trace["status"],
                    "time": date,
                }
            ]
        )
        log_rows = (
            []
            if stopped
            else [
                {"time": date, "severity": level, "body": text, "trace_id": tid}
                for level, text in [
                    ("INFO", "Request received"),
                    ("WARN", "Retry budget almost exhausted"),
                    ("ERROR", "Demo dependency timeout; request failed"),
                ]
            ]
        )
        fixtures[base + "/logs"] = {"logs": log_rows}
        fixtures[base + "/errors"] = {
            "groups": []
            if stopped
            else [
                {
                    "fingerprint": "demo-" + str(i),
                    "occurrences": 12 + i,
                    "first_seen": date,
                    "last_seen": date,
                    "sample": "Demo dependency timeout",
                }
            ],
            "failed_requests": trace_rows,
            "error_logs": log_rows[-1:],
        }
        fixtures[base + "/traces"] = {"traces": trace_rows}
        agent_id = "tr-demo-" + str(i)
        fixtures[base + "/agent-traces"] = {
            "experiment": "201" if a["genai"] else None,
            "traces": [
                {
                    "trace_id": agent_id,
                    "request_time": date,
                    "duration_ms": 6420,
                    "state": "ERROR",
                    "preview": "Check claim coverage",
                    "response_preview": "Retry suggested",
                    "client_request_id": "demo-request",
                    "tags": {"agent": "coverage"},
                }
            ]
            if a["genai"]
            else [],
        }
        origin = 1793352420000000000
        fixtures[base + "/agent-traces/" + agent_id] = {
            "mlflow": {
                "info": {
                    "state": "ERROR",
                    "preview": "Check claim coverage",
                    "response_preview": "Retry suggested",
                }
            },
            "client_request_id": "demo-request",
            "mlflow_url": "https://workspace.invalid/ml/experiments/201/traces?selectedTraceId="
            + agent_id,
            "otel_spans": [
                {
                    "span_id": s["id"],
                    "parent_span_id": s["parent"],
                    "name": s["name"],
                    "service_name": s["service"],
                    "span_type": s["kind"],
                    "status": s["status"],
                    "attributes": s["attrs"],
                    "start_time_unix_nano": str(origin + int(s["start_ms"] * 1e6)),
                    "end_time_unix_nano": str(
                        origin + int((s["start_ms"] + s["duration_ms"]) * 1e6)
                    ),
                    "in_tokens": s["attrs"].get("gen_ai.usage.input_tokens"),
                    "out_tokens": s["attrs"].get("gen_ai.usage.output_tokens"),
                }
                for s in trace["spans"]
            ],
            "logs": log_rows,
        }
        timeline = (
            []
            if stopped
            else [
                {
                    "ts": h,
                    "requests": a["series_24h"]["requests"][j],
                    "errors": round(
                        a["series_24h"]["requests"][j] * a["series_24h"]["error_rate_pct"][j] / 100
                    ),
                    "p50_ms": a["last24h"]["p50_ms"],
                    "p95_ms": a["series_24h"]["p95_ms"][j],
                }
                for j, h in enumerate(a["series_24h"]["hours"])
                if a["series_24h"]["requests"][j] is not None
            ]
        )
        fixtures[base + "/requests"] = {
            "timeline": timeline,
            "routes": []
            if stopped
            else [
                {
                    "route": "/api/report",
                    "requests": 100,
                    "errors": 3,
                    "avg_ms": 310,
                    "p50_ms": 200,
                    "p95_ms": 900,
                }
            ],
        }
        deps = (
            []
            if stopped
            else [
                {
                    "dependency": "databricks_sql/wh-7d1a",
                    "calls": 1200 + i * 20,
                    "avg_ms": 150,
                    "p95_ms": 560,
                    "errors": i,
                }
            ]
        )
        if i == 0:
            deps.extend(
                [
                    {
                        "dependency": "https://doc-intake-1008.aws.databricksapps.com/api/policies",
                        "calls": 420,
                        "avg_ms": 600,
                        "p95_ms": 2900,
                        "errors": 4,
                    },
                    {
                        "dependency": "https://workspace.invalid/serving-endpoints/claims-model/invocations",
                        "calls": 800,
                        "avg_ms": 1100,
                        "p95_ms": 2300,
                        "errors": 15,
                    },
                    {
                        "dependency": "api.example.invalid",
                        "calls": 70,
                        "avg_ms": 100,
                        "p95_ms": 180,
                        "errors": 0,
                    },
                ]
            )
        fixtures[base + "/deps"] = {"deps": deps}
        observed.extend({**r, "name": name, "workspace_id": a["workspace_id"]} for r in deps)
        releases = [
            {
                "deployment_id": "demo-current",
                "start_ts": date,
                "requests": 100,
                "p95_ms": 1200,
                "error_pct": 3,
                "tokens": 8000,
            },
            {
                "deployment_id": "demo-previous",
                "start_ts": "2026-10-28T10:00:00Z",
                "requests": 800,
                "p95_ms": 600,
                "error_pct": 0,
                "tokens": 40000,
            },
        ]
        fixtures[base + "/timeline"] = {
            "events": [
                {
                    "ts": date,
                    "type": "deploy",
                    "state": "SUCCEEDED",
                    "rule": "deployment",
                    "severity": "info",
                    "message": "Demo release",
                }
            ],
            "releases": releases,
        }
        fixtures[base + "/security"] = {
            "scan": a["scan"],
            "findings": [
                {
                    "severity": "medium",
                    "kind": "dependency",
                    "title": "Package update available",
                    "detail": "Demo finding",
                    "file": "requirements.txt",
                    "line": 2,
                }
            ],
        }
        fixtures[base + "/review"] = {
            "review": a["review"],
            "overview": {
                "purpose": a["description"],
                "tech_stack": ["Python", "FastAPI", "Node"],
                "endpoints": ["GET /api/report", "GET /healthz"],
            },
        }
        cfg = {
            "tags_json": json.dumps(a["tags"]),
            "budget_usd_month": a["cost"]["budget_usd_month"],
            "auto_stop": a["governance"]["auto_stop"],
            "idle_hours": 24,
            "capacity_path": "/monitor/capacity",
            "updated_at": date,
            "updated_by": "demo-operator",
        }
        daily = [
            {
                "date": day,
                "dbus": 0.5,
                "dbu_usd": value,
                "ai_calls": 20 if a["genai"] else 0,
                "ai_input_tokens": 1200 if a["genai"] else 0,
                "ai_output_tokens": 200 if a["genai"] else 0,
            }
            for day, value in zip(data["cost"]["days"], a["cost"]["daily_30d"], strict=True)
        ]
        fixtures[base + "/cost"] = {
            "daily": daily,
            "forecast": {"forecast_30d_usd": a["cost"]["forecast_usd_month"], "days_observed": 30},
            "budget": cfg["budget_usd_month"],
            "mtd_usd": a["cost"]["dbu_usd"],
        }
        units = {
            "name": name,
            "dbu_usd": a["cost"]["dbu_usd"],
            "ai_usd": a["cost"]["ai_usd"],
            "total_usd": a["cost"]["mtd_usd"],
            "idle_usd": a["cost"]["idle_usd"],
            "usd_per_1k_requests": a["cost"]["usd_per_1k_requests"],
            "usd_per_session": 0.02,
            "usd_per_user": 0.1,
            "usd_per_outcome": 0.05,
            "completions": 100,
            "unpriced_days": 0,
        }
        fixtures[base + "/unit-economics"] = {"days": 30, "apps": [units]}
        fixtures[base + "/genai"] = {
            "daily": [
                {
                    "date": d["date"],
                    "model": "claims-model",
                    "calls": d["ai_calls"],
                    "input_tokens": d["ai_input_tokens"],
                    "output_tokens": d["ai_output_tokens"],
                    "errors": 1,
                    "p95_ms": 900,
                }
                for d in daily
            ]
            if a["genai"]
            else [],
            "top": [
                {
                    "session_id": "hashed-session",
                    "user_hash": "hashed-user",
                    "calls": 10,
                    "tokens": 4000,
                    "last_call": date,
                }
            ]
            if a["genai"]
            else [],
            "error_taxonomy": [
                {"category": "rate_limit", "errors": 3, "last_seen": date, "sample": "429 upstream"}
            ]
            if a["genai"]
            else [],
            "agent_steps": [
                {"date": "2026-10-29", "avg_steps": 5, "max_steps": 8, "agent_runs": 32},
                {"date": "2026-10-30", "avg_steps": 7, "max_steps": 12, "agent_runs": 40},
            ]
            if a["genai"]
            else [],
            "quality": [
                {
                    "ts": date,
                    "relevance": 8,
                    "faithfulness": 7,
                    "toxicity": 0,
                    "traces_sampled": 10,
                    "comment": "Demo sampled evaluation",
                }
            ]
            if a["genai"]
            else [],
            "feedback": [{"date": "2026-10-30", "n": 10, "avg_rating": 4.2, "negative": 1}]
            if a["genai"]
            else [],
            "feedback_recent": [],
        }
        fixtures[base + "/drift"] = {
            "reports": [
                {
                    "week": "2026-10-26",
                    "samples": 60,
                    "k": 3,
                    "silhouette": 0.6,
                    "novel_share": 0.31,
                }
            ]
            if a["genai"]
            else []
        }
        fixtures[base + "/analytics"] = {
            "daily": []
            if stopped
            else [
                {
                    "date": d["date"],
                    "requests": 100,
                    "users": 20,
                    "sessions": 30,
                    "errors": 1,
                    "avg_ms": 200,
                }
                for d in daily[-7:]
            ],
            "users": []
            if stopped
            else [
                {
                    "user_hash": "u_demo_91a",
                    "first_seen": "2026-10-01",
                    "last_seen": date,
                    "requests": 80,
                    "sessions": 10,
                    "active_days": 7,
                    "errors": 1,
                    "tokens": 4000,
                }
            ],
            "mtd_usd": a["cost"]["dbu_usd"],
        }
        fixtures[base + "/events"] = {
            "events": []
            if stopped
            else [
                {
                    "event_name": "answer_shown",
                    "app_version": a["version"],
                    "events": 40,
                    "sessions": 32,
                    "last_seen": date,
                }
            ]
        }
        fixtures[base + "/funnels"] = {
            "specs": [{"funnel": "answer", "steps": ["ask_question", "answer_shown"]}],
            "steps": []
            if stopped
            else [
                {
                    "funnel": "answer",
                    "app_version": a["version"],
                    "step_name": step,
                    "sessions": 100 - j * 20,
                    "dropoff_pct": j * 20,
                }
                for j, step in enumerate(["ask_question", "answer_shown"])
            ],
        }
        fixtures[base + "/cohorts"] = {
            "cohorts": []
            if stopped
            else [
                {
                    "cohort_week": "2026-10-19",
                    "week_number": 1,
                    "cohort_size": 40,
                    "retained_users": 30,
                    "retention_pct": 75,
                    "partial_week": True,
                }
            ]
        }
        fixtures[base + "/rum"] = {
            "routes": []
            if stopped
            else [
                {
                    "date": "2026-10-30",
                    "route": "/",
                    "page_views": 200,
                    "p75_lcp": 650,
                    "p75_cls": 0.02,
                    "p75_inp": 80,
                    "js_errors": 1,
                    "fingerprint": "rum-demo",
                    "trace_id": tid,
                }
            ]
        }
        fixtures[base + "/guardrails"] = {
            "findings": [
                {
                    "ts": date,
                    "kind": "pii",
                    "severity": "warning",
                    "excerpt_masked": "[EMAIL]",
                    "excerpt_hash": "demo-hash",
                    "trace_id": agent_id,
                }
            ]
            if a["genai"]
            else [],
            "templates": [
                {
                    "date": "2026-10-30",
                    "template_hash": "template-demo",
                    "samples": 12,
                    "daily_samples": 40,
                    "share": 0.3,
                }
            ]
            if a["genai"]
            else [],
        }
        fixtures[base + "/product-config"] = {
            "outcome_event": "answer_shown",
            "token_budget_day": 100000,
            "throttle": "none",
            "tokens_today": 15000,
            "tokens_last_hour": 3000,
            "policy_updated_at": date,
        }
        fixtures[base + "/telemetry-health"] = {
            "health": None
            if stopped
            else {
                "quality": "healthy",
                "envelope_coverage": 0.9,
                "orphan_ratio_24h": 0.01,
                "sampler_ratio": 1,
                "last_span_at": date,
                "last_log_at": date,
                "last_metric_at": date,
                "semconv_legacy_only": 0,
                "semconv_stable_only": 0.1,
                "semconv_both": 0.9,
                "gateway_vs_otel_tokens": 12,
                "token_date": "2026-10-29",
            }
        }
        fixtures[base + "/slo"] = {
            "specs": [
                {
                    "slo": "availability",
                    "sli": "availability",
                    "target": 0.999,
                    "window_days": 28,
                    "budget_remaining_pct": a["slo"]["error_budget_remaining_pct"],
                    "observed_since": "2026-10-02",
                    "last_bucket": date,
                }
            ],
            "series": []
            if stopped
            else [
                {
                    "slo": "availability",
                    "date": "2026-10-" + str(j + 10),
                    "budget_remaining_pct": 100 - j * 20,
                }
                for j in range(7)
            ],
        }
        fixtures[base] = {
            **a["probe"],
            "compute_state": "STOPPED" if stopped else "ACTIVE",
            "last": None if stopped else {"code": 200, "ms": 120},
            "ttfb_ms": None if stopped else 110,
            "series": []
            if stopped
            else [
                [1793350800 + j * 60, j != 3, 200 if j != 3 else 502, 120 + j * 12]
                for j in range(8)
            ],
        }
        fixtures[base + "/synthetics"] = {
            "interval_s": 1800,
            "live": None
            if stopped
            else {
                "journey": "Report flow",
                "ok": i != 3,
                "budget_ms": 2500,
                "within_budget": i != 3,
                "ts": 1793352420,
                "steps": [
                    {
                        "name": "GET /api/report",
                        "ok": i != 3,
                        "code": 200 if i != 3 else 502,
                        "ms": 200,
                        "detail": "Demo assertion",
                    }
                ],
            },
            "browser": []
            if stopped
            else [
                {
                    "run_ts": date,
                    "journey": "browser-smoke",
                    "ok": i != 3,
                    "status_code": 200 if i != 3 else 502,
                    "latency_ms": 800,
                    "detail": "Demo browser result",
                    "vantage": "external",
                    "failure_stage": "http" if i == 3 else None,
                    "artifact": "/Volumes/demo/monitor/ui_tests/" + name + "/run",
                }
            ],
        }
        fixtures[base + "/ops"] = {
            "config": cfg,
            "resources": a["resources"],
            "deployments": [
                {
                    "create_time": date,
                    "deployment_id": "demo-current",
                    "state": "SUCCEEDED",
                    "mode": "SNAPSHOT",
                }
            ],
            "permissions": [
                {"principal": "operators", "principal_type": "group", "level": "CAN_MANAGE"}
            ],
            "audit": [
                {
                    "event_time": date,
                    "user": "demo-operator",
                    "action_name": "deploy",
                    "status_code": "200",
                }
            ],
            "telemetry_volume": [{"signal": "spans", "rows_24h": 0 if stopped else 320}],
            "job_health": [
                {"job_id": "101", "runs_7d": 7, "succeeded": 6, "avg_s": 60, "last_run": date}
            ],
            "capacity": None,
        }
    data["genie_url"] = None
    data["topology"] = topology.graph(data["apps"], observed)
    data["fleet_measures"] = {"real_p95_ms": 2300, "requests_24h": 320000, "probe_p95_ms": 270}
    data["maintenance_windows"][0]["id"] = "demo-mute"
    fixtures["api/actions/mute"] = {"mutes": data["maintenance_windows"]}
    fixtures["api/console/identity"] = {"actor": "demo-operator", "admin": True, "reason": ""}
    fixtures["api/alerts"] = {
        "active": [a for a in data["alerts"] if a["state"] == "firing"],
        "recent": [{**a, "ts": a["since"]} for a in data["alerts"]],
    }
    fixtures["api/governance"] = {
        "configs": [
            {"name": a["name"], **fixtures["api/apps/" + a["name"] + "/ops"]["config"]}
            for a in data["apps"]
        ],
        "mtd": [{"name": a["name"], "mtd_usd": a["cost"]["dbu_usd"]} for a in data["apps"]],
        "usage": [{"name": a["name"], **a["usage_7d"]} for a in data["apps"]],
        "telemetry_active": [a["name"] for a in data["apps"] if a["telemetry"]["otel_export"]],
        "chargeback": [
            {
                "team": a["team"],
                "cost_center": a["cost_center"],
                "apps": 1,
                "mtd_usd": a["cost"]["dbu_usd"],
                "mtd_tokens": 30000,
                "ai_calls": 1000,
            }
            for a in data["apps"]
        ],
        "audit": [
            {
                "event_time": e["ts"],
                "user": e["user"],
                "action_name": e["action"],
                "app": e["app"],
                "status_code": 200,
            }
            for e in data["governance"]["audit_events"]
        ],
    }
    fixtures["api/unit-economics"] = {
        "days": 30,
        "apps": [
            fixtures["api/apps/" + a["name"] + "/unit-economics"]["apps"][0] for a in data["apps"]
        ],
    }
    fixtures["api/leaderboard"] = {
        "formula": (
            "Weighted mean of available scores out of 100: availability 25%, errors 20%, "
            "latency 15%, scan 15%, review 10%, cost 10%, adoption 5%. "
            "Availability = probe uptime; errors = 100 - error percentage; "
            "latency = min(100, 100 * 2500 ms / p95); scan = scan quality; "
            "review = review score * 10; cost = clamp(100 * (1 - weekly cost growth)); "
            "adoption = min(100, active users). Missing evidence is excluded and "
            "weights renormalized. Stopped apps excluded. Demo adoption uses the "
            "snapshot active users; production uses distinct users in 7 days."
        ),
        "apps": [
            {
                "name": a["name"],
                **leaderboard_score(
                    {
                        "availability_pct": a["probe"]["uptime_24h"],
                        "error_pct": a["last24h"]["error_rate_pct"],
                        "p95_ms": a["last24h"]["p95_ms"],
                        "latency_budget_ms": 2500,
                        "scan_score": a["scan"]["quality_score"],
                        "review_score": a["review"]["score_overall"] * 10,
                        # Derive growth from the same displayed daily compute history.
                        "cost_growth": weekly_growth(a["cost"]["daily_30d"]),
                        "users": a["last24h"]["active_users"],
                    }
                ),
            }
            for a in data["apps"]
            if a["health"] != "stopped"
        ],
    }
    fixtures["api/model-prices"] = {
        "prices": [{**p, "effective_from": "2026-10-01"} for p in data["cost"]["model_prices"]]
    }
    fixtures["api/monitor/cost"] = {
        "daily": [
            {
                "date": "2026-10-30",
                "component": "warehouse",
                "usd": 4.5,
                "basis": "duration-share estimate",
            },
            {
                "date": "2026-10-30",
                "component": "review tokens",
                "usd": None,
                "input_tokens": 4000,
                "output_tokens": 500,
                "basis": "unpriced",
            },
        ],
        "storage": [{"table_name": "otel_spans", "size_bytes": 104857600, "measured_at": date}],
    }
    fixtures["api/reach/fleet"] = {
        "mode": "hub",
        "apps": [
            {
                "workspace_name": a["workspace"],
                "workspace_id": a["workspace_id"],
                "name": a["name"],
                "app_state": a["status"],
                "requests_7d": a["usage_7d"]["requests_7d"],
                "errors_7d": 20,
                "dbus_7d": 4,
                "usd_7d": a["cost_7d"]["usd_7d"],
                "snapshot_ts": date,
            }
            for a in data["apps"]
        ],
    }
    for app in data["apps"]:
        app["scan"]["has_npm"] = True
        app["scan"] = {
            k: v
            for k, v in app["scan"].items()
            if k
            in {
                "name",
                "quality_score",
                "findings_critical",
                "findings_high",
                "findings_medium",
                "findings_low",
                "deps",
                "deps_pinned",
                "scanned_at",
                "py_loc",
                "files",
                "has_npm",
            }
        }
        app["review"] = {
            k: v
            for k, v in app["review"].items()
            if k
            in {
                "name",
                "verdict",
                "score_overall",
                "model",
                "summary",
                "reviewed_at",
            }
        }
    (STATIC / "demo-data.js").write_text("window.MOCK = " + json.dumps(data, indent=2) + ";\n")
    (STATIC / "demo-fixtures.js").write_text(
        "window.CONSOLE_FIXTURES = " + json.dumps(fixtures, indent=2) + ";\n"
    )


if __name__ == "__main__":
    main()
