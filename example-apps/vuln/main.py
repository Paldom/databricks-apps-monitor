"""Demo fleet app — INTENTIONALLY smelly: scanner bait for the security iteration.

Everything here is inert (constants, fake example credentials, no user input reaches
anything dangerous) but pattern-detectable: old vulnerable pins in requirements.txt,
a hardcoded "credential", eval(), TLS verification off, debug flag. Behind workspace
OAuth like every Databricks App.
"""

from __future__ import annotations

import asyncio
import os
import random
from contextlib import asynccontextmanager

import httpx
import jinja2  # old pin with known CVE — bait
import requests
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from monitor_middleware import install

# --- scanner bait: hardcoded credentials (AWS's canonical EXAMPLE keys, not real) ---
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DATABASE_PASSWORD = "admin123"
DEBUG = True

TEMPLATE = jinja2.Template("<h1>{{ name }}</h1><p>intentionally vulnerable demo app</p>")


SYNTH_USERS = [
    "mira@synthetic.local",
    "jonas@synthetic.local",
    "petra@synthetic.local",
    "sam@synthetic.local",
]


async def self_traffic() -> None:
    await asyncio.sleep(15)
    port = os.environ.get("DATABRICKS_APP_PORT", "8000")
    while True:
        async with httpx.AsyncClient(
            base_url=f"http://127.0.0.1:{port}",
            timeout=15,
            headers={"x-forwarded-user": random.choice(SYNTH_USERS)},
        ) as c:
            for _ in range(random.randint(1, 4)):
                try:
                    await c.get(random.choice(["/api/items", "/api/calc", "/"]))
                except Exception:  # noqa: BLE001
                    pass
                await asyncio.sleep(random.uniform(2, 6))
        await asyncio.sleep(random.uniform(20, 50))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(self_traffic())
    yield
    task.cancel()


app = install(FastAPI(title="monitor-demo-vuln", lifespan=lifespan, docs_url=None, redoc_url=None))


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.get("/")
async def home() -> HTMLResponse:
    return HTMLResponse(TEMPLATE.render(name="monitor-demo-vuln"))


@app.get("/api/items")
async def items() -> dict:
    return {"items": list(range(3))}


@app.get("/api/calc")
async def calc() -> dict:
    return {"result": eval("21 * 2")}  # bait: eval on a constant — flagged, not exploitable


@app.get("/api/fetch")
async def fetch_insecure() -> dict:
    r = requests.get("https://example.com", verify=False, timeout=10)  # bait: TLS off
    return {"status": r.status_code}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("DATABRICKS_APP_PORT", 8000)))
