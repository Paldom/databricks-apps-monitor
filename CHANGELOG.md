# Changelog

All notable changes to the `monitor-middleware` package are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning:
[SemVer](https://semver.org/), static `project.version` bumped with
`uv version --bump patch|minor|major` (which also refreshes `uv.lock`).

## [Unreleased]

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
