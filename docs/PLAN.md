# Plan — Application Insights for Databricks Apps

> One Databricks-native monitoring toolkit that answers, across every app in the
> workspace: **Is it up? Is it slow? What failed? What does it cost? Is the code any
> good?** — the Azure Application Insights experience, rebuilt on Databricks primitives.

Target workspace: `https://fevm-serverless-stable-domo.cloud.databricks.com` (profile `fevm-domo`).
Concept sources: [`observ/MONITORING-ARTICLE.md`](../observ/MONITORING-ARTICLE.md),
[`observ/.../tracing/UNIFIED.md`](../observ/20260514_001842_locust_performance_testing_for/tracing/UNIFIED.md),
UI mockup [`observ/monitoring-app (2).html`](<../observ/monitoring-app%20(2).html>).
Boilerplate: [databricks-apps-fastapi-starter](https://github.com/Paldom/databricks-apps-fastapi-starter).
Synthetic-test reference: [databricks-apps-e2e-playwright-testing-dab](https://github.com/Paldom/databricks-apps-e2e-playwright-testing-dab).

---

## 1. Product definition

| Question a CTO / SRE asks         | Feature                                              | Primary source                                                              |
| --------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------- |
| Is every app up right now?        | Live probes + fleet status board                     | In-app prober (SP OAuth → app URL)                                          |
| Where is it slow? What failed?    | Requests / latency / error explorer                  | `otel_spans` / `otel_logs` (Apps → UC telemetry)                            |
| What did one request actually do? | Unified trace waterfall                              | OTel spans + MLflow traces joined on `trace_id`/request id                  |
| What does each app cost?          | Cost page: DBUs + AI spend, per app                  | `system.billing.usage` + `system.serving.endpoint_usage` / AI Gateway usage |
| Is the code healthy / secure?     | Scheduled source scans (deps, CVEs, secrets, smells) | Workspace Files API + OSV.dev + bandit                                      |
| Would a CTO approve this app?     | Scheduled agentic LLM review with scores             | Foundation Model API (Claude on Databricks)                                 |
| Do user journeys still work?      | Scheduled synthetic tests                            | HTTP journey checks; Playwright module                                      |
| Who gets told when it breaks?     | Alert rules + alert center + SQL alerts              | Monitor app + Databricks SQL alerts                                         |

**Most important metrics first** (the six KPI tiles, mirroring the mockup):

1. **Fleet health** — n/N apps OK (probe success)
2. **Availability** — 24 h uptime % per app
3. **p95 latency** — fleet + per app, from OTel root spans
4. **Error rate** — 5xx + exception share of requests
5. **Cost today** — app DBU $ + AI $ per app
6. **Open findings** — critical CVEs / security findings count

Everything else (adoption, journeys, quality scores, audit) layers on incrementally.

## 2. Platform facts this design relies on (verified in this workspace)

- **Apps → UC telemetry**: `telemetry_export_destinations` on the App resource ships
  OTel logs/spans/metrics via Zerobus into UC Delta tables (`otel_logs` auto-populated;
  spans/metrics need `opentelemetry-instrument` + SDK). Supported in DABs (`resources.apps.*.telemetry_export_destinations`).
- **System tables** available: `system.billing`, `system.ai_gateway`, `system.access`,
  `system.lakeflow`, `system.serving`, `system.compute`, `system.mlflow`, `system.query`.
- **Foundation Model APIs** (pay-per-token): `databricks-claude-opus-4-7`,
  `databricks-gpt-5-5`, `databricks-glm-5-2`, … → used by the LLM review job.
- **Apps expose source**: `apps get` → `source_code_path` in `/Workspace` → Files API
  export → scan jobs read every app's code, requirements, config.
- **App auth for probing**: M2M OAuth (`WorkspaceClient(client_id, client_secret).config.authenticate()`)
  against the app URL — the pattern proven in the playwright repo. The monitor app's own
  service principal (auto-injected `DATABRICKS_CLIENT_ID/SECRET`) probes fleet apps it has `CAN_USE` on.
- **Serverless-only workspace**: no classic clusters / Docker containers → Playwright runs
  in a serverless job env (best-effort) with plain HTTP journey checks as the guaranteed baseline;
  the classic-compute + custom-container pattern from the reference repo stays documented for
  workspaces that have DCS.
- **Alerts v2 + SQL warehouse** available; alerts deployable from the bundle.

## 3. Architecture

```
                        ┌────────────────────────────────────────────────┐
                        │ Fleet: N Databricks Apps                       │
                        │  demo-healthy · demo-flaky · demo-slow ·       │
                        │  demo-vuln · demo-agent · fastapi-starter · …  │
                        │  each: opentelemetry-instrument + envelope     │
                        │  middleware + telemetry_export_destinations ───┼──► UC monitoring schema
                        └────────────▲───────────────────────────────────┘      otel_logs/otel_spans/otel_metrics
                                     │ probes (SP OAuth, 60 s)                        │
┌───────────────┐      ┌────────────┴───────────────┐        ┌───────────────────────▼─────────────────┐
│  Lakeflow jobs │      │  Monitor app (FastAPI)     │        │  UC schema: <catalog>.monitor      │
│  inventory+scan│─────►│  · fleet overview (live)   │◄───────┤  apps_inventory · health_checks(view)    │
│  llm-review    │ write│  · app detail: requests /  │  SQL   │  code_scans · scan_findings · llm_reviews│
│  synthetics    │ Delta│    errors / traces / cost /│ (wh)   │  synthetic_runs · costs_daily · monitor_* vws│
│  cost-rollup   │      │    security / review       │        └───────────────────────▲─────────────────┘
└──────┬────────┘      │  · alert center + rules    │                                │
       │ reads          └────────────────────────────┘        system.billing.usage · system.ai_gateway │
       └── system tables, Workspace Files (app source), FMAPI ─────────────────────────────────────────┘
```

Design rules:

- **Native pipeline over custom ingestion.** No bespoke OTLP collector: apps write telemetry
  through the platform (`telemetry_export_destinations`) into **shared tables** in one schema;
  `service_name` (= app name) is the tenant key. The monitor never receives telemetry directly.
- **Jobs write, app reads.** Jobs run as the deploying user (sees all apps, system tables) and
  materialize Delta tables; the app's SP only needs SELECT on the schema + `CAN_USE` warehouse +
  `CAN_USE` on fleet apps (probing) + `CAN_MANAGE_RUN` on jobs (on-demand refresh/scan buttons).
- **Warm data in memory, history in Delta.** The in-app prober keeps a ring buffer for the live
  board and evaluates availability/latency alert rules in memory (no warehouse wake-ups);
  history and deep pages query UC on demand. Cost/security alerts are evaluated by the jobs.
  This keeps the serverless warehouse asleep unless a human is looking — monitoring that
  doesn't torch its own cost budget.

## 4. Data model (schema `serverless_stable_domo_catalog.monitor`)

| Table                                                                       | Writer         | Content                                                                             |
| --------------------------------------------------------------------------- | -------------- | ----------------------------------------------------------------------------------- |
| `otel_logs`                                                                 | platform       | stdout/stderr + system events, all apps (`service_name`)                            |
| `otel_spans`                                                                | platform       | HTTP server/client spans + custom spans, all apps                                   |
| `otel_metrics`                                                              | platform       | counters/gauges/histograms, all apps                                                |
| `apps_inventory`                                                            | inventory job  | snapshot per app: status, url, creator, resources, sc path, version                 |
| `health_checks`                                                             | monitor app    | probe results flushed periodically (app, ts, ok, latency_ms, code)                  |
| `code_scans`                                                                | scan job       | per app per run: dep counts, loc, quality score, posture summary                    |
| `scan_findings`                                                             | scan job       | finding rows: CVE / secret / smell, severity, file, detail                          |
| `llm_reviews`                                                               | review job     | per app: scores (security/reliability/cost/maintainability), verdict, findings JSON |
| `synthetic_runs`                                                            | synthetics job | journey step results: app, journey, step, ok, latency, detail                       |
| `costs_daily`                                                               | cost job       | per app per day: dbu, dbu_usd, ai_usd, tokens, requests                             |
| `alert_events`                                                              | app + jobs     | fired alerts: rule, app, severity, value, ts, state                                 |
| views `monitor_requests`, `monitor_errors`, `monitor_latency`, `fleet_kpis` | bundle SQL job | thin views over otel\_\* + tables for dashboards/Genie/alerts                       |

## 5. Components

### 5.1 Monitor app (`app/`) — "the Monitor"

FastAPI + a single-page vanilla-JS UI adapted from the user's mockup (dark fleet board,
KPI tiles, needs-attention list, charts). No React build step — one HTML file + fetch.
Endpoints: `/api/fleet` (live board), `/api/apps/{name}/…` (requests, errors, logs, traces,
cost, scans, reviews, synthetics), `/api/alerts`, `/api/actions/*` (trigger jobs), `/healthz`.
Background: asyncio prober (60 s, all fleet apps), rule evaluator, Delta flusher (15 min).
The monitor instruments **itself** (same telemetry export) — it is app #1 of the fleet.

### 5.2 Jobs (`jobs/` — serverless, one bundle)

| Job              | Schedule     | What it does                                                                                                                                                                                        |
| ---------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `inventory-scan` | hourly       | `apps list` → `apps_inventory`; export each app's source → deps/CVE (OSV.dev), secrets regexes, bandit, config smells → `code_scans` + `scan_findings`                                              |
| `llm-review`     | daily 05:00  | for apps with changed deployments: pack source (tree + key files ≤ ~60 KB) → Claude on FMAPI, structured-JSON CTO review → `llm_reviews`                                                            |
| `synthetics`     | every 30 min | per-app journey specs (YAML in repo): HTTP steps w/ assertions + latency budgets → `synthetic_runs`; Playwright journey best-effort on serverless                                                   |
| `cost-rollup`    | daily 06:00  | `system.billing.usage` (`billing_origin_product='APPS'`, `usage_metadata.app_id`) × `list_prices` + AI Gateway/serving usage joined by request tags → `costs_daily`; anomaly check → `alert_events` |

### 5.3 Example fleet (`example-apps/`) — the army

Tiny FastAPI apps (3 files each: `main.py`, `app.yaml`, `requirements.txt`), all with
telemetry export + envelope middleware, each engineered to light up one part of the toolkit:

| App                    | Behavior                                                           | Lights up                                     |
| ---------------------- | ------------------------------------------------------------------ | --------------------------------------------- |
| `monitor-demo-healthy` | clean 200s, fast                                                   | green baseline                                |
| `monitor-demo-flaky`   | ~10% 500s + unhandled exceptions                                   | error rate, error explorer                    |
| `monitor-demo-slow`    | random 0.3–3 s latency, occasional timeouts                        | p95/p99, latency alerts                       |
| `monitor-demo-vuln`    | pinned vulnerable deps, hardcoded fake secret, `eval()`, debug on  | CVE scan, secrets, smells, LLM review verdict |
| `monitor-demo-agent`   | periodic small FMAPI calls with MLflow traces + token/gateway tags | traces, AI cost correlation                   |

Plus the three apps already in the workspace (`fastapi-starter`, `domo-genai-bp`,
`solution-builder-o99kyp`) — monitored as-is: inventory, probes, scans and cost work with
**zero app changes**; telemetry depth arrives when an app opts in (see instrumentation guide).

### 5.4 Alerting

- In-app rules (yaml/table): app down ≥2 probes, p95 > budget, error rate > 5%, cost spike
  > 2× 7-day median, new critical CVE, review score drop. Fires → `alert_events` + alert
  > center UI (+ optional webhook env var).
- Bundle-managed **SQL alerts** on `fleet_kpis` views for email delivery via Databricks.

### 5.5 Instrumentation guide (`docs/INSTRUMENTATION.md`)

The "what to add to _your_ app" contract, in levels:

- **L0 — nothing**: inventory, probes, source scans, LLM review, DBU cost still work.
- **L1 — platform telemetry**: add `telemetry_export_destinations` + `opentelemetry-instrument`
  → requests, latency, errors, logs pages light up.
- **L2 — golden envelope**: copy `monitor_middleware.py` (request id, session, hashed user,
  app version attrs) → journeys, users, unified correlation.
- **L3 — GenAI**: MLflow autolog + `update_current_trace` + AI Gateway request tags →
  agent waterfalls + per-request AI cost joined to OTel via `trace_id`/request id.

## 6. Iterations (deploy to workspace after every one)

| #   | Deliverable                                                                                      | Proof                                   |
| --- | ------------------------------------------------------------------------------------------------ | --------------------------------------- |
| 1   | Bundle + schema + monitor app v1: live fleet board (probes) + inventory job                      | app URL shows real fleet                |
| 2   | Example apps army deployed + telemetry export wired for all → requests/errors/latency/logs pages | otel tables filling; flaky/slow visible |
| 3   | Source scan job → security page (CVEs on demo-vuln)                                              | findings rows + UI                      |
| 4   | LLM review job → review page with scores + verdicts                                              | Claude-written reviews in UI            |
| 5   | Cost rollup + cost page + demo-agent tokens correlation                                          | $ per app per day                       |
| 6   | Synthetics job (+ Playwright best-effort) → availability page                                    | journey runs in UI                      |
| 7   | Alert rules + alert center + SQL alerts + Genie-ready views; docs/README final                   | alert fires on induced failure          |

Each iteration ends with: deploy → run → screenshot/verify → `docs/BUILDLOG.md` entry.

## 7. Risks / known limits

- Zerobus ~200 QPS per stream, 1 MB log-line cap → sampling knobs in app.yaml (`OTEL_TRACES_SAMPLER`).
- System tables lag (not real-time) → cost/audit pages are "as of"; live board never depends on them.
- Telemetry export availability is region/preview-gated → verified empirically in iteration 2; if
  unavailable, fall back to OTLP-to-monitor ingestion (kept out of scope until proven needed).
- Playwright on serverless (no root, browser deps) may fail → HTTP journeys are the baseline;
  container pattern documented for DCS-enabled workspaces.
- App SP can only probe apps it can `CAN_USE` — bundle grants it on demo apps; existing apps
  need a one-time grant (documented).
