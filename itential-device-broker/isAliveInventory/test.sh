#!/bin/bash

# Test script for isAliveInventory service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/itential-device-isaliveinventory.py"

echo "================================"
echo "Testing isAliveInventory"
echo "================================"
echo ""

# Test 1: Default command (show version)
echo "Test 1: Default command (show version)"
echo "---------------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT"
echo ""
echo "Exit code: $?"
echo ""

# Test 2: Custom command
echo "Test 2: Custom command"
echo "----------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" -c "show hostname"
echo ""
echo "Exit code: $?"
echo ""

# Test 3: BigIP with default (show sys version)
echo "Test 3: BigIP with default command"
echo "-----------------------------------"
cat "$SCRIPT_DIR/test_input_bigip.json" | "$SCRIPT"
echo ""
echo "Exit code: $?"
echo ""

# Test 4: With custom options
echo "Test 4: With custom Netmiko options"
echo "------------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" \
  --options '{"global_delay_factor": 4, "timeout": 180}'
echo ""
echo "Exit code: $?"
echo ""

# Test 5: With delay (for testing)
echo "Test 5: With connection delay"
echo "------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" -d 2
echo ""
echo "Exit code: $?"
echo ""

echo "================================"
echo "All tests completed!"
echo "================================"
