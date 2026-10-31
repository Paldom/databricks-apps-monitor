"""Agentic code review — a Databricks-hosted LLM reviews each app's source like a CTO
gating a production sign-off. Runs daily; reviews only deployments not reviewed yet.

The prompt asks for strict JSON: verdict, scores (security / reliability /
maintainability / cost / monitoring), strengths, findings with recommendations.
Results land in llm_reviews; v_review_latest exposes the newest review per app.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime

import httpx
from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession

# serverless python tasks run without __file__ — the bundle passes --jobs-dir instead
_jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
if _jobs_dir:
    sys.path.append(_jobs_dir)
from source_scan import list_source_files, read_file  # noqa: E402 — shared helpers

MAX_TOTAL = 60_000  # chars of source shipped to the model
MAX_FILE = 8_000

SYSTEM = """You are a pragmatic CTO reviewing a Databricks App before production sign-off.
Databricks Apps context: the app runs behind workspace OAuth on managed serverless compute,
has a per-app service principal, gets resources (warehouse, endpoints, secrets) injected via
env vars, must bind 0.0.0.0:$DATABRICKS_APP_PORT, logs to stdout, has no persistent local disk,
and should export OpenTelemetry to Unity Catalog. Judge production readiness, not style.
Be specific and cite files. Respond with STRICT JSON only — no markdown, no prose around it:
{
 "verdict": "approve" | "approve_with_conditions" | "reject",
 "summary": "<= 60 words, the sign-off paragraph",
 "scores": {"security": 0-10, "reliability": 0-10, "maintainability": 0-10,
            "cost_efficiency": 0-10, "monitoring": 0-10},
 "strengths": ["..."],
 "findings": [{"severity": "critical|high|medium|low",
               "area": "security|reliability|maintainability|cost|monitoring",
               "title": "...", "recommendation": "..."}],
 "overview": {"purpose": "<= 25 words: what this app does and for whom>",
              "tech_stack": ["frameworks/major libs, e.g. FastAPI, MLflow, lodash"],
              "endpoints": ["METHOD /path — one-line purpose (max 8, user-facing first)"]}
}
At most 10 findings, ordered by severity."""


def pack_source(w: WorkspaceClient, root: str) -> tuple[str, int]:
    paths = list_source_files(w, root)

    # priority: config + entrypoints first, tests last
    def prio(p: str) -> int:
        base = p.rsplit("/", 1)[-1].lower()
        if base in ("app.yaml", "requirements.txt", "databricks.yml"):
            return 0
        if base in ("main.py", "app.py", "run_app.py"):
            return 1
        if "test" in base:
            return 3
        return 2

    tree = "\n".join(p.rsplit("/files/", 1)[-1] for p in sorted(paths))
    parts = [f"== FILE TREE ==\n{tree}\n"]
    total = len(parts[0])
    for p in sorted(paths, key=prio):
        if total > MAX_TOTAL:
            parts.append("== TRUNCATED: size budget reached ==")
            break
        content = read_file(w, p)
        if not content:
            continue
        chunk = f"\n== {p.rsplit('/files/', 1)[-1]} ==\n{content[:MAX_FILE]}"
        parts.append(chunk)
        total += len(chunk)
    return "".join(parts), len(paths)


def call_model(
    w: WorkspaceClient, model: str, source_pack: str, app_name: str, usage_sink=None
) -> tuple[dict, dict]:
    body = {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"App name: {app_name}\n\nSource:\n{source_pack}"},
        ],
        "max_tokens": 3000,
        "temperature": 0.1,
    }
    r = httpx.post(
        f"{w.config.host}/serving-endpoints/{model}/invocations",
        json=body,
        headers=w.config.authenticate(),
        timeout=240,
    )
    r.raise_for_status()
    data = r.json()
    if usage_sink:
        usage_sink(data.get("usage", {}))
    text = data["choices"][0]["message"]["content"]
    if isinstance(text, list):  # some endpoints return content blocks
        text = "".join(b.get("text", "") for b in text)
    m = re.search(r"\{.*\}", text, re.S)
    review = json.loads(m.group(0)) if m else {"verdict": "unparseable", "summary": text[:400]}
    return review, data.get("usage", {})


DDL = """
CREATE TABLE IF NOT EXISTS {fq}.llm_reviews (
  reviewed_at TIMESTAMP, name STRING, deployment_id STRING, model STRING,
  verdict STRING, summary STRING,
  score_security INT, score_reliability INT, score_maintainability INT,
  score_cost INT, score_monitoring INT, score_overall DOUBLE,
  strengths_json STRING, findings_json STRING, overview_json STRING,
  files_reviewed INT, prompt_chars INT, input_tokens INT, output_tokens INT
) COMMENT 'Agentic code reviews of app source (monitor-llm-review job, FMAPI)'"""


def main() -> None:
    from model_usage import record_usage
    from ops_tables import ensure_ops_tables

    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--model", default="databricks-claude-sonnet-4-5")
    p.add_argument("--max-apps", type=int, default=20)
    p.add_argument("--force", action="store_true")
    p.add_argument("--only-app", default="", help="review a single app regardless of state")
    p.add_argument("--jobs-dir", default="", help="workspace path of the jobs dir (import path)")
    args = p.parse_args()
    fq = f"`{args.catalog}`.`{args.schema}`"

    w = WorkspaceClient()
    spark = SparkSession.builder.getOrCreate()
    spark.sql(DDL.format(fq=fq))
    ensure_ops_tables(spark, fq)
    ws = str(w.get_workspace_id())
    try:  # table may predate the overview column
        spark.sql(f"ALTER TABLE {fq}.llm_reviews ADD COLUMNS (overview_json STRING)")
    except Exception:  # noqa: BLE001 — already there
        pass

    reviewed = (
        set()
        if (args.force or args.only_app)
        else {
            (r["name"], r["deployment_id"])
            for r in spark.sql(
                f"SELECT DISTINCT name, deployment_id FROM {fq}.llm_reviews"
            ).collect()
        }
    )

    ts = datetime.now(UTC)
    rows = []
    for a in w.apps.list():
        if args.only_app and a.name != args.only_app:
            continue
        dep = a.active_deployment
        if not dep or not dep.source_code_path:
            continue
        if (a.name, dep.deployment_id) in reviewed:
            print(f"{a.name}: deployment already reviewed")
            continue
        if len(rows) >= args.max_apps:
            break
        print(f"reviewing {a.name} with {args.model}")
        try:
            pack, n_files = pack_source(w, dep.source_code_path)
            review, usage = call_model(
                w,
                args.model,
                pack,
                a.name,
                usage_sink=lambda usage: record_usage(spark, fq, ws, "review", args.model, usage),
            )
        except Exception as e:  # noqa: BLE001 — one bad app must not sink the run
            print(f"  review failed: {e}")
            continue
        if review.get("verdict") not in ("approve", "approve_with_conditions", "reject"):
            review["verdict"] = "unparseable"  # model output is untrusted — whitelist it
        scores = review.get("scores", {})
        vals = [
            scores.get(k)
            for k in ("security", "reliability", "maintainability", "cost_efficiency", "monitoring")
        ]
        nums = [v for v in vals if isinstance(v, (int, float))]
        rows.append(
            {
                "reviewed_at": ts,
                "name": a.name,
                "deployment_id": dep.deployment_id,
                "model": args.model,
                "verdict": str(review.get("verdict", "unknown"))[:40],
                "summary": str(review.get("summary", ""))[:1000],
                "score_security": scores.get("security"),
                "score_reliability": scores.get("reliability"),
                "score_maintainability": scores.get("maintainability"),
                "score_cost": scores.get("cost_efficiency"),
                "score_monitoring": scores.get("monitoring"),
                "score_overall": round(sum(nums) / len(nums), 1) if nums else None,
                "strengths_json": json.dumps(review.get("strengths", []))[:4000],
                "findings_json": json.dumps(review.get("findings", []))[:16000],
                "overview_json": json.dumps(review.get("overview", {}))[:4000],
                "files_reviewed": n_files,
                "prompt_chars": len(pack),
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
            }
        )
        print(
            f"  verdict: {rows[-1]['verdict']} · overall {rows[-1]['score_overall']} · {len(review.get('findings', []))} findings"
        )

    if rows:
        spark.createDataFrame(
            rows, schema=spark.table(f"{args.catalog}.{args.schema}.llm_reviews").schema
        ).write.mode("append").saveAsTable(f"{args.catalog}.{args.schema}.llm_reviews")

    from source_scan import emit_alerts  # same jobs dir (path set above)

    emit_alerts(
        spark,
        args.catalog,
        args.schema,
        [
            {
                "rule": "review_reject",
                "app": r["name"],
                "severity": "high",
                "message": f"code review verdict: {r['verdict']} — {r['summary'][:150]}",
                "value": r["score_overall"],
            }
            for r in rows
            if r["verdict"] == "reject"
        ],
        owned_rules=("review_reject",),
        evaluated_apps={r["name"] for r in rows},
    )
    spark.sql(f"""CREATE OR REPLACE VIEW {fq}.v_review_latest
        COMMENT 'Latest code review per app' AS
        SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY name ORDER BY reviewed_at DESC) rn
                       FROM {fq}.llm_reviews) WHERE rn = 1""")
    print(f"done: {len(rows)} apps reviewed")


if __name__ == "__main__":
    main()
