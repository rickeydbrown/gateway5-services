#!/bin/bash

# Test script for runCommandInventory service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$SCRIPT_DIR/itential-device-runcommandinventory.py"

echo "================================"
echo "Testing runCommandInventory"
echo "================================"
echo ""

# Test 1: Simple command
echo "Test 1: Show version"
echo "-----------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" -c "show version"
echo ""
echo "Exit code: $?"
echo ""

# Test 2: Different command
echo "Test 2: Show IP interface brief"
echo "--------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" -c "show ip interface brief"
echo ""
echo "Exit code: $?"
echo ""

# Test 3: With custom options
echo "Test 3: With custom Netmiko options"
echo "------------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" \
  -c "show running-config" \
  --options '{"global_delay_factor": 4, "timeout": 180}'
echo ""
echo "Exit code: $?"
echo ""

# Test 4: With delay (for testing)
echo "Test 4: With connection delay"
echo "------------------------------"
cat "$SCRIPT_DIR/test_input.json" | "$SCRIPT" \
  -c "show hostname" \
  -d 2
echo ""
echo "Exit code: $?"
echo ""

echo "================================"
echo "All tests completed!"
echo "================================"
