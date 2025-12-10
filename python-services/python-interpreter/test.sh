#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "Test 1: Simple print statement"
echo "=================================================="
./python-interpreter.py --script 'print("Hello, World!")'

echo ""
echo "=================================================="
echo "Test 2: Math calculation"
echo "=================================================="
./python-interpreter.py --script "result = 5 + 3 * 2; print(f'Result: {result}')"

echo ""
echo "=================================================="
echo "Test 3: JSON output"
echo "=================================================="
./python-interpreter.py --script "import json; print(json.dumps({'status': 'success', 'value': 42}))"

echo ""
echo "=================================================="
echo "Test 4: Multiple lines with loop"
echo "=================================================="
./python-interpreter.py --script "
for i in range(3):
    print(f'Iteration {i}')
"

echo ""
echo "=================================================="
echo "Test 5: Error handling (divide by zero)"
echo "=================================================="
./python-interpreter.py --script "result = 10 / 0"

echo ""
echo "=================================================="
echo "Test 6: JSON format output (success)"
echo "=================================================="
./python-interpreter.py --script 'print("Success!")' --format json

echo ""
echo "=================================================="
echo "Test 7: JSON format output (error)"
echo "=================================================="
./python-interpreter.py --script "raise ValueError('Test error')" --format json

echo ""
echo "=================================================="
echo "Test 8: Import and use library"
echo "=================================================="
./python-interpreter.py --script "
import sys
print(f'Python version: {sys.version_info.major}.{sys.version_info.minor}')
"
