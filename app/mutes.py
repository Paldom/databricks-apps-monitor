"""Notification mute matching, shared with job emitters; no runtime dependencies."""

from datetime import UTC, datetime
from fnmatch import fnmatchcase


def utc(value: datetime | str) -> datetime:
    value = (
        datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    )
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def is_muted(app: str, rule: str, mutes: list[dict], now: datetime) -> bool:
    """Match case-sensitive globs in a half-open UTC window [start, end)."""
    for mute in mutes:
        try:
            if (
                utc(mute["starts_at"]) <= utc(now) < utc(mute["ends_at"])
                and fnmatchcase(app, mute["app"])
                and fnmatchcase(rule, mute["rule"])
            ):
                return True
        except (KeyError, TypeError, ValueError):
            continue
    return False
