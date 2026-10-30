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

The six `example-apps/` are living references: `healthy/` is L2, `agent/` is L3,
and `conformance/` exercises SDK v2 with deterministic fake providers and no self-traffic.
Use the [conformance runbook](CONFORMANCE.md) and `scripts/validate_workspace.py` to check
exact request/error counts, streaming usage, redaction, identity, health, events, RUM and
downstream monitor measurements in a live workspace. The fixture uses the byte-identical
SDK copy; its health toggle respects the SDK's 30-second cache. Bind `MONITOR_HASH_KEY`
from a secret before claiming HMAC conformance. Browser and webhook checks require real
browser/receiver evidence; skipped checks never constitute a successful acceptance run.

## SDK v2 contract

`install(app)` with no arguments is still the v1 envelope. Redaction is on by default.
Copy [`sdk/monitor_middleware.py`](../sdk/monitor_middleware.py), or pip-install the wheel —
only the wheel registers the sampler entry point.

| API                                                                           | What it does                                                                                                                                     |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `install(app, *, redact=True, health_checks=None, rum=False, rum_sample=0.1)` | Envelope, log guard, optional span redaction, `GET /monitor/health`, feedback, `POST /monitor/event`, optional RUM                               |
| `llm_call(model, *, streaming=False, operation="chat")`                       | One provider call. `usage.set` stores the **last** token counts; `usage.first_token()` stores time to first token                                |
| `track(name, request=None, **props)`                                          | Business event on logger `monitor.events` (non-scalars dropped, 20 props max)                                                                    |
| `set_step(name)`                                                              | Overrides `journey.step` for this request; otherwise the route template is used                                                                  |
| `trace_sql(warehouse_id, *, system="databricks_sql")`                         | Dependency span. Set `res.statement_id` and `res.rows`. SQL text is never an attribute                                                           |
| `warehouse_ready(warehouse_id)`                                               | Health check: control-plane warehouse GET. `RUNNING`, `STOPPED`, `STARTING`, and `STOPPING` are healthy                                          |
| `serving_ready(name)`                                                         | Health check: control-plane endpoint GET; `state.ready == READY`, including scale-to-zero. A failed update can leave an existing endpoint ready. |
| `BudgetExceeded`                                                              | Raised by `llm_call` when policy returns `{"throttle": "block"}`                                                                                 |

### Environment

| Variable                                           | Role                                                                                                       |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `MONITOR_HASH_KEY`                                 | HMAC-SHA256 key for `user.id_hash`, truncated to 16 hex chars. Unset → plain SHA-256[:16] (v1-compatible). |
| `MONITOR_TEAM`, `MONITOR_COST_CENTER`              | Copied onto the startup log only.                                                                          |
| `OTEL_RESOURCE_ATTRIBUTES`                         | Native way to put team / cost center on **every** signal. The middleware does not read them.               |
| `MONITOR_URL`                                      | Base URL for the token-budget policy.                                                                      |
| `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET` | Apps-injected credentials discovered lazily by the Databricks SDK for policy GETs.                         |
| `DATABRICKS_TOKEN`                                 | Fallback bearer for policy GETs when SDK authentication is unavailable.                                    |
| `MONITOR_REDACT_EXTRA`                             | Comma-separated span attribute keys to drop, besides the built-ins.                                        |
| `APP_VERSION`                                      | Stamped on spans and the health body.                                                                      |
| `OTEL_TRACES_SAMPLER`                              | `monitor_parentbased` (wheel only). `OTEL_TRACES_SAMPLER_ARG` is the ratio, default 1.0.                   |

### Redaction

On by default. `redact=False` skips installing the span guard and enables only log
truncation in a fresh process. Once enabled, privacy guards remain enabled for the
process; installing another app with `redact=False` cannot disable them. SDK event,
feedback and RUM payloads are always scrubbed.

**Does:** an `on_start` processor removes query strings, fragments and URL credentials
from `url.full` / `http.url` / `http.target`, replaces `url.query`, and replaces
`process.command_line`, `process.command_args`, `db.statement` and `db.query.text`.
It wraps each span's public mutation methods so late attributes, exception events,
names and status descriptions are scrubbed before exporters see them. The log filter
runs **after** formatting, covers exception text and structured extras, and masks
emails, bearer tokens, `dapi` PATs, JWTs, and
`token` / `access_token` / `refresh_token` / `password` / `secret` / `code` query
parameters. Feedback comments and decoded event / RUM bodies are scrubbed the same
way, including JSON Unicode escapes. Request IDs and session cookies must match
`[A-Za-z0-9._:-]{1,64}`; invalid values are replaced.

**Does not:** raw `print()` and other stdout (the platform captures those outside the
logging filter), handlers added after `install()` or handlers that bypass the root
logger, the platform's own logs, span links, or resource attributes already sealed on the
`TracerProvider` — so `process.command_line` set as a **resource** attribute is not
rewritten. The MLflow experiment copy of a trace is also outside this process. MLflow
dual export that goes through this same `TracerProvider` **is** covered by the span
processor (tested with a shared-provider MLflow-style tracer, not a live MLflow export).
Call `install()` after configuring the provider and root logging handlers. Span
redaction does not apply to a separate provider or an already-started span. The SDK
works with only `opentelemetry-api`; no provider or exporter is installed for you.
`monitor_parentbased` only works for a pip-installed wheel, because
`opentelemetry-instrument` builds the provider before app code runs. It always records
`monitor.error_summary` even when the ratio drops other root spans. This summary is
sampled explicitly; a head sampler cannot revive the original dropped request.

### Health, GenAI, journeys, RUM, budget

`GET /monitor/health` — not `/healthz`, which the Apps proxy intercepts. Body
`{status, version, boot_id, uptime_s, checks}` is **200** when every check passed and
**503** otherwise. Synchronous checks run concurrently on daemon workers with a 2s
response deadline and a 30s cache, without blocking the request loop. A timed-out
check retains its worker until it returns; subsequent probes do not spawn duplicates.
`warehouse_ready` / `serving_ready` call control-plane GETs only.

`llm_call` sets `gen_ai.request.model`, `gen_ai.operation.name`, `monitor.llm.billable`,
`monitor.llm.streaming`, token attributes from the **last** `set()`, `monitor.llm.ttft_ms`
after `first_token()`, and `error.type` in
`{rate_limit, timeout, policy, schema, server, <exception class name>}`. Histogram
`gen_ai.client.token.usage` is a metric, so trace sampling does not drop it.
Each billable span also copies `app.client_request_id`, `session.id`, `user.id_hash`
and `traffic.kind` from the middleware's request context. The context is isolated
between concurrent requests and propagates into `asyncio.to_thread` provider calls;
calls outside a request have no request identity attached.

`traffic.kind` is `x-monitor-synthetic` when it is `probe`, `journey`, or `capacity`;
otherwise `real`. `set_step("submit")` overrides `journey.step`; if you never call it,
the route template is used.

`install(rum=True)` serves `GET /monitor/rum.js` and `POST /monitor/rum` (same-origin,
8 KB, a token bucket of 10 posts replenished at 10/min per session, logger `monitor.rum`):

```html
<script src="/monitor/rum.js" data-sample="0.1" defer></script>
```

Origin matching includes scheme, host and port. Without `Origin`, only
`Sec-Fetch-Site: same-origin` is accepted. Request bodies are bounded while reading,
including chunked uploads. Bucket storage is capped at 1,024 sessions per process;
clients without a valid cookie share an address-based bucket. This is local abuse
control, not a fleet-wide quota or proof of session identity. The browser keeps
queries out of page/source paths, captures request IDs from same-origin fetch
responses, and sends periodic batches. LCP, session-window CLS and interaction-based
INP are lightweight estimates from the browser's available performance entries.
The log envelope contains a JSON-encoded `body` with an `events` batch. The gold
RUM view unwraps it and counts the SDK's `type="view"` alongside legacy page-view
names. Each event's `rid` takes precedence over the ingestion request ID.

If `MONITOR_URL` is set, each `llm_call` GETs `{MONITOR_URL}/api/policy/{APP_NAME}`
(60s cache, 2s timeout, **fail-open**) and raises `BudgetExceeded` on
`{"throttle": "block"}`. Failed refreshes clear a stale block. Policy responses are
bounded to 8 KB; redirects are refused so bearer tokens cannot follow a login or a
different host. Each refresh obtains renewable headers through a lazy
`databricks.sdk.WorkspaceClient().config.authenticate()` call, using the Apps-injected
client credentials. If the SDK or its authentication is unavailable, it falls back
to `DATABRICKS_TOKEN`. With neither source, it warns once per process and keeps
fail-open behavior. The SDK is optional for copy-in users. The check is synchronous;
run blocking provider calls in a worker, as the agent demo does.

`POST /monitor/feedback` over 4 KB is accepted as an empty payload (`{"ok": true}`) so
the widget does not break. `POST /monitor/event` over 4 KB returns **413**.

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

| Attribute                 | Purpose                                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `app.client_request_id`   | one request across UI ↔ app ↔ gateway ↔ logs                                                                       |
| `session.id`              | groups a user journey (cookie-persisted)                                                                           |
| `user.id_hash`            | per-user adoption/errors/cost **without PII** (HMAC-SHA256[:16] when `MONITOR_HASH_KEY` is set, else SHA-256[:16]) |
| `app.name`, `app.version` | release/regression tracking (set `APP_VERSION` env on deploy)                                                      |
| `journey.step`            | route template — powers "top journeys"                                                                             |

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

**1. Wrap each provider call with `llm_call`** (one billable span and one pair of token
histogram observations per call):

```python
from monitor_middleware import llm_call

with llm_call(endpoint_name) as usage:
    response = client.chat.completions.create(model=endpoint_name, messages=messages)
    usage.set(input_tokens=response.usage.prompt_tokens,
              output_tokens=response.usage.completion_tokens)
```

For streaming, call `first_token()` on the first content chunk, then `set()` with
the last usage report. Repeated `set()` calls replace counts; they never accumulate
repeated input tokens. Metrics emit once on exit, even when the trace is sampled
out. `trace_sql` and `llm_call` classify failures without automatically attaching
SQL/provider exception payloads. Do not repeat token totals on the server span:
the agent demo keeps response totals separately to avoid duplicate billing signals.
Service-side rollup changes are a separate roadmap task.

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
[ ] LLM calls: llm_call(...) + Databricks-Ai-Gateway-Request-Tags
[ ] MONITOR_HASH_KEY set where user.id_hash must not be a guessable SHA-256
[ ] GET /monitor/health for dependency checks — note: the apps proxy intercepts GET /healthz
    (returns 200 with an EMPTY body, even for stopped apps), so journey content assertions
    must target real paths (/api/..., /) and probes that need your body must not use /healthz
[ ] optional: journey spec added to app/journeys.json in the toolkit repo
```
