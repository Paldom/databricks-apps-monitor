"""Process-wide SDK providers. ``set_tracer_provider`` warns if called twice."""

from __future__ import annotations

import pytest
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_SPAN_EXPORTER = InMemorySpanExporter()
_METRIC_READER = InMemoryMetricReader()
_PROVIDERS_READY = False


def _install_providers() -> None:
    global _PROVIDERS_READY
    if _PROVIDERS_READY:
        return
    _PROVIDERS_READY = True
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(_SPAN_EXPORTER))
    trace.set_tracer_provider(provider)
    metrics.set_meter_provider(MeterProvider(metric_readers=[_METRIC_READER]))


_install_providers()


@pytest.fixture(autouse=True)
def _clear_finished_spans() -> None:
    _SPAN_EXPORTER.clear()


@pytest.fixture
def span_exporter() -> InMemorySpanExporter:
    return _SPAN_EXPORTER


@pytest.fixture
def metric_reader() -> InMemoryMetricReader:
    return _METRIC_READER
