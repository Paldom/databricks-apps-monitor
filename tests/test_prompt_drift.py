"""Drift math and deployment adapters, without a Spark runtime or network."""

import asyncio
import json
import sys
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from test_product import product_app, request
from test_service_correctness import ROOT
from test_service_correctness import service as service

NOW = datetime(2026, 10, 26, 7, tzinfo=timezone.utc)


def test_novel_share_uses_previous_centers_and_strict_cutoff(service):
    drift = service.prompt_drift
    points = [[0.0, 0.0], [3.0, 4.0], [10.0, 0.0], [20.0, 0.0]]
    centers = [[0.0, 0.0], [10.0, 0.0]]
    assert drift.nearest_distances(points, centers) == [0, 5, 0, 10]
    assert drift.novel_share(points, centers, 5) == 0.25
    assert drift.novel_share(points, centers[::-1], 5) == 0.25
    assert drift.novel_share([[0.0], [1.0]], [[0.0]], 0) == 0.5
    assert drift.novel_share([], centers, 5) is None


@pytest.mark.parametrize(
    "points,centers,p95",
    [
        ([[1]], [], 1),
        ([[1]], [[]], 1),
        ([[1, 2]], [[1]], 1),
        ([[float("nan")]], [[1]], 1),
        ([[1]], [[float("inf")]], 1),
        ([[1]], [[1]], -1),
        ([[1]], [[1]], float("nan")),
    ],
)
def test_invalid_distances_fail_instead_of_reporting_recovery(service, points, centers, p95):
    with pytest.raises(ValueError):
        service.prompt_drift.novel_share(points, centers, p95)


def test_p95_and_silhouette_selection(service):
    drift = service.prompt_drift
    assert drift.percentile95(list(range(21))) == 19
    assert drift.percentile95([0, 10]) == 9.5
    assert drift.percentile95([2]) == 2
    for values in ([], [-1], [float("inf")]):
        with pytest.raises(ValueError):
            drift.percentile95(values)
    assert drift.select_k({2: 0.1, 3: 0.7, 4: 0.7, 8: 0.5}) == 3
    assert drift.select_k({1: 1, 2: -0.5, 8: -0.1, 9: 1}) == 8
    assert drift.select_k({2: float("nan"), 3: float("inf"), 4: 1.1}) is None
    assert drift.select_k({}) is None


def test_report_records_baseline_cutoff_and_only_compares_same_endpoint(service):
    drift = service.prompt_drift
    baseline = {"centroids": [[0.0]], "p95_distance": 1.0, "endpoint": "embedding"}
    row = drift.report([[10.0], [11.0]], [[10.5]], 0.8, baseline, "embedding", NOW)
    assert row["novel_share"] == 1.0
    assert row["week"].isoformat() == "2026-10-26"
    stored = json.loads(row["centroids_json"])
    assert stored == {"centroids": [[10.5]], "p95_distance": 0.5, "endpoint": "embedding"}
    for previous, endpoint in ((None, "embedding"), (baseline, "new-endpoint")):
        row = drift.report([[10.0]], [[10.0]], None, previous, endpoint, NOW)
        assert row["novel_share"] is None
        assert row["silhouette"] is None


def test_spark_cluster_fits_candidates_once_and_returns_winning_centers(service, monkeypatch):
    clustering, evaluation, functions = MagicMock(), MagicMock(), MagicMock()
    for name, module in [
        ("clustering", clustering),
        ("evaluation", evaluation),
        ("functions", functions),
    ]:
        monkeypatch.setitem(sys.modules, f"pyspark.ml.{name}", module)
    models = {}

    def candidate(**params):
        k = params["k"]
        model = models[k] = MagicMock()
        model.transform.return_value = k
        model.clusterCenters.return_value = [[float(k)]] * k
        return SimpleNamespace(fit=lambda _frame: model)

    clustering.KMeans.side_effect = candidate
    evaluation.ClusteringEvaluator.return_value.evaluate.side_effect = lambda k: {
        2: 0.5,
        3: 0.8,
    }.get(k, 0.2)
    spark = MagicMock()
    centers, score = service.prompt_drift.cluster(spark, [[float(i)] for i in range(10)])
    assert list(models) == list(range(2, 9))
    assert centers == [[3.0]] * 3 and score == 0.8
    assert all(call.kwargs["seed"] == 14 for call in clustering.KMeans.call_args_list)
    spark.createDataFrame.assert_called_once()
    clustering.KMeans.reset_mock()
    assert service.prompt_drift.cluster(spark, [[1.0]] * 50) == ([[1.0]], None)
    assert service.prompt_drift.cluster(spark, [[0.0], [2.0]]) == ([[1.0]], None)
    clustering.KMeans.assert_not_called()


@pytest.mark.parametrize(
    "samples,share,expected",
    [(49, 1, False), (50, 0.25, False), (50, 0.251, True), (200, 0, False), (200, None, False)],
)
def test_drift_alert_threshold_and_minimum(service, samples, share, expected):
    result = service.prompt_drift.drift_alert(
        {"name": "app", "samples": samples, "novel_share": share}, 0.25
    )
    assert bool(result) is expected
    if expected:
        assert result[0]["rule"] == "prompt_drift"


def test_embedding_scrubs_before_spark_and_collects_once(service):
    spark = MagicMock()
    spark.sql.return_value.collect.return_value = [
        {"result": {"response": [1, 2], "errorMessage": None}}
    ]
    samples = [
        {
            "request": '  Summarize "weather"\nfor a@example.com token=secret123',
            "response": "must not embed responses",
        }
    ]
    assert service.prompt_drift.embed_prompts(spark, "endpoint'quoted", samples) == [[1, 2]]
    sent = spark.createDataFrame.call_args.args[0][0][0]
    assert "weather" in sent and "REDACTED" in sent
    assert "example.com" not in sent and "secret123" not in sent and "\n" not in sent
    assert "responses" not in sent
    assert "endpoint'quoted" not in spark.sql.call_args.args[0]
    assert spark.sql.call_args.kwargs["args"] == {"endpoint": "endpoint'quoted"}
    spark.sql.return_value.collect.assert_called_once()
    spark.catalog.dropTempView.assert_called_once_with("drift_prompts")


def test_embedding_errors_do_not_use_partial_sample(service):
    spark = MagicMock()
    spark.sql.return_value.collect.return_value = [
        {"result": {"response": [1], "errorMessage": None}},
        {"result": {"response": None, "errorMessage": "private upstream content"}},
    ]
    with pytest.raises(ValueError, match=r"^embedding failed$"):
        service.prompt_drift.embed_prompts(spark, "endpoint", [{"request": "hello"}])
    spark.catalog.dropTempView.assert_called_once()
    spark.reset_mock()
    assert service.prompt_drift.embed_prompts(spark, "endpoint", [{"request": ""}]) == []
    spark.sql.assert_not_called()


def test_job_resolves_only_observed_apps_and_merges_scoped_week(service, monkeypatch):
    drift = service.prompt_drift
    names = ["changed", "recovered", "small", "failed", "new", "empty"]
    baseline = json.dumps({"centroids": [[0.0]], "p95_distance": 1, "endpoint": "embedding"})
    spark = MagicMock()
    spark.sql.return_value.collect.return_value = [
        {"name": n, "centroids_json": baseline} for n in names if n != "new"
    ]
    client = service.main.w
    client.apps.list.return_value = [SimpleNamespace(name=n) for n in names]
    monkeypatch.setattr(service.quality_evals, "experiment_of", lambda _client, name: name)
    sampler = MagicMock(return_value=[{"request": "prompt"}] * 250)
    monkeypatch.setattr(service.quality_evals, "sample_traces", sampler)
    embed = MagicMock(
        side_effect=[
            [[10.0]] * 50,
            [[0.0]] * 50,
            [[0.0]] * 49,
            ValueError("failed"),
            [[0.0]] * 50,
            [],
        ]
    )
    monkeypatch.setattr(drift, "embed_prompts", embed)
    monkeypatch.setattr(drift, "cluster", lambda _spark, points: ([points[0]], None))
    emit = MagicMock()
    monkeypatch.setattr(service.source_scan, "emit_alerts", emit)
    drift.run(spark, client, "cat", "schema", "embedding", 200, 0.25, NOW)
    assert emit.call_args.kwargs == {
        "owned_rules": ("prompt_drift",),
        "evaluated_apps": {"changed", "recovered"},
    }
    assert [e["app"] for e in emit.call_args.args[3]] == ["changed"]
    assert all(len(call.args[2]) == 200 for call in embed.call_args_list)
    assert sampler.call_args.kwargs == {"hours": 168, "n": 200}
    baseline_query = spark.sql.call_args_list[1]
    assert baseline_query.kwargs["args"]["week"].isoformat() == "2026-10-19"
    writes = [call for call in spark.sql.call_args_list if "MERGE INTO" in call.args[0]]
    assert len(writes) == 4
    assert all(call.kwargs["args"]["workspace_id"] == "123" for call in writes)
    assert all("t.week = s.week" in call.args[0] for call in writes)
    assert "workspace_id STRING" in drift.DDL and "COMMENT" in drift.DDL


def test_drift_read_api_binds_app_and_workspace(service):
    service.queries.run = AsyncMock(return_value=[{"week": "2026-10-26", "novel_share": None}])
    api = product_app(service)
    status, data = asyncio.run(request(api, "GET", "/api/apps/o'hare/drift"))
    assert status == 200 and data["reports"][0]["novel_share"] is None
    assert service.queries.run.call_args.kwargs == {"ws": "123", "app": "o'hare"}
    sql = service.queries.run.call_args.args[0]
    assert "o'hare" not in sql and ":ws" in sql and ":app" in sql
    assert "centroids_json" not in sql
    assert asyncio.run(request(api, "POST", "/api/apps/demo/drift"))[0] == 405


def test_drift_job_is_opt_in_weekly_serverless():
    job = yaml.safe_load((ROOT / "resources/drift.job.yml").read_text())["resources"]["jobs"][
        "prompt_drift"
    ]
    assert job["schedule"] == {
        "quartz_cron_expression": "0 0 7 ? * MON",
        "timezone_id": "UTC",
        "pause_status": "PAUSED",
    }
    assert job["performance_target"] == "STANDARD"
    assert not {"job_clusters", "new_cluster", "existing_cluster_id"} & job.keys()
    task = job["tasks"][0]
    assert task["environment_key"] == "default"
    assert not {"job_cluster_key", "new_cluster", "existing_cluster_id"} & task.keys()
    variables = yaml.safe_load((ROOT / "databricks.yml").read_text())["variables"]
    assert variables["drift_embedding_endpoint"]["default"] == "databricks-gte-large-en"
    assert variables["drift_samples"]["default"] == 200
    assert variables["drift_threshold"]["default"] == 0.25
