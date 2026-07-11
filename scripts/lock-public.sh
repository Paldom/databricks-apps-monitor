#!/usr/bin/env bash
# Regenerates uv.lock and rewrites the Databricks-internal PyPI proxy URLs to their
# public equivalents (identical /packages/<hash> paths ⇒ hashes stay valid), so CI
# on GitHub runners can `uv sync --locked`. Run after any dependency change.
set -euo pipefail
cd "$(dirname "$0")/.."
uv lock "$@"
python3 - <<'PY'
s = open('uv.lock').read()
s = s.replace('https://pypi-proxy.dev.databricks.com/simple/', 'https://pypi.org/simple/')
s = s.replace('https://pypi-proxy.dev.databricks.com/simple', 'https://pypi.org/simple')
s = s.replace('https://pypi-proxy.dev.databricks.com/packages/', 'https://files.pythonhosted.org/packages/')
open('uv.lock', 'w').write(s)
print('uv.lock: proxy refs remaining =', s.count('pypi-proxy'))
PY
