#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Save stdin to cache file for dynamic inventory
CACHE_FILE="/tmp/ansible_inventory_cache.json"
cat > "$CACHE_FILE"

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
ansible-playbook \
    -i ./dynamic_inventory.py \
    get_config.yml \
    $EXTRA_VARS

# Clean up
rm -f "$CACHE_FILE"
