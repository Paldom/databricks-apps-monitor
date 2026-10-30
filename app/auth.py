"""Proxy identity and administrator authorization shared by API routers."""

import logging
import os

from fastapi import HTTPException, Request

log = logging.getLogger("monitor")
MONITOR_ADMINS = {
    e.strip().lower()
    for e in os.environ.get("MONITOR_ADMINS", "").split(",")
    if e.strip() and e.strip().lower() != "unset"
}


def actor_of(request: Request) -> str:
    return (
        request.headers.get("x-forwarded-email")
        or request.headers.get("x-forwarded-preferred-username")
        or request.headers.get("x-forwarded-user")
        or "unknown"
    )


def require_admin(request: Request) -> str:
    actor = actor_of(request)
    if actor.lower() not in MONITOR_ADMINS:
        log.warning("denied action %s %s by %s", request.method, request.url.path, actor)
        raise HTTPException(
            403,
            "This monitor is read-only for your account. "
            "Ask an operator to add you to MONITOR_ADMINS.",
        )
    log.info("action %s %s by %s", request.method, request.url.path, actor)
    return actor
