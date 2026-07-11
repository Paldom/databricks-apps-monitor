#!/usr/bin/env bash
# Deploys the toolkit with instance values from .env (never committed).
# Usage: scripts/deploy.sh [monitor|demos|all] [-p <profile>] [-t <target>]
set -euo pipefail
cd "$(dirname "$0")/.."
WHAT="${1:-monitor}"; shift || true
[ -f .env ] || { echo "missing .env — cp .env.example .env and fill it in"; exit 1; }
set -a; source .env; set +a
: "${BUNDLE_VAR_catalog:?set BUNDLE_VAR_catalog in .env}"
case "$BUNDLE_VAR_catalog" in main|unset|your_uc_catalog)
  echo "refusing to deploy with catalog '$BUNDLE_VAR_catalog' — set the real catalog in .env"; exit 1;; esac
run() { echo "+ $*"; "$@"; }
if [ "$WHAT" = "monitor" ] || [ "$WHAT" = "all" ]; then
  run databricks bundle deploy "$@"
  run databricks bundle run monitor "$@"
fi
if [ "$WHAT" = "demos" ] || [ "$WHAT" = "all" ]; then
  (cd example-apps && run databricks bundle deploy "$@")
fi
