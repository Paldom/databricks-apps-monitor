# Instrumenting your app for the monitoring toolkit

What to add to **your** Databricks App so the monitor can track its requests, errors,
logs, traces, and AI cost. Instrumentation is layered — each level unlocks more pages,
and every level is optional:

| Level                       | You add                                                 | The monitor gains                                                                              |
| --------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **L0 — nothing**            | —                                                       | fleet board (probes/uptime/latency), inventory, source & CVE scans, code review, app-compute $ |
| **L1 — platform telemetry** | telemetry destinations + `opentelemetry-instrument`     | requests, latency percentiles, routes, errors, log explorer, traces                            |
| **L2 — golden envelope**    | one middleware file                                     | request↔session↔user correlation, journeys, trace joins across apps                            |
| **L3 — GenAI signals**      | `gen_ai.*` span attrs + gateway request tags (+ MLflow) | per-app AI tokens & calls, cost correlation, agent waterfalls                                  |

The five `example-apps/` are living references: `healthy/` is L2, `agent/` is L3.

---

## L1 — platform telemetry (15 minutes)

**1. Declare telemetry destinations on the app resource** (bundle-managed, shared tables —
`service_name` = your app name keeps tenants apart):

```yaml
# resources/<your-app>.app.yml
resources:
  apps:
    my_app:
      name: my-app
      source_code_path: ../src
      telemetry_export_destinations:
        - unity_catalog:
            logs_table: main.monitor.otel_logs
            traces_table: main.monitor.otel_spans
            metrics_table: main.monitor.otel_metrics
```

**2. Start under `opentelemetry-instrument` and set the exporter env:**

```yaml
# app.yaml
command: [opentelemetry-instrument, python, main.py]
env:
  - name: OTEL_SERVICE_NAME
    value: my-app # MUST equal the app name — it's the join key
  - name: OTEL_TRACES_EXPORTER
    value: otlp
  - name: OTEL_METRICS_EXPORTER
    value: otlp
  - name: OTEL_LOGS_EXPORTER
    value: otlp
  - name: OTEL_TRACES_SAMPLER
    value: always_on # use parentbased_traceidratio + OTEL_TRACES_SAMPLER_ARG in high-QPS prod
  - name: OTEL_PYTHON_LOG_CORRELATION
    value: "true" # stamps trace_id/span_id onto every log line
```

> ⚠️ **Never set `OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_EXPORTER_OTLP_PROTOCOL`.**
> The Apps runtime injects them (the sidecar listens on `localhost:4314`, gRPC — not the
> 4317 you'll find in generic OTel docs). Pinning 4317 silently kills span/metric export
> while logs keep flowing through the platform pipeline.

**3. Add the OTel packages:**

```
# requirements.txt
opentelemetry-distro
opentelemetry-exporter-otlp
opentelemetry-instrumentation-fastapi   # match your framework (flask/django/starlette…)
opentelemetry-instrumentation-httpx     # + requests / sqlalchemy / asyncpg as applicable
opentelemetry-instrumentation-logging
```

That's it. Server spans (every request with route, status, duration), client spans
(every outbound call), and correlated logs now land in Unity Catalog and the monitor's
Requests / Errors / Logs / Traces tabs light up.

**Cardinality rules** (each unique attribute combo on a _metric_ is a time series):
templated routes only, no raw URLs/user ids as metric dimensions — put those on spans.

## L2 — golden envelope (5 minutes)

Copy [`sdk/monitor_middleware.py`](../sdk/monitor_middleware.py) into your app and install it:

```python
from monitor_middleware import install
app = install(FastAPI())
```

Every server span now carries the correlation envelope:

| Attribute                 | Purpose                                                                       |
| ------------------------- | ----------------------------------------------------------------------------- |
| `app.client_request_id`   | one request across UI ↔ app ↔ gateway ↔ logs                                  |
| `session.id`              | groups a user journey (cookie-persisted)                                      |
| `user.id_hash`            | per-user adoption/errors/cost **without PII** (SHA-256 of the forwarded user) |
| `app.name`, `app.version` | release/regression tracking (set `APP_VERSION` env on deploy)                 |
| `journey.step`            | route template — powers "top journeys"                                        |

The middleware also gives you two things for free:

- **`POST /monitor/feedback`** `{rating: 1-5, comment}` — user feedback lands in
  `otel_logs` through the native pipeline (no extra infra) and surfaces in the monitor's
  GenAI tab via `v_feedback`. Wire a ★-widget in your UI to it.
- **Log-line guard** — log records are truncated at 60 KB; Zerobus silently drops
  lines over 1 MB, so nothing vanishes unexplained.

### Guardrails for high-traffic apps (observability creep)

Unbounded tracing can add 30%+ DBU. Two knobs, both in `app.yaml`:

```yaml
- name: OTEL_TRACES_SAMPLER # head sampling in prod
  value: parentbased_traceidratio
- name: OTEL_TRACES_SAMPLER_ARG
  value: "0.2"
- name: OTEL_PROPAGATORS # cross-app stitching: httpx/requests inject traceparent
  value: tracecontext
```

The monitor's Ops tab shows each app's 24 h telemetry volume (logs/spans/metrics rows) so
creep is visible before the bill is. Raw telemetry is retained ~90 days (housekeeping task
of the cost job); gold aggregates are kept indefinitely.

## L3 — GenAI: traces + cost attribution

Goal: **every LLM call carries the same envelope**, so tokens and cost join back to
app / session / request, and agent traces stitch into the OTel request trace.

**1. Stamp token usage on the active span** (works with any client — this is what makes
per-app AI cost exact, from your own telemetry):

```python
from opentelemetry import trace

span = trace.get_current_span()
span.set_attribute("gen_ai.request.model", endpoint_name)
span.set_attribute("gen_ai.usage.input_tokens", usage["prompt_tokens"])
span.set_attribute("gen_ai.usage.output_tokens", usage["completion_tokens"])
```

The nightly cost job aggregates these `gen_ai.*` attributes per app/day into
`costs_daily` — no gateway dependency.

**2. Tag the request through AI Gateway** (adds server-side usage rows with your tags in
`system.ai_gateway.usage` — request-exact tokens, latency, status):

```python
headers["Databricks-Ai-Gateway-Request-Tags"] = json.dumps({
    "app": os.environ["DATABRICKS_APP_NAME"],
    "client_request_id": rid, "session_id": sid, "cost_center": "my-team",
})
```

> Caveat: rows appear only for endpoints with **AI Gateway usage tracking enabled**
> (provisioned/custom/external endpoints). Databricks **pay-per-token FMAPI endpoints
> don't log to `system.ai_gateway.usage` by default**, and enabling it on those shared
> endpoints is an admin decision — which is exactly why step 1 (own-telemetry tokens)
> is the baseline. Send the tags anyway; they cost nothing and become valuable the
> moment tracking is on.

**3. Agent frameworks — MLflow Tracing** (typed LLM/TOOL/AGENT waterfalls, the MLflow UI,
and the monitor's unified Agent tab):

> ⚠️ In Databricks Apps, set **`MLFLOW_ENABLE_DUAL_EXPORT=true`** (plus the newer spelling
> `MLFLOW_TRACE_ENABLE_OTLP_DUAL_EXPORT=true`). The Apps runtime injects an OTLP endpoint,
> which makes MLflow export traces to the sidecar **instead of** your experiment; dual
> export sends them to both — the experiment for the MLflow UI, `otel_spans` (with
> `mlflow.spanType`/`mlflow.traceRequestId` attributes) for UC-side correlation. Bind an
> `experiment` resource so `MLFLOW_EXPERIMENT_ID` is injected. The envelope middleware
> exposes ids as `request.state.monitor` — put the same `client_request_id` on the trace:

```python
import mlflow
mlflow.langchain.autolog()          # or openai/llamaindex/dspy autolog
mlflow.set_experiment(experiment_id=os.environ["MLFLOW_EXPERIMENT_ID"])

mlflow.update_current_trace(
    client_request_id=rid,
    metadata={"mlflow.trace.user": user_hash, "mlflow.trace.session": sid},
)
```

Bind an `experiment` resource to your app in the bundle so `MLFLOW_EXPERIMENT_ID` is
injected. MLflow spans are OTel-compatible; keep `OTEL_PROPAGATORS=tracecontext` (default)
so multi-agent hops propagate `traceparent` and stitch into one waterfall.

**4. Fan-out to sub-agents / other apps:** forward the `traceparent` header on outbound
calls (automatic once httpx/requests are instrumented) — otherwise waterfalls break into
sibling traces.

## Further options (platform decisions, documented not defaulted)

- **OBO per-user cost attribution** — with on-behalf-of user authorization scopes on the
  app, model calls execute as the end user and `system.ai_gateway.usage` attributes
  tokens to the _person_, upgrading the monitor's per-user cost from request-share
  allocation to exact. Needs `user_authorization.scopes: [serving.serving-endpoints]` on
  the app resource + consent flow — an org auth-model decision, so not the default here.
- **UC trace storage (Public Preview)** — binding the MLflow experiment to Unity Catalog
  trace tables exposes a `{prefix}_trace_unified` SQL view; when enabled in your
  workspace, the monitor's REST trace search can be swapped for plain SQL joins.
- **Vendor dual-export (Datadog/Dynatrace)** — keep UC as the source of truth and add a
  secondary OTLP exporter for live-alerting UX: run an OTel collector sidecar-style
  route (`OTEL_EXPORTER_OTLP_TRACES_HEADERS`-based routing), never a vendor agent in the
  Apps container (no ddtrace; OTLP/HTTP only). Don't touch `OTEL_EXPORTER_OTLP_ENDPOINT`
  — the platform injects it.
- **Genie Space** — the gold views now carry table comments; publishing the bundled
  Lakeview dashboard with a companion Genie Space (curate 5–10 example questions +
  glossary, expose **gold views only**) gives NL Q&A over the same SQL.

## Checklist

```
[ ] telemetry_export_destinations on the app resource (shared monitoring tables)
[ ] command wrapped in opentelemetry-instrument, OTEL_SERVICE_NAME == app name
[ ] no OTEL_EXPORTER_OTLP_ENDPOINT pin (sidecar is localhost:4314, auto-injected)
[ ] OTel packages in requirements.txt
[ ] monitor_middleware.py installed (golden envelope)
[ ] APP_VERSION env set on deploy (release tracking)
[ ] LLM calls: gen_ai.* span attrs + Databricks-Ai-Gateway-Request-Tags
[ ] /healthz endpoint (fast 200) for probes — note: the apps proxy intercepts GET /healthz
    (returns 200 with an EMPTY body, even for stopped apps), so journey content assertions
    must target real paths (/api/..., /)
[ ] optional: journey spec added to app/journeys.json in the toolkit repo
```
