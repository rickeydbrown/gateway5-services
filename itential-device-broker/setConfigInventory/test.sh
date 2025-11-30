#!/bin/bash

# Test script for setConfigInventory service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/itential-device-setconfiginventory.py"

echo "================================"
echo "Testing setConfigInventory"
echo "================================"
echo ""

# Test 1: Simple single change
echo "Test 1: Single configuration change"
echo "-----------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" \
  --config "$(cat $SCRIPT_DIR/test_config_changes.json)"
echo ""
echo "Exit code: $?"
echo ""

# Test 2: Multiple changes
echo "Test 2: Multiple configuration changes"
echo "---------------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" \
  --config "$(cat $SCRIPT_DIR/test_multiple_changes.json)"
echo ""
echo "Exit code: $?"
echo ""

# Test 3: With custom options
echo "Test 3: With custom Netmiko options"
echo "------------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" \
  --config "$(cat $SCRIPT_DIR/test_config_changes.json)" \
  --options '{"global_delay_factor": 4, "timeout": 180}'
echo ""
echo "Exit code: $?"
echo ""

# Test 4: With delay (for testing)
echo "Test 4: With connection delay"
echo "------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" \
  --config "$(cat $SCRIPT_DIR/test_config_changes.json)" \
  -d 2
echo ""
echo "Exit code: $?"
echo ""

echo "================================"
echo "All tests completed!"
echo "================================"
