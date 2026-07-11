# UX alternatives — evaluation set

Five alternative front-ends for the fleet monitor, each a distinct **navigation model**
distilled from a survey of 13 APM/monitoring products. All run on the **same live
`/api/*` endpoints** as the shipped UI (real data, not mockups) and are served at
`/ui/<concept>` alongside the untouched production UI at `/`. Launcher: `/ui/`.

Walkthrough videos (gitignored, in `walkthrough/`): `ui-current`, `ui-mission`,
`ui-catalog`, `ui-triage`, `ui-topology`, `ui-console`.

## The field survey (13 products)

Per-product analysis (navigation model, home screen, drill path, density, signature
interaction) covered: Azure Application Insights, Datadog, New Relic, Grafana, Dynatrace,
Honeycomb, Sentry, Elastic APM, SigNoz, Uptrace, Axiom, Coralogix, AppDynamics.

### Top transferable patterns (ranked for a 10–100 Databricks-Apps fleet; personas: tech-lead quality sweep, developer/support deep-debug)

1. **Golden-signal fleet table, sparklines, worst-first** (Datadog catalog / Elastic / SigNoz) — the daily 30-second sweep; switchable lenses over the same rows.
2. **Four-step drill contract**: KPI → ranked list → suggested sample → end-to-end waterfall (Azure) — time-to-first-example; every aggregate clickable, filters travel.
3. **Issue stream with grouping + lifecycle** (Sentry) — turns raw error volume into a finite to-do queue; best fit for a small team maintaining many apps.
4. **Status honeycomb / dense grid** (New Relic Navigator) — ambient "is anything red?"; whole fleet on one screen.
5. **BubbleUp diff** — select the bad region, get ranked "what's different" (Honeycomb; echoed by Datadog outlier facets, Elastic correlations) — root-causing unknown-unknowns.
6. **Facet sidebar with live counts** (Datadog / Uptrace / Sentry) — exploration without a query language.
7. **Problem cards with blast radius** (Dynatrace Davis) — collapse correlated anomalies into one incident.
8. **Live tail with pause-on-interact** (Azure Live Metrics / Axiom Stream) — deploy validation in real time.
9. **Deploy/version markers + deployments lens** (Datadog / Azure) — answers "did my deploy break it?".
10. **No-dead-ends escape hatch: every view opens as a query** (Grafana panel→Explore, Coralogix pivots).

Deliberately down-ranked for this scale: full topology maps (shallow graphs across mostly-independent apps) and dashboard-first composability as a _primary_ model.

## The five concepts (mapping to patterns)

| #       | Concept               | Route          | Navigation model                                    | Patterns           | Best for                                  |
| ------- | --------------------- | -------------- | --------------------------------------------------- | ------------------ | ----------------------------------------- |
| current | **Journey workbench** | `/`            | overview-first + grouped master-detail              | 1,2,9              | balanced default; both personas           |
| A       | **Mission Control**   | `/ui/mission`  | dark NOC tile wall, worst-first, pulse-on-unhealthy | 4                  | ambient awareness · wall/TV               |
| B       | **Service Catalog**   | `/ui/catalog`  | faceted sortable table + live-count rail            | 1,6                | compare & find at scale (toward 100 apps) |
| C       | **Triage**            | `/ui/triage`   | problem-first ranked issue feed, severity-grouped   | 3,7                | small team · "what needs me now"          |
| D       | **Topology**          | `/ui/topology` | app→dependency bipartite graph from CLIENT spans    | (map, down-ranked) | blast-radius understanding                |
| E       | **Console**           | `/ui/console`  | keyboard command/query bar, monospace results       | 5,10               | power users                               |

All five share one slide-over detail drawer (the app overview scorecard) and link back into
the production workbench for deep tabs — so a concept can win at the _fleet_ level without
re-implementing all 12 detail tabs.

## Round 2 — understandability & user journeys (2026-07-10)

Second exploration round against the shipped Dashboard+Inspect UI. Brief: **minimal, zero
new features** — only better ways to make the product understandable and to support
different journey types. Grounded in a second research pass over **40 more products**
(Splunk O11y, Instana, Lightstep, Sumo Logic, LogicMonitor, Site24x7, Chronosphere, Dash0,
groundcover, Last9, Middleware, HyperDX, Highlight, OpenObserve, KloudMate, Netdata,
Baselime/Cloudflare, Better Stack, Checkly, Pingdom, Uptime Kuma, Statuspage, PagerDuty,
Opsgenie, incident.io, Grafana IRM, Rollbar, Bugsnag, Raygun, Honeybadger, GlitchTip,
Kibana solution views, Vercel, Railway, Fly.io, Stripe, Linear, PostHog, Plausible, Fathom).

**Top patterns that drove the concepts** (full ranking in the research report):

1. _Answer-first home_ — a plain-language verdict + capped needs-attention list (PagerDuty, Stripe, Statuspage).
2. _Every number is a door_ — click narrows the whole view, context carried (Plausible, Vercel, Chronosphere DDx).
3. _One landing page per scope_ — kill the monitor/troubleshoot split (Splunk's merge, Grafana IRM).
4. _Fixed golden-signal grammar repeated per entity_ (Instana, groundcover, Bugsnag).
5. _Reweight, never remove_ — persona scoping must not hide content (Kibana's −70% lesson).
6. _Since-you-last-looked stream with persistent state strip_ (Linear inbox, Vercel deploy feed).

**The five round-2 concepts** (all live at `/ui/`, same APIs, production untouched):

| #   | Concept   | Route       | One-liner                                                                                                               | Journey it nails                    |
| --- | --------- | ----------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| A   | **Lens**  | `/ui/lens`  | Tech-lead / Operator / Developer switch reorders & re-emphasizes the same fleet — nothing hidden                        | journeys as the top-level control   |
| B   | **Story** | `/ui/story` | no tabs: one scannable narrative ("is it up → fast → failed → cost → code → users"), scrollspy chips carry verdict dots | first-glance understandability      |
| C   | **Zoom**  | `/ui/zoom`  | strict breadcrumb drill contract Fleet → App → Domain → Evidence; every number is a door                                | predictable drill, never lost       |
| D   | **Ask**   | `/ui/ask`   | home = the questions people ask, every card pre-answered with a live verdict                                            | language-first navigation           |
| E   | **Flow**  | `/ui/flow`  | day-grouped fleet event stream (alerts/platform/scans/reviews) + pinned "right now" strip                               | operator catch-up ("what changed?") |

Research verdicts folded in: Story's scrollspy chips carry their own status dot + number
(the sticky bar alone is the 5-second sweep); Ask's cards are pre-answered so the home is a
status page even unclicked; Flow pins fleet state above the stream so "what is" and "what
changed" share the screen; Lens reorders but never hides (Kibana lesson); Zoom's evidence
level deep-links into the production workbench.

Walkthroughs (gitignored): `walkthrough/ui/uiv2-{0-current,1-lens,2-story,3-zoom,4-ask,5-flow}.mp4`
— each explains the ENTIRE UI of its concept, current included.

## Round 3 — detail-view alternatives (2026-07-10)

Brief: the landing page stays **as-is**; the problems are in the single-app detail view —
hard to follow, unclear navigation path, non-obvious menu naming (Investigate/Assess/Ops/
Deps/GenAI). Four alternative ways to inspect ONE app, all on the same per-app APIs, all
sharing one plain-language section vocabulary (`app/static/ui/_app.js`): Summary · What
broke · Speed & traffic · Recent requests · Logs · Outside calls · Code & security · Money ·
People & AI · Uptime & tests · History & settings.

| #   | Concept                        | Route                | Model                                                                                                                                                                                                                                                                                                                                            | Fixes                                                           |
| --- | ------------------------------ | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| D1  | **Plain**                      | `/ui/inspect-plain`  | one flat row of plainly-named sections, breadcrumb `Fleet › app › section`, "Continue →" pager                                                                                                                                                                                                                                                   | jargon names, two-level tab maze                                |
| D2  | **Report**                     | `/ui/inspect-scroll` | no tabs: one scrollable report per app, sections in narrative order, sticky scrollspy                                                                                                                                                                                                                                                            | "where am I?" — reading order is the IA                         |
| D3  | **Guide**                      | `/ui/inspect-guide`  | pick the job ("Something is wrong" / "Quality & cost check" / "Operate it") → numbered stepper with one line of guidance per step                                                                                                                                                                                                                | not knowing the path — the path is drawn                        |
| D4  | **Board** ← _chosen direction_ | `/ui/inspect-board`  | **tiered board**: ① At-a-glance hero — stat strip + max-3 ranked takeaways, each a door that scrolls to & expands its panel; ② **Manage** band (app owner: code sign-off, money, adoption, uptime, history/access); ③ **Deep dive** band (engineers: what broke, speed & traffic, requests, logs, outside calls). Expand-in-place, Esc collapses | hidden features + mixed audiences — one screen, three altitudes |

Each has an app switcher in the header and deep-links into the production workbench for raw
evidence (traces, settings). Walkthroughs: `walkthrough/ui/uiv3-{1-plain,2-report,3-guide,4-board}.mp4`.

## Marketing walkthroughs (current UI, pick one)

Five marketing-ready videos of the shipped Dashboard/Inspect UI (gitignored,
`walkthrough/marketing-*.mp4`) — benefit-led, no under-the-hood/technical narration.
Same product, five different treatments (content, visuals, pacing, flow):

| #   | Treatment                    | Style                                          | Flow                                                                       |
| --- | ---------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------- |
| 1   | **One glance**               | punchy full-screen statements, fast            | dashboard → catalog sort → inspect → close                                 |
| 2   | **A morning with the fleet** | narrative/persona, calm lower-thirds           | a tech lead's 9 AM: dashboard → attention → inspect → governance           |
| 3   | **Every question, answered** | Q&A — question card then the answer on screen  | is anything wrong / riskiest / what depends on X / would I sign it off     |
| 4   | **Considered**               | premium, minimal, slow, airy centered captions | minimal intro → topology → inspect → tagline                               |
| 5   | **Everything, fast**         | sizzle montage, top chips, rapid               | dashboard → catalog → topology → inspect → investigate → cost → governance |

## Recommendation (pending your review)

For the stated personas the survey most favours a **B+C blend**: the Service Catalog table as
the tech-lead's home (worst-first, lens-switchable, scales to 100) with the Triage stream as
the shared action queue — the current Journey workbench already supplies the deep per-app
drill those two hand off to. Mission Control is the best _added_ view (a `/wall` mode) rather
than a primary. Topology and Console shine in specific moments but are weaker as an everyday
home. Final call is yours after the six walkthroughs.
