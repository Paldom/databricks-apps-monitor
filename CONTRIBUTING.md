# Contributing

## Setup

Everything is uv-managed — never `pip install` into the project:

```bash
uv sync                      # env from the committed uv.lock
uv run pre-commit install    # local hooks (same pinned revs as CI)
```

## Quality gate

The same four commands run locally, in the pre-commit/CI mirror, in `ci.yml`,
and in the agent Stop hook:

```bash
uv run ruff check .           # lint  (ruff 0.15.20, pinned)
uv run ruff format --check .  # format
uv run mypy                   # strict typing on src/ (mypy 2.1.0, pinned)
uv run pytest --cov -q        # tests + 85% branch-coverage floor
```

Notes:

- `app/`, `jobs/`, `example-apps/` are Databricks serverless deployment payloads —
  linted and formatted, but outside the strict-mypy and coverage scope.
- The middleware ships twice: `src/monitor_middleware/` (package) and
  `sdk/monitor_middleware.py` (+ demo/template copies). A test fails if they drift;
  after editing the package run `cp src/monitor_middleware/__init__.py sdk/monitor_middleware.py`
  and `example-apps/sync-demos.sh`.
- Deploy-test bundle changes with `databricks bundle validate -t dev -p <profile>`.

## PRs and issues

- Bugs and feature requests go through [GitHub issues](https://github.com/Paldom/databricks-apps-monitor/issues);
  usage questions → [SUPPORT.md](SUPPORT.md), vulnerabilities → [SECURITY.md](SECURITY.md).
- For anything bigger than a small fix, open an issue first so we agree on the
  approach before you write code.
- Branch from `main`, keep PRs focused, make the quality gate above pass. No
  CLA/DCO sign-off — contributions are accepted under the [MIT license](LICENSE).
- Review is by [@Paldom](https://github.com/Paldom) (solo maintainer), best effort.
- Everyone participating is expected to follow the
  [code of conduct](CODE_OF_CONDUCT.md).

## Releasing

Static versioning; `CHANGELOG.md` follows Keep a Changelog:

```bash
uv version --bump minor       # bumps pyproject.toml AND uv.lock
# roll CHANGELOG "Unreleased" into the new version, commit, then:
git tag -a "v$(uv version --short)" -m "v$(uv version --short)" && git push origin main --tags
```

The tag triggers `publish.yml` (test → build → gated OIDC publish to PyPI).
