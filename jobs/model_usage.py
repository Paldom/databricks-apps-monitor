"""Capture final FMAPI usage before parsing model output; SDK v2 is optional."""

from datetime import UTC, datetime
from uuid import uuid4


def record_usage(spark, fq: str, ws: str, component: str, model: str, usage: dict) -> None:
    spark.sql(
        f"""INSERT INTO {fq}.monitor_model_usage
      (id, ts, component, model, input_tokens, output_tokens, workspace_id)
      VALUES (:id, :ts, :component, :model, :input, :output, :ws)""",
        args={
            "id": uuid4().hex,
            "ts": datetime.now(UTC),
            "component": component,
            "model": model,
            "input": usage.get("prompt_tokens", usage.get("input_tokens")),
            "output": usage.get("completion_tokens", usage.get("output_tokens")),
            "ws": ws,
        },
    )
