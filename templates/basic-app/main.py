"""__APP_NAME__ — provisioned by the apps-monitor toolkit.

Born observable: OTel instrumented, golden-envelope middleware, /healthz for probes.
Replace the sample endpoints with your app.
"""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from monitor_middleware import install

app = install(FastAPI(title="__APP_NAME__", docs_url=None, redoc_url=None))


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "app": "__APP_NAME__"}


@app.get("/")
async def home() -> HTMLResponse:
    return HTMLResponse(
        "<h1>__APP_NAME__</h1><p>Provisioned by the apps-monitor toolkit — "
        "telemetry, probes, scans, reviews and cost tracking are already wired. "
        "Replace this app with your own code.</p>"
    )


@app.get("/api/hello")
async def hello() -> dict:
    return {"message": "hello from __APP_NAME__"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("DATABRICKS_APP_PORT", 8000)))
