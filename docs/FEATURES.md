# Full capability reference

Every feature of Apps Monitor mapped to the mechanism that powers it and the
table/view it reads or writes. The selling summary lives in the [README](../README.md);
this is the exhaustive list.

| Capability                       | How                                                                                                                                                                                       | Where                                                                                                               |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Live fleet board                 | 60 s HTTP probes with the monitor's SP OAuth; KPI tiles, needs-attention list, sparklines                                                                                                 | monitor app, in-memory                                                                                              |
| Requests / latency / errors      | platform OTel export into shared UC tables; per-app charts + route tables                                                                                                                 | `otel_spans`                                                                                                        |
| Log explorer                     | stdout/stderr + app logs, severity-filtered, trace-correlated                                                                                                                             | `otel_logs`                                                                                                         |
| Distributed traces               | request list → waterfall with correlated logs                                                                                                                                             | `otel_spans` + `otel_logs`                                                                                          |
| Unified agent traces             | MLflow AGENT/TOOL/LLM spans merged with app spans; one `client_request_id` from browser to token                                                                                          | `otel_spans` + MLflow REST                                                                                          |
| Fleet inventory                  | hourly snapshot + automated access grants                                                                                                                                                 | `apps_inventory`                                                                                                    |
| Source & dependency scans        | CVEs (OSV.dev), secrets, smells, quality score per deployment                                                                                                                             | `code_scans`, `scan_findings`                                                                                       |
| Package analysis (py + npm)      | installed vs latest (PyPI/npm registry), staleness class, per-package CVE ids                                                                                                             | `deps_json` in `code_scans`                                                                                         |
| Agentic code review              | Databricks-hosted Claude reviews each app's source: verdict + scores                                                                                                                      | `llm_reviews`                                                                                                       |
| Cost tracking                    | billing × list prices; billable LLM spans per model; gateway tokens stored separately; requester SP IDs resolved through inventory                                                        | `costs_daily`, `costs_ai_daily`, `apps_inventory`                                                                   |
| S4 unit economics                | effective-dated model prices, per-model token totals, hourly billing allocation for idle spend; per-app Cost tiles and fleet Governance tiles                                             | `model_prices`, `costs_ai_daily`, `costs_daily.idle_usd`, `v_unit_economics`, `app_config.outcome_event`            |
| S7 business funnels              | deduplicated `monitor.events` logs plus named server `journey.step`; ordered steps within 30 minutes, session deduplication and release split                                             | `v_events`, `funnel_specs`, `v_funnels`                                                                             |
| S7 cohorts                       | first observed week and weekly retention of real hashed users, including zero-retention weeks                                                                                             | `v_cohorts`, raw `otel_spans`                                                                                       |
| S7 leaderboard                   | weighted component scores, published formula and evidence coverage; excludes stopped and deleted apps                                                                                     | `v_leaderboard`, live probes, `app/routes_product.py`                                                               |
| S7 browser experience            | `monitor.rum` logs: page/route views, p75 LCP/CLS/INP per route/day and hashed JS error groups with trace links                                                                           | `v_rum_daily`, `otel_logs`                                                                                          |
| S8 guardrails                    | email/phone/IBAN/card detectors (IBAN checksum, card Luhn); redacted FMAPI jailbreak/policy classifier; fixed masks and hashes only                                                       | `guardrail_findings`, `guardrail_samples`, `monitor_quality`                                                        |
| S8 prompt drift                  | normalized prompt hashes; new hash exceeds 20% of daily samples, with a prior seven-day baseline and at least five prompts                                                                | `guardrail_samples`, `guardrail_findings`, `alert_events`                                                           |
| K7 token policy                  | hourly metric totals with billable-span fallback; warn/block budget state; memory-only policy API refreshed alongside fleet                                                               | `app_config.token_budget_day`, `throttle`, `tokens_today`, `tokens_last_hour`, `policy_updated_at`                  |
| Synthetic monitoring             | probes/journeys/capacity send `x-monitor-synthetic`; queries prefer `traffic.kind`, with legacy healthz-name fallback                                                                     | `app/journeys.json`, `otel_spans`                                                                                   |
| Alerting                         | startup rehydration; job-owned firing/resolved transitions; partial scans resolve only evaluated apps; open alerts in UI                                                                  | `alert_events`, `v_alerts_open`                                                                                     |
| Maintenance windows (S1)         | Admin mute/unmute with app/rule globs and UTC start/end; fleet-refresh cache; evaluation continues, muted transitions persist and skip webhooks                                           | `alert_mutes`, `alert_events.muted`, `monitor_audit`                                                                |
| Night maintenance (S1)           | Night stop mutes `app_stopped`/`app_down` before stopping; only automatically stopped apps restart on the first hourly run after 06:00 local                                              | `app_config`, `alert_mutes`, `alert_events`                                                                         |
| Service objectives (S2)          | Admin spec editor; quarter-hour serverless job MERGEs two hours of completed 5-minute buckets; both-window fast/slow/ticket burns and running-app no-data alerts; per-app budget chart    | `slo_specs`, `sli_5m`, `alert_events`                                                                               |
| Telemetry health (S5)            | Per-signal freshness, real-server envelope coverage, 24h suspected orphan ratio, HTTP semconv mix, token reconciliation and available app sampler config; six-hour sustained orphan alert | `v_telemetry_health`, `telemetry_health_samples`, `apps_inventory.sampler_ratio`, `costs_daily`                     |
| Monitor self-metering (S6)       | Monitor job/app billing, SP query-duration warehouse allocation, final review/eval token usage, Delta storage snapshots; configurable fleet-cost ratio alert and Governance tile          | `monitor_cost_daily`, `monitor_storage_daily`, `monitor_model_usage`, `alert_events`                                |
| Adoption analytics               | retained daily/hourly request counts and user/session HLL sketches; per-user detail within raw retention                                                                                  | `agg_app_daily`, `agg_app_hourly`, `v_usage_daily`, `v_users`                                                       |
| GenAI monitoring                 | retained billable model/token/latency trends by traffic kind; recent session detail                                                                                                       | `agg_genai_daily`, `v_genai_daily`, `v_genai_sessions`                                                              |
| Error groups & dependencies      | SDK exception fingerprints with normalized-log fallback; outbound peer latency                                                                                                            | `v_error_groups`, `v_dependencies`                                                                                  |
| Timeline & releases              | alerts+deploys+anomalies chronology; regression-by-version                                                                                                                                | `v_release_perf`                                                                                                    |
| Smart detection                  | hourly traffic/latency z-scores vs 7-day baselines                                                                                                                                        | gold job → alerts                                                                                                   |
| FinOps governance                | budgets, burn alerts, hard budget stop, forecast, chargeback, idle/night auto-stop                                                                                                        | `app_config`, `v_chargeback`, `v_cost_forecast`                                                                     |
| Security & compliance            | deny-list policy, freshness, permission drift, audit, compliance export                                                                                                                   | `policy.json`, `app_permissions`, `monitor_audit`                                                                   |
| Provisioning                     | one-click tagged app from template, telemetry pre-wired                                                                                                                                   | `monitor-provision-app`                                                                                             |
| Runtime quality evals            | daily LLM judge on sampled production traces + regression alerts                                                                                                                          | `monitor_quality`                                                                                                   |
| User feedback                    | `POST /monitor/feedback` ★ ratings through the native pipeline; comments scrubbed, bodies over 4 KB accepted as empty `{ok:true}`                                                         | `v_feedback`                                                                                                        |
| Privacy-safe capture             | creation-time and late span redaction, formatted log/extra scrubbing, HMAC user hash and validated IDs                                                                                    | `otel_spans`, `otel_logs`                                                                                           |
| Exception fingerprints           | `exception.fingerprint` on the request span, or `monitor.error_summary` when it was not recorded                                                                                          | `otel_spans`, `otel_logs`                                                                                           |
| Health contract                  | `GET /monitor/health`: concurrent bounded workers, 30s cache; startup package inventory and cold-start span                                                                               | app process, `otel_logs`, `otel_spans`                                                                              |
| Business events                  | `track`, `set_step`, `POST /monitor/event`                                                                                                                                                | `otel_logs`, `otel_spans`                                                                                           |
| LLM usage helper                 | `llm_call` and histogram `gen_ai.client.token.usage`                                                                                                                                      | `otel_spans`, `otel_metrics`                                                                                        |
| SQL dependency spans             | `trace_sql`: warehouse/Lakebase IDs and row counts; no SQL text or automatic exception payloads                                                                                           | `otel_spans`                                                                                                        |
| Browser RUM                      | opt-in errors, views and vital estimates; same-origin, 8 KB streaming cap, 10/min session bucket; fetch request correlation                                                               | `otel_logs`                                                                                                         |
| Token budget                     | SDK `llm_call` checks `/api/policy/{app}`: 60s cache, 2s timeout, fail-open refresh, `BudgetExceeded` on block                                                                            | monitor policy endpoint (service side separate)                                                                     |
| LLM error taxonomy & agent watch | rate-limit/policy/timeout/schema classes; spans-per-trace trend                                                                                                                           | GenAI tab                                                                                                           |
| Capacity probing                 | tagged step ramp on `/monitor/health`; missing route falls back to admin `capacity_path` or `/`                                                                                           | Ops tab, `app_config`                                                                                               |
| Ask Genie                        | curated Genie space (18 gold objects) embedded in the app                                                                                                                                 | `#/ask`                                                                                                             |
| AI/BI dashboard + watchdog       | versioned Lakeview dashboard; dead-man SQL alert                                                                                                                                          | `dashboards/fleet.lvdash.json`                                                                                      |
| Read-only MCP (S10)              | Official MCP Streamable HTTP at `/mcp`; seven existing-handler tools; Apps identity and per-caller rate limit                                                                             | Existing fleet, overview, errors, traces, costs, alerts; optional `slo_specs` / `sli_5m`                            |
| External vantage (S11)           | Scheduled OAuth M2M GitHub runner; HTTP and optional Playwright; named-parameter idempotent writes; two failed runs from each vantage before journey alerts                               | `synthetic_runs` (`workspace_id`, `vantage`, `run_id`, `failure_stage`), `ui_tests` volume                          |
| Federation (S12)                 | Feeder current overwrite + history/aggregate MERGE; hub discovery and UNION ALL; workspace filter; account billing priced once                                                            | `hub_catalog.af_<name>__<id>.{apps_current,apps_history,agg_app_daily,costs_daily,alert_events}`, local `v_fleet_*` |
| Status page (S13)                | Authenticated `/status` / `/api/status`; hourly probe bars, incidents, optional SLOs/maintenance; opt-in allowlisted GitHub Pages snapshot                                                | In-memory probes, `v_alerts_open`, optional `slo_specs`, `sli_5m`, `alert_mutes`; sanitized `status.json`           |

See [FEDERATION.md](FEDERATION.md) for deployment modes, grants, same-region
constraints, external workflow setup, MCP authentication and public-snapshot policy.

Phase 2 APIs live in `app/routes_ops.py`. Mute creation uses `POST /api/actions/mute`;
`GET` lists unexpired windows, including scheduled ones. `DELETE /api/actions/mute/{id}`
(or `DELETE /api/actions/mute?id=...`) removes a window. Times must include a timezone;
matching uses case-sensitive globs and an inclusive start / exclusive end. The Ops
panel supports a one-hour default or a chosen end time. Mutes suppress notifications
at transition time; expiration does not manufacture another firing transition.
Monitor-authored audit rows survive the gold job's platform audit refresh.

`POST`/`PUT /api/apps/{name}/slo` upserts a named objective;
`DELETE /api/apps/{name}/slo/{slo}` removes it. `GET /api/apps/{name}/slo` returns
specs, observed history, remaining budget percent and a daily cumulative budget series
within each spec's window (28 days by default). Negative remaining budget means
exhaustion. The SLI uses the shared real-traffic and HTTP semantic-convention helpers:
availability rejects HTTP 4xx/5xx or OTel ERROR; latency compares duration to the
configured threshold. Unknown windows do not resolve previously firing burn alerts.
Changed measurement definitions get a new revision, so old buckets cannot contaminate
them. Multiple failing specs share one alert per app/rule with all spec names listed.
Sampling affects these span-derived SLIs: use ratio 1 for SLO apps. A histogram-based
SLI is deferred until the SDK metric contract is available.

`GET /api/apps/{name}/telemetry-health` reads the telemetry quality view. Orphans
exclude roots and all-zero parent IDs, and parent lookup crosses apps within the same
trace. Sampling, parents outside the 24-hour horizon and late arrivals can all resemble
broken propagation. The alert needs 25 consecutive quarter-hour observations above
20% spanning six hours; gaps are unknown. Sampler settings come from Apps API
`config.env` when exposed; unavailable or indirect settings stay unknown. Token
reconciliation uses the latest completed cost day and shows its date.

`GET /api/monitor/cost` returns 30 days of component costs and the latest table sizes.
The daily cost job adds `self_meter` even if fleet rollup fails, and recomputes 30 days
to absorb delayed/corrected billing. `BUNDLE_VAR_monitor_cost_pct` configures the
cost alert (default 10% of the fleet's previous-day compute plus priced AI cost,
excluding the monitor). Warehouse USD is an estimate based on the monitor SP's
share of total query duration, including queue time. Unavailable source permissions
produce null costs. Unknown components cannot resolve an existing cost alert.
Review/eval usage is captured directly from each final FMAPI response before parsing
model output, without depending on the parallel SDK v2 branch. Token USD stays null
unless S4's workspace-scoped `model_prices` contains effective input/output prices;
the UI labels the known subtotal and unpriced components. Delta sizes are bytes,
not a storage-dollar estimate.

Inventory creates the new operations tables and grants schema SELECT plus MODIFY on
`alert_mutes`, `slo_specs` and `monitor_audit` to the monitor SP. Run inventory before
using the new APIs. The SLO/health job uses PERFORMANCE_OPTIMIZED for its 15-minute
cadence; daily self-metering uses the cost job's STANDARD mode. Every new operations
table includes `workspace_id` and a table comment.

Phase 0 summaries backfill all available raw spans on their first run, then MERGE the
last two days to incorporate late telemetry. The daily lifecycle retention job waits
for the inventory job's gold task to succeed before deleting raw data. Daily/hourly
summaries survive raw retention; user, session, dependency, error-log and release
drill-downs remain limited to retained raw data. HLL sketches can be combined with
`hll_union_agg` and counted with `hll_sketch_estimate`; daily distinct counts must not
be summed for a monthly total. Percentiles describe individual buckets and are not
additive either.

Cost and GenAI queries prefer `monitor.llm.billable` when an app/day has markers
(including explicit false). Otherwise they select MLflow `LLM`/`CHAT_MODEL` spans,
with untyped legacy spans used only when the trace has no typed LLM span. Model names
are priced with the latest `model_prices.effective_from` on or before the usage date.
`ai_usd` stays NULL if any consumed model/direction lacks a price; total unit costs also
stay unknown rather than understate the bill. Zero-token directions do not require a
price. The UI labels AI dollars **list price, estimate**, including estimates derived
from an operator-supplied contract price. `ai_tokens_gateway` is a
reconciliation signal, not an input to span token totals. Unmapped gateway requesters
are `(untagged)`, never requester emails. Existing costs are corrected within the
configured rollup window (30 days by default).

Token totals prefer `gen_ai.client.token.usage` histogram sums per app/model/day/token
direction, using billable spans only when that metric direction is absent. This avoids
adding sampled spans to unsampled metrics. Metric counters are differenced for cumulative
temporality (including reset handling), summed for delta temporality, and deduplicated
before aggregation. The reader accepts flattened `sum`, `histogram.sum`, `value.sum` and
`data.sum`, with model/direction in `attributes`; cumulative stream keys use start time,
instance ID and dimensions. A preceding day supplies the boundary sample. An absent
metrics table also falls back to spans. Missing exports and sampled span fallback can
underestimate tokens; first observations of long-lived cumulative streams can span the
reporting boundary. This is an hourly circuit breaker, not an exact token reservation.

Idle dollars apportion billing intervals across UTC hours and sum the portions with
zero **observed** real requests. They are a subset of compute dollars, not an extra
charge. Missing telemetry or trace sampling can overstate idle spend. Unit denominators
exclude synthetic traffic; cross-day users/sessions use HLL unions. Outcome counts and
funnels use retained raw events. Cohorts use individual hashed-user membership from
raw spans: HLL sketches cannot reconstruct retention. Cohort dates mean first observed
within retention, not lifetime signup, and the current week is marked incomplete.

Product UI is under **Usage → Product & guardrails**, **Cost**, and fleet **Governance**.
Read APIs are `GET /api/unit-economics`, `/api/leaderboard`, `/api/model-prices`, and
`/api/apps/{name}/{unit-economics|events|funnels|cohorts|rum|guardrails|product-config}`.
Admin writes use `PUT /api/model-prices` (model, effective_from, input/output_usd_per_mtok,
source=list|contract), `PUT /api/apps/{name}/funnels/{funnel}` (steps array, 2–20 entries),
and `PUT /api/apps/{name}/product-config` (outcome_event and token_budget_day).
Values are bound SQL parameters, mutations require the existing `MONITOR_ADMINS` check.
Prices are applied on the next daily cost rollup; outcome/funnel changes are read by views.

The leaderboard normalizes available components to 0–100 and weights availability 25%,
errors 20%, latency 15%, scan 15%, review 10%, cost trend 10%, adoption 5%. It shows each
component and observed weight; missing evidence is excluded, not scored as perfect.
Availability is explicitly probe/proxy reachability. Latency uses the worst daily p95
against a published 2500 ms budget; review scores are scaled from 0–10; adoption saturates
at 100 distinct weekly users. The complete formula is served by the API and displayed
in Governance. It is implemented once, as tested pure Python, over SQL components.

`monitor.events` accepts the roadmap `event=custom`, `name`, `event_id`, `sid`, `user`,
`rid` contract. Log attributes and a matching server envelope supply traffic kind and
app version (unknown versions stay explicit). `monitor.rum` accepts single events or
an `events` batch: type=page_view/pageview/route_view, type=error/js_error/unhandledrejection
with message/stack, and name/metric=LCP/CLS/INP with value; route/path identifies the route.
Each RUM event's `rid` joins the server request envelope for a backend trace link; the
batch ingestion request is not presented as the failing request. Route query strings
and fragments are removed. Logs can also carry `event=rum` when logger scope is unavailable. RUM is sampled browser
evidence; page views and vitals are reported separately from fingerprinted error groups.

The quality job reserves sampled trace IDs durably before calling the judge. Defaults:
10 new traces per run, 50 per app per UTC day (`--samples`, `--daily-sample-cap`), including
failed judge calls. The existing review job serializes runs. Detectors run on previews
locally, then PII and common secret patterns are redacted before FMAPI. This adds monitor
protection while SDK v2 is merged separately; it does not certify arbitrary prose as
PII-free. No preview or model-generated excerpt/comment is written to findings; the
ledger stores only IDs, hashes and classification state. Judge failures do not resolve
policy alerts. Alerts are owned/scoped separately: `guardrail_pii_rate`,
`guardrail_policy_rate`, `prompt_template_drift`, and existing `quality_regression`.
Finding-rate threshold defaults to 10% per app/day (`--finding-rate`); drift share is
configurable with `--drift-share`. Initial template baselines do not alert.

The hourly gold job evaluates today's UTC tokens and the previous completed UTC hour.
It warns at 80% of budget or if today's usage plus the last hour would reach budget,
and blocks at 100%; zero/unset budgets produce `none`. Owned alerts are
`token_budget_warn` and `token_budget_block`. `GET /api/policy/{app}` returns only
`{"throttle":"none|warn|block"}` from memory and **never issues SQL**. Fleet refresh loads
all policies in one query. Missing/invalid entries, cache older than five minutes,
policy computation older than three hours, and previous-day policies fail open to `none`.
SDK enforcement is on the separate SDK v2 branch; the monitor does not stop model calls itself.

For the existing externally managed Genie space, curate these additional gold objects:
`v_unit_economics`, `v_events`, `v_funnels`, `v_cohorts`, `v_leaderboard`, `v_rum_daily`.
This local implementation does not modify that external space. `v_leaderboard` exposes
components; its final score is computed by the monitor API. Avoid adding raw preview data.

HTTP queries coalesce stable and legacy status attributes, and count HTTP 4xx/5xx or
OTel error status as errors. The basic template opts into `http/dup` and parent-based
ratio sampling at `1.0`. Synthetic exclusion beyond legacy healthz names requires the
SDK's `traffic.kind` attribute. Capacity fallback paths can be set through the admin
app-config API; absolute URLs and the proxy `/healthz` path are rejected.

New aggregate/model tables and alert/cost writes carry `workspace_id`. Idempotent
migrations add missing service columns, including `alert_events.muted` and
`incident_id` for Phase 2 (muting behavior is not implemented here). Alert retention
keeps the latest transition for every workspace/source/rule/app, including old open
conditions, so restarts and later job runs can recover state without a time cutoff.

## Permissions model

| Principal          | Needs                                                                                                                                                                                                                                                                               | Granted by                                     |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| deploying user     | workspace admin-ish: create schema/apps/jobs, read system tables                                                                                                                                                                                                                    | —                                              |
| monitor app SP     | `CAN_USE` warehouse, `CAN_MANAGE_RUN` on jobs                                                                                                                                                                                                                                       | bundle resource bindings (automatic)           |
| monitor app SP     | `CAN_USE` on every fleet app (probing), `USE/SELECT` on the schema                                                                                                                                                                                                                  | **inventory job** (self-bootstrapping, hourly) |
| monitor app SP     | `MODIFY` on `model_prices`, `funnel_specs`, `app_config`; inherited schema `SELECT` covers product views, findings and sample ledger                                                                                                                                                | **inventory job**                              |
| every fleet app SP | `CAN_USE` on the monitor for the SDK policy request. **This grants access to all viewer endpoints and fleet telemetry exposed by the monitor, not just that app's policy.** Admin mutations still require `MONITOR_ADMINS`; fleet SPs receive no direct UC grants from this change. | **inventory job**, additive Apps ACL update    |
| demo app SPs       | `CAN_QUERY` serving endpoint (agent only)                                                                                                                                                                                                                                           | bundle resource binding                        |
