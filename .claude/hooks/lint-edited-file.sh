#!/usr/bin/env bash
# PostToolUse hook (matcher: Edit|Write) — lint/format ONLY the file just
# edited. Exit 2 cannot undo the edit (it already happened); it feeds the
# failure back into the agent's context so it self-corrects immediately.
# Keep this sub-second: it runs synchronously on every matching tool call.
#
# Scope: Python files under the Python surfaces only (src/ tests/ app/ jobs/
# sdk/ example-apps/ templates/). No-ops cleanly on everything else,
# including app/static/, dashboards/, observ/, walkthrough/.
set -u

command -v jq >/dev/null 2>&1 || exit 0
FILE_PATH=$(jq -r '.tool_input.file_path // empty' 2>/dev/null) || exit 0
[ -n "$FILE_PATH" ] && [ -f "$FILE_PATH" ] || exit 0   # tool may have errored

case "$FILE_PATH" in
  *.py) ;;
  *) exit 0 ;;                                    # non-Python edit: no-op
esac

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
case "$FILE_PATH" in
  "$ROOT"/*) REL="${FILE_PATH#"$ROOT"/}" ;;
  *) exit 0 ;;                                    # outside the repo: no-op
esac

case "$REL" in
  app/static/*|dashboards/*|observ/*|walkthrough/*) exit 0 ;;   # excluded
esac
case "$REL" in
  src/*|tests/*|app/*|jobs/*|sdk/*|example-apps/*|templates/*) ;;
  *) exit 0 ;;                                    # not a Python surface
esac

# --fix + format: auto-repair what is mechanical, report what is not.
OUT=$(uv run ruff check --fix "$FILE_PATH" 2>&1) || {
  echo "ruff found problems in $FILE_PATH it could not auto-fix:" >&2
  echo "$OUT" >&2
  exit 2
}
uv run ruff format "$FILE_PATH" >/dev/null 2>&1 || true

exit 0
