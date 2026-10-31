"""Network-free helpers for reach routes and synthetic alert evidence."""

from collections import defaultdict, deque
from datetime import UTC, datetime
from time import monotonic


class CallerRateLimit:
    def __init__(self, limit=60, window=60, max_callers=4096, clock=monotonic):
        self.limit, self.window, self.max_callers, self.clock = limit, window, max_callers, clock
        self.calls = {}

    def allow(self, caller):
        now = self.clock()
        for key in list(self.calls):
            if self.calls[key][-1] <= now - self.window:
                del self.calls[key]
        if caller not in self.calls:
            if len(self.calls) >= self.max_callers:
                return False
            self.calls[caller] = deque()
        calls = self.calls[caller]
        while calls and calls[0] <= now - self.window:
            calls.popleft()
        if len(calls) >= self.limit:
            return False
        calls.append(now)
        return True


def truth(value):
    return value is True or str(value).lower() == "true"


def epoch(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value.replace(tzinfo=value.tzinfo or UTC).timestamp()


def vantage_decisions(rows, now, max_age=7200, expected=()):
    """Tri-state per app: failure, recovery, or insufficient evidence (omitted).

    Steps and retries count once per run. Compare the same journey across the two
    vantages; stale/missing evidence must neither page nor clear an open incident.
    """
    runs = {}
    for row in rows:
        if row.get("vantage") not in ("internal", "external") or not row.get("run_id"):
            continue
        ts = epoch(row["run_ts"])
        if not now - max_age <= ts <= now:
            continue
        key = (row["app"], row["journey"], row["vantage"], row["run_id"])
        previous = runs.get(key, (ts, True))
        runs[key] = (max(previous[0], ts), previous[1] and truth(row["ok"]))
    histories = defaultdict(list)
    for (app, journey, vantage, run_id), (ts, ok) in runs.items():
        histories[app, journey, vantage].append((ts, run_id, ok))
    journeys = defaultdict(list)
    for app, journey in {(a, j) for a, j, _ in histories} | set(expected):
        latest = [
            sorted(histories[app, journey, v], reverse=True)[:2] for v in ("internal", "external")
        ]
        if all(len(h) == 2 for h in latest):
            journeys[app].append(all(not r[2] for h in latest for r in h))
        else:
            journeys[app].append(None)
    return {
        app: any(states)
        for app, states in journeys.items()
        if any(states) or all(s is not None for s in states)
    }


def uptime_bars(points, now, hours=24):
    """Fixed hourly buckets; absent observations remain unknown, including restarts."""
    start = int(now // 3600) * 3600 - (hours - 1) * 3600
    buckets = [[] for _ in range(hours)]
    for ts, ok, *_ in points:
        index = int((ts - start) // 3600)
        if 0 <= index < hours and ts <= now:
            buckets[index].append(bool(ok))
    return [
        {
            "ts": start + i * 3600,
            "checks": len(b),
            "uptime": round(100 * sum(b) / len(b), 2) if b else None,
        }
        for i, b in enumerate(buckets)
    ]
