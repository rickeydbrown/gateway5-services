#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

export PRE_CHECK_RESULT_FILE="$WORKDIR/pre_check.json"
export DOT1X_DETAIL_RESULT_FILE="$WORKDIR/dot1x_detail.json"
export RUNNING_CONFIG_RESULT_FILE="$WORKDIR/running_config.json"

python3 - "$PRE_CHECK_RESULT_FILE" "$DOT1X_DETAIL_RESULT_FILE" "$RUNNING_CONFIG_RESULT_FILE" <<'PYEOF'
import json
import sys

pre_check_path, dot1x_path, running_config_path = sys.argv[1:4]

# Simulate a switch with a few thousand dot1x-enabled interfaces, a couple
# of which are broken - large enough that inlining this through the
# decorator payload would risk hitting gRPC message-size limits.
INTERFACE_COUNT = 3000

json.dump(
    {"checks": [{"name": "reachability", "status": "pass"},
                {"name": "radius_reachable", "status": "pass"}]},
    open(pre_check_path, "w"),
)

sessions = [
    {"interface": f"GigabitEthernet1/0/{i}", "auth_state": "AUTHORIZED"}
    for i in range(1, INTERFACE_COUNT + 1)
]
sessions[41]["auth_state"] = "UNAUTHORIZED"
del sessions[99]  # simulate a missing/no-session interface
json.dump({"sessions": sessions}, open(dot1x_path, "w"))

interfaces = [
    {"name": f"GigabitEthernet1/0/{i}", "dot1x_enabled": True}
    for i in range(1, INTERFACE_COUNT + 1)
]
json.dump({"hostname": "sw-access-42", "interfaces": interfaces}, open(running_config_path, "w"))
PYEOF

echo "=================================================="
echo "Fixture sizes (proving these are 'large data'):"
echo "=================================================="
ls -lh "$WORKDIR"

echo ""
echo "=================================================="
echo "Test 1: Pre-fix behavior - inline argparse values"
echo "=================================================="
./large-data-test.py --target-device sw-access-42 --network-os ios --pre-check-success \
  --pre-check-result-json '{"checks": [{"name": "reachability", "status": "pass"}]}' \
  --dot1x-detail-result-json '{"sessions": [{"interface": "Gi1/0/1", "auth_state": "AUTHORIZED"}]}' \
  --running-config-result-json '{"hostname": "sw-access-42", "interfaces": []}' \
  | grep -E "_source|_size_bytes" || true

echo ""
echo "=================================================="
echo "Test 2: Post-fix behavior - env-var file-backed values, JSON output"
echo "=================================================="
./large-data-test.py --target-device sw-access-42 --network-os ios --pre-check-success || true

echo ""
echo "=================================================="
echo "Test 3: Post-fix behavior - text output"
echo "=================================================="
./large-data-test.py --target-device sw-access-42 --network-os ios --pre-check-success --format text || true

echo ""
echo "=================================================="
echo "Test 4: Neither argparse nor env var set (Gateway 5 failed to stage a file)"
echo "=================================================="
env -u RUNNING_CONFIG_RESULT_FILE ./large-data-test.py --target-device sw-access-42 --network-os ios || true
