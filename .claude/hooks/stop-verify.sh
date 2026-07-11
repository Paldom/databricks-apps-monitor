#!/usr/bin/env bash
# Stop hook — refuse to end the turn while the repo quality gate fails.
# Exit 2 on Stop means "keep working"; the harness force-overrides after 8
# consecutive blocks. The stop_hook_active guard below is MANDATORY — without
# it this hook loops the first time the agent cannot immediately fix a failure.
set -u

command -v jq >/dev/null 2>&1 || exit 0
INPUT=$(cat)
ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null) || exit 0
[ "$ACTIVE" = "true" ] && exit 0   # already re-running because of us — let go

cd "${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}" || exit 0

run() {
  OUT=$("$@" 2>&1) || {
    echo "Quality gate failed: $*" >&2
    echo "Fix before finishing:" >&2
    echo "$OUT" | tail -30 >&2
    exit 2
  }
}

run uv run ruff check .
run uv run ruff format --check .
run uv run mypy
run uv run pytest --cov -q

exit 0
