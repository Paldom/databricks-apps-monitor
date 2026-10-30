"""Deterministic SDK fixture. Only the validator generates traffic; see CONFORMANCE.md."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from monitor_middleware import BudgetExceeded, install, llm_call, set_step, trace_sql, track

MODEL = "conformance-fake-model"
# built at runtime so secret scanners never see a token-shaped literal in source
PAT = "dapi" + "0123456789abcdef" * 2
health_state = {"ok": True}
logging.basicConfig(level=logging.INFO)
app = install(
    FastAPI(),
    health_checks={"always_ok": lambda: True, "toggle": lambda: health_state["ok"]},
    rum=True,
    rum_sample=1.0,
)


class ProviderError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


FAILURES = {
    "rate_limit": ("rate limit", 429),
    "timeout": ("provider timeout", 504),
    "policy": ("content policy", 400),
    "schema": ("schema validation", 400),
    "server": ("provider unavailable", 503),
}


@app.get("/c/ok")
async def ok():
    return {"ok": True}


@app.get("/c/error")
async def error():
    raise RuntimeError("conformance deterministic exception")


@app.get("/c/client-error")
async def client_error():
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/c/slow")
async def slow(ms: int = Query(300, ge=0, le=10000)):
    await asyncio.sleep(ms / 1000)
    return {"slept_ms": ms}


@app.get("/c/llm")
async def llm(
    input_tokens: int = Query(1000, alias="in", ge=0, le=1000000),
    output_tokens: int = Query(200, alias="out", ge=0, le=1000000),
    stream: int = Query(0, ge=0, le=1),
    chunks: int = Query(10, ge=1, le=100),
    fail: Literal["none", "rate_limit", "timeout", "policy", "schema", "server"] = "none",
):
    # Fail before response headers, including when stream=1, so HTTP status is deterministic.
    if fail != "none":
        try:
            with llm_call(MODEL, streaming=bool(stream)):
                raise ProviderError(*FAILURES[fail])
        except ProviderError:
            return JSONResponse({"failure": fail}, status_code=502)
    if stream:

        async def generate():
            with llm_call(MODEL, streaming=True) as usage:
                for index in range(1, chunks + 1):
                    await asyncio.sleep(0.01)
                    usage.first_token()
                    usage.set(
                        input_tokens=input_tokens, output_tokens=output_tokens * index // chunks
                    )
                    yield f"data: {index}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    with llm_call(MODEL) as usage:
        usage.set(input_tokens=input_tokens, output_tokens=output_tokens)
    return {"input": input_tokens, "output": output_tokens}


@app.post("/c/event")
async def event(request: Request, name: str = Query(min_length=1, max_length=64)):
    track(name, request=request, fixture="conformance")
    return {"event": name}


@app.get("/c/step")
async def step(name: str = Query(min_length=1, max_length=64)):
    set_step(name)
    return {"step": name}


@app.get("/c/sql")
async def sql(rows: int = Query(42, ge=0, le=1000000)):
    with trace_sql("conformance-fake-warehouse") as result:
        result.statement_id = "conformance-fake-statement"
        result.rows = rows
    return {"rows": rows}


@app.get("/c/leak")
async def leak(token: str = Query(max_length=128), email: str = Query(max_length=128)):
    logging.getLogger("conformance.leak").warning("email=%s Bearer %s PAT=%s", email, token, PAT)
    return {"ok": True}


@app.post("/c/health-toggle")
async def health_toggle(ok: int = Query(ge=0, le=1)):
    health_state["ok"] = bool(ok)
    return {"ok": bool(ok), "cache_ttl_s": 30}


@app.get("/c/budget")
async def budget():
    try:
        with llm_call("conformance-budget-model") as usage:
            usage.set(input_tokens=0, output_tokens=0)
    except BudgetExceeded:
        return JSONResponse({"error": "budget exceeded"}, status_code=429)
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
async def index(run: str = Query("manual", pattern=r"^[A-Za-z0-9_.-]{1,32}$")):
    return """<!doctype html><title>SDK conformance</title><h1>SDK conformance</h1>
<script src="/monitor/rum.js" data-sample="1"></script>
<script>
setTimeout(() => { history.pushState({}, '', __ROUTE__);
  throw new Error('conformance browser error'); }, 100);
</script>""".replace("__ROUTE__", json.dumps(f"/conformance-route/{run}"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host="0.0.0.0", port=int(os.getenv("DATABRICKS_APP_PORT", "8000")), access_log=False
    )
