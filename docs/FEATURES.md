# Full capability reference

Every feature of Apps Monitor mapped to the mechanism that powers it and the
table/view it reads or writes. The selling summary lives in the [README](../README.md);
this is the exhaustive list.

| Capability                       | How                                                                                              | Where                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------- |
| Live fleet board                 | 60 s HTTP probes with the monitor's SP OAuth; KPI tiles, needs-attention list, sparklines        | monitor app, in-memory                            |
| Requests / latency / errors      | platform OTel export into shared UC tables; per-app charts + route tables                        | `otel_spans`                                      |
| Log explorer                     | stdout/stderr + app logs, severity-filtered, trace-correlated                                    | `otel_logs`                                       |
| Distributed traces               | request list → waterfall with correlated logs                                                    | `otel_spans` + `otel_logs`                        |
| Unified agent traces             | MLflow AGENT/TOOL/LLM spans merged with app spans; one `client_request_id` from browser to token | `otel_spans` + MLflow REST                        |
| Fleet inventory                  | hourly snapshot + automated access grants                                                        | `apps_inventory`                                  |
| Source & dependency scans        | CVEs (OSV.dev), secrets, smells, quality score per deployment                                    | `code_scans`, `scan_findings`                     |
| Package analysis (py + npm)      | installed vs latest (PyPI/npm registry), staleness class, per-package CVE ids                    | `deps_json` in `code_scans`                       |
| Agentic code review              | Databricks-hosted Claude reviews each app's source: verdict + scores                             | `llm_reviews`                                     |
| Cost tracking                    | billing × list prices; billable LLM spans per model; gateway tokens stored separately; requester SP IDs resolved through inventory | `costs_daily`, `costs_ai_daily`, `apps_inventory` |
| Synthetic monitoring             | probes/journeys/capacity send `x-monitor-synthetic`; queries prefer `traffic.kind`, with legacy healthz-name fallback | `app/journeys.json`, `otel_spans` |
| Alerting                         | startup rehydration; job-owned firing/resolved transitions; partial scans resolve only evaluated apps; open alerts in UI | `alert_events`, `v_alerts_open` |
| Adoption analytics               | retained daily/hourly request counts and user/session HLL sketches; per-user detail within raw retention | `agg_app_daily`, `agg_app_hourly`, `v_usage_daily`, `v_users` |
| GenAI monitoring                 | retained billable model/token/latency trends by traffic kind; recent session detail | `agg_genai_daily`, `v_genai_daily`, `v_genai_sessions` |
| Error groups & dependencies      | SDK exception fingerprints with normalized-log fallback; outbound peer latency | `v_error_groups`, `v_dependencies` |
| Timeline & releases              | alerts+deploys+anomalies chronology; regression-by-version                                       | `v_release_perf`                                  |
| Smart detection                  | hourly traffic/latency z-scores vs 7-day baselines                                               | gold job → alerts                                 |
| FinOps governance                | budgets, burn alerts, hard budget stop, forecast, chargeback, idle/night auto-stop               | `app_config`, `v_chargeback`, `v_cost_forecast`   |
| Security & compliance            | deny-list policy, freshness, permission drift, audit, compliance export                          | `policy.json`, `app_permissions`, `monitor_audit` |
| Provisioning                     | one-click tagged app from template, telemetry pre-wired                                          | `monitor-provision-app`                           |
| Runtime quality evals            | daily LLM judge on sampled production traces + regression alerts                                 | `monitor_quality`                                 |
| User feedback                    | `POST /monitor/feedback` ★ ratings through the native pipeline                                   | `v_feedback`                                      |
| LLM error taxonomy & agent watch | rate-limit/policy/timeout/schema classes; spans-per-trace trend                                  | GenAI tab                                         |
| Capacity probing                 | tagged step ramp on `/monitor/health`; missing route falls back to admin `capacity_path` or `/` | Ops tab, `app_config` |
| Ask Genie                        | curated Genie space (18 gold objects) embedded in the app                                        | `#/ask`                                           |
| AI/BI dashboard + watchdog       | versioned Lakeview dashboard; dead-man SQL alert                                                 | `dashboards/fleet.lvdash.json`                    |

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
are retained for future pricing; `ai_usd` remains unset. `ai_tokens_gateway` is a
reconciliation signal, not an input to span token totals. Unmapped gateway requesters
are `(untagged)`, never requester emails. Existing costs are corrected within the
configured rollup window (30 days by default).

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

| Principal      | Needs                                                              | Granted by                                     |
| -------------- | ------------------------------------------------------------------ | ---------------------------------------------- |
| deploying user | workspace admin-ish: create schema/apps/jobs, read system tables   | —                                              |
| monitor app SP | `CAN_USE` warehouse, `CAN_MANAGE_RUN` on jobs                      | bundle resource bindings (automatic)           |
| monitor app SP | `CAN_USE` on every fleet app (probing), `USE/SELECT` on the schema | **inventory job** (self-bootstrapping, hourly) |
| demo app SPs   | `CAN_QUERY` serving endpoint (agent only)                          | bundle resource binding                        |
