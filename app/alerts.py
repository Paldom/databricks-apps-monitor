"""Probe-based alert rules — evaluated in memory after every probe round.

State transitions (firing/resolved) are appended to alert_events in UC and optionally
POSTed to ALERT_WEBHOOK_URL. Deep-signal rules (cost spikes, critical findings, review
rejects, failed journeys) are emitted by the jobs that compute them — see jobs/*.py.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import httpx
from mutes import is_muted
from reach_logic import vantage_decisions

log = logging.getLogger("monitor.alerts")

P95_BUDGET_MS = float(os.environ.get("ALERT_P95_BUDGET_MS", "2500"))
ERROR_RATE_PCT = float(os.environ.get("ALERT_ERROR_RATE_PCT", "10"))
WEBHOOK = os.environ.get("ALERT_WEBHOOK_URL", "")

_active: dict[str, dict] = {}  # key = rule:app
_mutes: list[dict] = []


def set_mutes(rows: list[dict]) -> None:
    _mutes[:] = rows


def rehydrate(rows: list[dict]) -> None:
    """Restore durable monitor state before the first probe round."""
    _active.clear()
    _active.update({f"{r['rule']}:{r['app']}": {**r, "since": str(r["since"])} for r in rows})


def evaluate(
    fleet: dict,
    probes: dict,
    summary_fn,
    synth: dict | None = None,
    vantage_rows: list | None = None,
    expected_journeys: tuple = (),
) -> list[dict]:
    """Return state-transition events; keeps the active-alert set internally."""
    now = datetime.now(timezone.utc).isoformat()
    desired: dict[str, dict] = {}

    def want(rule: str, app: str, severity: str, message: str, value: float | None) -> None:
        desired[f"{rule}:{app}"] = {
            "rule": rule,
            "app": app,
            "severity": severity,
            "message": message,
            "value": value,
            "since": _active.get(f"{rule}:{app}", {}).get("since", now),
        }

    for name, info in fleet.items():
        s = summary_fn(name)
        pts = list(probes.get(name, ()))
        if info.get("app_state") not in ("RUNNING", None) or info.get("compute_state") not in (
            "ACTIVE",
            None,
        ):
            want(
                "app_stopped",
                name,
                "warning",
                f"app not running (state {info.get('app_state')}, compute {info.get('compute_state')})",
                None,
            )
        elif len(pts) >= 2 and not pts[-1][1] and not pts[-2][1]:
            want(
                "app_down",
                name,
                "critical",
                f"consecutive probe failures (last HTTP {pts[-1][2]})",
                float(pts[-1][2]),
            )
        if (s.get("error_rate_1h") or 0) > ERROR_RATE_PCT:
            want(
                "probe_error_rate",
                name,
                "warning",
                f"probe error rate {s['error_rate_1h']}% over the last hour",
                s["error_rate_1h"],
            )
        if (s.get("p95_ms") or 0) > P95_BUDGET_MS:
            want(
                "slow_p95",
                name,
                "warning",
                f"probe p95 {s['p95_ms']} ms over {P95_BUDGET_MS:.0f} ms budget",
                s["p95_ms"],
            )

    decisions = vantage_decisions(
        vantage_rows or [], datetime.now(timezone.utc).timestamp(), expected=expected_journeys
    )
    for name, failed in decisions.items():
        if failed:
            want(
                "journey_failed",
                name,
                "high",
                "Two consecutive journey failures from both internal and external vantages",
                4.0,
            )

    events = []
    # A restarted process needs two probes before it can clear a consecutive-failure alert.
    for key, a in _active.items():
        if (
            a["app"] not in fleet
            or (a["rule"] == "app_down" and len(probes.get(a["app"], ())) < 2)
            or (a["rule"] == "journey_failed" and a["app"] not in decisions)
        ):
            desired.setdefault(key, a)
    for key, a in desired.items():
        if key not in _active:
            events.append({**a, "state": "firing"})
    for key, a in list(_active.items()):
        if key not in desired:
            events.append({**a, "state": "resolved"})
    _active.clear()
    _active.update(desired)
    for a in [*events, *_active.values()]:
        a["muted"] = is_muted(a["app"], a["rule"], _mutes, datetime.fromisoformat(now))
    for e in events:
        log.warning("alert %s: %s %s — %s", e["state"], e["severity"], e["rule"], e["message"])
    return events


def active() -> list[dict]:
    return list(_active.values())


def job_webhook_batch(
    rows: list[dict], cursor: datetime, *, posted: bool = False
) -> tuple[list[dict], datetime]:
    """Acknowledge the whole batch only after delivery, including equal timestamps."""
    events = []
    latest = cursor
    for row in rows:
        ts = datetime.fromisoformat(str(row["ts"]).replace("Z", "+00:00"))
        ts = ts.replace(tzinfo=ts.tzinfo or timezone.utc)
        if ts <= cursor or row.get("source") != "job":
            continue
        latest = max(latest, ts)
        if str(row.get("muted")).lower() == "true":
            continue
        events.append(
            {
                **{k: row[k] for k in ("rule", "app", "severity", "message", "state")},
                "value": float(row["value"]) if row.get("value") is not None else None,
                "since": ts.isoformat(),
                "muted": False,
                "workspace_id": row["workspace_id"],
            }
        )
    return events, latest if posted and events else cursor


def notify_webhook(events: list[dict]) -> bool:
    events = [e for e in events if str(e.get("muted")).lower() != "true"]
    if not WEBHOOK or not events:
        return False
    try:
        r = httpx.post(WEBHOOK, json={"source": "apps-monitor", "events": events}, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:  # noqa: BLE001 — alerting must not break monitoring
        log.warning("webhook failed: %s", type(e).__name__)
        return False
