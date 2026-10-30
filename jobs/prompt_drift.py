"""Opt-in weekly prompt drift; only numeric summaries survive the run."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timedelta, timezone

_jobs_dir = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--jobs-dir=")), "")
if _jobs_dir:
    sys.path.append(_jobs_dir)

DDL = """
CREATE TABLE IF NOT EXISTS {fq}.drift_reports (
  workspace_id STRING, name STRING, week DATE, k INT, silhouette DOUBLE,
  novel_share DOUBLE, samples INT, centroids_json STRING, computed_at TIMESTAMP
) CLUSTER BY (name, week)
COMMENT 'Weekly sampled prompt drift; centroids, training p95 distance and endpoint only, never text'
"""


def nearest_distances(points: list[list[float]], centroids: list[list[float]]) -> list[float]:
    """Euclidean distance to the closest center, independent of cluster labels."""
    if not centroids or not centroids[0]:
        raise ValueError("centroids must be nonempty")
    dimensions = len(centroids[0])
    if any(
        len(v) != dimensions or not all(math.isfinite(x) for x in v) for v in [*points, *centroids]
    ):
        raise ValueError("vectors must have matching dimensions and finite coordinates")
    return [min(math.dist(point, center) for center in centroids) for point in points]


def percentile95(distances: list[float]) -> float:
    """Linear-interpolated p95, persisted with the baseline that produced it."""
    if not distances or any(not math.isfinite(d) or d < 0 for d in distances):
        raise ValueError("distances must be finite and nonnegative")
    ordered = sorted(distances)
    position = (len(ordered) - 1) * 0.95
    lo, hi = math.floor(position), math.ceil(position)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def novel_share(
    points: list[list[float]], centroids: list[list[float]], previous_p95: float
) -> float | None:
    if not math.isfinite(previous_p95) or previous_p95 < 0:
        raise ValueError("baseline p95 must be finite and nonnegative")
    distances = nearest_distances(points, centroids)
    return sum(d > previous_p95 for d in distances) / len(distances) if distances else None


def select_k(scores: dict[int, float]) -> int | None:
    """Highest valid silhouette over 2..8; ties favor the simpler model."""
    valid = {k: s for k, s in scores.items() if 2 <= k <= 8 and math.isfinite(s) and -1 <= s <= 1}
    return min(valid, key=lambda k: (-valid[k], k)) if valid else None


def cluster(spark, points: list[list[float]]) -> tuple[list[list[float]], float | None]:
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.evaluation import ClusteringEvaluator
    from pyspark.ml.functions import array_to_vector

    unique = len({tuple(p) for p in points})
    upper = min(8, unique, len(points) - 1)
    if upper < 2:
        # Silhouette is undefined for one cluster or one point per cluster.
        center = [sum(axis) / len(points) for axis in zip(*points, strict=True)]
        return [center], None
    frame = spark.createDataFrame([(p,) for p in points], "embedding ARRAY<DOUBLE>").select(
        array_to_vector("embedding").alias("features")
    )
    evaluator = ClusteringEvaluator(distanceMeasure="squaredEuclidean")
    models, scores = {}, {}
    for k in range(2, upper + 1):
        model = KMeans(k=k, seed=14, distanceMeasure="euclidean").fit(frame)
        models[k] = model
        scores[k] = float(evaluator.evaluate(model.transform(frame)))
    k = select_k(scores)
    if k is None:
        raise ValueError("no valid silhouette")
    return [[float(x) for x in c] for c in models[k].clusterCenters()], scores[k]


def embed_prompts(spark, endpoint: str, samples: list[dict]) -> list[list[float]]:
    from quality_evals import normalize_prompt

    prompts = [normalize_prompt(s.get("request") or "") for s in samples]
    prompts = [p for p in prompts if p]
    if not prompts:
        return []
    # Only scrubbed text enters Spark; collect once so fitting seven models never re-embeds.
    spark.createDataFrame([(p,) for p in prompts], "text STRING").createOrReplaceTempView(
        "drift_prompts"
    )
    try:
        rows = spark.sql(
            "SELECT ai_query(:endpoint, text, failOnError => false) AS result FROM drift_prompts",
            args={"endpoint": endpoint},
        ).collect()
    finally:
        spark.catalog.dropTempView("drift_prompts")
    points = []
    for row in rows:
        result = row["result"]
        if result["errorMessage"] or result["response"] is None:
            # Partial embedding failure must not become an apparent recovery.
            raise ValueError("embedding failed")
        points.append([float(x) for x in result["response"]])
    if points:
        nearest_distances(points, [points[0]])
    return points


def report(points, centers, silhouette, baseline, endpoint, now):
    share = None
    if baseline and baseline.get("endpoint") == endpoint:
        share = novel_share(points, baseline["centroids"], baseline["p95_distance"])
    return {
        "week": now.date() - timedelta(days=now.weekday()),
        "k": len(centers),
        "silhouette": silhouette,
        "novel_share": share,
        "samples": len(points),
        "centroids_json": json.dumps(
            {
                "centroids": centers,
                "p95_distance": percentile95(nearest_distances(points, centers)),
                "endpoint": endpoint,
            },
            allow_nan=False,
        ),
        "computed_at": now,
    }


def drift_alert(row: dict, threshold: float) -> list[dict]:
    if row["samples"] < 50 or row["novel_share"] is None or row["novel_share"] <= threshold:
        return []
    return [
        {
            "rule": "prompt_drift",
            "app": row["name"],
            "severity": "warning",
            "message": f"{row['novel_share']:.1%} novel prompts in {row['samples']} samples (threshold {threshold:.0%})",
            "value": row["novel_share"],
        }
    ]


def run(spark, client, catalog, schema, endpoint, samples, threshold, now):
    from federation import identifier
    from quality_evals import experiment_of, sample_traces

    from source_scan import emit_alerts

    fq = f"{identifier(catalog)}.{identifier(schema)}"
    ws = str(client.get_workspace_id())
    week = now.date() - timedelta(days=now.weekday())
    spark.sql(DDL.format(fq=fq))
    previous = {
        r["name"]: json.loads(r["centroids_json"])
        for r in spark.sql(
            f"SELECT name, centroids_json FROM {fq}.drift_reports "
            "WHERE workspace_id = :ws AND week = :week",
            args={"ws": ws, "week": week - timedelta(days=7)},
        ).collect()
    }
    events, evaluated = [], set()
    for app in client.apps.list():
        try:
            experiment = experiment_of(client, app.name)
            if not experiment:
                continue
            points = embed_prompts(
                spark, endpoint, sample_traces(client, experiment, hours=168, n=samples)[:samples]
            )
            if not points:
                continue
            centers, score = cluster(spark, points)
            row = {
                "workspace_id": ws,
                "name": app.name,
                **report(points, centers, score, previous.get(app.name), endpoint, now),
            }
            spark.sql(
                f"""MERGE INTO {fq}.drift_reports t USING (
                  SELECT :workspace_id AS workspace_id, :name AS name, :week AS week,
                    :k AS k, :silhouette AS silhouette, :novel_share AS novel_share,
                    :samples AS samples, :centroids_json AS centroids_json,
                    :computed_at AS computed_at) s
                  ON t.workspace_id = s.workspace_id AND t.name = s.name AND t.week = s.week
                  WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *""",
                args=row,
            )
            events.extend(drift_alert(row, threshold))
            if row["samples"] >= 50 and row["novel_share"] is not None:
                evaluated.add(app.name)
        except Exception as e:  # noqa: BLE001 — one app's failure must not clear its incident
            print(f"{app.name}: drift unavailable ({type(e).__name__})")
    emit_alerts(
        spark, catalog, schema, events, owned_rules=("prompt_drift",), evaluated_apps=evaluated
    )


def main():
    from databricks.sdk import WorkspaceClient
    from pyspark.sql import SparkSession

    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--embedding-endpoint", default="databricks-gte-large-en")
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument("--threshold", type=float, default=0.25)
    parser.add_argument("--jobs-dir", default="")
    args = parser.parse_args()
    if args.samples < 1 or not 0 <= args.threshold <= 1 or not args.embedding_endpoint.strip():
        parser.error("samples must be positive, threshold 0-1, and endpoint nonempty")
    run(
        SparkSession.builder.getOrCreate(),
        WorkspaceClient(),
        args.catalog,
        args.schema,
        args.embedding_endpoint,
        args.samples,
        args.threshold,
        datetime.now(timezone.utc),
    )


if __name__ == "__main__":
    main()
