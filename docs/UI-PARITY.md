# Classic → Operations console parity

Audit: 2026-10-30. Read all 1,675 lines of `app/static/index.html`, including
the supplementary S1/S2/S5/S6 scripts, and the console renderer, transport,
styles, tokens and deterministic sample. This matrix was written **before**
implementation. ✅ = implemented natively and verified locally.
Routes below are hash routes within `/`; `:app` is the console app identity.
The `/classic` route remains an emergency fallback, not a workflow dependency.

| Classic capability (source)                                                       | Console route → section                              | Status |
| --------------------------------------------------------------------------------- | ---------------------------------------------------- | ------ |
| Fleet health counts and attention ranking (`overviewSegHtml`)                     | `#/fleet` → health / attention                       | ✅     |
| Reachability, probe errors, real vs probe p95, cost 7d, findings KPIs             | `#/fleet` → fleet measures                           | ✅     |
| App cards, descriptions, probe history, technology / complexity                   | `#/fleet`, app Overview → inventory / provenance     | ✅     |
| Scan, review, budget, tags and alert badge details / navigation                   | `#/catalog`, app Overview → evidence / detail links  | ✅     |
| Catalog status and team facets / counts                                           | `#/catalog` → filters                                | ✅     |
| Catalog tag facets, tag search, untagged display                                  | `#/catalog` → filters / tags                         | ✅     |
| Catalog sortable name/status/uptime/p95/errors/MTD/scan/review/alerts/team        | `#/catalog` → inventory table                        | ✅     |
| Declared SQL warehouse resource bindings (`TRES`)                                 | `#/topology` → graph / relationship table            | ✅     |
| Declared model serving bindings                                                   | `#/topology` → graph / relationship table            | ✅     |
| Declared job bindings                                                             | `#/topology` → graph / relationship table            | ✅     |
| Declared MLflow experiment bindings                                               | `#/topology` → graph / relationship table            | ✅     |
| Declared Lakebase/database/postgres bindings                                      | `#/topology` → graph / relationship table            | ✅     |
| Declared UC securable bindings                                                    | `#/topology` → graph / relationship table            | ✅     |
| Declared secret scope bindings                                                    | `#/topology` → graph / relationship table            | ✅     |
| Declared Genie bindings                                                           | `#/topology` → graph / relationship table            | ✅     |
| Declared app-to-app bindings                                                      | `#/topology` → graph / relationship table            | ✅     |
| Shared resources, “· N apps”, blast radius                                        | `#/topology` → resource selection / dependent health | ✅     |
| Hover/focus app edge highlighting, click through                                  | `#/topology` → keyboard graph nodes                  | ✅     |
| Observed outbound relationships, volume/p95/error %, distinct legend              | `#/topology` → graph / relationship table            | ✅     |
| Workspace/team/resource filters, mobile graph/list alternative                    | `#/topology` → filters / relationship table          | ✅     |
| Genie iframe and unconfigured state                                               | `#/ask` → Ask Genie                                  | ✅     |
| Federation feeder/hub, remote inventory and usage/cost                            | `#/workspaces` → federation                          | ✅     |
| Workspace scope and feeder monitor navigation                                     | Global scope / `#/workspaces`                        | ✅     |
| Firing/resolved/muted alert views                                                 | `#/alerts` → state tabs                              | ✅     |
| Alert transition history (not just latest state)                                  | `#/alerts` → history                                 | ✅     |
| Live alert count tick and source freshness                                        | Sidebar / `#/alerts` → 60 s refresh                  | ✅     |
| Rule-specific next best actions (`nbaOf`)                                         | `#/alerts` → next action                             | ✅     |
| Maintenance windows, mute/unmute                                                  | `#/alerts`, app Operate → maintenance                | ✅     |
| Governance usage/cost 7d                                                          | `#/governance` → usage / cost                        | ✅     |
| MTD chargeback by team and cost center                                            | `#/governance` → allocation                          | ✅     |
| Fleet audit with actor, action, app, status                                       | `#/governance` → audit 7d                            | ✅     |
| Readiness checklist / compliance matrix                                           | `#/governance` → readiness                           | ✅     |
| Compliance Markdown export                                                        | `#/governance` → export                              | ✅     |
| Auto-stop rule preview and apply                                                  | `#/governance` → policy editor                       | ✅     |
| One-click template provisioning                                                   | `#/governance` → create app                          | ✅     |
| Effective model prices editor                                                     | `#/governance` → model prices                        | ✅     |
| Fleet unit economics, unpriced coverage and idle cost                             | `#/governance` → economics                           | ✅     |
| Leaderboard, components and disclosed formula                                     | `#/governance` → leaderboard                         | ✅     |
| Monitor self-cost, storage, basis and unknown subtotal                            | `#/governance` → monitor cost                        | ✅     |
| Refresh inventory action                                                          | `#/governance` → actions                             | ✅     |
| Run journeys action                                                               | `#/governance`, app Operate → actions                | ✅     |
| Fleet outcome/token settings shortcut                                             | `#/governance` → app product settings                | ✅     |
| Status page navigation                                                            | Sidebar → `/status`                                  | ✅     |
| Read-only MCP endpoint discovery (roadmap S10)                                    | `#/governance` → integrations                        | ✅     |
| App URL / description / owner / platform state                                    | `#/app/:app/overview` → header / record              | ✅     |
| Header health, reachability 24h, real p95, probe RTT, users 7d, errors 1h, alerts | All app sections → head stats                        | ✅     |
| Ranked takeaways and reliability/code/cost/adoption drilldowns                    | App Overview → related signals / evidence            | ✅     |
| Recent events and latest journey                                                  | App Overview → changes / synthetics                  | ✅     |
| Error fingerprints, counts, sample, first/last seen                               | `#/app/:app/errors` → groups                         | ✅     |
| Failed request spans with trace links                                             | App Errors → failed requests                         | ✅     |
| Error-level logs                                                                  | App Errors → error logs                              | ✅     |
| OTel request trace list                                                           | `#/app/:app/traces` → requests                       | ✅     |
| Waterfall, span hierarchy/attributes, correlated logs, return navigation          | `#/trace/:id` → waterfall                            | ✅     |
| MLflow agent trace list / experiment identity                                     | App Traces → agent runs                              | ✅     |
| Unified MLflow/OTel waterfall, tokens, services, MLflow deep link                 | `#/app/:app/agent-trace/:id` → unified trace         | ✅     |
| Logs explorer with severity, search and trace correlation                         | `#/app/:app/logs` → explorer                         | ✅     |
| Traffic request/error timeline, latency p50/p95                                   | `#/app/:app/traffic` → small multiples               | ✅     |
| Traffic per-route requests/errors/avg/p50/p95                                     | App Traffic → routes                                 | ✅     |
| Outbound dependency calls/avg/p95/errors                                          | `#/app/:app/dependencies` → observed peers           | ✅     |
| Declared resource details / permission bindings                                   | App Dependencies / Operate → resources               | ✅     |
| Incident/deploy/anomaly/lifecycle chronology                                      | `#/app/:app/changes` → timeline                      | ✅     |
| Release performance / regression against previous version                         | App Changes → releases                               | ✅     |
| Scan score, severity counts, source metrics and freshness                         | `#/app/:app/security` → source scan                  | ✅     |
| Python/npm installed/latest/staleness/CVEs                                        | App Security → packages                              | ✅     |
| Scan findings: type/title/detail/file/line                                        | App Security → findings                              | ✅     |
| Review purpose/tech stack/endpoints                                               | App Security → app overview                          | ✅     |
| AI verdict/overall and five scores/strengths/recommendations/model/tokens         | App Security → advisory review                       | ✅     |
| Fresh review action / printable app review                                        | App Security → actions                               | ✅     |
| Daily compute/AI calls/input/output tokens                                        | `#/app/:app/cost` → daily history                    | ✅     |
| Forecast and observations, MTD budget chart/config link                           | App Cost → budget / forecast                         | ✅     |
| Per-app unit economics / outcomes                                                 | App Cost → economics                                 | ✅     |
| AI daily tokens/models/calls/errors/latency                                       | `#/app/:app/ai` → daily / models                     | ✅     |
| AI top user/session consumers                                                     | App AI usage → consumers                             | ✅     |
| LLM error taxonomy and examples                                                   | App AI usage → taxonomy                              | ✅     |
| Agent complexity / steps per run                                                  | App AI usage → steps                                 | ✅     |
| Runtime judge quality and user feedback                                           | App AI usage → evaluations / ratings                 | ✅     |
| Prompt drift weekly samples/clusters/silhouette/novel share                       | App AI usage → drift                                 | ✅     |
| Daily requests, DAU, sessions, known users                                        | `#/app/:app/usage` → adoption                        | ✅     |
| Hashed user history, errors/tokens/active days and estimated cost share           | App Usage → users                                    | ✅     |
| Business events and versions                                                      | `#/app/:app/product` → events                        | ✅     |
| Ordered funnels, dropoff by version, editor                                       | App Product → funnels                                | ✅     |
| Weekly cohorts and partial-week caveat                                            | App Product → cohorts                                | ✅     |
| RUM web vitals / JS errors with trace links                                       | App Product → browser experience                     | ✅     |
| Masked guardrail findings / agent trace links                                     | App Product → guardrails                             | ✅     |
| Normalized prompt template shares                                                 | App Product → template drift                         | ✅     |
| Outcome event / daily token budget / current throttle policy                      | App Product → settings                               | ✅     |
| Tags/budget/auto-stop/idle-hours save                                             | `#/app/:app/operate` → configuration                 | ✅     |
| Start/stop/restart with in-page destructive confirmation                          | App Operate → lifecycle                              | ✅     |
| Capacity ramp and results (classic helper was unwired)                            | App Operate → capacity                               | ✅     |
| Probe history, last HTTP, TTFB, uptime and compute                                | App Operate → reachability                           | ✅     |
| Live synthetic journey steps / budget / run action                                | App Operate → journeys                               | ✅     |
| SLO list/editor/delete, observed coverage and budget burn-down                    | App Operate → objectives                             | ✅     |
| Telemetry quality, last signals, semconv, orphan/token reconciliation             | App Overview / Telemetry / Operate → data quality    | ✅     |
| Telemetry volume per signal                                                       | App Operate → export volume                          | ✅     |
| Deployment history/state/mode                                                     | App Operate → deployments                            | ✅     |
| Bound job health and runs                                                         | App Operate → jobs                                   | ✅     |
| ACL principals/levels and app audit trail                                         | App Operate → access / audit                         | ✅     |
| Browser check runs/result/HTTP/latency/failure detail                             | `#/app/:app/browser` → runs                          | ✅     |
| Browser artifacts, screenshot location / access                                   | App Browser checks → artifacts                       | ✅     |
| Time selection 1h/6h/24h/72h                                                      | Global range / deep sections → labelled window       | ✅     |
| Lazy deep reads, partial errors, missing-data explanation, retry                  | All deep sections → loading / source states          | ✅     |
| Session cache, visible-tab refresh, form/filter/sort preservation                 | Console transport / route lifecycle                  | ✅     |
| Existing admin endpoints and require_admin, read-only reason                      | All editors/actions → permissions                    | ✅     |
| Every route in deterministic offline demo                                         | `?demo=1` → snapshot / lazy fixtures                 | ✅     |
| Keyboard navigation, sortable tables, 320–1440 responsive Cobalt UI               | All routes                                           | ✅     |

## Validation

All **105 capability rows** were implemented after this matrix was first written.
No feature is deferred to Classic. The fallback route remains available.

- Repository gates: `uv run pytest --cov -q` — **374 passed, 2 existing skips**,
  **99.62% branch-aware coverage** (85% floor); Ruff check, Ruff format check and
  strict mypy pass. The two unchanged skips require the app-runtime MCP dependency.
  Commands used the existing environment with `--frozen --no-sync` and a
  workspace-local uv cache; no dependencies or lockfile changes.
- Backend regression tests cover Apps API/inventory resource parsing, all binding
  types, typed peer matching, shared resources, weighted aggregation, missing
  metrics, workspace isolation, requester identity, admin enforcement, actual
  stop/wait/start sequencing and failure behavior, partial source errors,
  consistent policy previews, bounded browser history, and snapshot/demo keys.
- Python Playwright: **168 route/width checks** — all 11 sidebar routes plus all
  15 app sections for `fraud-triage`, `claims-assistant`, `legacy-reports`, at
  **1440, 390 and 320 px**. **Zero JavaScript errors and zero page overflow.**
  Topology nodes/edges, mouse hover, focus highlights, sequential Tab navigation
  through every node, resource/team filters, accessible relationship table and
  shared-resource blast radius pass.
- Workflow checks: config save and draft preservation; start/stop/restart wiring
  with destructive confirmation/cancel; capacity results; SLO and mute/unmute
  editors; product settings and funnels; MLflow and OTel trace drilldowns;
  compliance download; model prices; provisioning; auto-stop preview/apply;
  disabled controls and reasons for non-admins or unavailable saved settings.
  Lazy first read, session cache, visible-only refresh, retained data on failure,
  retry, Genie iframe configuration, and prefixed production HTTP paths were
  exercised with local fixtures. Screenshots and reports: `.cache/console-qa/`.
- Demo regeneration is deterministic. Deep fixtures are separate from the fleet
  snapshot. The demo dispatcher never issues workspace requests.
- Roadmap coverage: S1/S2 operational quality, S4/S7/S8 product analytics,
  S5/S6 economics/governance, S10/S11/S12/S13 reach, S14 drift, and F0.8 workspace
  identities. Adaptations use actual existing endpoints and schema fields:
  daily dependency percentiles are labelled **worst daily p95**, and the former
  start-only “restart” now waits for stop before start.

Validation is offline: Databricks deployment, warehouse execution and real
workspace mutations were not run. Existing data limits remain explicit in the UI:
resource health has no signal without direct evidence; absent telemetry is unknown;
remote deep evidence opens the configured feeder monitor; browser artifacts use
their recorded UC volume folder (screenshots exist only when captured). These
are existing source constraints, not workflows requiring Classic.

## Design-quality verification

All **105/105 capability rows remain** after the presentation pass. See
[CONSOLE-DESIGN-AUDIT.md](CONSOLE-DESIGN-AUDIT.md) for the Hallmark route audit,
all ten punch items, changed files, screenshots and validation. No route or editor
was delegated to Classic or removed. Topology now uses one visible node for a
monitored app, workspace-qualified resource labels, neutral missing health and
merged declared/observed edges. Operate and Governance retain all their evidence
and actions behind navigable section indexes.
