"""Demo fleet app — two basic agents with full monitoring correlation:

  qa_agent  — picks a topic with the LLM, calls a knowledge tool, answers (2 LLM calls)
  ops_agent — calls the apps-monitor /api/fleet API as a TOOL (cross-app OTel trace via
              traceparent propagation!) and has the LLM write an ops brief

Every request carries one correlation context end to end:
  - envelope middleware stamps client_request_id / session / user on the OTel server span
  - the same client_request_id + session go onto the MLflow trace (update_current_trace)
  - the same ids ride the AI-Gateway request tags header on every LLM call
  - llm_call records one billable span and token histogram per provider call;
    MLflow LLM spans remain available through mlflow.openai.autolog()
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from contextlib import asynccontextmanager

import httpx
import mlflow
import uvicorn
from databricks.sdk import WorkspaceClient
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from monitor_middleware import install, llm_call, set_step, track

logging.basicConfig(level="INFO")
log = logging.getLogger("agent")

NAME = os.environ.get("DATABRICKS_APP_NAME", "monitor-demo-agent")
ENDPOINT = os.environ.get("SERVING_ENDPOINT_NAME", "databricks-meta-llama-3-3-70b-instruct")
MONITOR_URL = os.environ.get("MONITOR_URL", "")
if MONITOR_URL.lower() == "unset":
    MONITOR_URL = ""
ASK_EVERY = int(os.environ.get("SELF_ASK_SECONDS", "300"))

w = WorkspaceClient()
oai = w.serving_endpoints.get_open_ai_client()

mlflow.set_tracking_uri("databricks")
if os.environ.get("MLFLOW_EXPERIMENT_ID"):
    mlflow.set_experiment(experiment_id=os.environ["MLFLOW_EXPERIMENT_ID"])
mlflow.openai.autolog()

KNOWLEDGE = {
    "delta": "Delta Lake is an open table format adding ACID transactions, time travel and schema enforcement to data lakes.",
    "otel": "OpenTelemetry is the CNCF standard for traces, metrics and logs sharing one TraceId/SpanId context.",
    "apps": "Databricks Apps host web apps on managed serverless compute behind workspace OAuth, with a service principal per app.",
    "latency": "p95 latency matters because averages hide tail pain: 1 in 20 requests is slower than p95.",
    "mlflow": "MLflow Tracing captures GenAI calls as typed spans (LLM/TOOL/AGENT) linked to OTel context.",
}

QUESTIONS = [
    "What is Delta Lake?",
    "Why watch p95 latency?",
    "What is OpenTelemetry?",
    "How do Databricks Apps authenticate?",
    "What does MLflow tracing capture?",
]


class ReqCtx:
    """Correlation ids for one request, passed explicitly through the agent."""

    def __init__(self, rid: str, sid: str, user: str):
        self.rid, self.sid, self.user = rid, sid, user
        self.in_tokens = 0
        self.out_tokens = 0

    def __repr__(self) -> str:  # shows up in MLflow trace request previews
        return f"ReqCtx({self.rid[:8]}, session={self.sid[:8]})"

    def gateway_tags(self) -> str:
        return json.dumps(
            {
                "app": NAME,
                "client_request_id": self.rid,
                "session_id": self.sid,
                "cost_center": "monitor-demo",
            }
        )


def _llm(ctx: ReqCtx, messages: list[dict], max_tokens: int = 200) -> str:
    with llm_call(ENDPOINT) as usage:
        resp = oai.chat.completions.create(
            model=ENDPOINT,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
            extra_headers={"Databricks-Ai-Gateway-Request-Tags": ctx.gateway_tags()},
        )
        inp = getattr(resp.usage, "prompt_tokens", 0) or 0
        out = getattr(resp.usage, "completion_tokens", 0) or 0
        usage.set(input_tokens=inp, output_tokens=out)
        ctx.in_tokens += inp
        ctx.out_tokens += out
        content = resp.choices[0].message.content
        return content if isinstance(content, str) else str(content)


@mlflow.trace(span_type="TOOL")
def knowledge_lookup(topic: str) -> str:
    text = topic.strip().lower()
    for key, fact in KNOWLEDGE.items():  # fuzzy: models rarely return the bare key
        if key in text:
            return fact
    return "no entry — answer from general knowledge, briefly."


@mlflow.trace(span_type="TOOL")
def fetch_fleet_status() -> dict:
    """Calls the monitor app's API — traceparent propagates, so the monitor's server
    span joins THIS trace (cross-app correlation)."""
    if not MONITOR_URL:
        return {"error": "MONITOR_URL not configured"}
    r = httpx.get(f"{MONITOR_URL}/api/fleet", headers=w.config.authenticate(), timeout=20)
    r.raise_for_status()
    d = r.json()
    return {"kpis": d["kpis"], "attention": [(a["name"], a["status"]) for a in d["attention"]]}


@mlflow.trace(span_type="AGENT")
def qa_agent(ctx: ReqCtx, question: str) -> dict:
    mlflow.update_current_trace(
        client_request_id=ctx.rid,
        metadata={"mlflow.trace.session": ctx.sid, "mlflow.trace.user": ctx.user},
        tags={"app": NAME, "agent": "qa"},
    )
    topic = _llm(
        ctx,
        [
            {
                "role": "system",
                "content": f"Pick the single most relevant topic key from: {list(KNOWLEDGE)}. Reply with just the key.",
            },
            {"role": "user", "content": question},
        ],
        max_tokens=10,
    )
    facts = knowledge_lookup(topic)
    answer = _llm(
        ctx,
        [
            {"role": "system", "content": f"Answer in <=2 sentences using this context: {facts}"},
            {"role": "user", "content": question},
        ],
    )
    return {"agent": "qa", "topic": topic.strip(), "answer": answer}


@mlflow.trace(span_type="AGENT")
def ops_agent(ctx: ReqCtx) -> dict:
    mlflow.update_current_trace(
        client_request_id=ctx.rid,
        metadata={"mlflow.trace.session": ctx.sid, "mlflow.trace.user": ctx.user},
        tags={"app": NAME, "agent": "ops"},
    )
    fleet = fetch_fleet_status()
    summary = _llm(
        ctx,
        [
            {
                "role": "system",
                "content": "You are an SRE. Write a 2-sentence ops brief from this fleet status JSON.",
            },
            {"role": "user", "content": json.dumps(fleet)[:3000]},
        ],
    )
    return {"agent": "ops", "summary": summary, "fleet": fleet}


def _run_agent(fn, ctx: ReqCtx, *args) -> dict:
    result = fn(ctx, *args)
    return {
        **result,
        "usage": {"input_tokens": ctx.in_tokens, "output_tokens": ctx.out_tokens},
        "client_request_id": ctx.rid,
        "model": ENDPOINT,
    }


def _ctx(request: Request) -> ReqCtx:
    env = getattr(request.state, "monitor", None) or {}
    return ReqCtx(
        rid=env.get("rid", "unknown"),
        sid=env.get("sid", "unknown"),
        user=env.get("user", "anon"),
    )


SYNTH_USERS = [
    "mira@synthetic.local",
    "jonas@synthetic.local",
    "petra@synthetic.local",
    "sam@synthetic.local",
]


async def self_traffic() -> None:
    await asyncio.sleep(45)
    port = os.environ.get("DATABRICKS_APP_PORT", "8000")
    while True:
        # fresh client per ask = fresh session; rotating users → GenAI top-consumer analytics
        async with httpx.AsyncClient(
            base_url=f"http://127.0.0.1:{port}",
            timeout=120,
            headers={"x-forwarded-user": random.choice(SYNTH_USERS)},
        ) as c:
            try:
                if random.random() < 0.5:
                    await c.get("/api/ask", params={"q": random.choice(QUESTIONS)})
                else:
                    await c.get("/api/ops/brief")
                if random.random() < 0.3:  # occasional user feedback → v_feedback demo data
                    await c.post(
                        "/monitor/feedback",
                        json={
                            "rating": random.choices([1, 2, 3, 4, 5], weights=[1, 1, 2, 5, 6])[0],
                            "comment": random.choice(
                                [
                                    "helpful",
                                    "great answer",
                                    "too slow",
                                    "wrong answer",
                                    "exactly what I needed",
                                    "",
                                ]
                            ),
                        },
                    )
            except Exception:
                log.exception("self-traffic failed")
        await asyncio.sleep(ASK_EVERY * random.uniform(0.8, 1.2))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(self_traffic())
    yield
    task.cancel()


app = install(FastAPI(title=NAME, lifespan=lifespan, docs_url=None, redoc_url=None))


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "endpoint": ENDPOINT, "agents": ["qa", "ops"]}


@app.get("/")
async def home() -> HTMLResponse:
    return HTMLResponse(
        f"<h1>{NAME}</h1><p>two demo agents on <code>{ENDPOINT}</code>, MLflow-traced &"
        f" cost-tagged.<br>Try <code>/api/ask?q=what is delta lake</code> or"
        f" <code>/api/ops/brief</code>. Self-traffic every ~{ASK_EVERY}s.</p>"
    )


@app.get("/api/ask")
async def ask(q: str, request: Request) -> dict:
    ctx = _ctx(request)
    set_step("ask")
    result = await asyncio.to_thread(_run_agent, qa_agent, ctx, q[:500])
    track("answer_generated", request, agent="qa")
    return result


@app.get("/api/ops/brief")
async def ops_brief(request: Request) -> dict:
    ctx = _ctx(request)
    set_step("ops_brief")
    result = await asyncio.to_thread(_run_agent, ops_agent, ctx)
    track("brief_generated", request, agent="ops")
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("DATABRICKS_APP_PORT", 8000)))
