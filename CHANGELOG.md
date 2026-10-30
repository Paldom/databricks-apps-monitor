# Changelog

All notable changes to the `monitor-middleware` package are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning:
[SemVer](https://semver.org/), static `project.version` bumped with
`uv version --bump patch|minor|major` (which also refreshes `uv.lock`).

## [Unreleased]

## [0.2.0] - 2026-10-29

### Added

- SDK v2 on the same one-file middleware: `llm_call`, `track`, `set_step`,
  `trace_sql`, `warehouse_ready`, `serving_ready`, and `BudgetExceeded`.
- Span redaction (query strings, `url.query`, `process.command_line` /
  `process.command_args`, `MONITOR_REDACT_EXTRA`) and a log filter that scrubs
  emails, bearer tokens, `dapi` PATs, and JWTs after formatting.
- `GET /monitor/health` (concurrent checks, 2s timeout, 30s cache) and a startup
  log (`MONITOR_TEAM`, `MONITOR_COST_CENTER`, package inventory).
- `POST /monitor/event` and opt-in browser RUM (`/monitor/rum.js`, `/monitor/rum`).
- Keyed user hash (`MONITOR_HASH_KEY` → HMAC-SHA256; unset stays plain SHA-256).
- `exception.fingerprint` on the request span, plus `monitor.error_summary` when
  that span was not recorded.
- Wheel entry point `OTEL_TRACES_SAMPLER=monitor_parentbased`: parent-based ratio
  sampling that always keeps `monitor.error_summary`.
- Histogram `gen_ai.client.token.usage` from the last `llm_call` usage (trace
  sampling does not drop it). Token budget: `MONITOR_URL` `/api/policy/{app}`,
  fail-open, `BudgetExceeded` on `{"throttle": "block"}`.

### Changed

- SDK review closes late span/exception/log-extra redaction gaps, bounds streamed
  ingress and RUM bucket storage, checks complete origins, and refuses policy redirects.
- Health probes leave the request loop responsive and reuse timed-out workers;
  serving checks use the endpoint's actual readiness state.
- The agent demo uses one `llm_call` per provider invocation, retains response usage
  totals and gateway tags, and emits named journey steps and business events.
- `user.id_hash` is HMAC-SHA256 (16 hex chars) when `MONITOR_HASH_KEY` is set,
  else SHA-256[:16].
- Log lines are formatted before the 60 KB cap, so a huge `%s` argument is what
  gets truncated.
- Feedback bodies over 4 KB are accepted as an empty payload (`{"ok": true}`);
  comments are scrubbed. `POST /monitor/event` and `POST /monitor/rum` over their
  caps return 413.
- Package version is 0.2.0. `opentelemetry-sdk` is a dev dependency only; the
  published module still imports the SDK lazily.

## [0.1.0]

### Added

- `monitor_middleware.install()` — golden-envelope OpenTelemetry middleware for
  Databricks Apps: stamps every server span with `app.client_request_id`,
  `session.id`, `user.id_hash`, `app.name`, `app.version` and `journey.step`,
  echoes `x-request-id`, and manages the `monitor_session` cookie.
- `POST /monitor/feedback` route: user feedback (rating 1–5, comment) logged as
  a structured JSON event into the OTel log pipeline.
- Log-line truncation filter keeping records under the telemetry export's 1 MB
  drop threshold.
- `py.typed` — the package ships its type annotations (strict mypy clean).
