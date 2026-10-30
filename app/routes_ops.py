"""Maintenance, SLOs, telemetry quality and monitor cost APIs."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from auth import require_admin
from fastapi import APIRouter, Depends, HTTPException
from pydantic import AwareDatetime, BaseModel, Field, model_validator

import alerts
import queries as q

router = APIRouter()


class MuteSpec(BaseModel):
    app: str = Field(min_length=1, max_length=128)
    rule: str = Field(default="*", min_length=1, max_length=128)
    starts_at: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ends_at: AwareDatetime
    reason: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def window(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must follow starts_at")
        return self


class SloSpec(BaseModel):
    slo: str = Field(min_length=1, max_length=80, pattern=r"^[\w.-]+$")
    sli: Literal["availability", "latency"]
    target: float = Field(gt=0, lt=1, allow_inf_nan=False)
    threshold_ms: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    window_days: int = Field(default=28, ge=1, le=90)
    route_filter: str | None = Field(default=None, max_length=256)

    @model_validator(mode="after")
    def latency_threshold(self):
        if self.sli == "latency" and self.threshold_ms is None:
            raise ValueError("latency SLOs require threshold_ms")
        return self


async def workspace() -> str:
    return str(await asyncio.to_thread(q.w.get_workspace_id))


async def audit(ws: str, actor: str, action: str, app: str, params: dict) -> None:
    await q.run_dml(
        q.OPS_AUDIT, ws=ws, actor=actor, action=action, app=app, params=json.dumps(params)
    )
    q._cache.clear()


@router.get("/api/actions/mute")
async def list_mutes() -> dict:
    return {"mutes": await q.run(q.ACTIVE_MUTES, ttl=0, ws=await workspace())}


@router.post("/api/actions/mute")
async def mute(body: MuteSpec, actor: str = Depends(require_admin)) -> dict:
    ws, ident = await workspace(), uuid4().hex
    if body.ends_at <= datetime.now(timezone.utc):
        raise HTTPException(422, "ends_at must be in the future")
    params = body.model_dump(mode="json")
    await q.run_dml(q.MUTE_INSERT, ws=ws, id=ident, actor=actor, **params)
    alerts.set_mutes(await q.run(q.ACTIVE_MUTES, ttl=0, ws=ws))
    await audit(ws, actor, "mute", body.app, {"id": ident, **params})
    return {"id": ident, "ok": True}


@router.delete("/api/actions/mute")
@router.delete("/api/actions/mute/{id}")
async def unmute(id: str, actor: str = Depends(require_admin)) -> dict:
    ws = await workspace()
    rows = await q.run(q.MUTE_GET, ttl=0, ws=ws, id=id)
    if not rows:
        raise HTTPException(404, "mute not found")
    await q.run_dml(q.MUTE_DELETE, ws=ws, id=id)
    alerts.set_mutes(await q.run(q.ACTIVE_MUTES, ttl=0, ws=ws))
    await audit(ws, actor, "unmute", rows[0]["app"], {"id": id})
    return {"ok": True}


@router.post("/api/apps/{name}/slo")
@router.put("/api/apps/{name}/slo")
async def upsert_slo(name: str, body: SloSpec, actor: str = Depends(require_admin)) -> dict:
    ws = await workspace()
    params = body.model_dump()
    await q.run_dml(
        q.SLO_UPSERT,
        ws=ws,
        app=name,
        actor=actor,
        revision=uuid4().hex,
        **{k: "" if v is None else v for k, v in params.items()},
    )
    await audit(ws, actor, "slo_upsert", name, params)
    return {"ok": True}


@router.delete("/api/apps/{name}/slo/{slo}")
async def delete_slo(name: str, slo: str, actor: str = Depends(require_admin)) -> dict:
    ws = await workspace()
    await q.run_dml(q.SLO_DELETE, ws=ws, app=name, slo=slo)
    await audit(ws, actor, "slo_delete", name, {"slo": slo})
    return {"ok": True}


@router.get("/api/apps/{name}/slo")
async def get_slo(name: str) -> dict:
    ws = await workspace()
    specs, series = await asyncio.gather(
        q.run(q.SLO_SUMMARY, ws=ws, app=name), q.run(q.SLO_SERIES, ws=ws, app=name)
    )
    return {
        "specs": specs,
        "series": series,
        "basis": "sampled server spans; no traffic is unknown",
    }


@router.get("/api/apps/{name}/telemetry-health")
async def telemetry_health(name: str) -> dict:
    rows = await q.run(q.TELEMETRY_HEALTH, ws=await workspace(), app=name)
    return {"health": rows[0] if rows else None}


@router.get("/api/monitor/cost")
async def monitor_cost() -> dict:
    ws = await workspace()
    cost, storage = await asyncio.gather(
        q.run(q.MONITOR_COST, ws=ws), q.run(q.MONITOR_STORAGE, ws=ws)
    )
    return {"daily": cost, "storage": storage}
