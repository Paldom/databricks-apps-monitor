# Metrics audit — are the numbers real?

Audit date: 2026-07-10. Method: read every query/job/UI claim, then verified live against
the workspace (SQL over `monitor.*`, live curls with SP OAuth). Verdict per feature:
**INVALID** (wrong as presented) · **DEMO-FED** (real pipeline, fabricated demo data) ·
**IMPRECISE** (real data, shaky semantics) · **REAL**.

## A. Invalid or misleading as presented

1. **Probe uptime / availability / p95 / error-rate — measures the proxy, not the app.**
   `/healthz` on an app URL is answered by the Apps ingress itself: verified live — 200,
   empty body, no content-type (the app would return JSON), and **zero** healthz SERVER
   spans exist in `otel_spans`. So the headline numbers on every card/tile/KPI
   (uptime 24h, p95 ms, err 1h) monitor Databricks' ingress, not your code:
   `monitor-demo-flaky` throws ~10% errors on real routes (58/583 today; 2 of 6 live
   curls returned 500) yet shows **100% uptime, 0% errors**; `monitor-demo-slow`
   (0.2–2.5 s routes) shows p95 ≈ 90 ms. The `app_down`/`probe_error_rate`/`slow_p95`
   alert rules can effectively never fire for app-level failure; only journeys catch it.
   _Fix path: make the synthetic journeys (which hit real routes) the headline
   reliability signal, and/or compute uptime/p95 from `otel_spans` server spans._

2. **Capacity probe ("max healthy QPS", "recommended QPS", Ops tab)** — the ramp hits
   `/healthz`, i.e. load-tests the proxy. The knee says nothing about app capacity
   (especially for LLM apps). INVALID as labeled. (Same for the TTFB stat.)

3. **"Error rate 1h" placement** — it's probe-failure rate (≈ always 0, see #1) but the
   catalog column / card badge / inspect stat read as request error rate; the Errors tab
   on the same screen shows the real ~10%. Two contradictory "error rates" in one product.

4. **AI-Gateway attribution fallback** — `coalesce(request_tags['app'], requester)` puts
   human emails into the app dimension: `domonkos.pal@databricks.com` is currently a row
   in `costs_daily`.

5. **Deleted/renamed apps' cost is orphaned** — $124 of last-7d spend sits under the old
   `obs-demo-*` names: invisible on fleet cards (live apps only) yet included in
   governance chargeback. Fleet "Cost 7d / MTD" understates true workspace app spend;
   there is no lifecycle mapping for renamed apps.

## B. Real pipeline, fabricated demo data

6. **Adoption analytics (DAU, sessions, per-user history, user cost share)** — every
   "user" is `*@synthetic.local` from the demo apps' built-in self-traffic generators
   (verified: 6 synthetic hashes per app + 1 more = the monitor's own SP via journeys —
   the bot counts as a DAU). Requests 7d ≈ 100% bot traffic.

7. **User feedback (GenAI tab)** — the agent app posts random 1–5 ratings with canned
   comments every ~5 min. `v_feedback` is pure fabrication by design.

8. **"Real HTTP traffic (probe traffic excluded)"** (Requests tab) — the healthz filter
   is vestigial (no healthz spans exist, see #1); journeys and self-traffic are NOT
   excluded and are ~all of the traffic at demo scale.

## C. Real data, questionable semantics / precision

9. **"AI calls"** counts server spans tagged `gen_ai.request.model` = agent _requests_,
   not model invocations (qa_agent makes 2 LLM calls/request → ~2× undercount). GenAI
   "model latency" is whole-request latency. Token counts are correct.
10. **"24 h" probe windows** — in-memory ring buffer; after every monitor restart the
    "24h" uptime/availability covers only minutes. Labels don't say so.
11. **Release windows / regression-by-version** — deployment windows derived from hourly
    inventory snapshots: up to 1 h of traffic mis-attributed per release; deployments
    between snapshots collapse into one window.
12. **Cost forecast** — linear fit over ≤14 days; for the 1–2-day-old apps it's noise
    (days_observed is in the payload but the forecast renders regardless).
13. **"No PII stored"** — `user_hash` is unsalted `sha256(email)[:16]`: pseudonymous and
    dictionary-reversible; legally still personal data. Overstated.
14. **Permission drift** — if one app's ACL fetch fails during a snapshot, its entries
    diff as "removed" next round → spurious drift alerts (fragile, not wrong-by-design).
15. **Alert lifecycle across restarts** — the probe-rule active set is in-memory; alerts
    firing before a monitor restart never emit "resolved" rows.
16. **Journey `within_budget`** — the journey latency budget is applied per step, not to
    the journey total.

## D. Verified real

Compute $ per app (`system.billing.usage` `billing_origin_product='APPS'` +
`usage_metadata.app_name` × `list_prices`, honest NULL for AI $); tokens from the apps'
own `gen_ai.*` spans; requests/errors/latency/routes/logs/traces/error-groups from
`otel_*`; source scan (workspace export → OSV CVEs, bandit, secrets/smells regex,
PyPI/npm freshness, policy.json); agentic review + LLM-judge quality evals over real
MLflow traces; anomaly z-scores; budget burn; audit (`system.access.audit`);
ACL/deployment snapshots; job health (`system.lakeflow`); synthetic journeys (real
routes, real assertions); topology (declared resource bindings); auto-stop and
provisioning actions; telemetry-volume guardrail.

**Net:** the "insight" layers (cost, quality, security, GenAI, governance) are real and
honestly sourced. The **live reliability layer is the weak spot**: everything derived
from `/healthz` probes is proxy telemetry wearing an app-health costume, and everything
"user" is a bot population. #1–#3 are the ones worth fixing before showing this to
anyone as production monitoring.
