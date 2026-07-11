"""Demo fleet app — behavior selected by DEMO_MODE: healthy | flaky | slow.

A background task generates its own traffic so telemetry flows without external
load. flaky ≈ 8% HTTP 500 + 3% unhandled exceptions; slow adds 0.2–2.5 s latency
with occasional 8 s stalls.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
import uuid
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from monitor_middleware import install

logging.basicConfig(level="INFO")
log = logging.getLogger("demo")

MODE = os.environ.get("DEMO_MODE", "healthy")
NAME = os.environ.get("DATABRICKS_APP_NAME", f"monitor-demo-{MODE}")


async def misbehave() -> None:
    if MODE == "slow":
        await asyncio.sleep(8 if random.random() < 0.04 else random.uniform(0.2, 2.5))
    elif MODE == "flaky":
        r = random.random()
        if r < 0.08:
            raise HTTPException(500, "synthetic upstream failure")
        if r < 0.11:
            raise ValueError("synthetic unhandled exception")


# synthetic population: weighted users so adoption/per-user analytics have shape
SYNTH_USERS = [
    "mira@synthetic.local",
    "jonas@synthetic.local",
    "petra@synthetic.local",
    "sam@synthetic.local",
    "aki@synthetic.local",
    "lena@synthetic.local",
]
USER_WEIGHTS = [8, 5, 3, 2, 1, 1]


async def self_traffic() -> None:
    await asyncio.sleep(15)
    port = os.environ.get("DATABRICKS_APP_PORT", "8000")
    while True:
        user = random.choices(SYNTH_USERS, weights=USER_WEIGHTS)[0]
        # a fresh client per burst = a fresh session cookie → real session analytics
        async with httpx.AsyncClient(
            base_url=f"http://127.0.0.1:{port}", timeout=15, headers={"x-forwarded-user": user}
        ) as c:
            for _ in range(random.randint(2, 6)):
                path = random.choice(
                    ["/api/items", "/api/items", "/api/work", "/api/checkout", "/api/missing"]
                )
                try:
                    await (c.post(path) if path == "/api/checkout" else c.get(path))
                except Exception:  # noqa: BLE001 — traffic generator must never die
                    pass
                await asyncio.sleep(random.uniform(1, 5))
        await asyncio.sleep(random.uniform(15, 45))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(self_traffic())
    yield
    task.cancel()


app = install(FastAPI(title=NAME, lifespan=lifespan, docs_url=None, redoc_url=None))


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "mode": MODE}


@app.get("/")
async def home() -> HTMLResponse:
    return HTMLResponse(
        f"<h1>{NAME}</h1><p>mode: <b>{MODE}</b> — part of the apps-monitoring demo fleet</p>"
    )


@app.get("/api/items")
async def items() -> dict:
    await misbehave()
    return {"items": [{"id": i, "sku": f"SKU-{i:04d}"} for i in range(5)]}


@app.post("/api/checkout")
async def checkout() -> dict:
    await misbehave()
    return {"order": uuid.uuid4().hex[:10], "status": "confirmed"}


@app.get("/api/work")
async def work() -> dict:
    await misbehave()
    t = time.perf_counter()
    sum(x * x for x in range(50_000))
    return {"work_ms": round((time.perf_counter() - t) * 1000, 2)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("DATABRICKS_APP_PORT", 8000)))
