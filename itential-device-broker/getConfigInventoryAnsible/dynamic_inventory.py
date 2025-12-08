#!/usr/bin/env python3
"""
Dynamic Ansible Inventory Script
Reads JSON from stdin and converts it to Ansible inventory format.
"""

import json
import sys

def main():
    # Read raw stdin
    try:
        stdin_data = sys.stdin.read()
        print(f"DEBUG: Received stdin data: {stdin_data}", file=sys.stderr)

        # Try to parse as JSON
        if stdin_data:
            data = json.loads(stdin_data)
            print(f"DEBUG: Parsed JSON: {json.dumps(data, indent=2)}", file=sys.stderr)
        else:
            print("DEBUG: No stdin data received", file=sys.stderr)
            data = None
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON decode error - {e}", file=sys.stderr)
        data = None
    except Exception as e:
        print(f"DEBUG: Error reading stdin - {e}", file=sys.stderr)
        data = None

    # Return minimal empty inventory
    inventory = {
        "_meta": {
            "hostvars": {}
        },
        "all": {
            "hosts": [],
            "vars": {}
        }
    }

    print(json.dumps(inventory, indent=2))

if __name__ == "__main__":
    main()
