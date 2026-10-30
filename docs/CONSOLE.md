# Operations console

`/` serves the chosen V1 Operations workbench from `app/static/console`. Its tokens,
layout and “Every app, at a glance” tiles come from the approved reference. The
classic UI remains at `/classic` as a fallback. The native console now includes
all capabilities in [the parity matrix](UI-PARITY.md), including topology, catalog,
Genie, governance, lifecycle controls, capacity ramps, review triggers and editors.

`/?demo=1` or `/console/index.html?demo=1` loads the bundled deterministic sample
without querying the service. The latter also works over a local static server or
`file://`. Demo provenance is always labelled. Static assets, snapshot requests,
lazy details and the Classic link retain an enclosing application path prefix.

`GET /api/console/snapshot` returns the V1 `window.MOCK` keys plus `traces: {}` and
`sources: {name: "ok" | "missing" | "error"}`. Warehouse sections run concurrently
and are assembled into a 60-second cache. Each read has a 50-second deadline,
matching the existing Statement API timeout. Initial requests return live inventory
and probes with a collection notice while warehouse reads run in the background;
the next refresh adds their results. Concurrent clients share that work. Cached
responses overlay current local probe health, inventory membership and active
monitor alerts without waiting on SQL. `generated_at` dates the warehouse snapshot;
`notes.live_as_of` dates the live overlay. No new tables, jobs, dependencies or grants
are introduced. The existing lifecycle job now accepts `restart`: it waits up to
ten minutes for stop to complete before requesting start. Protected monitor apps
cannot be stopped or restarted through this action.

The browser polls every 60 seconds without reloading the script. Route, filters,
sort order, page scroll, expanded details, trace selection and an open search dialog
survive refresh. Fetch failures retain the last successful snapshot and offer retry.
Null measurements render as `—` or “not collected yet”; chart gaps remain gaps.

| Source / mechanism                                                       | Snapshot field                                                                               | Availability and period                                                                                                                                                                                                                                                                          |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Apps API `fleet`, `probes`, `_summary()`, `health_detail`                | `apps` identity, platform state, health, version, probe uptime; local `workspaces` freshness | Monitor scheduler; no warehouse required. Health is down/degraded/stopped/idle/healthy, or null before evidence. Idle requires observed zero real requests. Probe latency never becomes request latency.                                                                                         |
| `REAL_PERF_FLEET` / `otel_spans`                                         | `apps.last24h` requests, errors, p50/p95/p99, active users                                   | Real server spans over rolling 24h, after platform OTel export; user counts need SDK user identifiers.                                                                                                                                                                                           |
| `agg_app_hourly`                                                         | `apps.series_24h`                                                                            | Hourly inventory **gold** task. Exactly 24 UTC hour buckets including the current partial hour; absent buckets and invalid rates are null.                                                                                                                                                       |
| `CONFIGS_ALL` / `app_config`                                             | team, cost center, monthly budget, auto-stop, tag completeness                               | Gold bootstraps the table; populate policy/tags in app Operate. Unknown configuration stays null.                                                                                                                                                                                                |
| `SLO_SUMMARY` fleet variant / `slo_specs`, `sli_5m`                      | `apps.slo`                                                                                   | Configure SLOs, then `monitor-slo-eval` every 15 minutes. V1 availability tiles select an unfiltered **28-day** availability objective; other specs remain in `slo.specs` and the native Operate editor. No samples means no attainment.                                                         |
| `v_telemetry_health`                                                     | `apps.telemetry` freshness, coverage, sampling and orphan share                              | Inventory gold task; missing exports remain unknown. Ratios are converted to percentages. Observed spans establish export activity, not export configuration.                                                                                                                                    |
| `UNIT_ECONOMICS` / `v_unit_economics`, `costs_daily`                     | `apps.cost` actual, compute, AI, idle and per-1k-request cost                                | Daily `monitor-cost-rollup` plus gold views and configured model prices. MTD total stays null when compute or AI pricing is unknown.                                                                                                                                                             |
| Daily unit economics and app config                                      | `apps.cost.daily_30d`, `cost.days`, `cost.by_team`, monthly forecast                         | 30 aligned calendar dates, gaps null. Forecast is labelled an estimate: trailing completed-day mean × calendar-month length, only after seven observed completed days. Budgets remain separate.                                                                                                  |
| `monitor_cost_daily`, `model_prices`                                     | `cost.monitor_self_cost_*`, `cost.model_prices`                                              | Cost job's **self_meter** task; missing price/component coverage stays null. Model prices are configured in Governance → Model prices.                                                                                                                                                           |
| `SEC_BY_APP`, `v_findings_latest`, scan `deps_json`                      | `apps.security` CVEs by severity, secrets, quality, outdated packages                        | Inventory **source_scan** task. Only actual CVE findings are labelled CVEs. A known scan with no findings reports zero. Incomplete registry checks keep the outdated-package count null.                                                                                                         |
| `REVIEW_BY_APP` / `v_review_latest`                                      | `apps.security.review_*`                                                                     | `monitor-llm-review` or the native Security review action. Scores retain their source scale.                                                                                                                                                                                                     |
| `alerts.active()`, `OPEN_JOB_ALERTS`, `RECENT_ALERTS`                    | `alerts`, alert `timeline`, active permission drift                                          | Scheduler plus inventory/cost/SLO/quality alert emitters. Latest states are deduplicated; live firing alerts and retained resolved history stay distinct. No permission-drift alert does not prove a clean ACL scan.                                                                             |
| Bounded log/span fingerprint query, following `v_error_groups` algorithm | `error_groups`                                                                               | OTel export. Fleet top 100 within 24h, with trace references and a latest sample. Per-app groups load on demand (up to 100). The existing gold view counts all retained history, so its count cannot be labelled 24h.                                                                            |
| `TRACE_SPANS`, `TRACE_LOGS`                                              | Lazy `traces[id]`; `trace_example` is null in live snapshots                                 | `GET /api/console/trace/{trace_id}`; local seven-day window, at most 500 spans and 200 logs. Unknown IDs return 404, invalid IDs 422, unavailable span source 503. Logs may degrade independently. Missing parents are roots with an orphan attribute; UI depth traversal also tolerates cycles. |
| `app_deployments`, `monitor_audit`                                       | Deployment `timeline`, `apps.deployed_at`, `governance.audit_events`                         | Inventory gold snapshots. App version comes from the health contract; a deployment ID is not relabelled as a version.                                                                                                                                                                            |
| `synthetic_runs` completion rows                                         | `synthetics` by app/journey/vantage                                                          | In-app journeys and the external runner; up to 12 runs per check within 24h. No completion evidence means not collected.                                                                                                                                                                         |
| `alert_mutes`                                                            | `maintenance_windows`                                                                        | Configure in Alerts or app Operate; active and scheduled unexpired windows. A stopped app without a recorded window is not claimed to be under maintenance.                                                                                                                                      |
| `v_genai_daily`                                                          | `apps.genai` models, calls and tokens                                                        | Gold task; **previous complete UTC day**, explicitly labelled in the UI. Daily gold does not provide rolling-24h totals. Billable-call aggregation avoids counting agent parent spans twice.                                                                                                     |
| Billable SDK spans                                                       | GenAI TTFT p95 and error classes                                                             | Real spans in rolling 24h after `llm_call` instrumentation and export. TTFT remains null without observations; probe TTFB is never substituted.                                                                                                                                                  |
| `monitor_quality`, `guardrail_findings`, `v_feedback`, `drift_reports`   | GenAI quality, guardrails, feedback and prompt drift                                         | Review job **quality_evals**, gold feedback, optional weekly **prompt-drift** job. Missing evaluations/drift are null. Drift job is paused by default.                                                                                                                                           |
| `v_funnels`, `v_cohorts`, `USAGE_FLEET`                                  | `funnel_example`, `cohorts_example`, `apps.usage_7d`                                         | Gold task after business events, funnel specs and identified-user traffic. V1 displays the first configured funnel and first app with cohort rows; event names are not hardcoded. Current cohort week is partial.                                                                                |
| Hub `REACH_FLEET`, `v_fleet_costs_daily`, `v_fleet_alerts_open`          | Remote apps, workspaces, compute costs, 7d usage, alerts                                     | Feeder inventory/cost/gold followed by hub gold; only in `DEPLOYMENT_MODE=hub`. App IDs include workspace ID to prevent same-name collisions.                                                                                                                                                    |

Local collection becomes STALE after five minutes without a successful Apps API
refresh. Feeder inventory becomes STALE after two hours without collection. The UI
derives unverified health from those workspace states. Fresh remote inventory alone
cannot establish healthy probes: remote live health remains unknown. Feeder hourly
series, SLOs, model pricing, raw traces and logs are not published by the existing
federation contract. Open the configured `MONITOR_WORKSPACES` feeder link for them.
Remote compute spend is retained separately; it is not labelled total app spend.

Some V1 fields have no authoritative existing source: workspace region, explicit
SDK version, and first-ever error occurrence relative to deployment remain null.
The roadmap's `runtime_packages` table is not implemented in this branch, so no
query assumes it exists. Exception groups' `first_seen` is first observed in the
24h query; `new_since_deploy` stays unknown. MLflow REST calls run only when an app’s Traces section or an agent trace opens.
The existing agent-trace endpoint joins MLflow metadata to dual-exported OTel
AGENT/LLM/TOOL spans and correlated logs. A native deep link opens MLflow even
when OTel delivery has not supplied spans yet.

Implementation follows roadmap F0.4/F0.5/F0.8 and surfaces S1/S2/S4–S8/S11/S12/S14.
No roadmap file outside this worktree was edited. Adaptations to its sketches are
explicit: asynchronous `q.run`, revision-aware SLO joins, workspace-qualified
federation identities, and the actual implemented source schemas.

Deep sections use the existing `/api/apps/{name}/...` endpoints. Each endpoint
loads on first use, stays in a session cache, and refreshes on the 60-second cycle
only while visible. Loading, empty, failed and retained-last-result states are
separate. Optional source failures are exposed in `_source_errors`; other source
results remain usable. Request bodies, method and server-side `require_admin`
enforcement are shared with Classic. `GET /api/console/identity` is evaluated for
each requester, outside the shared snapshot cache. Non-admins receive disabled
controls and the server's read-only reason. Stop, restart, objective deletion and
policy application use in-page confirmation. Policy apply requires the same
targets as the preview; unavailable configuration prevents application.

`#/topology` combines Apps API resource bindings (falling back to inventory
`resources_json`) and a single fleet-wide `v_dependencies` read. Typed,
workspace-qualified identities prevent equal warehouse/endpoint names and remote
app names from being merged. Calls and errors sum; average latency is weighted by
calls. The graph explicitly labels its **worst daily p95**, since daily percentiles
cannot produce an exact seven-day percentile. Resources without evidence use neutral “No health signal” labels. Known app
dependencies resolve by name and workspace, then a unique URL host, and retain
the same node and health as the monitored app. Ambiguous hosts never guess.
Resource labels include their workspace; type headers and barycentric ordering
make shared dependencies easier to scan. Hover/focus highlights edges; selecting a
target shows direct dependents and their health. The same filtered edge set drives
the accessible sortable relationship table and mobile layout. Runtime observations
are local; the existing feeder contract does not publish raw dependency edges.

The deterministic fixture generator is `scripts/generate_console_demo.py`.
`demo-data.js` contains fleet summaries and graph data; `demo-fixtures.js` holds
small endpoint fixtures separately, and `demo-details.js` handles offline reads
and session-only simulated writes. `?demo=1&readonly=1` exercises non-admin UI.
No demo action calls a workspace API.

Validation uses `scripts/check_console_ui.py` with Python Playwright. It covers
all 11 sidebar routes and all 15 app sections for fraud-triage, claims-assistant
and legacy-reports at 1440, 390 and 320 pixels (168 route/width checks), graph
interaction and keyboard targets, form saves, stop/restart confirmation, SLOs,
maintenance, capacity results, trace drilldowns, compliance export, auto-stop
preview/apply, read-only controls, and live transport fulfilled with local fixtures
under an application path prefix. All external browser requests are blocked.
Reports/screenshots are written under `.cache/console-qa/`.

Run the browser audit with an existing Playwright installation:

```sh
uv run python scripts/check_console_ui.py
# If the repo environment lacks Playwright, reuse an existing installation:
uv run python scripts/check_console_ui.py --package-root /path/to/site-packages
```

Unit tests cover resource parsing, graph aggregation and workspace isolation,
missing metrics, snapshot/demo contracts, identity and write authorization,
restart sequencing/failure, source errors, preview consistency, and browser
history bounds. Repository gates also cover the existing SDK and services.
Workspace deployment and SQL execution are outside this offline validation.

The design-quality pass is documented in [the route audit](CONSOLE-DESIGN-AUDIT.md).
Operate has eight anchored sections and Governance has nine, with return links;
all parity views, sortable tables and controls remain available. Structured values
use human labels, compact definition lists, UTC dates, percentages and units.
V1 and deep time series share one renderer with HTML axis labels, so resizing an
SVG does not scale its typography. Missing samples stay gaps and negative error
budgets remain visible. Integrations displays the app-prefixed HTTP MCP endpoint;
offline demos show an explicitly labelled placeholder.

Demo leaderboard components are derived from the fixture's health, request errors,
p95, scan, review, weekly cost change and active users. The offline score formula
is tested against the production helper; stopped apps are excluded. The UI names
the demo adoption proxy (active users instead of distinct seven-day users).
