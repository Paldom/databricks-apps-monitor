"""Run the demo's provider path with local stand-ins for deployment dependencies."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import monitor_middleware as mm


def test_agent_billable_calls_keep_usage_and_gateway_tags(
    monkeypatch: pytest.MonkeyPatch, span_exporter: InMemorySpanExporter
) -> None:
    monkeypatch.delenv("MONITOR_URL", raising=False)
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=3),
            choices=[SimpleNamespace(message=SimpleNamespace(content="delta"))],
        )

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    workspace = SimpleNamespace(
        serving_endpoints=SimpleNamespace(get_open_ai_client=lambda: client)
    )
    sdk = ModuleType("databricks.sdk")
    sdk.WorkspaceClient = lambda: workspace
    monkeypatch.setitem(sys.modules, "databricks.sdk", sdk)
    mlflow = ModuleType("mlflow")
    mlflow.set_tracking_uri = lambda *args: None
    mlflow.set_experiment = lambda **kwargs: None
    mlflow.update_current_trace = lambda **kwargs: None
    mlflow.openai = SimpleNamespace(autolog=lambda: None)
    mlflow.trace = lambda **kwargs: lambda fn: fn
    monkeypatch.setitem(sys.modules, "mlflow", mlflow)
    for name in ("httpx", "uvicorn"):
        monkeypatch.setitem(sys.modules, name, ModuleType(name))
    demo = runpy.run_path(str(Path(__file__).parents[1] / "example-apps/agent/main.py"))
    ctx = demo["ReqCtx"]("rid", "sid", "hash")
    result = demo["_run_agent"](demo["qa_agent"], ctx, "What is Delta?")
    assert result["usage"] == {"input_tokens": 20, "output_tokens": 6}
    assert result["answer"] == "delta"
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 2
    for span in spans:
        assert span.attributes["monitor.llm.billable"] is True
        assert span.attributes["gen_ai.usage.input_tokens"] == 10
        assert span.attributes["gen_ai.usage.output_tokens"] == 3
    assert len(calls) == 2
    for call in calls:
        tags = json.loads(call["extra_headers"]["Databricks-Ai-Gateway-Request-Tags"])
        assert tags["client_request_id"] == "rid" and tags["session_id"] == "sid"
    monkeypatch.setattr(mm, "_policy", lambda: {"throttle": "block"})
    with pytest.raises(mm.BudgetExceeded):
        demo["_llm"](ctx, [])
    assert len(calls) == 2
