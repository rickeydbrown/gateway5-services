#!/bin/bash
"""
Wrapper script to run Ansible playbook with dynamic inventory from stdin

Usage:
  cat input.json | ./run_playbook.sh
  cat input.json | ./run_playbook.sh -c "show version"
"""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Save stdin to temporary file
TEMP_INPUT=$(mktemp)
cat > "$TEMP_INPUT"

# Parse command line arguments
COMMAND=""
EXTRA_VARS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--command)
            COMMAND="$2"
            shift 2
            ;;
        --options)
            OPTIONS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build extra vars
if [ -n "$COMMAND" ]; then
    EXTRA_VARS="-e device_command='$COMMAND'"
fi

# Run ansible-playbook with dynamic inventory
cat "$TEMP_INPUT" | ansible-playbook \
    -i ./dynamic_inventory.py \
    get_config.yml \
    $EXTRA_VARS

# Clean up
rm -f "$TEMP_INPUT"
