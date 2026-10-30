"""V1 console adapter. Pure shaping below, bounded optional reads at the edge."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import math
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import auth
import console_topology
from fastapi import APIRouter, HTTPException, Request

import queries as q

log = logging.getLogger("monitor.console")
CACHE_SECONDS = 60
QUERY_TIMEOUT = 50  # Match the Statement API timeout; a stalled section cannot hold probes.
TRACE_ID = re.compile(r"[0-9a-fA-F]{1,64}\Z")


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def boolean(value):
    if value in (True, "true", "True", "1", 1):
        return True
    if value in (False, "false", "False", "0", 0):
        return False
    return None


def probe_percentile(live):
    latencies = sorted(
        value
        for points in live.get("probes", {}).values()
        for point in points
        if len(point) > 3 and point[1] and (value := number(point[3])) is not None
    )
    return latencies[min(int(len(latencies) * 0.95), len(latencies) - 1)] if latencies else None


def timestamp(value):
    try:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(value, timezone.utc)
        else:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def iso(value):
    dt = timestamp(value)
    return dt.isoformat().replace("+00:00", "Z") if dt else None


def obj(value):
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def ratio(numerator, denominator, scale=100):
    a, b = number(numerator), number(denominator)
    return a / b * scale if a is not None and b is not None and b > 0 else None


def total(values):
    values = list(values)
    parsed = [number(v) for v in values]
    return sum(parsed) if parsed and all(v is not None for v in parsed) else None


def daily_cost_series(rows, days):
    by_day = {str(r.get("date"))[:10]: r for r in rows}
    return [
        number(by_day[day].get("total_usd"))
        if day in by_day and number(by_day[day].get("dbu_usd")) is not None
        else None
        for day in days
    ]


def health(info, summary, detail=None, points=(), requests=None):
    """Only observed evidence can establish health; no probe is unknown, not green."""
    state = str(info.get("app_state") or "").upper()
    compute = str(info.get("compute_state") or "").upper()
    if state in ("STOPPED", "STOPPING") or compute in ("STOPPED", "STOPPING"):
        return "stopped"
    if state in ("FAILED", "ERROR", "CRASHED") or compute in ("ERROR", "FAILED"):
        return "down"
    last = summary.get("last") or {}
    if (detail or {}).get("status") == "degraded":
        return "degraded"
    if boolean(last.get("ok")) is False:
        points = list(points)
        return "down" if len(points) >= 2 and not points[-2][1] else "degraded"
    if boolean(last.get("ok")) is not True:
        return None
    if (number(summary.get("error_rate_1h")) or 0) > 5 or (
        number(summary.get("p95_ms")) or 0
    ) > 2500:
        return "degraded"
    return "idle" if number(requests) == 0 else "healthy"


def hourly_series(rows, now):
    """Align UTC hours, preserving missing buckets and invalid rates as gaps."""
    end = now.replace(minute=0, second=0, microsecond=0)
    hours = [end - timedelta(hours=23 - i) for i in range(24)]
    by_hour = {}
    for row in rows:
        hour = timestamp(row.get("hour"))
        if hour:
            by_hour[hour.replace(minute=0, second=0, microsecond=0)] = row
    result = {"hours": [iso(h) for h in hours], "requests": [], "p95_ms": [], "error_rate_pct": []}
    for hour in hours:
        row = by_hour.get(hour, {})
        requests, errors = number(row.get("requests")), number(row.get("errors"))
        result["requests"].append(requests if requests is not None and requests >= 0 else None)
        latency = number(row.get("p95_ms"))
        result["p95_ms"].append(latency if latency is not None and latency >= 0 else None)
        rate = ratio(errors, requests)
        result["error_rate_pct"].append(rate if rate is not None and 0 <= rate <= 100 else None)
    return result


def error_groups(rows):
    return [
        {
            "fingerprint": r.get("fingerprint"),
            "app": r.get("name"),
            "type": r.get("type") or "Exception",
            "message": r.get("message"),
            "count_24h": number(r.get("count_24h")),
            "first_seen": iso(r.get("first_seen")),
            "last_seen": iso(r.get("last_seen")),
            # First observed in a bounded query does not prove first occurrence ever.
            "new_since_deploy": None,
            "sample_trace_id": r.get("sample_trace_id"),
            "route": r.get("route"),
        }
        for r in rows
    ]


def nanoseconds(value):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def shape_trace(trace_id, spans, logs):
    if not spans:
        return None
    starts = [nanoseconds(s.get("start_time_unix_nano")) for s in spans]
    start = min((v for v in starts if v is not None), default=None)
    ids = {s.get("span_id") for s in spans}
    shaped = []
    for s in spans:
        a, b = nanoseconds(s.get("start_time_unix_nano")), nanoseconds(s.get("end_time_unix_nano"))
        attrs = obj(s.get("attributes"))
        parent = s.get("parent_span_id")
        orphan = bool(parent and not re.fullmatch("0+", parent) and parent not in ids)
        if orphan:
            attrs = {**attrs, "monitor.orphan_parent": parent}
        shaped.append(
            {
                "id": s.get("span_id"),
                "parent": parent if parent in ids and parent != s.get("span_id") else None,
                "name": s.get("name"),
                "kind": str(attrs.get("mlflow.spanType") or s.get("kind") or "INTERNAL").strip('"'),
                "service": s.get("service_name"),
                "start_ms": (a - start) / 1e6 if a is not None and start is not None else None,
                "duration_ms": (b - a) / 1e6
                if a is not None and b is not None and b >= a
                else None,
                "status": s.get("status") or "unknown",
                "attrs": attrs,
            }
        )
    shaped.sort(key=lambda s: s["start_ms"] if s["start_ms"] is not None else math.inf)
    root = next((s for s in shaped if not s["parent"]), shaped[0])
    durations = [
        s["start_ms"] + s["duration_ms"]
        for s in shaped
        if s["start_ms"] is not None and s["duration_ms"] is not None
    ]
    services = {s["id"]: s["service"] for s in shaped}
    return {
        "trace_id": trace_id,
        "app": root["service"],
        "root": root["name"],
        "started_at": iso(start / 1e9) if start is not None else None,
        "duration_ms": max(durations) if durations else None,
        "status": "error" if any(s["status"] == "error" for s in shaped) else root["status"],
        "user_hash": root["attrs"].get("user.id_hash"),
        "session_id": root["attrs"].get("session.id"),
        "spans": shaped,
        "logs": [
            {
                "ts_ms": (timestamp(r.get("time")).timestamp() * 1e9 - start) / 1e6
                if timestamp(r.get("time")) and start is not None
                else None,
                "severity": r.get("severity"),
                "service": r.get("service_name") or services.get(r.get("span_id")),
                "body": r.get("body"),
            }
            for r in logs
        ],
    }


def shape_slo(rows):
    availability = next(
        (
            r
            for r in rows
            if r.get("sli") == "availability"
            and number(r.get("window_days")) == 28
            and not r.get("route_filter")
        ),
        {},
    )
    latency = next((r for r in rows if r.get("sli") == "latency" and not r.get("route_filter")), {})
    return {
        "availability_target": ratio(availability.get("target"), 1),
        "attainment_28d": ratio(availability.get("good"), availability.get("total")),
        "error_budget_remaining_pct": number(availability.get("budget_remaining_pct")),
        "latency_threshold_ms": number(latency.get("threshold_ms")),
        "specs": rows,
    }


def shape_usage(rows, cohorts):
    funnel = None
    if rows:
        first = rows[0]
        by_version = defaultdict(list)
        for row in rows:
            if row.get("name") == first.get("name") and row.get("funnel") == first.get("funnel"):
                by_version[str(row.get("app_version") or "Unknown version")].append(
                    {"step": row.get("step_name"), "sessions": number(row.get("sessions"))}
                )
        funnel = {
            "app": first.get("name"),
            "funnel": first.get("funnel"),
            "by_version": dict(by_version),
        }
    cohort = None
    if cohorts:
        selected = [r for r in cohorts if r.get("name") == cohorts[0].get("name")]
        weeks = sorted({str(r["cohort_week"]) for r in selected})
        values, sizes = [], []
        width = min(9, max(int(r.get("week_number") or 0) for r in selected) + 1)
        for week in weeks:
            group = [r for r in selected if str(r["cohort_week"]) == week]
            sizes.append(number(group[0].get("cohort_size")))
            values.append(
                [
                    next(
                        (
                            number(r.get("retention_pct"))
                            for r in group
                            if int(r.get("week_number") or 0) == i
                        ),
                        None,
                    )
                    for i in range(width)
                ]
            )
        cohort = {
            "app": cohorts[0].get("name"),
            "weeks": weeks,
            "sizes": sizes,
            "retention_pct": values,
        }
    return funnel, cohort


def shape_synthetics(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row.get("app"), row.get("journey"), row.get("vantage"))].append(row)
    checks = []
    for (app, journey, vantage), items in groups.items():
        items.sort(key=lambda r: iso(r.get("run_ts")) or "")
        last = items[-1]
        checks.append(
            {
                "app": app,
                "journey": journey,
                "vantage": vantage,
                "ok": boolean(last.get("ok")),
                "failed_step": last.get("detail") if boolean(last.get("ok")) is False else None,
                "failure_stage": last.get("failure_stage"),
                "last_run": iso(last.get("run_ts")),
                "history": [boolean(r.get("ok")) for r in items[-12:]],
            }
        )
    return checks


def shape_alerts(rows):
    result = {}
    for r in rows:
        key = (r.get("app"), r.get("rule"), r.get("source", "monitor"))
        state = r.get("state") or "firing"
        # Recent history may include several transitions; only expose the latest state.
        ts = iso(r.get("since") or r.get("ts"))
        if key in result and (result[key]["since"] or "") > (ts or ""):
            continue
        result[key] = {
            "id": ":".join(str(v) for v in key),
            "app": r.get("app"),
            "rule": r.get("rule"),
            "severity": r.get("severity") or "info",
            "state": state,
            "since": ts,
            "message": r.get("message"),
            "muted": boolean(r.get("muted")) is True,
        }
    return list(result.values())


def build_snapshot(live, data, sources, now):
    """Join optional sections by app; unavailable measurements stay JSON null."""

    def rows(source):
        return data.get(source, [])

    def by_app(source, name):
        return [r for r in rows(source) if r.get("name") == name]

    def one(source, name):
        return next(iter(by_app(source, name)), {})

    ws = live["workspace"]
    days = [(now.date() - timedelta(days=29 - i)).isoformat() for i in range(30)]
    last_run = iso(live.get("last_collection"))
    workspaces = [
        {
            "id": live.get("workspace_id"),
            "name": ws,
            "region": None,
            "role": live.get("mode", "standalone"),
            "status": "OK"
            if last_run and (now - timestamp(last_run)).total_seconds() <= 300
            else "STALE",
            "last_run": last_run,
        }
    ]
    apps = []
    alerts = shape_alerts(
        [
            *rows("recent_alerts"),
            *[{**r, "source": "job"} for r in rows("job_alerts")],
            *live.get("alerts", []),
        ]
    )
    for name, info in live.get("fleet", {}).items():
        perf, cfg, telemetry = (
            one("performance", name),
            one("configs", name),
            one("telemetry", name),
        )
        unit, scan, review = one("unit_economics", name), one("scans", name), one("reviews", name)
        findings = one("findings", name)
        if not findings and scan and sources.get("findings") == "ok":
            findings = dict.fromkeys(("critical", "high", "medium", "low", "secrets"), 0)
        tags = obj(cfg.get("tags_json"))
        summary = live.get("summaries", {}).get(name, {})
        span_at = timestamp(telemetry.get("last_span_at"))
        deployments = by_app("deployments", name)
        genai = by_app("genai", name)
        signals = one("genai_signals", name)
        package_row = one("packages", name)
        packages = []
        try:
            packages = json.loads(package_row.get("deps_json") or "[]")
        except (ValueError, TypeError):
            pass
        packages = (
            [p for p in packages if isinstance(p, dict)] if isinstance(packages, list) else []
        )
        outdated = (
            sum(p.get("behind") in ("major", "minor", "patch") for p in packages)
            if packages
            and all(p.get("behind") in ("current", "major", "minor", "patch") for p in packages)
            else None
        )
        quality, feedback, drift = one("quality", name), one("feedback", name), one("drift", name)
        actual = number(unit.get("total_usd")) if number(unit.get("dbu_usd")) is not None else None
        # Forecast is an explicit straight-line estimate from complete observed days.
        daily = by_app("daily_cost", name)
        completed = [r for r in daily if str(r.get("date", ""))[:10] < now.date().isoformat()]
        daily_total = total(
            r.get("total_usd") if number(r.get("dbu_usd")) is not None else None for r in completed
        )
        next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
        days_in_month = (next_month.date() - now.replace(day=1).date()).days
        forecast = (
            daily_total / len(completed) * days_in_month
            if daily_total is not None and len(completed) >= 7
            else None
        )
        requests = number(perf.get("requests_24h"))
        # An empty real-traffic group means zero only when export was observed in
        # the same window. An uninstrumented app must keep an unknown request count.
        if (
            not perf
            and sources.get("performance") == "ok"
            and span_at
            and now - timedelta(hours=24) <= span_at <= now
        ):
            requests = 0
        apps.append(
            {
                "id": name,
                "name": name,
                "workspace": ws,
                "workspace_id": live.get("workspace_id"),
                "team": tags.get("team"),
                "cost_center": tags.get("cost_center"),
                "owner": tags.get("owner") or info.get("creator"),
                "kind": "agent" if genai or signals else tags.get("kind"),
                "health": health(
                    info,
                    summary,
                    live.get("health_detail", {}).get(name),
                    live.get("probes", {}).get(name, ()),
                    requests,
                ),
                "status": info.get("app_state"),
                "version": live.get("health_detail", {}).get(name, {}).get("version")
                or info.get("version"),
                "deployed_at": iso(deployments[0].get("create_time")) if deployments else None,
                "url": info.get("url"),
                "description": info.get("description"),
                "tags": tags,
                "resources": console_topology.resources(
                    info.get("resources")
                    if "resources" in info
                    else info.get("resources_json")
                    or one("inventory_resources", name).get("resources_json")
                ),
                "probe": summary,
                "scan": scan,
                "review": review,
                "cost_7d": one("cost_7d", name),
                "sdk_version": None,
                "telemetry": {
                    "otel_export": True if span_at else None,
                    "envelope_coverage_pct": ratio(telemetry.get("envelope_coverage"), 1),
                    "last_span_age_s": max(0, (now - span_at).total_seconds()) if span_at else None,
                    "sampler_ratio": number(telemetry.get("sampler_ratio")),
                    "orphan_span_pct": ratio(telemetry.get("orphan_ratio_24h"), 1),
                },
                "last24h": {
                    "requests": requests,
                    "error_rate_pct": ratio(perf.get("errors_24h"), requests),
                    "p50_ms": number(perf.get("p50_ms")),
                    "p95_ms": number(perf.get("real_p95_ms")),
                    "p99_ms": number(perf.get("p99_ms")),
                    "uptime_pct": number(summary.get("uptime_24h")),
                    "active_users": number(perf.get("active_users")),
                },
                "series_24h": hourly_series(by_app("hourly", name), now),
                "usage_7d": one("usage", name),
                "slo": shape_slo(by_app("slos", name)),
                "cost": {
                    "mtd_usd": actual,
                    "dbu_usd": number(unit.get("dbu_usd")),
                    "ai_usd": number(unit.get("ai_usd")),
                    "idle_usd": number(unit.get("idle_usd")),
                    "budget_usd_month": number(cfg.get("budget_usd_month")),
                    "forecast_usd_month": forecast,
                    "daily_30d": daily_cost_series(daily, days),
                    "usd_per_1k_requests": number(unit.get("usd_per_1k_requests"))
                    if actual is not None
                    else None,
                },
                "genai": {
                    "models": [r.get("model") for r in genai],
                    "period": "Previous UTC day",
                    "calls_24h": total(r.get("calls") for r in genai),
                    "input_tokens_24h": total(r.get("input_tokens") for r in genai),
                    "output_tokens_24h": total(r.get("output_tokens") for r in genai),
                    "ttft_p95_ms": number(signals.get("ttft_p95_ms")),
                    "quality": {
                        k: number(quality.get(k)) for k in ("relevance", "faithfulness", "toxicity")
                    },
                    "feedback": {k: number(feedback.get(k)) for k in ("avg_stars", "count_7d")},
                    "error_classes_24h": {
                        k: number(signals.get(k))
                        for k in ("rate_limit", "timeout", "policy", "schema", "server")
                    },
                    "guardrail_findings_7d": {
                        r["kind"]: number(r.get("findings")) for r in by_app("guardrails", name)
                    },
                    "prompt_drift_novel_share": number(drift.get("novel_share")),
                }
                if genai or signals
                else None,
                "security": {
                    "cve": {
                        k: number(findings.get(k)) if scan else None
                        for k in ("critical", "high", "medium", "low")
                    },
                    "secrets": number(findings.get("secrets")) if scan else None,
                    "review_verdict": review.get("verdict"),
                    "review_score": number(review.get("score_overall")),
                    "quality_score": number(scan.get("quality_score")),
                    "outdated_packages": outdated,
                    "last_scan": iso(scan.get("scanned_at")),
                },
                "governance": {
                    "tags_complete": all(
                        tags.get(k) for k in ("team", "cost_center", "env", "tier")
                    )
                    if cfg
                    else None,
                    "auto_stop": cfg.get("auto_stop"),
                    "permission_drift": True
                    if any(
                        a["app"] == name
                        and a["rule"] == "permission_drift"
                        and a["state"] == "firing"
                        for a in alerts
                    )
                    else None,
                },
            }
        )
    # Feeder identities are qualified; their local telemetry must never join by name.
    for row in rows("federation"):
        remote_ws = str(row.get("workspace_id"))
        if remote_ws == str(live.get("workspace_id")):
            continue
        workspace_name = row.get("workspace_name") or remote_ws
        existing = next((w for w in workspaces if str(w["id"]) == remote_ws), None)
        if not existing:
            last = timestamp(row.get("snapshot_ts"))
            workspaces.append(
                {
                    "id": remote_ws,
                    "name": workspace_name,
                    "region": None,
                    "role": "feeder",
                    "status": "OK" if last and (now - last).total_seconds() <= 7200 else "STALE",
                    "last_run": iso(last),
                }
            )
        remote = build_snapshot(
            {"workspace": workspace_name, "workspace_id": remote_ws, "fleet": {row["name"]: row}},
            {},
            {},
            now,
        )["apps"][0]
        remote["id"] = f"{remote_ws}:{row['name']}"
        remote["remote"] = True
        remote["monitor_url"] = next(
            (w.get("url") for w in live.get("workspaces", []) if w.get("name") == workspace_name),
            None,
        )
        cost = next(
            (
                c
                for c in rows("federation_cost")
                if str(c.get("workspace_id")) == remote_ws and c.get("name") == row["name"]
            ),
            {},
        )
        remote["cost"]["dbu_usd"] = number(cost.get("dbu_usd"))
        remote["usage_7d"] = {
            "requests": number(row.get("requests_7d")),
            "errors": number(row.get("errors_7d")),
        }
        apps.append(remote)
    remote_alerts = [
        {**r, "app": f"{r.get('workspace_id')}:{r.get('app')}"}
        for r in rows("federation_alerts")
        if str(r.get("workspace_id")) != str(live.get("workspace_id"))
    ]
    alerts += shape_alerts(remote_alerts)
    funnel, cohorts = shape_usage(rows("funnels"), rows("cohorts"))
    monitor_cost = total(
        r.get("usd")
        for r in rows("monitor_cost")
        if str(r.get("date", ""))[:7] == now.strftime("%Y-%m")
    )
    return {
        "generated_at": iso(now),
        "product": "Apps Monitor",
        "genie_url": live.get("genie_url"),
        "topology": console_topology.graph(apps, rows("dependencies")),
        "fleet_measures": {
            **one("fleet_performance", None),
            "probe_p95_ms": probe_percentile(live),
        },
        "workspaces": workspaces,
        "apps": apps,
        "alerts": alerts,
        "timeline": [
            *[
                {
                    "ts": iso(r.get("create_time")),
                    "app": r.get("name"),
                    "type": "deploy",
                    "text": f"Deployment {r.get('deployment_id') or '—'} · {r.get('state') or '—'}",
                }
                for r in rows("deployments")
            ],
            *[
                {
                    "ts": a["since"],
                    "app": a["app"],
                    "type": "alert",
                    "text": f"{a['rule']} {a['state']}: {a['message'] or ''}",
                }
                for a in alerts
            ],
        ],
        "error_groups": error_groups(rows("errors")),
        "trace_example": None,
        "traces": {},
        "synthetics": shape_synthetics(rows("synthetics")),
        "funnel_example": funnel,
        "cohorts_example": cohorts,
        "cost": {
            "days": days,
            "by_team": {
                team: [
                    total(a["cost"]["daily_30d"][i] for a in apps if (a["team"] or "—") == team)
                    for i in range(30)
                ]
                for team in sorted({a["team"] or "—" for a in apps})
            },
            "model_prices": rows("model_prices"),
            "monitor_self_cost_mtd_usd": monitor_cost,
            "monitor_self_cost_pct_of_fleet": ratio(
                monitor_cost, total(a["cost"]["mtd_usd"] for a in apps)
            ),
        },
        "maintenance_windows": [
            {**r, "starts_at": iso(r.get("starts_at")), "ends_at": iso(r.get("ends_at"))}
            for r in rows("maintenance")
        ],
        "governance": {
            "required_tags": ["team", "cost_center", "env", "tier"],
            "audit_events": [
                {
                    "ts": iso(r.get("event_time")),
                    "app": r.get("app"),
                    "user": r.get("user"),
                    "action": r.get("action_name"),
                    "detail": f"HTTP {r.get('status_code') or '—'}",
                }
                for r in rows("audit")
            ],
        },
        "notes": {
            "refresh_seconds": CACHE_SECONDS,
            "workspace": ws,
            "errors_top_n": 100,
            "costs": "Compute at list prices; AI tokens times configured model prices. Missing prices keep total unknown. Forecast: trailing completed-day mean times calendar-month length, minimum 7 days.",
            "genai": "Billable calls and tokens from gold: previous complete UTC day, not a rolling 24h window.",
            "slo": "Only unfiltered 28-day availability objectives populate the V1 availability tiles; all configured specs remain on each app.",
            "federation": "Remote daily usage and compute cost only; open the feeder monitor for live health, hourly series, SLOs and traces.",
        },
        "sources": dict(sources),
    }


def query_plan(ws, now):
    month = now.replace(day=1).date().isoformat()
    return {
        "performance": (q.REAL_PERF_FLEET, {}),
        "fleet_performance": (q.REAL_P95_FLEETWIDE, {}),
        "cost_7d": (q.COST_FLEET, {}),
        "inventory_resources": (q.CONSOLE_RESOURCES, {"ws": ws}),
        "dependencies": (q.CONSOLE_DEPENDENCIES, {"ws": ws}),
        "hourly": (q.CONSOLE_HOURLY, {"ws": ws}),
        "configs": (q.CONFIGS_ALL, {}),
        "scans": (q.SEC_BY_APP, {}),
        "findings": (q.CONSOLE_FINDINGS, {}),
        "reviews": (q.REVIEW_BY_APP, {}),
        "usage": (q.USAGE_FLEET, {}),
        "unit_economics": (q.CONSOLE_UNIT_ECONOMICS, {"ws": ws, "since": month, "app": ""}),
        "daily_cost": (q.CONSOLE_DAILY_COST, {"ws": ws}),
        "job_alerts": (q.OPEN_JOB_ALERTS, {"ws": ws}),
        "recent_alerts": (q.RECENT_ALERTS, {}),
        "slos": (q.CONSOLE_SLOS, {"ws": ws}),
        "telemetry": (q.CONSOLE_TELEMETRY, {"ws": ws}),
        "errors": (q.CONSOLE_ERRORS, {"app": ""}),
        "deployments": (q.CONSOLE_DEPLOYMENTS, {"ws": ws}),
        "synthetics": (q.CONSOLE_SYNTHETICS, {"ws": ws}),
        "maintenance": (q.ACTIVE_MUTES, {"ws": ws}),
        "audit": (q.AUDIT_FLEET, {}),
        "monitor_cost": (q.MONITOR_COST, {"ws": ws}),
        "model_prices": (q.MODEL_PRICES, {"ws": ws}),
        "funnels": (q.CONSOLE_FUNNELS, {"ws": ws}),
        "cohorts": (q.CONSOLE_COHORTS, {"ws": ws}),
        "genai": (q.CONSOLE_GENAI, {"ws": ws}),
        "quality": (q.CONSOLE_QUALITY, {}),
        "genai_signals": (q.CONSOLE_GENAI_SIGNALS, {}),
        "packages": (q.CONSOLE_PACKAGES, {}),
        "feedback": (q.CONSOLE_FEEDBACK, {}),
        "guardrails": (q.CONSOLE_GUARDRAILS, {"ws": ws}),
        "drift": (q.CONSOLE_DRIFT, {"ws": ws}),
        **(
            {
                "federation": (q.REACH_FLEET, {"ws": ""}),
                "federation_cost": (q.CONSOLE_REMOTE_COST, {}),
                "federation_alerts": (q.CONSOLE_REMOTE_ALERTS, {}),
            }
            if q.DEPLOYMENT_MODE == "hub"
            else {}
        ),
    }


async def optional_read(sql, params):
    try:
        return await asyncio.wait_for(q.run(sql, ttl=CACHE_SECONDS, **params), QUERY_TIMEOUT), "ok"
    except Exception as exc:  # noqa: BLE001 — each optional source degrades independently
        missing = any(
            s in str(exc).upper()
            for s in (
                "TABLE_OR_VIEW_NOT_FOUND",
                "TABLE_NOT_FOUND",
                "DOES NOT EXIST",
                "UNRESOLVED_COLUMN",
                "SCHEMA_NOT_FOUND",
            )
        )
        log.warning("console source unavailable: %s", type(exc).__name__)
        return [], "missing" if missing else "error"


def build_router(handlers):
    router = APIRouter(prefix="/api/console")
    cached = None
    cached_at = 0.0
    pending = None

    def live():
        return {
            "workspace": handlers["WORKSPACE_NAME"],
            "workspace_id": str(
                handlers.get("_ws_id") or os.environ.get("DATABRICKS_WORKSPACE_ID") or ""
            ),
            "mode": q.DEPLOYMENT_MODE,
            "workspaces": handlers["WORKSPACES"],
            "last_collection": handlers.get("_last_fleet_refresh") or None,
            "fleet": copy.deepcopy(handlers["fleet"]),
            "summaries": {name: handlers["_summary"](name) for name in handlers["fleet"]},
            "health_detail": copy.deepcopy(handlers["health_detail"]),
            "probes": {name: list(points) for name, points in handlers["probes"].items()},
            "alerts": handlers["alerts"].active(),
            "genie_url": handlers.get("GENIE_EMBED_URL"),
        }

    async def collect():
        nonlocal cached, cached_at
        state = live()
        if not state["workspace_id"]:
            try:
                state["workspace_id"] = str(
                    await asyncio.wait_for(
                        asyncio.to_thread(handlers["_workspace_id"]), QUERY_TIMEOUT
                    )
                )
            except Exception:  # noqa: BLE001 — inventory can still render before SDK identity is available
                log.warning("console workspace identity unavailable")
        now = datetime.now(timezone.utc)
        plan = query_plan(state["workspace_id"], now)
        results = await asyncio.gather(
            *(optional_read(sql, params) for sql, params in plan.values())
        )
        data = {name: result[0] for name, result in zip(plan, results, strict=True)}
        sources = {name: result[1] for name, result in zip(plan, results, strict=True)}
        cached = build_snapshot(live(), data, sources, now)
        cached_at = time.monotonic()

    @router.get("/snapshot")
    async def snapshot():
        nonlocal pending
        if cached is None or time.monotonic() - cached_at >= CACHE_SECONDS:
            if pending is None or pending.done():
                pending = asyncio.create_task(collect())
            if cached is None:
                # Warm probes are useful immediately even if warehouse startup takes 50s.
                await asyncio.wait({pending}, timeout=0.05)
        state = live()
        now = datetime.now(timezone.utc)
        if cached is None:
            result = build_snapshot(
                state, {}, dict.fromkeys(query_plan(state["workspace_id"], now), "missing"), now
            )
            result["notes"]["collecting"] = True
        else:
            result = copy.deepcopy(cached)
            current = build_snapshot(state, {}, {}, now)
            result["workspaces"] = current["workspaces"] + [
                w
                for w in result["workspaces"]
                if w["role"] == "feeder" and w["name"] != state["workspace"]
            ]
            by_name = {a["name"]: a for a in result["apps"] if not a.get("remote")}
            local = []
            for a in current["apps"]:
                old = by_name.get(a["name"], a)
                old["status"] = a["status"]
                old["health"] = health(
                    state["fleet"][a["name"]],
                    state["summaries"][a["name"]],
                    state["health_detail"].get(a["name"]),
                    state["probes"].get(a["name"], ()),
                    old["last24h"]["requests"],
                )
                old["last24h"]["uptime_pct"] = a["last24h"]["uptime_pct"]
                old["probe"] = a["probe"]
                old["url"] = a["url"]
                local.append(old)
            result["apps"] = local + [a for a in result["apps"] if a.get("remote")]
            result["alerts"] = [
                a
                for a in result["alerts"]
                if not (
                    a["id"].endswith(":monitor")
                    and a["state"] == "firing"
                    and a["app"] in state["fleet"]
                )
            ] + shape_alerts(state["alerts"])
        result["notes"]["live_as_of"] = iso(now)
        result["fleet_measures"]["probe_p95_ms"] = probe_percentile(state)
        result["sources"]["inventory"] = "ok" if state["last_collection"] else "missing"
        result["sources"]["probes"] = "ok" if handlers.get("_last_probe_ts") else "missing"
        return result

    @router.get("/identity")
    async def identity(request: Request):
        actor = auth.actor_of(request)
        allowed = actor.lower() in auth.MONITOR_ADMINS
        return {
            "actor": actor,
            "admin": allowed,
            "reason": ""
            if allowed
            else "This monitor is read-only for your account. Ask an operator to add you to MONITOR_ADMINS.",
        }

    @router.get("/trace/{trace_id}")
    async def trace(trace_id: str):
        if not TRACE_ID.fullmatch(trace_id):
            raise HTTPException(422, "Trace ID must be 1-64 hexadecimal characters")
        spans, logs = await asyncio.gather(
            optional_read(q.TRACE_SPANS, {"tid": trace_id}),
            optional_read(q.TRACE_LOGS, {"tid": trace_id}),
        )
        if spans[1] != "ok":
            raise HTTPException(503, "Trace source unavailable; retry after collection resumes")
        result = shape_trace(trace_id, spans[0], logs[0])
        if result is None:
            raise HTTPException(404, "Trace not found in this workspace's seven-day trace window")
        result["sources"] = {"spans": spans[1], "logs": logs[1]}
        return result

    @router.get("/apps/{name}/errors")
    async def app_errors(name: str):
        if name not in handlers["fleet"]:
            raise HTTPException(404, "Application not found in this workspace")
        rows, source = await optional_read(q.CONSOLE_ERRORS, {"app": name})
        if source != "ok":
            raise HTTPException(503, "Error groups unavailable; retry after collection resumes")
        return {"error_groups": error_groups(rows), "limit": 100}

    return router
