# Full capability reference

Every feature of Apps Monitor mapped to the mechanism that powers it and the
table/view it reads or writes. The selling summary lives in the [README](../README.md);
this is the exhaustive list.

| Capability | How | Where |
| --- | --- | --- |
| Live fleet board | 60 s HTTP probes with the monitor's SP OAuth; KPI tiles, needs-attention list, sparklines | monitor app, in-memory |
| Requests / latency / errors | platform OTel export into shared UC tables; per-app charts + route tables | `otel_spans` |
| Log explorer | stdout/stderr + app logs, severity-filtered, trace-correlated | `otel_logs` |
| Distributed traces | request list → waterfall with correlated logs | `otel_spans` + `otel_logs` |
| Unified agent traces | MLflow AGENT/TOOL/LLM spans merged with app spans; one `client_request_id` from browser to token | `otel_spans` + MLflow REST |
| Fleet inventory | hourly snapshot + automated access grants | `apps_inventory` |
| Source & dependency scans | CVEs (OSV.dev), secrets, smells, quality score per deployment | `code_scans`, `scan_findings` |
| Package analysis (py + npm) | installed vs latest (PyPI/npm registry), staleness class, per-package CVE ids | `deps_json` in `code_scans` |
| Agentic code review | Databricks-hosted Claude reviews each app's source: verdict + scores | `llm_reviews` |
| Cost tracking | daily rollup: billing $ × list prices + AI tokens/calls from telemetry | `costs_daily` |
| Synthetic monitoring | in-app journey runner (multi-step, assertions, budgets) every 30 min | `app/journeys.json`, OTel spans |
| Alerting | in-app rules + job-emitted alerts + SQL alerts; alert center UI | `alert_events` |
| Adoption analytics | DAU/sessions/requests, per-(hashed)-user history + cost share | `v_usage_daily`, `v_users` |
| GenAI monitoring | token/model/latency trends, top consumers | `v_genai_daily`, `v_genai_sessions` |
| Error groups & dependencies | fingerprinted clusters; outbound peer latency | `v_error_groups`, `v_dependencies` |
| Timeline & releases | alerts+deploys+anomalies chronology; regression-by-version | `v_release_perf` |
| Smart detection | hourly traffic/latency z-scores vs 7-day baselines | gold job → alerts |
| FinOps governance | budgets, burn alerts, hard budget stop, forecast, chargeback, idle/night auto-stop | `app_config`, `v_chargeback`, `v_cost_forecast` |
| Security & compliance | deny-list policy, freshness, permission drift, audit, compliance export | `policy.json`, `app_permissions`, `monitor_audit` |
| Provisioning | one-click tagged app from template, telemetry pre-wired | `monitor-provision-app` |
| Runtime quality evals | daily LLM judge on sampled production traces + regression alerts | `monitor_quality` |
| User feedback | `POST /monitor/feedback` ★ ratings through the native pipeline | `v_feedback` |
| LLM error taxonomy & agent watch | rate-limit/policy/timeout/schema classes; spans-per-trace trend | GenAI tab |
| Capacity probing | on-demand step ramp → max qps, knee, recommended ceiling | Ops tab |
| Ask Genie | curated Genie space (18 gold objects) embedded in the app | `#/ask` |
| AI/BI dashboard + watchdog | versioned Lakeview dashboard; dead-man SQL alert | `dashboards/fleet.lvdash.json` |

## Permissions model

| Principal | Needs | Granted by |
| --- | --- | --- |
| deploying user | workspace admin-ish: create schema/apps/jobs, read system tables | — |
| monitor app SP | `CAN_USE` warehouse, `CAN_MANAGE_RUN` on jobs | bundle resource bindings (automatic) |
| monitor app SP | `CAN_USE` on every fleet app (probing), `USE/SELECT` on the schema | **inventory job** (self-bootstrapping, hourly) |
| demo app SPs | `CAN_QUERY` serving endpoint (agent only) | bundle resource binding |
