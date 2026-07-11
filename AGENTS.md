# AGENTS.md

Databricks Apps monitoring toolkit. Two things live here:

1. A DABs bundle — `app/` (FastAPI monitor app), `jobs/` (serverless jobs),
   `example-apps/` (demo fleet DAB), `resources/` (bundle yml), rooted at
   `databricks.yml`.
2. A published Python package — `src/monitor_middleware`, shipped as the
   `monitor-middleware` wheel. Only `src/` ships in the wheel; `app/` and
   `jobs/` are Databricks deployment payloads, NOT package code.

## Environment

- uv-managed. Run everything via `uv run <cmd>` — never pip, never poetry,
  never bare `python`.
- `uv.lock` is orchestrator-owned: do not run `uv add`, `uv lock`, or
  `uv sync`, and never edit `uv.lock` or dependency lists by hand. State
  needed dependencies and let the orchestrator add them.

## Quality gate

Pinned toolchain: ruff==0.15.20, mypy==2.1.0. All four must pass before
calling any task done (the Stop hook enforces this):

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy` (strict, scoped to `src/` — `app/` and `jobs/` run on
  Databricks serverless with pyspark/databricks-sdk at runtime and stay out
  of mypy scope)
- `uv run pytest --cov -q` (85% branch-coverage floor via `fail_under`)

Never weaken a gate to pass it: no lowering `fail_under`, no skipping or
deleting failing tests, no `|| true`, no `--no-verify`.

## Deploying

Instance values (UC catalog, admin emails, Genie space id, demo `monitor_url`,
workspace list) are NOT in the repo — they live in an uncommitted `.env` as
`BUNDLE_VAR_*` entries (template: `.env.example`; DABs reads that prefix as
bundle variables). Always deploy through `scripts/deploy.sh
[monitor|demos|all] -t <target> -p <profile>`, which sources `.env` and
refuses placeholder catalogs. Never run a bare `databricks bundle deploy`:
without `.env` the catalog falls back to `main` and DABs will plan a
**destructive schema recreate** (this happened once — see BUILDLOG).

App env in bundle YAML uses snake_case `value_from:` (camelCase `valueFrom`
is silently ignored by DABs and strips the value — apps then fail to start
with "Must specify environment variable source").

## Boundaries

- Never `git commit` or `git push` without an explicit user request.
- Telemetry/platform gotchas (OTel sidecar port, `/healthz` interception,
  MLflow dual export, billing tables) live in `docs/` — read the relevant
  doc before touching instrumentation.
