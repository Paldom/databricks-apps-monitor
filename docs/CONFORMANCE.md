# Live workspace conformance

The `conformance` demo is a deterministic fixture for SDK v2 and monitor measurements.
It makes no background requests and uses no model serving endpoint or real SQL query.
`scripts/validate_workspace.py` drives known inputs, saves a reproducible plan, and checks
the resulting telemetry. Local unit tests exercise the app, the validator, and corrupted
evidence. They do **not** certify a Databricks deployment.

The fixture deliberately remains capable of exposing defects in the monitor. The
`monitor observed health 503 window` check proves that `app/main.py::_probe_one` reaches the
SDK health contract (`/monitor/health`, falling back to `/healthz` for v1 apps) and records
the app's own 503. Do not turn a failure of that check into a skip or weaken the assertion.

## Prepare an isolated validation deployment

1. Deploy the monitor and demos with `scripts/deploy.sh all -t <target> -p <profile>`.
   Populate the existing uncommitted `.env` first. Never use a bare bundle deploy.
   The fixture resource is `conformance`, app name `monitor-demo-conformance`.
   `BUNDLE_VAR_conformance_version` overrides `APP_VERSION`; keep one version throughout
   a run. Disable auto-stop for the fixture and arrange exclusive validation access.
   Keep the drive and its metric flush window away from UTC midnight: span timestamps
   and batched metric timestamps can fall on different days at that boundary.
2. Run the inventory job so tables, views, grants and fleet discovery exist. The chosen
   profile must have warehouse access and read access to the telemetry schema, `CAN_USE`
   on both app URLs, and monitor administrator rights to create the run's funnel/SLO.
   The fixture SP needs `CAN_USE` on the monitor for K7 (also bound by its bundle resource).
3. Bind `MONITOR_HASH_KEY` to a secret. Existing demos have no secret binding pattern, so
   this is an installation prerequisite, not a checked-in secret or a plaintext variable.
   Merge the following into the conformance App resource, preserving its other resources:

   ```yaml
   resources:
     - name: monitor-hash-key
       secret:
         scope: <your-scope>
         key: <your-key>
         permission: READ
   config:
     env:
       - name: MONITOR_HASH_KEY
         value_from: monitor-hash-key
   ```

   Use snake_case `value_from` inside bundle config. Also set the same `MONITOR_HASH_KEY`
   in the validator's local environment. It is never written to the report. Without the
   key the negative SHA-256 control still runs, but positive HMAC verification is `SKIP`.

4. Start the fixture under `opentelemetry-instrument` with the bundle environment.
   Sampling is `parentbased_traceidratio` at `1.0`, `http/dup` exports both HTTP semconvs,
   and team/cost center are native resource attributes. Leave the platform-injected OTLP
   endpoint intact; do not pin a sidecar port. `uvicorn` access logging is disabled because
   raw access logs can echo the deliberately sensitive query outside SDK redaction.
5. Use an app-URL-compatible OAuth profile. Redirects are rejected, credentials are
   refreshed for every HTTP request, and HTTP requests are never retried. Some workspace
   proxies replace `x-forwarded-email` or inject `x-forwarded-user`, which the SDK prefers.
   If so, the five-user/HMAC checks will fail: the deployment cannot prove the requested
   simulated identities with these credentials. Use an approved test ingress that preserves
   these fixture identities, or repeat with five authenticated test identities. Do not
   disable platform authentication or modify SDK identity handling to make the test pass.

Do not deploy the fixture into a production fleet: the operational checks intentionally
stop it, restart the monitor, and change its budget temporarily. They run only with
`--exercise-ops`. Ordinary `drive` creates a run-specific funnel/SLO and toggles the fixture's
health; ordinary `verify` reads workspace data. No validation action runs merely on import.

## Drive, materialize, verify

Use a unique run ID and report path. The SDK is a lazy runtime dependency; it is not needed
to import the validator or run unit tests. `--with` supplies the existing runtime dependency
without changing the project's dependency lists or lockfile.

```sh
uv run --with 'databricks-sdk>=0.38.0' scripts/validate_workspace.py \
  --profile <profile> --catalog <catalog> --schema <schema> \
  --monitor-url https://<monitor-app-host> \
  --conformance-url https://<conformance-app-host> \
  --warehouse-id <warehouse-id> --run-id acceptance-001 \
  --phase drive --report acceptance-001.json
```

The complete plan, golden expectations, each HTTP result, health evidence, and recovery
intent are saved incrementally. A failed/ambiguous request is never replayed. Keep a partial
report and start a new run instead. The validator refuses to overwrite a drive report or
reuse a run ID already present in telemetry. `verify` requires the existing complete report
and checks the target, workspace ID, plan and expectations before using it.

Wait for telemetry to land, then run these jobs from the **root** bundle with your profile
and target (the harness prints the relevant command for each missing materialization):

```sh
databricks bundle run inventory_scan -t <target> --profile <profile>
databricks bundle run cost_rollup -t <target> --profile <profile>
databricks bundle run slo_eval -t <target> --profile <profile>
```

`gold_views` is a **task of `inventory_scan`**, not a bundle job named `gold_views`.
Run `slo_eval` within two hours of traffic; its source window is two hours. Materializations
must run after telemetry has landed, including browser events. Repeat the validator command
with `--phase verify`, the same report, and optionally `--exercise-ops`. The default
`--wait-minutes 15` waits until at least 15 minutes after the drive finished; rerunning verify
does not add another 15-minute delay. `--phase all` combines drive and verification, but does
not launch these jobs. Missing job data is `SKIP` with instructions, not a successful check.
Permission errors, SQL errors, and incorrect populated results are failures.

Exit codes: **0** all requested checks passed, **1** at least one failure, **2** incomplete
because evidence is skipped/manual. `drive` alone can exit 0 with status `driven`; that is
not a conformance certificate. Every check includes expected/actual and tolerance in JSON
and the printed summary table. All live SQL values and table identifiers are named parameters.
Statement execution polls asynchronous queries, fetches every result chunk, and rejects
truncated results.

## Golden traffic table

The source of truth is `PLAN_TABLE` plus `FUNNEL` in the validator. Ordering and assignment
to sessions are seeded by `run_id`. Every request gets `x-request-id: val-<run_id>-<n>`, a
`monitor_session` cookie and one of five `x-forwarded-email` identities. Fifteen sessions
are reused across the plan. No validator trace context is injected, so ratio 1.0 samples
each request independently.

| Input                                       | Requests |            HTTP | Expected contribution                                                    |
| ------------------------------------------- | -------: | --------------: | ------------------------------------------------------------------------ |
| `/c/ok`                                     |      100 |             200 | 100 real requests                                                        |
| `/c/error`                                  |       20 |             500 | 20 identical exception fingerprints                                      |
| `/c/client-error`                           |       10 |             404 | 10 monitor errors; zero HTTP 5xx                                         |
| `/c/slow?ms=300`                            |       30 |             200 | 300 ms population                                                        |
| `/c/slow?ms=1500`                           |       10 |             200 | 1500 ms population                                                       |
| `/c/llm?in=1000&out=200&stream=0`           |        8 |             200 | 8000 input / 1600 output tokens                                          |
| `/c/llm?in=1000&out=200&stream=1&chunks=10` |        4 |             200 | 4000 input / 800 output tokens, not 40000 input                          |
| `/c/llm?fail=<class>`                       |        5 |             502 | One each `rate_limit`, `timeout`, `policy`, `schema`, `server`; no usage |
| `/c/event?name=<run>:<step>`                |       30 |             200 | `signup` 15, `verify` 10, `activate` 5 sessions                          |
| `/c/step?name=conformance-step-N`           |        5 |             200 | Five distinct journey overrides                                          |
| `/c/sql?rows=42`                            |        5 |             200 | Five CLIENT SQL spans, 42 returned rows each                             |
| `/c/leak`                                   |        3 |             200 | Three scrubbed warning logs                                              |
| `/c/budget`                                 |        1 |             200 | Policy is initially open; separate budget model, zero tokens             |
| `/monitor/event`                            |        1 |             200 | Ingress business event named `val-<run>:ingress`                         |
| `/monitor/feedback`                         |        1 |             200 | Rating 99 clamps to 5; bearer comment scrubbed                           |
| `/c/ok` with `x-monitor-synthetic: journey` |        5 |             200 | Present as `journey`, excluded from real counts                          |
| Health down → probe → up → probe            |        4 | 200/503/200/200 | Tagged `probe`, excluded from real counts                                |

Total: **242** driven requests, **233** real, **5** journey, **4** probe. Real errors:
**35/233 = 15.021459%**, including 10 client errors and 25 HTTP 5xx. The current monitor's
shared error expression treats HTTP **>=400 or OTel ERROR** as an error, including in
availability SLIs. It does not claim that a 404 is an HTTP server error. Successful model
usage is **12000 input / 2400 output**. There are **18 billable LLM spans**: 12 successful
fake-model calls, 5 failed fake-model calls, 1 zero-token budget-model call.

The requested “15 events across a 15/10/5 funnel” is arithmetically inconsistent: **15
sessions produce 30 events**. Names are `val-<run_id>:signup`, `:verify`, `:activate` to
isolate `v_funnels`, which has no run-ID dimension. Expected drop-off is null at signup,
33.333333% at verify, 50% at activate. The extra ingress event is outside that funnel.

The SDK caches health results for 30 seconds. The driver waits 31 seconds after each
toggle, holds the down state another 150 seconds for default monitor probe intervals,
and captures the monitor's probe series before recovery. It checks the direct 503 and a
503 recorded by the monitor. Custom probe intervals longer than this hold require a longer
fixture plan and a new report. Cleanup resets health if the drive is interrupted by an error.

## Endpoint telemetry contract

All normal HTTP handlers receive a SERVER span from FastAPI auto-instrumentation. The
SDK adds `app.name`, `app.version`, `app.client_request_id`, `session.id`, `user.id_hash`,
`traffic.kind`, and `journey.step`. Stable HTTP status is coalesced with legacy status in
queries. Additional ASGI send/receive spans are not counted as requests. Child spans and
logs without request IDs are joined through the run's SERVER trace IDs.

| Endpoint / feature                         | Span, log or metric expectations                                                                                                                                                                                                                                                       |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /c/ok`                                | HTTP 200; `journey.step=/c/ok`                                                                                                                                                                                                                                                         |
| `GET /c/error`                             | Raised `RuntimeError`, HTTP 500, `exception.fingerprint` stable across all 20; ERROR log on `monitor.errors`; matching fingerprint in `v_error_groups`                                                                                                                                 |
| `GET /c/client-error`                      | HTTP 404 response; no unhandled exception fingerprint required                                                                                                                                                                                                                         |
| `GET /c/slow?ms=N`                         | Await N ms. Per-population p50/p95 within −20% to +20% + 100 ms processing allowance; mixed route p50=300, p95=1500 ms                                                                                                                                                                 |
| `GET /c/llm`                               | One CLIENT span `chat conformance-fake-model`, `gen_ai.request.model`, `gen_ai.operation.name=chat`, `monitor.llm.billable=true`, streaming flag; final input/output usage; histogram `gen_ai.client.token.usage` for input and output                                                 |
| LLM stream                                 | Ten SSE chunks; input=1000 re-reported on every chunk, output cumulative; final usage overwrites; one histogram record per direction on exit; positive `monitor.llm.ttft_ms`                                                                                                           |
| LLM failure                                | One CLIENT span with canonical `error.type`; HTTP 502 for all five fake provider failures, including `stream=1` (failure precedes headers); no usage recorded                                                                                                                          |
| `POST /c/event?name=X`                     | `track(X, request=...)`; `monitor.events` JSON log with event ID, request/session/user envelope and scalar fixture property; exact `v_events` counts                                                                                                                                   |
| `GET /c/step?name=S`                       | SERVER `journey.step=S`                                                                                                                                                                                                                                                                |
| `GET /c/sql?rows=R`                        | CLIENT `sql.execute`; `db.system.name=databricks_sql`, `db.namespace=conformance-fake-warehouse`, `databricks.statement_id=conformance-fake-statement`, `db.response.returned_rows=R`; **neither** `db.statement` nor `db.query.text` exists                                           |
| `GET /c/leak?token=SECRET&email=...`       | Warning log containing formatted email, bearer, and a fake `dapi…` PAT-shaped string (32 hex digits, assembled at runtime) before filtering. Exported body masks all three; query URL attributes are removed/scrubbed. Three logs must exist, so empty telemetry cannot pass redaction |
| `POST /c/health-toggle?ok=0\|1`            | Change in-memory toggle only; always-ok check stays true                                                                                                                                                                                                                               |
| `GET /monitor/health`                      | SDK JSON with version, boot ID, uptime and check statuses, 503 when toggle is down after cache expiry                                                                                                                                                                                  |
| `GET /c/budget`                            | CLIENT `chat conformance-budget-model`, zero usage when open; HTTP 429 and **no provider span** when policy blocks before entry                                                                                                                                                        |
| `GET /`                                    | Tiny page loads `/monitor/rum.js`, changes path via pushState, then throws `conformance browser error`                                                                                                                                                                                 |
| `POST /monitor/event`, `/monitor/feedback` | SDK ingress log with correlated envelope; feedback clamp and comment scrub checked                                                                                                                                                                                                     |
| Process startup                            | `monitor.lifecycle` JSON for the health probe's boot ID, nonempty packages, `team=conformance`, `cost_center=cc-test`; native resource attributes repeat team/cost center on telemetry                                                                                                 |

Input bounds prevent accidental long sleeps/large streams; invalid parameters return 422.
Use the plan exactly when checking counts. Real warehouse/serving readiness helpers are
covered by SDK unit tests; this fixture's health checks intentionally do not contact those
services. The wheel-only error-biased sampler cannot be registered by a copied file and is
covered by the existing wheel tests. Raw `print()` and platform logs bypass SDK redaction;
the leak fixture deliberately uses Python logging.

## Evidence scope and materializations

Request IDs must each occur on exactly one SERVER span, including failures. Duplicate
ingestion is a failure. Direct request/status/session/identity expectations are independent
of the monitor SQL. Exact HMAC equality uses the local key, and each stored value is also
checked against the plain SHA-256[:16] negative control. If an HTTP proxy replaces test
identities, that is reported as a failed identity contract.

`agg_app_daily` and `agg_app_hourly` have no run dimension. The validator compares their
entire touched day/hour populations against raw SERVER counts, errors, distinct sessions
and users, **grouped by traffic kind**, while separately checking this run's golden inputs.
`costs_ai_daily` similarly compares the touched days' fake-model totals and call counts to
raw billable spans; prior runs are included in that daily expectation. The successful calls
in this run must still total exactly 12000/2400. Cost metrics are unsampled, cumulative
streams; their rows cannot be reliably filtered by request ID. The harness checks model/
direction/time presence and verifies their downstream daily totals against unsampled spans.
Keep the fixture at sampling 1.0 and retain all raw data for the touched days.

The availability SLO is `val-<run_id>`, filter `/c/%`, target 0.99. `sli_5m` is compared
against full raw five-minute buckets overlapping the run, including any other traffic in
those buckets. The two real SDK ingress requests are outside `/c/%`. Prior runs in the
same bucket are accounted for, not attributed to the new plan. No new UC tables are added.
The events, funnel and SLO monitor API values are checked as measurements, not just HTTP 200.

## Browser evidence

If Playwright and Chromium are available in the validator environment, drive launches a
browser with credentials restricted to the fixture origin, visits `/?run=<run_id>`, waits
for the SDK beacon flush, and navigates away to flush pagehide events. It never fabricates
a RUM HTTP payload. The unique `/conformance-route/<run_id>` must have a page view and a
JS error in `v_rum_daily` after the inventory/gold job. Browser traffic has its own request
IDs and is outside the 242-request plan; daily aggregate comparisons include it.

If Playwright or its browser is unavailable, the report marks RUM **MANUAL**:

1. Sign into the workspace in a real browser and open `<conformance-url>/?run=<run_id>`.
2. Observe the route change, console error, and successful `/monitor/rum` beacons. Wait
   at least 12 seconds and leave the page to flush pending events.
3. After telemetry and the inventory job, inspect the monitor's RUM page/API or
   `v_rum_daily` for this unique route: at least one page view and one JS error. Attach
   browser/receiver evidence to the report. A manual check remains incomplete in machine
   output until an engineer signs off; a synthetic POST is not browser evidence.

## Budget, restart, alerts, and mute evidence

`--exercise-ops` on verify temporarily saves `token_budget_day=1`, preserving and later
restoring the original product settings in the report. In another terminal, run
`inventory_scan` when prompted; it evaluates usage and refreshes policy state. After
`GET /api/policy/monitor-demo-conformance` reports `block`, `/c/budget` must return 429
within the SDK's 60-second cache plus a 15-second polling allowance. Missing policy
materialization is SKIP with the job command. Restore/recompute policy with another
inventory run after the settings are restored. The budget requests are synthetic and use
separate IDs/model, so they do not change the golden run's accounting.

The harness then stops the fixture, waits for exactly one `app_stopped` firing, restarts
the monitor while the fixture is still stopped, waits through fleet refresh, and requires
no duplicate firing. Starting the fixture must produce exactly one resolution. It repeats
the stop/start with an active mute and requires firing/resolution rows with `muted=true`.
No rows are deleted. A `finally` block starts the fixture and removes its temporary mute;
the report records recovery intent and the mute ID before changes. If the process is killed
or cleanup fails, use those saved details to start both apps, remove the temporary mute,
and restore product settings. `--monitor-app-name` defaults to `apps-monitor`.

Webhook delivery cannot be inferred from a muted database row. Configure a capture receiver
before exercising operations. Export its actual received alert payloads and the complete
search windows to a JSON file, then pass `--webhook-evidence receiver.json` on a later
`--phase verify` **without** repeating `--exercise-ops` (saved operation checks are reused):

```json
{
  "run_id": "acceptance-001",
  "receiver": "capture-receiver/export-reference",
  "windows": {
    "alert lifecycle + monitor restart": {
      "since": "<ISO timestamp at or before report operations window>",
      "until": "<ISO timestamp at or after report operations window>",
      "alerts": [
        {
          "app": "monitor-demo-conformance",
          "rule": "app_stopped",
          "state": "firing",
          "muted": false
        },
        {
          "app": "monitor-demo-conformance",
          "rule": "app_stopped",
          "state": "resolved",
          "muted": false
        }
      ]
    },
    "muted lifecycle": {
      "since": "<ISO window start>",
      "until": "<ISO window end>",
      "alerts": []
    }
  }
}
```

`alerts` is the flattened set of alert entries from received webhook batches, with
duplicates preserved. Export from the receiver; do not construct it from expected values.
The validator checks run, receiver identification, coverage, exactly one unmuted transition
of each state and zero muted deliveries. Include delivery lag in the exported windows.
Without receiver evidence this check is MANUAL, never PASS. Keep this deployment idle
while capturing windows so unrelated incidents cannot be mistaken for this test.

After acceptance, remove the run's funnel/SLO settings if desired, retain the JSON and
receiver evidence, and shut down the fixture through the normal deployment/operations
workflow. All live validation described here is for the later engineer; no workspace
actions are part of the local test suite.
