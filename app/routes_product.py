"""S4/S7/S8/K7 API; policy reads never execute SQL."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

import queries as q

log = logging.getLogger("monitor.product")
_policies: dict[str, str] = {}
_policies_at = 0.0

WEIGHTS = {
    "availability": 25,
    "errors": 20,
    "latency": 15,
    "scan": 15,
    "review": 10,
    "cost": 10,
    "adoption": 5,
}
FORMULA = (
    "Weighted mean of available 0-100 components: availability 25%, errors 20%, "
    "latency 15%, scan 15%, review 10%, cost 10%, adoption 5%. "
    "Availability = live probe uptime (proxy reachability); errors = 100 - error%; "
    "latency = min(100, 100 * 2500ms / worst daily p95); scan = scan quality; "
    "review = 10 * review score; cost = clamp(100 * (1 - weekly compute cost growth)); "
    "adoption = min(100, distinct users in 7 days). Missing components are excluded "
    "and weights renormalized; coverage is the observed weight. Stopped apps are excluded."
)


def leaderboard_score(row: dict) -> dict:
    def number(key):
        try:
            n = float(row[key])
            return n if math.isfinite(n) else None
        except (KeyError, TypeError, ValueError):
            return None

    def clamp(n):
        return None if n is None else max(0.0, min(100.0, n))

    errors, latency, budget = number("error_pct"), number("p95_ms"), number("latency_budget_ms")
    growth = number("cost_growth")
    components = {
        "availability": clamp(number("availability_pct")),
        "errors": clamp(100 - errors) if errors is not None else None,
        "latency": clamp(100 * budget / latency)
        if latency and latency > 0 and budget and budget > 0
        else None,
        "scan": clamp(number("scan_score")),
        "review": clamp(number("review_score")),
        "cost": clamp(100 * (1 - growth)) if growth is not None else None,
        "adoption": clamp(number("users")),
    }
    coverage = sum(WEIGHTS[k] for k, v in components.items() if v is not None)
    score = sum(WEIGHTS[k] * v for k, v in components.items() if v is not None)
    return {
        "score": round(score / coverage, 2) if coverage else None,
        "coverage_pct": coverage,
        "components": components,
    }


async def refresh_policies(workspace_id: str) -> None:
    global _policies, _policies_at
    try:
        rows = await q.run(q.POLICIES, ttl=0, ws=workspace_id)
        now = datetime.now(timezone.utc)
        fresh = {}
        for row in rows:
            try:
                stamp = datetime.fromisoformat(str(row["policy_updated_at"]).replace("Z", "+00:00"))
            except (KeyError, ValueError, TypeError):
                continue
            age = (now - stamp.replace(tzinfo=stamp.tzinfo or timezone.utc)).total_seconds()
            if (
                0 <= age < 3 * 3600
                and stamp.date() == now.date()
                and row.get("throttle") in ("none", "warn", "block")
            ):
                fresh[row["name"]] = row["throttle"]
        _policies, _policies_at = fresh, time.monotonic()
    except Exception:  # noqa: BLE001 — SQL outages must not prevent fleet refresh
        log.warning("policy refresh unavailable", exc_info=True)


def cached_policy(name: str) -> dict:
    return {
        "throttle": _policies.get(name, "none") if time.monotonic() - _policies_at < 300 else "none"
    }


class ModelPrice(BaseModel):
    model: str = Field(min_length=1, max_length=200)
    effective_from: date
    input_usd_per_mtok: float = Field(ge=0, allow_inf_nan=False)
    output_usd_per_mtok: float = Field(ge=0, allow_inf_nan=False)
    source: Literal["list", "contract"] = "list"


class ProductConfig(BaseModel):
    outcome_event: str = Field(default="", max_length=64)
    token_budget_day: int = Field(default=0, ge=0, le=9_223_372_036_854_775_807, strict=True)


class FunnelSpec(BaseModel):
    steps: list[str] = Field(min_length=2, max_length=20)


def router(require_admin, workspace_id, fleet: dict, summary) -> APIRouter:
    api = APIRouter()

    async def ws():
        return str(await asyncio.to_thread(workspace_id))

    async def read(sql, **params):
        try:
            return await q.run(sql, ws=await ws(), **params)
        except Exception as e:
            raise HTTPException(
                502, "Product data unavailable; check the hourly/daily jobs."
            ) from e

    async def write(sql, **params):
        try:
            await q.run_dml(sql, ws=await ws(), **params)
            q._cache.clear()
        except Exception as e:
            raise HTTPException(
                502, "Product settings save failed; check the inventory job."
            ) from e

    @api.get("/api/policy/{name}")
    async def policy(name: str):
        return cached_policy(name)

    @api.get("/api/model-prices")
    async def prices():
        return {"prices": await read(q.MODEL_PRICES), "basis": "list price, estimate"}

    @api.put("/api/model-prices")
    async def save_price(body: ModelPrice, actor: str = Depends(require_admin)):
        await write(
            q.MODEL_PRICE_UPSERT,
            model=body.model,
            effective=body.effective_from,
            input=body.input_usd_per_mtok,
            output=body.output_usd_per_mtok,
            source=body.source,
        )
        return {"ok": True, "reprice": "next cost rollup"}

    @api.get("/api/unit-economics")
    async def fleet_economics(days: int = Query(30, ge=1, le=365)):
        return {
            "apps": await read(q.UNIT_ECONOMICS, app="", since=q.since(days * 24)),
            "basis": "list price, estimate",
            "days": days,
        }

    @api.get("/api/apps/{name}/unit-economics")
    async def economics(name: str, days: int = Query(30, ge=1, le=365)):
        return {
            "apps": await read(q.UNIT_ECONOMICS, app=name, since=q.since(days * 24)),
            "basis": "list price, estimate",
            "days": days,
        }

    @api.get("/api/apps/{name}/product-config")
    async def config(name: str):
        rows = await read(q.PRODUCT_CONFIG, app=name)
        return rows[0] if rows else {}

    @api.put("/api/apps/{name}/product-config")
    async def save_config(name: str, body: ProductConfig, actor: str = Depends(require_admin)):
        await write(
            q.PRODUCT_CONFIG_UPSERT,
            app=name,
            outcome=body.outcome_event,
            budget=body.token_budget_day,
            actor=actor,
        )
        return {"ok": True, "policy_refresh": "next hourly evaluation"}

    @api.get("/api/apps/{name}/funnels")
    async def funnels(name: str):
        return {
            "specs": await read(q.FUNNEL_SPECS, app=name),
            "steps": await read(q.FUNNELS, app=name),
        }

    @api.get("/api/apps/{name}/events")
    async def events(name: str, days: int = Query(7, ge=1, le=90)):
        return {"events": await read(q.EVENTS, app=name, since=q.since(days * 24))}

    @api.put("/api/apps/{name}/funnels/{funnel}")
    async def save_funnel(
        name: str, funnel: str, body: FunnelSpec, actor: str = Depends(require_admin)
    ):
        if not 1 <= len(funnel) <= 100 or any(not s.strip() or len(s) > 128 for s in body.steps):
            raise HTTPException(
                422, "Use a funnel name up to 100 characters and nonempty steps up to 128."
            )
        await write(q.FUNNEL_UPSERT, app=name, funnel=funnel, steps=json.dumps(body.steps))
        return {"ok": True}

    @api.get("/api/apps/{name}/cohorts")
    async def cohorts(name: str):
        return {
            "cohorts": await read(q.COHORTS, app=name),
            "basis": "observed first week within raw retention",
        }

    @api.get("/api/leaderboard")
    async def leaderboard():
        rows = await read(q.LEADERBOARD)
        ranked = []
        for row in rows:
            live = fleet.get(row["name"])
            if (
                not live
                or live.get("app_state") != "RUNNING"
                or live.get("compute_state") != "ACTIVE"
            ):
                continue
            row = {**row, "availability_pct": summary(row["name"]).get("uptime_24h")}
            ranked.append({**row, **leaderboard_score(row)})
        ranked.sort(key=lambda r: (-(r["score"] if r["score"] is not None else -1), r["name"]))
        return {"apps": ranked, "formula": FORMULA, "weights": WEIGHTS}

    @api.get("/api/apps/{name}/rum")
    async def rum(name: str, days: int = Query(7, ge=1, le=90)):
        return {"routes": await read(q.RUM, app=name, since=q.since(days * 24))}

    @api.get("/api/apps/{name}/guardrails")
    async def guardrails(name: str, days: int = Query(7, ge=1, le=90)):
        return {
            "findings": await read(q.GUARDRAILS, app=name, since=q.since(days * 24)),
            "templates": await read(q.TEMPLATE_DRIFT, app=name, since=q.since(days * 24)),
        }

    @api.get("/api/apps/{name}/drift")
    async def drift(name: str):
        return {"reports": await read(q.DRIFT_REPORTS, app=name)}

    return api
