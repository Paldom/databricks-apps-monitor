# Build log

Running record of what was built, deployed, and learned — one entry per iteration.
(Plan: [PLAN.md](PLAN.md).)

## Iteration 26 — instance config → .env (deployed 2026-07-11)

Nothing identifying remains in tracked files: admin emails, Genie space id, UC catalog and
the demo `monitor_url` moved to bundle variables fed from an **uncommitted `.env`**
(`BUNDLE_VAR_*` — the DABs env-variable convention; template committed as `.env.example`).
`app/app.yaml` is gone — the monitor's command + env live in `resources/monitor.app.yml`
`config:`, interpolated from `${var.*}`. `scripts/deploy.sh [monitor|demos|all]` sources
`.env`, guards against placeholder catalogs, and is the only supported deploy path (README
quickstart + AGENTS.md updated).

Fail-safe defaults for a bare deploy: `monitor_admins=unset` → deny-all (read-only),
`genie_space_id=unset` → feature hidden ("unset" sentinels because the Apps API rejects
empty env values). Two platform lessons captured: (1) the env prefix is `BUNDLE_VAR_`
(singular — with the wrong prefix catalog fell back to `main` and DABs planned a schema
**recreate**; the CLI's destructive-action prompt caught it); (2) bundle YAML env sources
must be snake_case `value_from:` — camelCase is ignored, which is what had been stripping
the demo agent's env all along; both bundles fixed and the agent now restarts cleanly.

## Iteration 25 — UX structure pass + workspace selector + fleet auto-stop rules (deployed 2026-07-11)

Six-item review round (plus Topology/Governance restores from the prior mini-round):

- **Structured fleet cards**: replaced the free-flowing meta/chips rows with a fixed
  4-column stat grid (reachable · p95 real/probe · users 7d · cost MTD) and a single
  footer line — tech stack as plain text ("Python · SQL · Jobs — moderate, 1.6k loc") with
  scan/review/alert signals right-aligned. Every card now has identical row structure.
- **Actions separated from data**: Governance gained a distinct top **Admin actions** bar
  (＋ Create app, ⏻ Auto-stop rules) with collapsible panels — the provision form no longer
  sits between data tables. Inspect's app header gained an **Actions** strip (Stop/Start
  app with confirm, Request review, Run journeys) — lifecycle controls live at the top,
  not inside content tabs. All admin-gated server-side (403 for non-admins).
- **No colored left borders** (called out as AI slop): takeaway rows (production Overview
  - Board concept) now use a small severity dot; the review quote block uses a muted
    background instead of a border-left.
- **Workspace selector** (header): `/api/fleet` now returns the current workspace name +
  a `MONITOR_WORKSPACES` env-configured list of federated monitors ([{name,url}]);
  selecting another workspace navigates to its monitor. Single-workspace default.
- **Fleet auto-stop rules** (Governance → Auto-stop rules): `POST
/api/actions/autostop-policy` (admin) applies idle/night/none + idle-hours to every app
  except the monitor and `env=prod`-tagged apps, with a **dry-run preview** ("Would apply
  idle (24 h) to 8 apps: …") before Apply; per-app rows written to `app_config` with the
  real actor; the hourly lifecycle job enforces (idle mode keeps the fail-safe: no request
  evidence → never stopped).
- **Genie: iframe only** — the Conversation-API fast path (endpoint + native ask box +
  per-app prefill button) removed per review of usage; the Ask header button opens the
  embedded Genie space.

## Iteration 24 — external review response (GPT + Grok), deployed 2026-07-10

Implemented the actionable core of `observ/REVIEW-GPT.md` + `observ/REVIEW-GROK.md`
(trust & authorization first, then truth, then IA/copy). Retested live.

**P0 safety**

- **Server-side authorization**: every mutating endpoint (config save, appctl, provision,
  run-journeys, review, refresh-inventory, capacity) now requires the caller to be in
  `MONITOR_ADMINS` (app env), resolved from proxy-injected `X-Forwarded-Email`; denials
  and actions are logged with the real actor; config writes record the actor (was
  "monitor-ui"). **Spoof-tested**: a forged `X-Forwarded-Email: attacker@…` header is
  overridden by the Apps proxy (request still executed as the token's real principal) —
  the header is trustworthy, viewers are read-only.
- `/api/debug/otelenv` removed (leaked telemetry env).
- **Secret redaction**: the scanner now stores `match redacted · sha256:<fp>` instead of
  the matched value; all 10 historical stored secret values purged from `scan_findings`
  (verified 0 remaining); fresh scan ran.
- **Auto-stop fails safe**: idle mode with no request evidence skips (was: treated as
  999 h idle); manual stop now honors `PROTECTED` too.
- Provisioning **fails closed** on existing app names (was: redeployed over them), tag SQL
  escaped, names capped at 26 chars.

**Truth (P0.2/P0.5)**

- Probe-derived KPIs relabeled: Availability→**Reachability**, Error rate→**Probe errors**,
  per-app "uptime"→"reachable"; statuses sentence-cased (Healthy/Degraded/Unreachable/
  Stopped/Starting) — "OK" was overclaiming ingress reachability.
- No auto-PASS: the automatic `/healthz` journey removed; unconfigured apps show
  "not configured".
- Overview takeaways can no longer say all-clear on missing evidence — "Not fully
  evaluated" when scan/review are absent.
- **Cost reconciliation panel removed** (`ai_usd` is NULL by design — it compared
  different services); capacity probe removed from the UI (endpoint admin-gated).
- "Agentic code review"→"Automated review (advisory)"; "Compliance report"→"Readiness
  checklist"; "No PII stored"→pseudonymous phrasing; README CTO/product claims corrected.

**Correctness defects fixed** (review list): llm_review `monitoring` score key (was
dropped from overall), verdict whitelist + escaped at the HTML sink, housekeeping
`synthetic_runs.run_ts` retention, `JOB_HEALTH` counts DISTINCT run_id, cost job passes
`--jobs-dir` (spike-alert import), synthetics `within_budget` mirrors ok, webhook
`raise_for_status`, NBA `app_down` mapping, Board latency sparkline plotted status code
(tuple[2]→[3]), app.yaml 4317→4314 comment, tags JSON 400 on oversize (was silent
truncation).

**IA & copy** (both reviews): segments → **Overview · Apps · Alerts · Cost & policy**;
Ask moved to a header affordance; Topology folded under Apps as "Configured dependencies";
Alerts is first-class (Active alerts / Alert history); per-app tabs renamed (Traffic,
Changes, Code & security, AI usage, Usage, Browser checks); tab intros cut to one
sentence; card badges capped (tag/budget chips dropped); header subtitle "Fleet health,
cost, usage & code risk for Databricks Apps"; "Sync fleet"→"Refresh inventory"; slop
phrases removed ("fast path — no iframe roundtrip", "storyline check", "Nothing needs
you", "born observable", "observability-creep watch").

**Deferred** (documented, per review sequencing): frontend componentization/split of
index.html, side-nav restructure, journeys-as-job with durable per-step results, durable
alert state machine, middleware HMAC + validation hardening, app/jobs test suites,
portable per-target config. These are the review's phases 3–5.

## Iteration 23 — storyline "Now" items from observ/rebuild.md (deployed 2026-07-10)

Implemented the six §3-Now items; §4 UX principles applied; §5 removals done. The Next/Later
tiers (cost-policy panel, Playwright recordings infra, SDK wheel, cross-workspace P0–P2,
Node SDK) are parked pending the §6 decisions — deliberately not faked on serverless.

1. **Real-traffic p95 as the headline** (the storyline's "nem tudom mennyire valid!!" — it
   wasn't valid): fleet KPI, cards, catalog and Inspect header now show p95 from real
   server spans (probes excluded, source-labeled `real`), probe RTT relabeled
   **reachability**. The gap is dramatic and honest: fleet real p95 ≈ 1.9 s vs ~99 ms probe
   RTT; monitor-demo-slow 2 449 ms real vs 97 ms reach. `REAL_PERF_FLEET` + fleet-wide
   scalar ride `/api/fleet/enrich` (`perf`, `real_fleet`; `usage` too — user count on cards).
2. **Cost reconciliation** (Cost tab): bottom-up (app-reported gen_ai tokens × list price)
   vs top-down (billed system.billing.usage) per day with divergence flags (consistent /
   unbilled yet / bottom-up > billed) — proves attribution can be trusted for chargeback.
3. **App Review report** (Quality tab, printable): new LLM **app overview** (purpose ·
   tech-stack chips · endpoints) — two extra fields in the existing review prompt
   (`overview_json` column via ALTER, view passes through), composed above scan + package
   table + verdict. Verified live on monitor-demo-vuln.
4. **Alert next-best-action**: rule→action map rendered as a button per firing alert (run
   journeys / re-scan / re-review / start app / budget form / open traces…), wired to the
   existing action endpoints.
5. **Genie fast path** (kills the slow iframe): `POST /api/genie/ask` → Conversation API,
   answer + generated SQL + result rows rendered natively (~13 s); "Ask Genie about this
   app" entry point on Inspect; iframe demoted to a `<details>` fallback. Fix en route: the
   app SP needed CAN_RUN on the Genie space.
6. **UI consolidation** (§2.4/§5): the 13 non-chosen concept UIs deleted from the deployed
   app (git history keeps them; walkthrough recordings stay); `/ui/` offers only production
   - the chosen tiered Board; board-style **ranked takeaways** now open the production
     Overview tab.

## Iteration 22 — landing aspects, IA fixes, audit validity, UI-test volume (deployed 2026-07-10)

Six review items in one pass:

- **Fleet cards show more aspects**: the app's description (2-line clamp), **technology
  chips** (Python always; Node from the scan's npm ecosystem; LLM/SQL/Jobs/MLflow/
  Lakebase/Genie/UC data/App-to-app from declared resource bindings) and a **complexity**
  line (simple/moderate/complex · LOC · deps, tooltip with files) from the latest scan —
  `SEC_BY_APP` now returns `py_loc, files, has_npm`.
- **Fleet audit trail validity**: it IS real data — `system.access.audit` (platform audit
  log) filtered to `service_name='apps'`, snapshotted hourly into `monitor_audit`. BUT the
  system table is **account-wide** and the query lacked a workspace filter, so foreign
  workspaces' apps events leaked in (user caught `ai-sales-assistant`). Fixed: `AND
workspace_id = <this workspace>`; verified post-run only our apps appear; source caption
  added under the Governance table.
- **Overview scorecard grid**: explicit responsive columns (4 ≥1500px / 2×2 default /
  1 ≤760px — never 3+1) and the Inspect container widened 1120→1440px.
- **Adoption promoted** to a top-level menu item (out of Assess).
- **Operate merged**: Uptime + Ops are one tab (availability section, then operations &
  governance); old `uptime`/`ops`/`probes`/`synthetics` hashes alias to it.
- **UI tests as a separate top-level item + UC volume**: the Playwright job now creates
  volume `monitor.ui_tests`, uploads per-run **result JSON + screenshot** per app
  (`/Volumes/…/ui_tests/<app>/<ts>/`), adds an `artifact` column to `synthetic_runs`, and
  the new **UI tests** tab lists runs (PASS/FAIL, latency, detail, artifact path). Ran the
  job: volume + artifacts + rows verified (browser launch itself stays best-effort on
  serverless — recorded as such; screenshots appear where a browser can run, e.g. DCS).
  Also fixed: warehouse booleans arrive as strings ('false') — PASS/FAIL pill compares
  properly now.

## Iteration 21 — Board chosen: tiered detail view (deployed 2026-07-10)

The Board (D4) won the detail-view round; rebuilt `/ui/inspect-board` as a **tiered board**
— one screen, three altitudes:

1. **At a glance** (hero, no interaction needed): stat strip (status/uptime/p95/code
   score/review/spend/DAU) + **max-3 ranked takeaways**, worst first, composed live
   (down > failed review > critical findings > firing alerts > budget overrun > slow >
   all-clear). Each takeaway is a door: click scrolls to and expands its panel (with a
   focus flash).
2. **Manage** band — for the app owner: Code & security sign-off, Money, People & AI,
   Uptime & tests, History & settings. Governance altitude, no telemetry digging.
3. **Deep dive** band — for engineers: What broke, Speed & traffic, Recent requests, Logs,
   Outside calls, with deep links to raw trace waterfalls in the workbench.
   UX contract: same expand-in-place gesture everywhere; Esc collapses; app switcher in the
   header; band captions state the audience. Walkthrough re-recorded:
   `walkthrough/ui/uiv3-4-board.mp4` (70 s). Production Inspect unchanged pending the word to
   swap it in.

## Iteration 20 — round-3 UX: detail-view alternatives (deployed 2026-07-10)

Landing page untouched; the target was the single-app detail experience (hard to follow,
unclear navigation path, jargon menu names). Four alternative inspect models at `/ui/`
(launcher top section), all over the existing per-app APIs via a shared plain-language
section library `app/static/ui/_app.js` (11 sections: Summary / What broke / Speed & traffic
/ Recent requests / Logs / Outside calls / Code & security / Money / People & AI / Uptime &
tests / History & settings):

- **D1 Plain** (`/ui/inspect-plain`) — flat nav, plain words, breadcrumb + "Continue →" pager.
- **D2 Report** (`/ui/inspect-scroll`) — no tabs; one lazy-loading scroll report with scrollspy.
- **D3 Guide** (`/ui/inspect-guide`) — job-first stepper paths (debug / sign-off / operate)
  with per-step guidance text.
- **D4 Board** (`/ui/inspect-board`) — all sections as live panels on one screen, expand-in-place.

Fixed along the way: `/api/apps/{name}` requests with a trailing slash 404 (Starlette
doesn't redirect that direction), and that payload lacks the computed `status` field —
concepts fall back to the fleet list's record. Walkthroughs:
`walkthrough/ui/uiv3-{1-plain,2-report,3-guide,4-board}.mp4` (52–69 s). Selection pending.

## Iteration 19 — Genie space + in-app embedding (deployed 2026-07-10)

Natural-language Q&A over the fleet, per the article's companion-Genie design
(`observ/MONITORING-ARTICLE.md` §"From data model to UI"), created programmatically
(space id `01f17c54ead41aa8945603d2bd405c63`, "Apps Monitor — Fleet Q&A"):

- **Curation = security boundary** (article rule): 18 objects — 14 gold `v_*` views +
  `costs_daily`/`alert_events`/`app_config`/`monitor_quality`; **no** raw `otel_*`.
  Semantic layer: every object already carries COMMENTs (iteration 18) + space
  text instructions (glossary: app/name key, MTD, scan vs review, alert states,
  hashed users; rules: prefer views, money formatting, "raw telemetry lives in the UI").
- **5 example SQLs** (chargeback, WoW AI growth >50%, over-budget, alerts-firing-now,
  riskiest apps) + **10 sample questions** distilled from the research's tier-1 triage
  list ("is my app OK?", "what did we spend?", CTO sign-off, heaviest AI consumers…).
- **API gotchas**: `serialized_space` v2 requires every id-list sorted by id;
  benchmark questions require answers (user-visible suggestions belong in
  `config.sample_questions`, one create-payload per the genie-rooms skill builder).
- **Validated via Conversation API** (3/3): alerts-firing (reused the curated SQL
  verbatim, correct fleet answer), chargeback (correct aggregate), CVE question
  (correct join over v_findings_latest, surfaced the npm bait axios/urllib3 rows).
- **Embedded in the app** (docs.databricks.com/aws/en/genie/embed): app domain added to
  workspace `aibi-dashboard-embedding-approved-domains`; new **Ask Genie** dashboard
  segment (`#/ask`) renders the `/embed/genie/rooms/<id>` iframe (`allow="clipboard-write"`);
  `MONITOR_GENIE_SPACE_ID` env → `genie_url` in `/api/fleet`. Users auth with their own
  workspace session inside the frame — UC ACLs stay the access boundary.

## Iteration 18 — article-derived features (deployed 2026-07-10)

Implemented the feature list distilled from the blog-article review
(`observ/article-review.md` list 2) — the behavioral/FinOps loops the article has and the
toolkit lacked:

- **Runtime quality evals** — new `quality_evals` task on the review job: LLM judge scores
  each experiment-bound app's sampled production traces (MLflow REST previews) on
  relevance/faithfulness/toxicity → `monitor_quality`; regression/floor breaches →
  `quality_regression` alerts. Verified live: agent scored 9.0/8.0/0.0 over 10 traces.
  Gotcha refound: typed SDK models drop app-resource fields — experiment ids must come
  from raw REST.
- **User feedback loop** — middleware now serves `POST /monitor/feedback` (rating 1–5 +
  comment), logged through the native pipeline into `otel_logs` → `v_feedback` view →
  GenAI tab (avg ★, negative count). Gotcha: with `from __future__ import annotations`,
  FastAPI can't resolve a function-local `Request` import — annotation types must be
  module-global. The agent demo posts occasional synthetic feedback.
- **Dead-man watchdog** — bundle-managed SQL alert `telemetry_watchdog` (every 30 min):
  monitor telemetry silent > 30 min ⇒ notify. The monitor watches the fleet; this watches
  the monitor, independent of the in-app rule engine.
- **Lakeview dashboard in the bundle** — `dashboards/fleet.lvdash.json` (KPI counters,
  requests/day line, MTD cost bar, scans table over the gold views) deployed via the DABs
  `dashboards` resource (note: DABs doesn't interpolate vars inside `.lvdash.json`).
- **Hard budget enforcement** — `auto_stop: budget` mode in the stopper job: MTD compute $
  ≥ budget ⇒ stop the app (`budget_stopped` critical alert); selectable on the Ops tab.
- **In-app capacity probe** — `POST /api/actions/capacity/{app}`: bounded step ramp
  (1→2→4→8 concurrent × 8 s, SP OAuth — job tokens are rejected by app URLs, so it runs
  in the monitor) → per-level qps/p95, saturation knee, and a recommended ceiling at 65%
  of peak. Verified: healthy demo = 506 qps max at concurrency 4, knee visible (p95
  11.6→41.5 ms at 8). Ops tab button + result table.
- **LLM error taxonomy + agent complexity** — GenAI tab now classifies gen_ai span errors
  (rate-limit / content-policy / timeout / schema / other) and trends spans-per-agent-trace
  (runaway-agent watch).
- **TTFB** — probes stream responses and record time-to-first-byte separately from total
  latency (Uptime tab stat) — the streaming SLO a total p95 hides.
- **Observability-cost guardrails** — middleware truncates log lines at 60 KB (Zerobus
  silently drops >1 MB); Ops tab shows per-app 24 h telemetry volume; sampler + propagator
  knobs documented in the template `app.yaml`.
- **Retention** — `housekeeping` task on the cost job: raw otel\_\*/event rows > 90 d
  deleted + VACUUM; gold aggregates kept indefinitely.
- **Bound-job health** — Ops tab rolls `system.lakeflow.job_run_timeline` (workspace-
  filtered) for the job ids each app declares; real signal on first render (one bound job
  0/1 succeeded).
- **Semantic metadata** — COMMENT ON the platform otel tables + cost/alert tables
  (apostrophes need SQL-escaping); all gold views already carried comments — the Genie
  prerequisite.
- **Documented, deliberately not defaulted** (INSTRUMENTATION.md "further options"): OBO
  per-user cost attribution (org auth-model decision), UC trace storage binding (public
  preview), vendor OTLP dual-export, Genie Space curation rules.

## Iteration 17 — Dependabot-style package analysis, Python + npm (deployed 2026-07-10)

Question audited: are installed packages analyzed for risk/staleness? Python partially was
(OSV CVEs + aggregate freshness); **Node.js wasn't at all**, and there was no per-package
report anywhere. Now `source_scan.py`:

- parses `package.json` (dependencies + devDependencies, `^~>=` specs normalized) alongside
  `requirements.txt`; OSV querybatch covers both ecosystems (npm + PyPI) in one call
- per-package report in `code_scans.deps_json` (same column, richer rows): installed vs
  **latest** (PyPI JSON API / npm registry), behind-class (current/patch/minor/major/
  unpinned/unknown), and the package's OSV vulnerability ids
- findings unchanged in shape: npm CVEs/policy rows cite `package.json`; majors-behind get
  freshness findings in both ecosystems
- Quality tab renders the report as a sortable-by-risk package table (eco chip, installed →
  latest, freshness badge, GHSA/CVE ids); fixed `SCAN_LATEST` never selecting
  `freshness_score`/`policy_violations` (Overview always showed "–")
- demo: `monitor-demo-vuln` gains an inert `package.json` bait (lodash 4.17.15, axios 0.21.0,
  minimist 1.2.0, node-fetch 2.6.0, webpack ^4) — scan now shows 18 deps (5 npm),
  freshness 22/100, 121 high findings, npm CVEs verified end-to-end (registry + OSV reachable
  from serverless). Old-format scan rows render without the table (graceful).
- also fixed: unescaped `'` in the `costs_daily` COMMENT (gold job noise every run)

## Iteration 16 — round-2 UX concepts: understandability & journeys (deployed 2026-07-10)

Second alternative-UI round against the shipped Dashboard+Inspect UI. Brief: minimal,
**zero new features** — only better presentation for understandability and per-journey use;
walkthroughs that explain each ENTIRE UI. Grounded in a second research pass over **40 more
monitoring/APM/status products** (see `docs/UX-ALTERNATIVES.md` round-2 section for the
pattern ranking and per-concept verdicts).

Five new concepts live at `/ui/` (production untouched; round-1 concepts archived on the
launcher): **A·Lens** (`/ui/lens` — Tech-lead/Operator/Developer switch that reorders,
never hides), **B·Story** (`/ui/story` — no tabs, one narrative page, scrollspy chips carry
verdict dots so the sticky bar is the 5-second sweep), **C·Zoom** (`/ui/zoom` — breadcrumb
drill contract Fleet→App→Domain→Evidence), **D·Ask** (`/ui/ask` — question-driven home,
every card pre-answered with a live verdict), **E·Flow** (`/ui/flow` — day-grouped fleet
event stream from alerts+audit+scans+reviews with a pinned "right now" strip).

Six explainer walkthroughs (gitignored): `walkthrough/ui/uiv2-{0-current,1-lens,2-story,
3-zoom,4-ask,5-flow}.mp4` (56–100 s) — the current video tours all four dashboard segments
plus every Inspect tab group; each concept video covers its complete navigation model.
Selection pending: switch, keep current, or mix.

## Iteration 15 — terminology refactor: "observ/obs" → "monitor" (deployed 2026-07-10)

The project is _monitor_; the leftover "observ"/"obs" term was refactored out **everywhere,
including the data layer**, then retested against the live workspace.

- **Data namespace**: UC schema `observability` → **`monitor`**; table `obs_audit` → `monitor_audit`.
  Migrated by emptying the old schema, letting DABs swap it (schema resource key `monitor_schema`,
  name `monitor`), and re-running jobs to repopulate — old `observability` schema dropped, verified gone.
- **Telemetry**: OTel scope `observ.*`/`"observ"` → `monitor.*`; env `OBS_CATALOG`/`OBS_SCHEMA` →
  `MONITOR_CATALOG`/`MONITOR_SCHEMA`.
- **Jobs**: `observ-*` → `monitor-inventory-scan`/`-llm-review`/`-cost-rollup`/`-synthetics-browser`/
  `-app-stopper`/`-provision-app` (renamed in place).
- **Demo apps**: `obs-demo-*` → `monitor-demo-{healthy,flaky,slow,vuln,agent}` (DABs recreated them;
  old apps + orphaned `obs-demo-provisioned` deleted).
- **UI**: "Apps Observability" → **"Apps Monitor"** (+ all concept UIs); `/Shared/observ-apps` →
  `/Shared/monitor-apps`; all comments + docs.
- **Kept**: the two internal bundle deploy-identifiers (`apps-observability`, `obs-demo-fleet`) —
  invisible workspace-path/state keys; renaming forces a full teardown for zero product/data benefit.
  The `observ/` concept-material folder keeps its name.

**Retest (green)**: old schema absent, `monitor` schema holds every table/view; telemetry from
`apps-monitor` + `monitor-demo-*` landing in `monitor.otel_spans`; `costs_daily` (34),
`monitor_audit` (3097), `alert_events` populated; all monitor + `/ui/*` endpoints 200; agent
envelope (`request.state.monitor`) works; dashboard renders "Apps Monitor" with the renamed fleet.
Also fixed a latent unrelated bug the retest surfaced: `cost_rollup`'s spike-alert path imports
`source_scan` (needs `httpx`) but the cost job env lacked it — added.

## Iteration 14 — Dashboard + Inspect, segmented front page, shadcn-minimal (deployed 2026-07-10)

Acting on the UI review after the concept videos:

- **Killed the app-list side rail.** Inspecting an app is now a full-width **Inspect** page
  (`#/app/<name>/<tab>`) with a "← Dashboard" back link — no persistent side menu. The
  grouped tabs (Overview/Investigate/Assess/Operate) stay.
- **Front page = Dashboard** with a **segmented control**: **Overview · Catalog · Topology ·
  Governance** (`#/`, `#/catalog`, `#/topology`, `#/governance`). High-level fleet info lives
  on the dashboard; per-app detail lives in Inspect — the split the user asked for.
- **Topology promoted to first-class** — the resource-binding dependency graph (from the
  alternatives) now renders inline as a dashboard segment (light theme, hover-to-trace,
  click-to-inspect).
- **Service Catalog as an alternative front-page view** — the faceted sortable table with
  governance-relevant columns ($ MTD, scan, review, team) + status/team facets + filter box.
- **Governance promoted from a header button to a first-class segment.**
- **Minimal shadcn styling** — neutral zinc palette (`--muted`/`--border`/`--primary`),
  8 px radius, subtle `shadow-sm`, segmented control as a shadcn toggle-group; brand red
  kept only as a sparing accent (logo, destructive). Layout otherwise unchanged.
- Old hash routes still alias-redirect; live refresh only re-renders the Overview segment
  (never clobbers a catalog sort, the topology graph, or the governance provision form).

The five `/ui/*` exploration concepts and their videos remain as the archived evaluation set.

## Iteration 13 — five alternative UI concepts + selection videos (deployed 2026-07-10)

The current UI is untouched; five _alternative front-ends_ were built to evaluate different
navigation models, all on the **same live `/api/*` endpoints** (real data, not mockups),
served at `/ui/<concept>` (launcher `/ui/`, StaticFiles mount). Grounded in a research pass
over 13 APM/monitoring products (Datadog, New Relic, Sentry, Dynatrace, Honeycomb, Azure
App Insights, Grafana, Elastic, SigNoz, Uptrace, Axiom, Coralogix, AppDynamics) →
`docs/UX-ALTERNATIVES.md` (per-product analysis + 10 ranked transferable patterns).

- **A · Mission Control** (`/ui/mission`) — dark NOC tile wall, worst-first, pulse-on-unhealthy. _New Relic Navigator._
- **B · Service Catalog** (`/ui/catalog`) — faceted sortable table, live-count rail. _Datadog catalog / Elastic._
- **C · Triage** (`/ui/triage`) — problem-first severity-ranked issue feed synthesized across the fleet. _Sentry / Dynatrace._
- **D · Topology** (`/ui/topology`) — apps↔declared-dependency bipartite graph (serving endpoints, warehouses, jobs, Lakebase, app→app), shared nodes = blast radius. _Smartscape / flow map._
- **E · Console** (`/ui/console`) — keyboard command bar (`worst`/`cost`/`risk`/`alerts`/`team:`/name). _Honeycomb / k9s._

All five share one slide-over overview-scorecard drawer and link back to the production
workbench for deep tabs. Six selection videos (gitignored, `walkthrough/ui-*.mp4`, 30–41 s):
`ui-0-current`, `ui-1-mission-control`, `ui-2-service-catalog`, `ui-3-triage`,
`ui-4-topology`, `ui-5-console` — each opens with a concept card naming its inspiration.

Recommendation pending review (in the doc): a **B+C blend** — Service Catalog as the
tech-lead home, Triage as the shared action queue, current workbench as the per-app drill;
Mission Control as an added wall mode. Awaiting your pick (one, keep current, or mix).

Platform note: topology's first cut derived edges from CLIENT spans, but demo self-traffic
is localhost labelled by HTTP method (correctly dropped) → empty graph; switched to each
app's **declared resource bindings** (already in `/api/fleet`), which is both populated and
the more honest "governed dependency" signal.

## Iteration 12 — journey-shaped IA: Overview + grouped nav (deployed 2026-07-09)

Feedback: 15 flat tabs = bloat; a tech lead's "is this app OK?" and a support engineer's
"why did it 500 at 14:32?" are different journeys forced through the same wall of nouns.
Alternatives weighed: a hard persona _mode switch_ (rejected — personas cross over, modes
hide features) and mere visual grouping (rejected — the lead still has no answer surface).
Landed on **overview-first + journey groups** (the App-Insights/Datadog shape):

- **Overview** (new default tab, `/api/apps/{name}/overview` composes cached queries):
  Reliability / Code quality / Cost / Adoption scorecards with verdict dots, headline
  numbers, deep links, and recent activity — the tech-lead journey ends here ~80% of the
  time. Header stat strip slimmed to five (its scorecard duties moved here).
- **Two-row nav**: groups Overview · **Investigate** (Errors, Traces, Logs, Requests,
  Dependencies, Timeline — the engineer's context, shared time-range) · **Assess**
  (Quality, Cost, Adoption, GenAI — the lead's drill-down) · **Operate** (Uptime, Ops);
  sub-tabs only for the active group.
- **Merges**: Security+Review → Quality; Probes+Synthetics → Uptime; Agent traces joined
  into Traces (agent runs above HTTP traces). 15 tabs → 12, better homed.
- **Smart routing**: old hash ids alias-redirect (probes→uptime, security→quality, …);
  alert-center rows jump to the tab matching the rule (journey_failed→uptime,
  budget_burn→cost, review_reject→quality, permission_drift→ops…).
- Walkthrough video re-recorded for the new IA; outro cleaned of repo-path clutter.

## Iteration 11 — data richness + tab context + UI polish (deployed 2026-07-09)

- **Synthetic population**: demo apps now simulate a weighted user base (6 users on
  healthy/flaky/slow, 4 on vuln/agent, zipf-ish weights) with session bursts — a fresh
  cookie jar per burst means real sessions, and `x-forwarded-user` headers mean distinct
  hashed users. Analytics (DAU/sessions/per-user), GenAI top consumers and per-user cost
  now have realistic shape instead of a single "anon" row. Redeploying the fleet also
  produced new deployment ids → the next scan fills the freshness/policy columns
  (vuln's old pins trip the min-version policy).
- **Tab context**: every detail tab opens with a one-paragraph explainer (what the view
  shows, which table feeds it, freshness caveats) — `TAB_INFO` map rendered above content.
- **UI polish**: styled inputs/selects (padding, focus ring), Ops tab restructured into
  spaced sections (`.sec`, `.btnrow`), settings table cells padded, right-column caps
  separated, auto-stop row aligned.

## Iteration 10 — governance & analytics wave (deployed 2026-07-09)

One goal-sized batch of ~20 features, each at MVP depth, all riding existing primitives:

**Adoption & product analytics (EXTRAS §E)** — `v_usage_daily` / `v_users` gold views over
envelope attrs: Analytics tab with requests/DAU charts, per-(hashed)-user history (first/last
seen, sessions, active days, errors, tokens) and **per-user cost** (MTD $ × request share).
Fleet leaderboard on the Governance page.

**GenAI monitoring** — `v_genai_daily` / `v_genai_sessions`: GenAI tab with token trends,
per-model latency/error table, top consumers by session/user. Complements the Agent tab.

**APM extras** — **error fingerprinting** (`v_error_groups`: normalized+hashed log bodies,
first/last seen, counts → Errors tab), **dependency latency breakdown** (`v_dependencies`
from CLIENT spans → Deps tab), **release annotations & regression-by-version**
(`v_release_windows`/`v_release_perf` from inventory snapshots → Timeline tab with
worse/better verdicts per deployment), **incident timeline** (alerts + deployments +
anomalies + lifecycle merged), **smart detection** (hourly traffic/latency z-score vs 7-day
baseline → `anomaly_*` alerts, deduped 3 h).

**FinOps** — `app_config` table (tags/budget/auto-stop; monitor SP granted MODIFY): budget
limits with 70/100% `budget_burn` alerts + budget bar on Cost tab + ◔ card badge;
**cost forecasting** (`v_cost_forecast`, linear 14 d fit → 30 d projection);
**chargeback/showback** (`v_chargeback` by team/cost_center, MTD, on Governance);
**idle/night auto-stop** (`monitor-app-stopper` hourly job + per-app switch on Ops tab +
manual stop/start buttons routed through the job — the monitor SP can't stop apps itself).

**Security & compliance** — **package policy** (`jobs/policy.json` deny-list + min-versions
→ `policy` findings), **dependency freshness score** (PyPI latest per pinned dep, majors-behind
findings), **permission drift detection** (hourly ACL snapshots + diff → `permission_drift`
alerts + Ops tab table), **audit trail** (`monitor_audit` snapshot of `system.access.audit`
service=apps → Ops tab + Governance), **compliance report** (6 checks per app — telemetry,
scan ≥60, no crit/high, review ok, tagged, budget — with ✅/❌ matrix + .md export).

**Tag management** — tags editor on every app's Ops tab (team/cost_center/env/tier) stored
in `app_config`, driving chargeback grouping + card badges. (Platform governed-tags remain
the deploy-time complement.)

**CI/CD health** — deployment history per app (`app_deployments` hourly snapshot) with
state pills on the Ops tab; used resources shown as tooltip'd badges (warehouse, endpoints,
Genie spaces, Lakebase, experiments…).

**Provisioning** — `monitor-provision-app` job + Governance-page wizard: name+tags form →
template (`templates/basic-app`, envelope+OTel pre-wired) → workspace files →
`apps.create` **with telemetry_export_destinations** → deploy → tags into `app_config` →
`app_provisioned` event. New apps are born observable.

UI: five new tabs (GenAI, Analytics, Deps, Timeline, Ops) + the **Governance** page
(chargeback, compliance, leaderboard, provision wizard, fleet audit).

**Verified live**: `monitor-demo-provisioned` created via the wizard job (fleet #10, probed,
answering); smart detection's first real alert fired within the hour
(`anomaly_traffic apps-monitor: 435/h vs 7d baseline 110±92` — my own test traffic);
chargeback groups `fe-ai/cc-monitor` right after tagging via the Ops form; ops tab shows
9 deployments / 3 ACL entries / 10 audit rows for the agent app. Freshness/policy columns
populate as apps ship new deployments (scans are deployment-id-keyed; monitor's own row
proves the path: unpinned deps → freshness None, 0 policy hits).

## Iteration 9 — UX overhaul: master–detail workbench (deployed 2026-07-09)

Feedback: key metrics (cost/risk/alerts/review) invisible on cards, URLs wasting space,
and the richest views squeezed into a 560 px side drawer. Alternatives weighed:
(a) full-page detail with back-nav, (b) mockup-style global sidebar of fleet pages,
(c) **master–detail split: slim app rail + full-width detail canvas** → picked (c): keeps
one-click app switching while the complex tabs get the whole screen; (b) fits fleet-level
pages, not the per-app drill-down that dominates usage.

- **Hash routing** (`#/app/<name>/<tab>`, `#/alerts`) — deep-linkable, browser back works.
- **Home** = fleet overview: KPI row (cost + findings now real, from `/api/fleet/enrich`),
  needs-attention, and **enriched cards**: slug only (no URL), sparkline, uptime/p95 +
  badges for 7-day $ / tokens, scan score (+crit/high count), CTO verdict (✓/⚠/✗ + score),
  firing-alert count.
- **App page** = workbench: sticky rail (all apps, status dots, p95, current highlighted),
  header with quick-stats strip (status·uptime·p95·errors·cost·tokens·score·review·alerts),
  tab bar + full-width content; charts are viewBox-scaled to container (900-wide), chart
  pairs side-by-side on wide screens. Live ticks refresh rail/header only — tab content
  never gets clobbered mid-read.
- Drawer deleted entirely; alert center is a page (`#/alerts`).
- New endpoint `/api/fleet/enrich` (per-app scan score, review verdict, 7-day cost/tokens;
  cached 10–15 min, partial data on missing tables).

**Built**

- `monitor-demo-agent` is now two real agents on one FastAPI app: **qa** (LLM topic pick →
  knowledge TOOL → LLM answer) and **ops** (TOOL = the monitor's own `/api/fleet` API →
  LLM ops brief). MLflow-traced (`@mlflow.trace` + `mlflow.openai.autolog()` over the
  SDK's OpenAI client), gateway-tagged, self-traffic every ~5 min + the 30-min ops-brief
  journey → continuous observable agentic usage and cost.
- One **correlation context** end to end: the envelope middleware exposes
  `request.state.monitor` → the same `client_request_id`/session/user go onto the OTel
  server span, the MLflow trace (`update_current_trace`), and the AI-Gateway tags header;
  token usage lands on the OTel server span (`gen_ai.*` → cost rollup) and on MLflow LLM spans.
- Demo bundle: MLflow `experiment` resource bound to the app; app-to-app `CAN_USE`
  binding so the agent may call the monitor. Inventory job grants the monitor SP
  `CAN_READ` on every experiment bound to any app (generic — it picked up
  fastapi-starter's experiment too).
- Monitor: **Agent tab** — MLflow trace list (state, agent tag, duration, previews) →
  **unified waterfall**: MLflow-typed spans (AGENT/TOOL/CHAT_MODEL, purple/teal/red) and
  app OTel spans (per-service chips) on one timeline + correlated logs + deep link to the
  MLflow UI. Verified cross-app: one trace shows monitor `synthetic.journey` → agent
  `/api/ops/brief` (133/67 tokens on the server span) → `AGENT ops_agent` →
  `TOOL fetch_fleet_status` → monitor `GET /api/fleet` server span → `CHAT_MODEL Completions`.

**Platform learnings (each cost a debug cycle)**

- With the Apps-injected `OTEL_EXPORTER_OTLP_ENDPOINT`, **MLflow diverts traces to the
  OTLP sidecar instead of the MLflow backend**. `MLFLOW_ENABLE_DUAL_EXPORT=true`
  (+ newer spelling `MLFLOW_TRACE_ENABLE_OTLP_DUAL_EXPORT`) sends them to **both** —
  experiment for the MLflow UI, `otel_spans` for UC correlation.
- Dual-exported MLflow spans in `otel_spans` carry `mlflow.spanType` and
  **`mlflow.traceRequestId`** attributes (values JSON-quoted — strip quotes) — a direct
  MLflow⟷OTel join, sharper than the client_request_id fallback.
- The app container **can't reach MLflow artifact storage** (trace data download,
  `*.storage.cloud.databricks.com` egress-blocked) — so the monitor reads trace _info_
  via REST (`/api/3.0/mlflow/traces/search`) and takes span _detail_ from `otel_spans`.
  Bonus: no mlflow dependency in the monitor at all.
- The job-side SDK silently drops fields its models don't know (`App.resources` empty on
  older preinstalled versions) — resource discovery in jobs uses raw REST responses.

## Iteration 7 — alerting (deployed 2026-07-08)

- **In-app rules** (`app/alerts.py`): `app_down` (2 consecutive probe failures), `app_stopped`,
  `probe_error_rate` >10%/1h, `slow_p95` > budget — evaluated in memory after every probe
  round, zero warehouse cost. Transitions (firing/resolved) append to `alert_events` +
  optional `ALERT_WEBHOOK_URL` POST. Alert-center UI behind the 🔔 (active + 3-day history).
- **Job-emitted deep rules**: `critical_findings` (source scan), `review_reject` (LLM review),
  `journey_failed` (synthetics), `cost_spike` (>2× prior-week median) — each job appends to
  `alert_events` when it computes the signal; no extra scheduler.
- **SQL alert (Alerts v2, bundle-managed)**: daily email when any app has critical findings —
  the exemplar for email/notification-destination delivery. Gotchas: v2 uses `evaluation` /
  `quartz_cron_schedule` (not `condition`/`cron_schedule`); triggers on TRUE.

### Post-verification fixes & platform gotchas (2026-07-08)

- **A stopped app's URL returns HTTP 200** (HTML placeholder) — status-code probing can't
  see stopped apps. Fixed: `compute_state != ACTIVE` ⇒ stopped (fleet refresh now 120 s)
  - an HTML answer to `/healthz` counts as down. Verified live: stopping `monitor-demo-flaky`
    fired `app_stopped` within 2 min, transition persisted to `alert_events`, resolved on restart.
- **Serverless job kernels** run inside IPython: no `__file__` (use `--jobs-dir` param) and
  `asyncio.run()` raises — synthetics rewritten to sync httpx.
- **Dogfood:** the scanner scores the monitor itself 48/100 — 21 bandit B608 (f-string SQL)
  findings in `queries.py`. Identifiers are constants and values are parameterized
  (`:app` bind params), but the flag is fair and stays visible — honest scanners beat
  quiet ones.

## Iteration 6 — synthetic journeys (deployed 2026-07-08, reworked same day)

- Journeys are data (`app/journeys.json`): multi-step HTTP tests with status/content
  assertions + latency budgets; apps without a spec get an auto smoke journey.
- **Rework after live testing:** the journeys now run **inside the monitor app** every
  30 min (custom `synthetic.journey` OTel spans + in-memory latest results + "Run journeys
  now" button). Two hard reasons discovered:
  1. **Job-runtime tokens are rejected by app URLs** (401, or a login page served with 200) — exactly why the reference playwright DAB provisions a dedicated M2M service
     principal + secret scope. The monitor app's own SP token is already the working
     identity for app-to-app calls.
  2. **The apps proxy intercepts `GET /healthz`** — answers 200 with an empty body
     (even for stopped apps), so content assertions must target real paths (`/api/...`, `/`).
- `jobs/synthetics.py` remains as the **browser-mode** job (Playwright page-load smoke,
  PAUSED schedule): on serverless the headless shell lacks system deps → recorded as
  `playwright unavailable`; the custom-container pattern from
  databricks-apps-e2e-playwright-testing-dab applies where classic compute + DCS exist.
- Journey failures feed the same alert engine (`journey_failed`, verified firing + resolving live).

## Iteration 5 — cost tracking (deployed 2026-07-08)

- `jobs/cost_rollup.py` (daily): app compute DBUs/$ = `system.billing.usage`
  (`billing_origin_product='APPS'`, **workspace_id filtered** — FEVM billing is account-wide!)
  × `list_prices`; AI tokens per app = `gen_ai.*` span attributes from our own otel_spans
  (+ `system.ai_gateway.usage` merged when endpoints have usage tracking). → `costs_daily`,
  `v_cost_summary`; Cost tab + KPI tile.
- **Honesty note:** pay-per-token FMAPI endpoints don't log to `system.ai_gateway.usage` by
  default, and enabling gateway usage tracking on the shared endpoint was out of scope
  (permission-gated) — per-app AI **tokens** are exact from own telemetry; per-app AI **$**
  stays null rather than guessed. `usage.currency_code` doesn't exist → join prices on
  sku+cloud with `currency_code='USD'`. Workspace id: `WorkspaceClient().get_workspace_id()`
  (spark confs unreliable on serverless).

## Iteration 4 — agentic CTO review (deployed 2026-07-08)

- `jobs/llm_review.py` (daily + on-demand `only_app` param, `databricks-claude-sonnet-4-5`):
  packs each app's source (tree + prioritized files, 60 KB budget) → strict-JSON review:
  verdict, 5 scores, strengths, findings with recommendations → `llm_reviews`. Reviews only
  unreviewed deployments (content-addressed by deployment_id).
- First fleet round: **monitor-demo-vuln = reject**, others approve_with_conditions, scores
  differentiated (healthy 8.0 … solution-builder 5.8). Review tab with verdict/score meters/
  findings + "Request fresh review" button (app SP has CAN_MANAGE_RUN on the job).
- Serverless python tasks have **no `__file__`** — cross-file imports in jobs need the
  `--jobs-dir=${workspace.file_path}/jobs` parameter appended to `sys.path`.

## Iteration 3 — source & dependency scans (deployed 2026-07-08)

- `jobs/source_scan.py` (2nd task of hourly inventory job): exports each app's source from
  the workspace (bounded: text files, 400 files/200 KB caps, skip dirs), then
  requirements → **OSV.dev** CVE batch lookup, secret regexes, code-smell regexes, **bandit**;
  0–100 quality score (severity-weighted, per-category caps) → `code_scans` + `scan_findings`.
- Fleet round: monitor-demo-vuln **score 0** (92 findings: planted AWS key = critical, aiohttp/
  urllib3/requests/jinja2 CVEs = high); demo apps 83; the real starters got meaningful CVE
  lists on their large dependency sets. Incremental by deployment_id.

## Iteration 2 — demo fleet + telemetry pipeline (deployed 2026-07-08)

- 5 demo apps (own bundle `example-apps/`): healthy / flaky (~8% 500s + exceptions) /
  slow (0.2–2.5 s + 8 s stalls) / vuln (inert scanner bait) / agent (tagged LLM calls),
  all with self-traffic generators, envelope middleware, shared telemetry destinations.
- **THE gotcha:** platform docs/examples say OTLP sidecar at `localhost:4317`; it actually
  listens on **`localhost:4314`** and the runtime injects `OTEL_EXPORTER_OTLP_ENDPOINT` —
  pinning 4317 killed span/metric export ("connection reset by peer") while logs kept
  flowing. Fix: never pin endpoint/protocol. Also: DABs forbids two apps sharing one
  `source_code_path` (hence healthy/flaky/slow copies + `sync-demos.sh`).
- otel table facts: `attributes` is VARIANT (`variant_get(attributes,'$["http.route"]','string')`),
  `kind`='SPAN_KIND_SERVER…', `severity_number` is a mostly-null STRING enum → filter error
  logs on `severity_text`; probe/self-traffic spans propagate `traceparent` so server spans
  are rarely roots (traces list must not filter to roots); `/healthz` probe spans excluded
  from request metrics as synthetic traffic.
- Monitor pages shipped: Requests (volume+errors, p50/p95, routes), Errors (failed requests
  - error logs), Logs (severity-chipped tail), Traces (list → waterfall + correlated logs).

## Iteration 1 — bundle, schema, inventory job, monitor app v1 (deployed 2026-07-08)

**Built**

- `databricks.yml` — toolkit bundle (`apps-monitoring`), target `dev`, vars for catalog/schema/warehouse.
- `resources/monitoring.schema.yml` — UC schema `serverless_stable_domo_catalog.monitor`.
- `resources/monitor.app.yml` — the `apps-monitor` app with **`telemetry_export_destinations`**
  pointing at shared `otel_logs` / `otel_spans` / `otel_metrics` tables in the schema (the
  platform provisions the tables), plus warehouse + inventory-job resource bindings.
- `resources/inventory.job.yml` — hourly serverless job (`monitor-inventory-scan`).
- `jobs/inventory_scan.py` — snapshots all apps into `apps_inventory` (+`v_apps_latest` view),
  grants the monitor SP `CAN_USE` on every app (probing) and read on the schema.
- `app/` — FastAPI monitor: 60 s SP-OAuth probes of every visible app (the auth pattern from
  the playwright reference repo), in-memory 24 h ring buffer, `/api/fleet`, per-app detail,
  `Sync fleet` button that triggers the inventory job. UI follows the prepared mockup's
  Databricks light theme (KPI tiles, status pills, sparklines, needs-attention strip, drawer).

**Design decisions**

- **No custom telemetry ingestion.** Fleet apps export OTel through the platform into shared
  UC tables; `service_name` is the tenant key. The monitor reads, never receives.
- **Warm-in-memory, history-in-UC.** Probes/board never touch the SQL warehouse; probe calls
  are themselves OTel data (auto-instrumented httpx spans + `monitor.probe.*` metrics), so
  durable probe history comes for free through the telemetry pipeline instead of INSERTs
  that would keep the serverless warehouse awake 24/7.
- **Jobs write, app reads.** Jobs run as the deploying user (see all apps + system tables);
  the app SP gets narrow grants, automated by the inventory job itself (self-bootstrapping).
