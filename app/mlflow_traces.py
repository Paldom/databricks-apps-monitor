"""MLflow trace info via REST — powers the unified OTel + agent trace view.

Only trace *info* comes from MLflow (list, state, previews, client_request_id).
Span detail comes from otel_spans: with MLFLOW_*_DUAL_EXPORT the agent's typed spans
land there too (attributes mlflow.spanType / mlflow.traceRequestId), and the app
container can't reach the MLflow artifact storage host anyway (egress-blocked).
"""

from __future__ import annotations

import re
import time

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
_cache: dict = {}


def _dur_ms(v) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 1)
    m = re.match(r"([\d.]+)s", str(v))  # proto duration: "1.234s"
    return round(float(m.group(1)) * 1000, 1) if m else None


def _info_dict(i: dict) -> dict:
    return {
        "trace_id": i.get("trace_id"),
        "client_request_id": i.get("client_request_id"),
        "state": str(i.get("state", "")),
        "request_time": i.get("request_time"),
        "duration_ms": _dur_ms(i.get("execution_duration_ms") or i.get("execution_duration")),
        "preview": (i.get("request_preview") or "")[:180],
        "response_preview": (i.get("response_preview") or "")[:180],
        "tags": {
            k: str(v)[:80] for k, v in (i.get("tags") or {}).items() if not k.startswith("mlflow.")
        },
    }


def search(experiment_id: str, limit: int = 50) -> list[dict]:
    key = ("search", experiment_id)
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < 45:
        return hit[1]
    d = w.api_client.do(
        "POST",
        "/api/3.0/mlflow/traces/search",
        body={
            "locations": [{"mlflow_experiment": {"experiment_id": experiment_id}}],
            "max_results": limit,
        },
    )
    infos = [t.get("trace_info", t) for t in d.get("traces", [])]
    out = sorted(
        (_info_dict(i) for i in infos), key=lambda x: x["request_time"] or "", reverse=True
    )
    _cache[key] = (time.time(), out)
    return out


def get(trace_id: str) -> dict:
    d = w.api_client.do("GET", f"/api/3.0/mlflow/traces/{trace_id}")
    info = (d.get("trace") or {}).get("trace_info") or d.get("trace_info") or d
    return {"info": _info_dict(info)}
