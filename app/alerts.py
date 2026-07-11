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

log = logging.getLogger("monitor.alerts")

P95_BUDGET_MS = float(os.environ.get("ALERT_P95_BUDGET_MS", "2500"))
ERROR_RATE_PCT = float(os.environ.get("ALERT_ERROR_RATE_PCT", "10"))
WEBHOOK = os.environ.get("ALERT_WEBHOOK_URL", "")

_active: dict[str, dict] = {}  # key = rule:app


def evaluate(fleet: dict, probes: dict, summary_fn, synth: dict | None = None) -> list[dict]:
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
            "since": now,
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

    for name, jr in (synth or {}).items():
        if not jr.get("ok"):
            failed = next((s for s in jr["steps"] if not s["ok"]), {})
            want(
                "journey_failed",
                name,
                "high",
                f"synthetic journey '{jr['journey']}' failed at {failed.get('name')}: "
                f"{failed.get('detail') or failed.get('code')}",
                failed.get("code"),
            )

    events = []
    for key, a in desired.items():
        if key not in _active:
            events.append({**a, "state": "firing"})
    for key, a in list(_active.items()):
        if key not in desired:
            events.append({**a, "state": "resolved"})
    _active.clear()
    _active.update(desired)
    for e in events:
        log.warning("alert %s: %s %s — %s", e["state"], e["severity"], e["rule"], e["message"])
    return events


def active() -> list[dict]:
    return list(_active.values())


def notify_webhook(events: list[dict]) -> None:
    if not WEBHOOK or not events:
        return
    try:
        r = httpx.post(WEBHOOK, json={"source": "apps-monitor", "events": events}, timeout=10)
        r.raise_for_status()
    except Exception as e:  # noqa: BLE001 — alerting must not break monitoring
        log.warning("webhook failed: %s", type(e).__name__)
