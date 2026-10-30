# Console design-quality pass

Hallmark review, 30 October 2026. Scope: the approved V1 Cobalt workbench and all
105 parity capabilities. Audience: operators locating an incident, its evidence,
and the control that addresses it. This is an analytic workbench: native tables,
definition lists, time series, section indexes and the existing status primitives.
The framework, route ownership, tokens and data APIs remain unchanged.

Reviewed against the supplied Hallmark `references/anti-patterns.md` and all
58 gates in `references/slop-test.md`. The explicit V1-preservation requirement
supersedes macrostructure rotation (gates 8/32). Hero, video, illustration and
study-only gates do not apply. Dense evidence tables and composite graph nodes
allow long identifiers to wrap; navigation and primary actions retain short
labels. This preserves the complete evidence at phone widths rather than
truncating resource names to meet the marketing-oriented single-line rule.

Pre-emit critique: Philosophy 4 · Hierarchy 4 · Execution 4 · Specificity 5 ·
Restraint 4 · Variety 4 (grouping varies by task inside the chosen workbench).

## Findings and corrections

The audit phase identified the findings below; the user explicitly authorized
fixes after the audit. Locations refer to the revised implementation.

| Severity | Tell / integrity finding                           | Where                                                             | Correction                                                                                                              |
| -------- | -------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Critical | Ambiguous identity and conflicting health evidence | `app/console_topology.py`, `app/static/console/topology.js`       | Preserve workspace/type identity; resolve apps by workspace/name then unique host; render a monitored app once.         |
| Critical | Missing evidence presented as a warning            | `app/static/console/topology.js`                                  | Neutral icon and “No health signal”; amber remains available for stale app feeds and actual problems.                   |
| Major    | Uniform section rhythm (Hallmark gate 9)           | `app/static/console/sections.js` Operate/Governance               | Named local indexes, return links, task grouping and compact paired evidence blocks.                                    |
| Major    | Inconsistent visual scale (hierarchy/execution)    | `app/static/console/app.js` `seriesChart`, `sections.js` `series` | Shared V1 chart renderer; HTML axes keep 12px type while the SVG plot resizes.                                          |
| Major    | Raw payloads overwhelm the information hierarchy   | `app/static/console/sections.js` `cell`, `resources`              | Structured records become labelled lists; UTC dates, percentages, units and permission summaries replace serialization. |
| Minor    | Repeated headings                                  | `app/static/console/sections.js` table/panel callers              | One visible section heading; table names and sorting remain accessible.                                                 |
| Minor    | Demo scores provide no useful comparison           | `scripts/generate_console_demo.py`                                | Deterministic components derived from existing fixture evidence, tested against the production scoring helper.          |

Initial findings: **2 critical · 3 major · 2 minor**. All seven corrected within
this scope. No gradient heroes, side-stripes, italic headings, decorative chrome,
new fonts, extra palette or motion were introduced. Existing tabular numerals,
focus rings, reduced motion, partial/error/loading states and disabled controls
remain in use. Status carries icon, word and semantic colour.

## Every route reviewed

“Checked” includes the shared chrome, readable text, missing data, keyboard targets
and 320/390/1440px layouts. Automated coverage also includes 375/414/768px.

| Route / app section                | Audit result and action                                                                                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fleet                              | Checked V1 hierarchy, freshness and nulls; retained overview and tiles.                                                                           |
| Topology                           | Workspace labels, single app identities, neutral absent health, type groups, barycentric ordering, explicit both-evidence edges and blast radius. |
| Catalog                            | Readable review verdicts; tags and sorting preserved.                                                                                             |
| Ask Genie                          | Existing configured/unconfigured and trust states retained; local-fixture iframe checked.                                                         |
| Alerts                             | Readable rule/state/date values; removed repeated maintenance/transition headings; all actions retained.                                          |
| Investigations                     | Error groups and source states retained; drilldowns checked.                                                                                      |
| Reliability                        | Existing V1 SLO evidence, status and units retained.                                                                                              |
| Costs                              | Existing billing/estimate distinctions, units, unknowns and sorting retained.                                                                     |
| Governance                         | Nine-section index; no duplicate captions; readable costs/audits; evidence-based demo leaderboard; HTTP MCP endpoint.                             |
| Usage                              | Existing funnel, cohort and partial-week context retained.                                                                                        |
| Workspaces / Federation            | Readable remote status, units and collection timestamps; workspace identity retained.                                                             |
| App Overview                       | Shared fixed-font charts, compact facts, readable tags, probe/objective/telemetry evidence.                                                       |
| App Errors                         | Readable event times, counts and statuses; all groups/spans/logs retained.                                                                        |
| App Traces                         | Formatted request times and structured tags; HTTP and MLflow drilldowns retained.                                                                 |
| App Logs                           | UTC timestamps and structured messages; shorter trace labels retain full IDs in accessible labels/tooltips and destinations.                      |
| App Traffic                        | Shared charts, labelled latency units, formatted timeline and sortable route table.                                                               |
| App Dependencies                   | Readable resource/permission bindings, remaining binding details, rounded error rates and latency units.                                          |
| App Changes                        | Human labels/times/statuses; release comparisons and chronology retained.                                                                         |
| App Code & security                | Compact scan/review definitions; structured packages/endpoints, human dates and score units.                                                      |
| App Cost                           | Shared daily charts and readable unit economics; forecast/budget controls retained.                                                               |
| App AI usage                       | Shared daily charts; readable model, consumer, quality, feedback and drift values.                                                                |
| App Usage                          | Shared adoption charts; readable dates, amounts and user history.                                                                                 |
| App Product & guardrails           | Readable event/step names, cohort percentages, masked findings and policy times; all editors retained.                                            |
| App Operate                        | Eight named groups with index/return links; paired evidence, compact facts, fixed-size charts and all controls.                                   |
| App Browser checks                 | Readable run time/status/latency and preserved artifact information.                                                                              |
| App Telemetry                      | Human signal labels, UTC freshness, percentages and token reconciliation units.                                                                   |
| Trace / agent trace / error detail | Human attribute labels and structured values; full identity, waterfall, correlated logs and source states retained.                               |

## Task punch list

1. **Identity:** typed workspace-qualified resources remain distinct. App references
   match name/workspace before a unique URL host; ambiguous hosts do not guess.
   Explicit target workspace is supported. Duplicate bindings collapse; one edge
   carries both declared and observed flags. One visible node per monitored app.
2. **Unknown health:** resource nodes show neutral “No health signal”. Dependency
   call counts or error rates never manufacture resource health.
3. **Graph scanning:** type headers, visible workspace qualification, alternating
   barycentric ordering, line-style legend, keyboard highlights and direct
   dependent counts. Known dependent apps stay in the application column.
4. **Readable values:** structured arrays/records use lists/definitions; explicit
   labels, formatted UTC times, bounded numeric precision, units and readable
   resource permissions. Nulls remain unknown. Rule and attribute keys are humanized.
5. **Charts:** V1 and deep views share one renderer with HTML axes, consistent
   gridlines and fixed label/plot heights. Missing values remain gaps and negative
   error budgets remain visible; deployment markers and thresholds are retained.
6. **Headings:** section ownership prevents maintenance, economics, usage, prices
   and leaderboard caption repetition. Tables retain accessible names and sorting.
7. **Long pages:** Operate has the eight requested groups; Governance has the nine
   requested anchors. Both include return links. Facts use two compact columns,
   collapsing on phones. Optional fleet policy links remain under a named disclosure.
8. **Integrations:** live MCP uses the application-relative HTTP base plus `/mcp`;
   demo shows `https://your-monitor.example/mcp`, explicitly labelled a placeholder.
9. **Leaderboard:** available components use the production formula with the demo
   active-user proxy disclosed. Scores vary with fixture evidence; stopped apps
   are excluded. Regeneration is byte-for-byte deterministic.
10. **Responsive/accessibility:** six viewport sizes, keyboard graph/index access,
    preserved sortable tables/controls, semantic status, existing tokens, no page
    overflow, no side-stripes, roman headings and honest nulls.

## Verification and artifacts

- `uv run pytest --cov -q`: **381 passed, 2 existing skips; 99.62% branch-aware
  coverage**. Skips require the MCP app-runtime dependency, absent from SDK dev.
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`: passed
  with the existing pinned tools. Commands set `UV_FROZEN=1`, `UV_NO_SYNC=1` and
  a worktree-local cache; no lock or dependency changes.
- `python3 scripts/check_console_ui.py`: **390 route/viewport checks**, zero
  JavaScript errors and zero page overflow. All disclosures are expanded for the
  readable-text sweep. Tests reject visible raw object/array starts, ISO timestamps,
  raw field labels and local file URLs; reject duplicate topology identities;
  check neutral absent resource health and fixed chart typography.
- All 25 checked shared palette pairs meet WCAG text/control/focus contrast thresholds.
- Workflow coverage includes graph hover/focus/Tab traversal, filters, blast radius,
  local section indexes, preserved form drafts, saves, confirmations, capacity,
  maintenance/SLO editors, traces, compliance export, model prices, provisioning,
  policy preview/apply, read-only controls, cache/refresh/retry and prefixed APIs.
- Live-fixture `/prefix/mcp` and an actual `file://` demo Governance render are
  checked separately. All external browser requests are blocked.
- New Python cases cover local-name precedence, cross-workspace name isolation,
  unique host/URL and explicit target workspace matching, duplicate bindings,
  shared host ambiguity, health retention, graph fixture identities and every
  demo score against the production helper. Existing weighted edge-metric tests pass.
- JavaScript syntax checks, deterministic regeneration and `git diff --check` pass.

Six 1440px review captures: [Topology](../.cache/console-qa/after-topology.png) ·
[Operate](../.cache/console-qa/after-operate.png) ·
[Governance](../.cache/console-qa/after-governance.png) ·
[Dependencies](../.cache/console-qa/after-deps.png) ·
[Logs](../.cache/console-qa/after-logs.png) ·
[Alerts](../.cache/console-qa/after-alerts.png).
Machine report: `.cache/console-qa/report.json`.
They were visually compared with the supplied originals. Operate fell from 6698px
to 4640px high without losing a section. Topology deliberately adds type headings
and visible workspace identities; its complete sortable relationship list remains.
Governance prioritizes navigation and readable evidence over hiding parity features.

The requested second screenshot destination is outside this worktree. The six
captures are ready here; copying them there awaits the user's exception to the
explicit worktree-only write rule.

## Changed files and roadmap mapping

- `app/console_topology.py`, `app/static/console/topology.js`: F0.8/S12 identity,
  grouping and evidence semantics.
- `app/static/console/app.js`, `sections.js`, `styles.css`: S1/S2 operations,
  S4/S7 economics/adoption, S5 telemetry, S6 monitoring cost, S8 guardrails,
  S10 integrations, S11/S13 reachability, S14 drift presentation.
- `scripts/generate_console_demo.py`, `app/static/console/demo-data.js`,
  `demo-fixtures.js`: deterministic identity and leaderboard fixtures.
- `tests/test_console.py`, `scripts/check_console_ui.py`: regression and visual QA.
- `docs/FEATURES.md`, `docs/CONSOLE.md`, `docs/UI-PARITY.md`, this report: capability,
  source, parity and audit documentation.

No roadmap snippet needed correction. No new APIs, tables, dependencies or
instrumentation were added. Existing unrelated worktree changes were preserved.
No Databricks command, deployment, commit or push was run. All 105 parity rows remain.
