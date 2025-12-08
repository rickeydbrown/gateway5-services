#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "Test 1: Test dynamic inventory script"
echo "=================================================="
cat test_input.json | ./dynamic_inventory.py

echo ""
echo "=================================================="
echo "Test 2: Run playbook with default command"
echo "=================================================="
cat test_input.json | ./run_playbook.sh

echo ""
echo "=================================================="
echo "Test 3: Run playbook with custom command"
echo "=================================================="
cat test_input.json | ./run_playbook.sh -c "show version"
