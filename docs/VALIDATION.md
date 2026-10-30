# Workspace validation plan

How to prove, on a real Databricks workspace, that every part of this repository works and that every
number it shows is **correct**, not merely present. Local tests (`uv run pytest`) cover logic with mocks.
They cannot prove what the platform does with telemetry, grants, jobs, system tables or the Apps proxy.
This plan closes that gap.

The plan is built around two tools in this repository:

- **`example-apps/conformance/`**: a deterministic fixture app that exercises every SDK v2 feature and
  makes **no background traffic**, so every count is known in advance.
- **`scripts/validate_workspace.py`**: drives a seeded 242-request plan against the fixture, then checks
  raw telemetry, gold aggregates, costs, SLIs, policy, alerts and webhook evidence against golden values.
  Full contract: [CONFORMANCE.md](CONFORMANCE.md).

Everything the harness checks, plus everything it cannot check (UI, jobs on the real fleet, federation,
external probes, MCP, drift, cost reconciliation against billing), has a manual procedure below with the
exact expected result.

---

## 0. Ground rules

1. **Use a non-production workspace**, or at least a dedicated catalog and schema. The validation stops
   and starts apps, restarts the monitor, changes budgets and creates SLOs and funnels.
2. **Never run a bare `databricks bundle deploy`.** Always use `scripts/deploy.sh`, which sources `.env`
   and refuses placeholder catalogs. Without `.env` the catalog falls back to `main`, and DABs plans a
   **destructive schema recreate**. If the CLI ever shows a destructive-action prompt for a schema,
   answer **no**.
3. **Never pin `OTEL_EXPORTER_OTLP_ENDPOINT`.** The Apps sidecar listens on `localhost:4314`. Pinning
   4317 silently kills span and metric export while logs keep flowing.
4. **Pick the CLI profile explicitly** (`-p <profile>`) on every command. Don't rely on `DEFAULT`.
5. **Record everything.** Keep the validator JSON reports, job run URLs, screenshots and query results in
   one evidence folder per validation run (`evidence/<date>-<workspace>/`).
6. **Telemetry is batched.** Spans and logs land in UC minutes after the request; metrics are exported
   every 30 s and land later. Wait at least 15 minutes after traffic before judging absence.
7. **Keep the drive away from UTC midnight.** Span and batched-metric timestamps can fall on different
   days at the boundary.

---

## 1. Prerequisites

| Requirement                                                                                                                                                | Why                                                                           | How to check                                               |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Databricks CLI ≥ 0.283, authenticated OAuth profile                                                                                                        | DABs features used by the bundles; app URLs need OAuth                        | `databricks -v`; `databricks current-user me -p <profile>` |
| Unity Catalog + serverless jobs + serverless SQL warehouse                                                                                                 | All jobs are serverless; the monitor queries via a warehouse                  | `databricks warehouses list -p <profile>`                  |
| A catalog you can create schemas in                                                                                                                        | The bundle creates `<catalog>.<schema>`                                       | `databricks schemas list <catalog> -p <profile>`           |
| Read access to `system.billing.usage`, `system.billing.list_prices`, `system.access.audit`, `system.query.history`, `system.ai_gateway.usage`              | Cost, audit, self-metering, gateway reconciliation                            | `SELECT 1 FROM system.billing.usage LIMIT 1` etc.          |
| Foundation Model API endpoints: `review_model` (default `databricks-claude-sonnet-4-5`) and `drift_embedding_endpoint` (default `databricks-gte-large-en`) | LLM code review, quality evals, guardrail classifier, prompt-drift embeddings | `databricks serving-endpoints get <name> -p <profile>`     |
| Apps telemetry export (`telemetry_export_destinations`) enabled in the workspace                                                                           | The whole telemetry pipeline                                                  | Deploy, then check `otel_*` tables appear (§4)             |
| A secret scope holding `MONITOR_HASH_KEY` (random 32+ bytes)                                                                                               | HMAC user pseudonyms (K1)                                                     | `databricks secrets list-secrets <scope> -p <profile>`     |
| A webhook capture receiver you control (any HTTPS endpoint that logs request bodies)                                                                       | Proving webhook delivery and mute suppression                                 | Send a test POST and see it arrive                         |
| Optional: a second workspace on the same metastore and region                                                                                              | Federation (S12)                                                              | —                                                          |
| Optional: a GitHub repo with Actions + a service principal with OAuth M2M secret                                                                           | External-vantage synthetics (S11)                                             | —                                                          |
| Optional: Playwright + Chromium on the validator machine                                                                                                   | Automatic browser-RUM evidence                                                | `uv run --with playwright playwright install chromium`     |
| Optional: a Genie space ID                                                                                                                                 | Ask-Genie tab                                                                 | —                                                          |

Local machine: `uv`, `node` (for prettier/JS syntax checks), `git`.

---

## 2. Pre-deployment checks (local, 10 minutes)

```sh
uv sync --locked
uv run pytest --cov -q          # expect: all passed, 2 MCP tests skipped, coverage ≥ 85% (≈99.6%)
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run --with mcp pytest -q tests/test_reach.py      # MCP tests that the default env skips
SKIP=prettier uv run pre-commit run --all-files      # prettier hook may fail to bootstrap nodeenv;
npx -y prettier@3.8.2 --check "**/*.{yml,yaml,md,json}"   # run the same version via npx instead
```

Then configure the instance:

```sh
cp .env.example .env
# Required: BUNDLE_VAR_catalog, BUNDLE_VAR_monitor_admins (your email, comma-separated list).
# Optional: BUNDLE_VAR_genie_space_id, BUNDLE_VAR_monitor_url (monitor app URL, for demo apps and K7),
#           BUNDLE_VAR_workspaces, BUNDLE_VAR_external_sp, BUNDLE_VAR_deployment_mode/hub_catalog/workspace_name.
# Other overridable vars (--var or BUNDLE_VAR_*): schema (monitor), warehouse_id, review_model, night_tz,
#           monitor_cost_pct (10), drift_embedding_endpoint, drift_threshold (0.25), drift_samples (200).
set -a; source .env; set +a
databricks bundle validate -t dev -p <profile>
(cd example-apps && databricks bundle validate -t dev -p <profile>)
```

**Expected:** both validations succeed with no warnings about unknown variables. Read the plan summary.
It must **not** show a schema being deleted or recreated.

Things to watch for:

- The env prefix is `BUNDLE_VAR_` (singular "VAR"). With the wrong prefix the catalog silently falls back
  to `main`.
- App env in bundle YAML must use snake_case `value_from:`. camelCase is silently ignored and the app
  fails to start with "Must specify environment variable source".
- Bind `MONITOR_HASH_KEY` into the conformance app before deploying (YAML in
  [CONFORMANCE.md §Prepare](CONFORMANCE.md#prepare-an-isolated-validation-deployment)). For fleet apps,
  use the same secret-resource pattern.

---

## 3. Deploy

```sh
scripts/deploy.sh monitor -t dev -p <profile>      # schema, monitor app, jobs, dashboard, alerts; starts the app
databricks bundle run inventory_scan -t dev -p <profile>   # creates tables, grants, gold views (task `gold`)
scripts/deploy.sh demos -t dev -p <profile>        # demo fleet incl. monitor-demo-conformance
cd example-apps && for a in healthy flaky slow vuln agent conformance; do
  databricks bundle run $a -t dev -p <profile>; done; cd ..
databricks bundle run inventory_scan -t dev -p <profile>   # again: discovers demos, grants CAN_USE
```

Bundle jobs and schedules (all serverless):

| Job (bundle key)                                     | Tasks                          | Schedule                     | Notes                                                                  |
| ---------------------------------------------------- | ------------------------------ | ---------------------------- | ---------------------------------------------------------------------- |
| `inventory_scan`                                     | `scan` → `source_scan`, `gold` | hourly :15                   | Creates most tables, grants, gold views, K7 policy, federation publish |
| `cost_rollup`                                        | `rollup` → `self_meter`        | daily 05:30                  | Costs, AI tokens, model pricing, self-metering                         |
| `telemetry_retention`                                | `gold` → `housekeeping`        | daily 05:45                  | Gold runs before raw deletion (F0.4)                                   |
| `app_stopper`                                        | `stopper`                      | hourly :05                   | Idle/night auto-stop, automatic mutes                                  |
| `llm_review`                                         | `review` → `quality_evals`     | daily 05:00                  | LLM review, quality judge, guardrails                                  |
| `slo_eval`                                           | `evaluate`                     | every 15 min                 | SLIs and burn-rate alerts                                              |
| `prompt_drift` (drift.job.yml)                       | —                              | weekly Mon 07:00, **PAUSED** | S14, opt-in                                                            |
| `synthetics`                                         | `browser_smoke`                | daily, **PAUSED**            | Superseded by external synthetics (S11)                                |
| `provision_app`                                      | `provision`                    | on demand                    | One-click provisioning                                                 |
| SQL alerts `telemetry_watchdog`, `critical_findings` | —                              | 30 min / daily               | Dead-man and findings email                                            |

**Expected after deploy:** the monitor URL opens and the fleet board lists the six demo apps plus the
monitor itself. Every bundle job's first manual run succeeds.

---

## 4. V0: Smoke and plumbing (30 minutes)

| #   | Check                            | How                                                            | Expected                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| --- | -------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0.1 | Monitor up                       | Open the app URL; `GET /healthz`                               | Board renders; JSON `{"status":"ok","apps_tracked":N,"last_probe":<recent>}`                                                                                                                                                                                                                                                                                                                                                                                                        |
| 0.2 | Tables exist                     | `SHOW TABLES IN <catalog>.<schema>`                            | `otel_logs`, `otel_spans`, `otel_metrics` (created by the platform on first export), plus `apps_inventory`, `alert_events`, `app_config`, `costs_daily`, `costs_ai_daily`, `agg_app_daily`, `agg_app_hourly`, `agg_genai_daily`, `alert_mutes`, `slo_specs`, `sli_5m`, `model_prices`, `funnel_specs`, `guardrail_findings`, `guardrail_samples`, `monitor_cost_daily`, `monitor_storage_daily`, `synthetic_runs`, `drift_reports` (after the first drift run), and the `v_*` views |
| 0.3 | `workspace_id` everywhere        | `DESCRIBE` each table above                                    | `workspace_id STRING` present; `SELECT count(*) WHERE workspace_id IS NULL` = 0 after one inventory and cost run                                                                                                                                                                                                                                                                                                                                                                    |
| 0.4 | Grants bootstrapped              | `SHOW GRANTS ON SCHEMA …`; `SHOW GRANTS ON TABLE …alert_mutes` | Monitor SP has `USE SCHEMA`, `SELECT`, plus `MODIFY` on `alert_events`, `alert_mutes`, `slo_specs`, `monitor_audit`, `model_prices`, `funnel_specs`, `app_config`                                                                                                                                                                                                                                                                                                                   |
| 0.5 | Probes reach apps                | Fleet board                                                    | Every running demo green within 2 probe rounds (≤ 2 min); `GET /api/apps/<name>` returns `series` with HTTP 200 points                                                                                                                                                                                                                                                                                                                                                              |
| 0.6 | SDK health contract              | `GET /api/apps/monitor-demo-conformance`                       | `health` contains `status`, `version`, `boot_id`, `uptime_s`, `checks` (proves the probe hits `/monitor/health`, not the proxy-intercepted `/healthz`)                                                                                                                                                                                                                                                                                                                              |
| 0.7 | Telemetry lands for every app    | SQL below                                                      | One row per demo app with `last_span` < 10 min ago                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 0.8 | Warehouse stays asleep when idle | Leave the board open 30 min, no clicks; check warehouse state  | Warehouse auto-stops. The live board is in-memory; only page drill-downs and jobs wake it.                                                                                                                                                                                                                                                                                                                                                                                          |

```sql
-- 0.7 telemetry freshness per app and signal
SELECT service_name, max(time) AS last_span, count(*) AS spans_1h
FROM <catalog>.<schema>.otel_spans WHERE time >= now() - INTERVAL 1 HOUR GROUP BY 1 ORDER BY 1;
SELECT service_name, max(time) AS last_log FROM <catalog>.<schema>.otel_logs
WHERE time >= now() - INTERVAL 1 HOUR GROUP BY 1;
SELECT service_name, max(time) AS last_metric FROM <catalog>.<schema>.otel_metrics
WHERE time >= now() - INTERVAL 1 HOUR GROUP BY 1;
```

If spans are missing but logs flow, someone pinned the OTLP endpoint (§0.3).

---

## 5. V1: SDK conformance with exact measurements (the core check)

Run the harness exactly as in [CONFORMANCE.md](CONFORMANCE.md). Summary:

```sh
export MONITOR_HASH_KEY=<same value as the secret>     # for positive HMAC verification
uv run --with 'databricks-sdk>=0.38.0' --with playwright scripts/validate_workspace.py \
  --profile <profile> --catalog <catalog> --schema <schema> \
  --monitor-url https://<monitor-host> --conformance-url https://<conformance-host> \
  --warehouse-id <wh> --run-id acc-001 --phase drive --report evidence/acc-001.json
# wait ≥ 15 min, then materialize:
databricks bundle run inventory_scan -t dev -p <profile>
databricks bundle run cost_rollup    -t dev -p <profile>
databricks bundle run slo_eval       -t dev -p <profile>      # within 2 h of the drive
uv run --with 'databricks-sdk>=0.38.0' scripts/validate_workspace.py … --phase verify --report evidence/acc-001.json
```

Exit codes: **0** = all checks passed, **1** = at least one failed, **2** = incomplete (SKIP or MANUAL
remaining). Only exit 0 with zero MANUAL counts as a certificate.

### 5.1 Golden values to see in the report

| Measurement                                               | Expected                                                                                                                                                       | Proves                                                                            |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Driven requests / real / journey / probe                  | **242 / 233 / 5 / 4**                                                                                                                                          | Request accounting; synthetic tagging (F0.5)                                      |
| SERVER spans per `val-<run>-<n>` request ID               | exactly **1** each                                                                                                                                             | No duplicate ingestion, no loss at sampling 1.0                                   |
| Real errors                                               | **35 / 233 = 15.021459 %** (10 client 4xx + 25 HTTP 5xx)                                                                                                       | Error definition = HTTP ≥ 400 or OTel ERROR; semconv coalescing (F0.6)            |
| `/c/slow` populations                                     | 300 ms and 1500 ms: p50/p95 within −20 % … +20 % + 100 ms; mixed route p50 ≈ 300, p95 ≈ 1500                                                                   | Latency math                                                                      |
| Successful LLM input / output tokens                      | **12 000 / 2 400** (8 non-stream + 4 stream × 1000/200)                                                                                                        | Streaming fix: **not** 48 000 input (the 10-chunk re-report would give 4×10×1000) |
| Billable LLM spans                                        | **18** (12 ok + 5 failed + 1 budget-model)                                                                                                                     | `monitor.llm.billable`; no double counting (F0.3)                                 |
| `error.type` on failed calls                              | one each `rate_limit`, `timeout`, `policy`, `schema`, `server`                                                                                                 | Error taxonomy (K2)                                                               |
| `monitor.llm.ttft_ms`                                     | > 0 on all 4 streaming spans                                                                                                                                   | TTFT                                                                              |
| `gen_ai.client.token.usage` metric                        | rows for input and output, model `conformance-fake-model`                                                                                                      | Unsampled token metric                                                            |
| `exception.fingerprint` on `/c/error`                     | **1** distinct value across 20 requests, present in `v_error_groups`                                                                                           | K3                                                                                |
| Funnel `val-<run>:signup → verify → activate`             | sessions **15 / 10 / 5**; drop-off null / **33.333333 %** / **50 %**                                                                                           | `track()`, `v_events`, `v_funnels`                                                |
| `journey.step` overrides                                  | 5 distinct `conformance-step-N`                                                                                                                                | `set_step()`                                                                      |
| SQL dependency spans                                      | **5** CLIENT spans, `db.response.returned_rows = 42`, **no** `db.statement` / `db.query.text`                                                                  | K8, no SQL text                                                                   |
| Redaction                                                 | **0** occurrences of the leaked token, email and `dapi…` PAT in any `otel_spans.attributes` or `otel_logs.body` for the run; **3** scrubbed warning logs exist | K1 (an empty result can't pass)                                                   |
| User pseudonyms                                           | 5 distinct `user.id_hash`; each equals HMAC(key, email)[:16] and ≠ SHA-256(email)[:16]                                                                         | Keyed hash                                                                        |
| Feedback                                                  | rating 99 stored as **5**; bearer token in comment masked                                                                                                      | Feedback validation                                                               |
| Startup event                                             | `monitor.lifecycle` with matching `boot_id`, non-empty packages, `team=conformance`, `cost_center=cc-test`                                                     | K4 startup inventory; `OTEL_RESOURCE_ATTRIBUTES`                                  |
| Health window                                             | direct `/monitor/health` 503 while toggled down; the monitor's probe series records **503** in that window                                                     | Probe uses the SDK contract (K4 service side)                                     |
| `agg_app_daily` / `agg_app_hourly`                        | equal to raw SERVER counts, errors, distinct sessions and users for touched days/hours, **by traffic kind**                                                    | Durable aggregates (F0.4)                                                         |
| `costs_ai_daily`                                          | fake-model totals equal raw billable spans for touched days                                                                                                    | Cost rollup (F0.3)                                                                |
| `sli_5m` for SLO `val-<run>` (filter `/c/%`, target 0.99) | good/total equal raw 5-minute bucket counts                                                                                                                    | SLO pipeline (S2)                                                                 |
| RUM route `/conformance-route/<run>`                      | ≥ 1 page view and ≥ 1 JS error in `v_rum_daily`                                                                                                                | Browser RUM (K6); MANUAL without Playwright                                       |

### 5.2 Operational checks (`--phase verify --exercise-ops`)

Run once after 5.1 passes, during a quiet window:

| Check                    | Expected                                                                                                                                                                                                                           |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| K7 budget block          | After `token_budget_day=1` and an `inventory_scan` run, `GET /api/policy/monitor-demo-conformance` → `{"throttle":"block"}`; `/c/budget` returns **429** within 75 s and emits **no** provider span. Settings restored afterwards. |
| Alert lifecycle          | Stopping the fixture produces **exactly one** `app_stopped` firing row                                                                                                                                                             |
| Restart rehydrate (F0.1) | Restarting the monitor while the fixture is stopped produces **no second** firing row                                                                                                                                              |
| Resolution               | Starting the fixture produces **exactly one** resolved row                                                                                                                                                                         |
| Mute (S1)                | Repeated with an active mute: both rows have `muted=true`; **zero** webhook deliveries                                                                                                                                             |
| Webhook delivery         | With `--webhook-evidence receiver.json`: exactly one unmuted firing and one resolved delivery, zero muted                                                                                                                          |

If the run is killed mid-way, use the recovery details saved in the report to restart both apps, delete
the temporary mute and restore product settings.

---

## 6. V2: Phase 0 correctness on the real fleet

The harness covers the fixture. These checks use the real demo fleet and jobs.

| #   | Feature                             | Procedure                                                                                                                            | Expected                                                                                                           |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| 2.1 | Job alerts resolve (F0.2)           | Let `flaky` raise `anomaly_*` or `cost_spike`, or force one by lowering a threshold; then fix the condition and rerun the owning job | One `firing` and later one `resolved` row per (rule, app) with `source='job'`; `v_alerts_open` empty for that pair |
| 2.2 | No re-emit spam                     | Run `inventory_scan` 3 times while an anomaly persists                                                                               | Still exactly one firing row                                                                                       |
| 2.3 | Aggregates survive retention (F0.4) | In a **scratch schema**: run gold, note `agg_app_daily` counts, run `housekeeping --days 0` (deletes raw), rerun gold                | `agg_app_daily` counts unchanged; `v_usage_daily` still shows history                                              |
| 2.4 | Gateway privacy (F0.7)              | `SELECT DISTINCT name FROM costs_daily`                                                                                              | No value contains `@`; unknown requesters show as `(untagged)`                                                     |
| 2.5 | Gateway reconciliation              | `SELECT name, ai_input_tokens+ai_output_tokens AS otel, ai_tokens_gateway FROM costs_daily WHERE ai_tokens_gateway IS NOT NULL`      | For gateway-tracked endpoints, difference < 2 %; the gap shows in telemetry health                                 |
| 2.6 | Semconv (F0.6)                      | Routes and Errors tabs for every demo                                                                                                | HTTP status populated whether the app emits `http.status_code` or `http.response.status_code`                      |
| 2.7 | Template defaults                   | Provision an app (§9.6) and read its `app.yaml`                                                                                      | `parentbased_traceidratio`, `OTEL_SEMCONV_STABILITY_OPT_IN=http/dup`                                               |

---

## 7. V3: Operations (S1, S2, S5, S6)

| #    | Feature              | Procedure                                                                                                          | Expected                                                                                                                            |
| ---- | -------------------- | ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| 3.1  | Mute API auth        | `POST /api/actions/mute` as a non-admin                                                                            | **403**; as admin 200 with an `id`; audit row in `monitor_audit`                                                                    |
| 3.2  | Mute globs           | Mute `app=monitor-demo-*`, `rule=*` for 1 h; stop `flaky`                                                          | `alert_events` row `muted=true`; no webhook; mute expiry does **not** create a new firing                                           |
| 3.3  | Night auto-stop mute | Set `flaky` auto-stop `night` and run `app_stopper` in the night window                                            | Mute rows for `app_stopped` / `app_down` until the scheduled start; app restarts on the first hourly run after 06:00 `night_tz`     |
| 3.4  | SLO create           | `POST /api/apps/monitor-demo-flaky/slo` with `{"slo":"avail","sli":"availability","target":0.99,"window_days":28}` | 200; row in `slo_specs` with `revision`                                                                                             |
| 3.5  | SLI correctness      | After `slo_eval`, compare `sli_5m` with the raw query below                                                        | `good` and `total` equal per bucket                                                                                                 |
| 3.6  | Fast burn            | `flaky` has ~8 % 5xx against a 0.99 target: burn ≈ 8. Lower target to 0.999 (burn ≈ 80)                            | `slo_fast_burn` fires (1 h and 5 m windows both ≥ 14.4); budget-remaining tile goes negative                                        |
| 3.7  | Both-windows rule    | Stop `flaky`'s errors (redeploy healthy copy)                                                                      | Fast burn resolves after the 5 m window clears, even though the 1 h window is still high                                            |
| 3.8  | No data              | Stop an app with an SLO for > 30 min                                                                               | `slo_no_data`, never "good"                                                                                                         |
| 3.9  | Revision isolation   | Change an SLO's target                                                                                             | New `revision`; old buckets excluded from `/api/apps/{name}/slo` **and** `/api/reach/slos`, `/status` and the MCP `slo_status` tool |
| 3.10 | Telemetry health     | `GET /api/apps/<name>/telemetry-health` for each demo                                                              | Freshness < 10 min; envelope coverage ≈ 100 % for SDK apps; orphan ratio low; semconv mix shown; sampler ratio when exposed         |
| 3.11 | Orphan alert         | Deploy an app that calls another app **without** trace propagation for > 6 h                                       | `telemetry_orphans` fires only after 25 consecutive 15-min observations > 20 %                                                      |
| 3.12 | Self-metering        | Run `cost_rollup`; `GET /api/monitor/cost`                                                                         | Rows per component (jobs, app, warehouse share, storage, eval tokens); totals reconcile with §11                                    |
| 3.13 | Self-cost alert      | Set `monitor_cost_pct` very low and rerun                                                                          | Monitor-cost alert fires and later resolves                                                                                         |

```sql
-- 3.5 independent SLI recount for one bucket window
SELECT window(time, '5 minutes').start AS bucket,
       count(*) AS total,
       count_if(coalesce(variant_get(attributes,'$["http.response.status_code"]','int'),
                         variant_get(attributes,'$["http.status_code"]','int'), 200) < 400
                AND coalesce(status.code,'') NOT ILIKE '%error%') AS good
FROM <catalog>.<schema>.otel_spans
WHERE service_name = 'monitor-demo-flaky' AND kind ILIKE '%server%'
  AND coalesce(variant_get(attributes,'$["traffic.kind"]','string'),'real') = 'real'
  AND time >= now() - INTERVAL 2 HOURS
GROUP BY 1 ORDER BY 1;
```

---

## 8. V4: Product and GenAI (S4, S7, S8, K7, S14)

| #    | Feature                       | Procedure                                                                                                                                         | Expected                                                                                                                                                                                                                                     |
| ---- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 4.1  | Model prices auth + injection | `PUT /api/model-prices` as non-admin; then as admin with model `x'); DROP TABLE costs_daily; --`                                                  | 403; then 200 with the literal string stored as a model name and `costs_daily` intact                                                                                                                                                        |
| 4.2  | `ai_usd`                      | Add a price for the `agent` demo's model; rerun `cost_rollup`                                                                                     | `ai_usd = in_t/1e6 × input_price + out_t/1e6 × output_price` for each day (recompute by hand from `costs_ai_daily`); UI labels it "list price, estimate"; unpriced models leave `ai_usd` NULL, never 0                                       |
| 4.3  | Effective dating              | Add a second price with a later `effective_from`                                                                                                  | Days before use the old price, days after the new one                                                                                                                                                                                        |
| 4.4  | `idle_usd`                    | Leave `healthy` running with its traffic generator off for 3 h                                                                                    | `idle_usd` ≈ DBU $ for those hours                                                                                                                                                                                                           |
| 4.5  | Unit economics                | `GET /api/apps/<name>/unit-economics`                                                                                                             | `usd_per_1k_requests = total_usd / requests × 1000` (recompute); with `outcome_event` set, `usd_per_outcome` uses `track()` counts                                                                                                           |
| 4.6  | Events / funnels              | Covered exactly by V1; also define a funnel on `agent` in the UI                                                                                  | Steps and drop-off render per `app.version`                                                                                                                                                                                                  |
| 4.7  | Cohorts                       | `GET /api/apps/<name>/cohorts` after ≥ 2 weeks of demo traffic                                                                                    | Week-0 retention 100 %; later weeks ≤ 100 %; synthetic traffic excluded                                                                                                                                                                      |
| 4.8  | Leaderboard                   | `GET /api/leaderboard`                                                                                                                            | Stopped apps excluded; formula string returned; recompute one app's score from its listed components                                                                                                                                         |
| 4.9  | Guardrails                    | Run `llm_review` (→ `quality_evals`) after the `agent` demo serves prompts containing an email and a Luhn-valid test card (`4111 1111 1111 1111`) | `guardrail_findings` rows of kind `email` / `credit_card` with `excerpt_masked` and `excerpt_hash` only (**no raw text**); judge inputs are redacted; daily sample cap respected                                                             |
| 4.10 | Template drift                | Change the agent's system prompt; run `quality_evals` on 2 days                                                                                   | New `template_hash` exceeds the share threshold, and a drift alert fires and later resolves                                                                                                                                                  |
| 4.11 | No-sample safety              | Stop the agent for a day; run `quality_evals`                                                                                                     | Existing guardrail incidents stay **open** (not resolved without evidence)                                                                                                                                                                   |
| 4.12 | K7 on a real agent            | Set `token_budget_day` on `agent`, set `MONITOR_URL` in its env, run `inventory_scan`                                                             | Policy `warn` at 80 %, `block` at 100 %; `llm_call` raises `BudgetExceeded`; with the monitor stopped, the agent keeps working (fail-open) and logs one warning                                                                              |
| 4.13 | Prompt drift (S14)            | Unpause or run `prompt_drift` after ≥ 50 agent prompts in a week; then shift prompt topics and run again the next week                            | `drift_reports` row with k ∈ [2, 8] and a silhouette; second run `novel_share` > 0.25 raises `prompt_drift`, which resolves when topics return; `/api/apps/agent/drift` and the GenAI tab show it; **no raw prompt text** in `drift_reports` |
| 4.14 | GenAI taxonomy                | GenAI tab on `agent`                                                                                                                              | Error classes come from `error.type` (`policy` shows as policy, not other)                                                                                                                                                                   |

```sql
-- 4.2 recompute ai_usd independently
SELECT a.date, a.name, a.model, a.in_t, a.out_t,
       a.in_t/1e6*p.input_usd_per_mtok + a.out_t/1e6*p.output_usd_per_mtok AS expected_usd
FROM <catalog>.<schema>.costs_ai_daily a
JOIN <catalog>.<schema>.model_prices p ON p.model = a.model AND p.effective_from <= a.date
QUALIFY row_number() OVER (PARTITION BY a.date, a.name, a.model ORDER BY p.effective_from DESC) = 1;
```

---

## 9. V5: Reach (S10–S13) and remaining service features

| #    | Feature                      | Procedure                                                                                                                                                                                                                                                                                                                                                                                                                                  | Expected                                                                                                                                                                                                                                                                            |
| ---- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 5.1  | MCP endpoint                 | Point an MCP client (streamable HTTP) at `https://<monitor>/mcp` with workspace OAuth                                                                                                                                                                                                                                                                                                                                                      | Exactly 7 tools: `fleet_summary`, `app_overview`, `error_groups`, `trace`, `cost_summary`, `open_alerts`, `slo_status`; answers match the corresponding `/api/*` responses; no mutating tool exists                                                                                 |
| 5.2  | MCP rate limit               | Call one tool in a tight loop                                                                                                                                                                                                                                                                                                                                                                                                              | Throttled per caller with an explicit error, not a 500                                                                                                                                                                                                                              |
| 5.3  | External synthetics (S11)    | Create SP + OAuth secret; set `BUNDLE_VAR_external_sp`; run `inventory_scan` (grants `CAN_USE`); set repo secrets `SYNTHETICS_HOST`, `SYNTHETICS_CLIENT_ID`, `SYNTHETICS_CLIENT_SECRET`, `MONITOR_URL` and vars `EXTERNAL_SYNTHETICS_ENABLED=true`, `SYNTHETICS_WAREHOUSE_ID`, `SYNTHETICS_WORKSPACE_ID`, `MONITOR_CATALOG`, `MONITOR_SCHEMA` (+ optional `SYNTHETICS_PLAYWRIGHT`, `SYNTHETIC_ARTIFACT_VOLUME`); run the workflow manually | `synthetic_runs` rows with `vantage='external'`, `run_id`, step `-1` completion rows                                                                                                                                                                                                |
| 5.4  | Failure stages               | Break the secret / point at a wrong host / stop an app / break an assertion                                                                                                                                                                                                                                                                                                                                                                | `failure_stage` = `auth` / `dns` / `http` / `assertion` respectively                                                                                                                                                                                                                |
| 5.5  | Two-vantage rule             | Stop `healthy`                                                                                                                                                                                                                                                                                                                                                                                                                             | Alert only after **2 consecutive failures from both** internal and external vantages; one vantage alone does not alert                                                                                                                                                              |
| 5.6  | Status page (S13)            | Open `/status` and `GET /api/status`                                                                                                                                                                                                                                                                                                                                                                                                       | Uptime bars per app match the probe history; open incidents = `v_alerts_open`; active mute windows listed                                                                                                                                                                           |
| 5.7  | Public snapshot              | Run the workflow with `publish_status`, `PUBLIC_STATUS_APPS` set                                                                                                                                                                                                                                                                                                                                                                           | GitHub Pages artifact contains only the listed apps and no user or trace data                                                                                                                                                                                                       |
| 5.8  | Federation (S12)             | Workspace A `deployment_mode=feeder`, `hub_catalog=<shared>`, `workspace_name=a`; workspace B the same with `b`; hub `deployment_mode=hub`. Run inventory + cost in A and B, then gold in the hub                                                                                                                                                                                                                                          | Schemas `af_a__<idA>` and `af_b__<idB>` each with `apps_current`, `apps_history`, `agg_app_daily`, `costs_daily` (DBUs only), `alert_events`; hub `v_fleet_*` views union both; UI workspace filter shows both; deleting an app in A removes it from `apps_current` on the next run |
| 5.9  | Federation idempotence       | Rerun feeder jobs twice                                                                                                                                                                                                                                                                                                                                                                                                                    | No duplicate rows in `*_history` or `agg_app_daily`                                                                                                                                                                                                                                 |
| 5.10 | Billing priced once          | Hub `v_fleet_costs_daily` vs `system.billing.usage` for both workspaces                                                                                                                                                                                                                                                                                                                                                                    | Matches; no double pricing                                                                                                                                                                                                                                                          |
| 5.11 | Standalone untouched         | In a standalone deployment, federation tasks are no-ops                                                                                                                                                                                                                                                                                                                                                                                    | No `af_*` schemas created                                                                                                                                                                                                                                                           |
| 5.12 | Job alerts → webhook         | Configure `ALERT_WEBHOOK_URL`; cause a job alert (SLO burn, 3.6)                                                                                                                                                                                                                                                                                                                                                                           | Receiver gets it within 5 min; restarting the monitor does **not** resend history; muted rows are not sent                                                                                                                                                                          |
| 5.13 | Provisioning                 | Governance → provision app from template                                                                                                                                                                                                                                                                                                                                                                                                   | New tagged app with telemetry pre-wired; appears on the board and in telemetry within 15 min                                                                                                                                                                                        |
| 5.14 | Capacity ramp                | Ops tab → capacity on `healthy`                                                                                                                                                                                                                                                                                                                                                                                                            | Ramp targets `/monitor/health` (or the configured `capacity_path`); requests tagged `capacity` and excluded from real metrics                                                                                                                                                       |
| 5.15 | Genie                        | With `genie_space_id` set, ask "which apps cost the most this week?"                                                                                                                                                                                                                                                                                                                                                                       | Answer consistent with `v_chargeback`                                                                                                                                                                                                                                               |
| 5.16 | AI/BI dashboard and watchdog | Open the bundle dashboard; pause all demo traffic for > 1 h                                                                                                                                                                                                                                                                                                                                                                                | Dashboard tiles match the API numbers; `telemetry_watchdog` SQL alert fires                                                                                                                                                                                                         |

---

## 10. V6: Security and failure modes

| #    | Check                                                                                                                                                              | Expected                                                                                                       |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| 6.1  | Every mutating route as a non-admin (`POST/PUT/DELETE` under `/api/actions/*`, `/api/apps/*/config`, `/slo`, `/product-config`, `/funnels/*`, `/api/model-prices`) | **403** for all; no rows written                                                                               |
| 6.2  | `MONITOR_ADMINS=unset` deploy                                                                                                                                      | Read-only monitor; all mutations 403                                                                           |
| 6.3  | SQL injection strings in every free-text input (app name, SLO name, route filter, funnel steps, mute reason)                                                       | Stored as literals; no errors; tables intact                                                                   |
| 6.4  | RUM ingress abuse: cross-origin POST, > 8 KB body, > 10 batches/min/session                                                                                        | 403 / 413 / 429 respectively; nothing logged                                                                   |
| 6.5  | `/monitor/event` and `/monitor/feedback` with > 4 KB bodies                                                                                                        | Rejected or accepted as empty; no oversized log lines                                                          |
| 6.6  | Request-ID injection: `x-request-id: a\nb` or a 500-character value                                                                                                | Replaced with a generated ID                                                                                   |
| 6.7  | Redaction on a **real** app (`agent`, `vuln`) with all auto-instrumentation on                                                                                     | Grep `otel_spans` and `otel_logs` for `?token=`, `Bearer `, `dapi`, `@`: nothing beyond hashed or masked forms |
| 6.8  | Monitor restart mid-incident                                                                                                                                       | No duplicate firing (V1 §5.2)                                                                                  |
| 6.9  | Warehouse stopped or deleted                                                                                                                                       | Board keeps working (in memory); drill-downs show an error, not a crash                                        |
| 6.10 | A job fails (revoke one grant temporarily)                                                                                                                         | Job run fails loudly; no partial alert resolution                                                              |
| 6.11 | Apps proxy: `GET /healthz`                                                                                                                                         | Proxy answers; the monitor uses `/monitor/health` for SDK v2 apps                                              |

---

## 11. V7: Measurement cross-checks against independent sources

The goal: every number in the UI equals a number computed **independently** from raw data or system tables.

| Number in UI or API                                        | Independent source                                                                          | Tolerance                                                  |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Requests, errors, p50 and p95 per app/route (Requests tab) | Raw `otel_spans` (SERVER, real traffic)                                                     | Exact counts; p95 within `approx_percentile` error (≤ 1 %) |
| DAU and sessions (`v_usage_daily`)                         | `count(DISTINCT user.id_hash)` and sessions on raw spans per day                            | Exact within retention; HLL ≈ 2 % beyond                   |
| Compute $ per app (`costs_daily.dbu_usd`)                  | `system.billing.usage` × `system.billing.list_prices` filtered by `usage_metadata.app_name` | ≤ 0.5 % (list price; invoices differ by discounts)         |
| AI tokens per app/day                                      | Raw billable spans; `system.ai_gateway.usage` where enabled                                 | Exact vs spans; < 2 % vs gateway                           |
| Chargeback per team                                        | Sum of `costs_daily` by `app_config.tags_json.team`                                         | Exact                                                      |
| Monitor self-cost                                          | Billing for monitor jobs + app; `system.query.history` share for the monitor SP             | Warehouse share is an estimate; label must say so          |
| Probe uptime % (board and status page)                     | `/api/apps/{name}` `series`                                                                 | Exact                                                      |
| Alert counts (alert center)                                | `v_alerts_open` and `alert_events`                                                          | Exact                                                      |
| Leaderboard score                                          | Formula over the listed components                                                          | Exact                                                      |

```sql
-- compute $ per app per day, independently
SELECT u.usage_date, u.usage_metadata.app_name AS name,
       sum(u.usage_quantity) AS dbus, sum(u.usage_quantity * p.pricing.default) AS usd
FROM system.billing.usage u
JOIN system.billing.list_prices p
  ON u.sku_name = p.sku_name AND u.usage_start_time >= p.price_start_time
 AND (p.price_end_time IS NULL OR u.usage_start_time < p.price_end_time)
WHERE u.usage_metadata.app_name IS NOT NULL AND u.workspace_id = '<workspace_id>'
  AND u.usage_date >= current_date() - 7
GROUP BY 1, 2 ORDER BY 1, 2;
```

---

## 12. V8: Overhead and cost of monitoring

| Measurement           | Procedure                                                                                                                      | Pass criterion                                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SDK request overhead  | Deploy two copies of `healthy` (SDK v2 with `redact=True` vs SDK disabled); drive 2 000 requests each with a fixed concurrency | p95 delta < 10 ms; CPU delta reported (Python OTel is the costly part; compare at sampling 1.0 and 0.2)                                                 |
| Telemetry volume      | Ops tab 24 h telemetry volume per app                                                                                          | No app near ~200 QPS per stream; no log lines > 60 000 characters                                                                                       |
| Warehouse wake-ups    | `system.query.history` for the monitor SP over 24 h idle                                                                       | Only scheduled jobs and user drill-downs; no per-minute queries (policy endpoint and job-alert forwarder every 5 min only when a webhook is configured) |
| Monitoring cost ratio | `GET /api/monitor/cost` vs fleet cost                                                                                          | Below `monitor_cost_pct`                                                                                                                                |

---

## 13. Updating and redeploying

| Change                    | Procedure                                                                                                                                                                                                                                                                                                                 |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Monitor code or jobs      | Edit, run local gates, `scripts/deploy.sh monitor -t dev -p <profile>`; jobs pick up new code on the next run; run `inventory_scan` once for schema migrations                                                                                                                                                            |
| Schema change             | Add columns with the `ensure_columns` / `workspace_column` helpers (idempotent `ALTER … ADD COLUMNS`); never `CREATE OR REPLACE TABLE` on a data table                                                                                                                                                                    |
| SDK change                | Edit `src/monitor_middleware/__init__.py` only; copy it to `sdk/monitor_middleware.py` and `templates/basic-app/monitor_middleware.py`, then run `example-apps/sync-demos.sh` (copies `sdk/` into every demo); `tests/test_copies_in_sync.py` must pass; bump `pyproject.toml` version and `CHANGELOG.md`; redeploy demos |
| New fleet app             | Follow [INSTRUMENTATION.md](INSTRUMENTATION.md): telemetry destinations, `opentelemetry-instrument`, `install(app)`, `MONITOR_HASH_KEY` secret, `OTEL_RESOURCE_ATTRIBUTES=team=…,cost_center=…`, optional `MONITOR_URL` for budgets                                                                                       |
| Bundle variable           | `.env` (`BUNDLE_VAR_*`) or `--var`; redeploy; dashboard dataset queries are the one place DABs variables cannot reach (edit `dashboards/fleet.lvdash.json`)                                                                                                                                                               |
| Enable prompt drift       | Unpause the `prompt_drift` job in `resources/drift.job.yml` (`pause_status: UNPAUSED`) and redeploy                                                                                                                                                                                                                       |
| Switch to federation      | See [FEDERATION.md](FEDERATION.md); feeders first, hub last; verify §9 5.8–5.11                                                                                                                                                                                                                                           |
| Rollback                  | Redeploy the previous git tag with `scripts/deploy.sh`; new tables and columns are additive and can stay                                                                                                                                                                                                                  |
| Clean up a validation run | Delete the run's SLO and funnel (`DELETE /api/apps/monitor-demo-conformance/slo/val-<run>`), keep the reports, stop the fixture app                                                                                                                                                                                       |

---

## 14. Sign-off checklist

- [ ] §2 local gates green; bundle validate shows no destructive actions
- [ ] §4 V0 all rows pass
- [ ] §5 validator `--phase verify` exit **0** with zero MANUAL, and `--exercise-ops` plus webhook evidence pass
- [ ] §6–§9 every row executed, with result and evidence link recorded
- [ ] §10 security rows all pass
- [ ] §11 every UI number matches its independent source within tolerance
- [ ] §12 overhead and cost within criteria
- [ ] Evidence folder archived; open defects filed with the failing check name
