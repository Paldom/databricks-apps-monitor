#!/bin/sh
# healthy/ is the canonical demo source; flaky/ and slow/ are copies
# (DABs forbids two apps sharing one source_code_path).
cd "$(dirname "$0")"
for d in flaky slow; do cp healthy/main.py healthy/requirements.txt healthy/monitor_middleware.py "$d/"; done
cp ../sdk/monitor_middleware.py healthy/ && cp ../sdk/monitor_middleware.py flaky/ && cp ../sdk/monitor_middleware.py slow/ && cp ../sdk/monitor_middleware.py vuln/ && cp ../sdk/monitor_middleware.py agent/
echo synced
