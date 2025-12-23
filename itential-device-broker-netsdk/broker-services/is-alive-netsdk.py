#!/usr/bin/env python3
"""
Check if network devices are alive using netsdk.

This script follows the same pattern as itential-device-isaliveinventory.py
but uses the netsdk library instead of directly using netmiko.

Requirements:
- pip install -r requirements.txt

Usage:
    # From stdin
    cat inventory.json | python3 is-alive-netsdk.py

    # Or read from file
    python3 is-alive-netsdk.py < inventory.json

    # From file argument
    python3 is-alive-netsdk.py -f inventory.json

    # With custom command
    cat inventory.json | python3 is-alive-netsdk.py -c "show version"

    # With different log level
    cat inventory.json | python3 is-alive-netsdk.py --log-level DEBUG
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path


def setup_netsdk_import() -> Path:
    """
    Configure Python's import path to include the local netsdk package.

    Returns:
        Path: The resolved path to the netsdk package directory

    Raises:
        FileNotFoundError: If the netsdk package doesn't exist
        ImportError: If the netsdk package structure is invalid
    """
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()

    # The netsdk package is in the same directory as this script
    netsdk_package = script_dir / "netsdk"

    # Verify netsdk package exists
    if not netsdk_package.exists() or not (netsdk_package / "__init__.py").exists():
        msg = f"netsdk package not found at: {netsdk_package}"
        raise ImportError(msg)

    # Add script directory to Python path if not already present
    script_dir_str = str(script_dir)
    if script_dir_str not in sys.path:
        sys.path.insert(0, script_dir_str)

    return netsdk_package




async def main():
    """
    Main function to check if network devices are alive.

    Reads inventory from stdin and checks connectivity.
    """
    parser = argparse.ArgumentParser(
        description='Check if network devices are alive using netsdk (reads inventory from stdin)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    # Check device status
    cat inventory.json | python3 is-alive-netsdk.py

    # With custom command for alive check
    cat inventory.json | python3 is-alive-netsdk.py -c "show version"

    # With different log level
    cat inventory.json | python3 is-alive-netsdk.py --log-level DEBUG

Input format (stdin):
{
  "inventory_nodes": [
    {
      "name": "device-name",
      "attributes": {
        "itential_host": "10.0.0.1",
        "itential_user": "admin",
        "itential_password": "password",
        "itential_platform": "cisco_iosxr",
        "itential_port": 22,
        "itential_driver": "scrapli"
      }
    }
  ]
}

Output format (stdout):
- Single device: true or false
- Multiple devices: JSON array of results with name, alive, and host fields
'''
    )

    parser.add_argument('-c', '--command',
                       help='Custom command to run for alive check (uses default if not provided)')
    parser.add_argument('--log-level', choices=['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level (default: INFO)')
    parser.add_argument('-f', '--file',
                       help='Read inventory from file instead of stdin')

    args = parser.parse_args()

    # Setup the import path
    setup_netsdk_import()

    # Import netsdk after setting up the path
    import netsdk

    # Initialize logging
    netsdk.logging.initialize()
    log_level = getattr(netsdk.logging, args.log_level)
    netsdk.logging.set_level(log_level)

    try:
        # Read inventory from file or stdin
        if args.file:
            with open(args.file, 'r') as f:
                inventory_data = json.load(f)
        else:
            stdin_data = sys.stdin.read()
            if not stdin_data.strip():
                print("Error: No input provided on stdin", file=sys.stderr)
                print("Usage: cat inventory.json | python3 is-alive-netsdk.py", file=sys.stderr)
                sys.exit(1)
            inventory_data = json.loads(stdin_data)

        # Validate inventory structure
        if "inventory_nodes" not in inventory_data or not inventory_data["inventory_nodes"]:
            print("Error: No inventory_nodes found in input", file=sys.stderr)
            sys.exit(1)

        # Convert back to JSON string for netsdk.broker.load_inventory
        inventory_json_str = json.dumps(inventory_data)
        inventory = netsdk.broker.load_inventory(inventory_json_str)

        # Check alive status
        results = await netsdk.broker.is_alive(inventory)

        # Convert results to list
        results_list = json.loads(results.model_dump_json())

        # For single device, output just true or false (matching itential-device-isaliveinventory behavior)
        if len(inventory_data["inventory_nodes"]) == 1:
            result = results_list[0]
            print(json.dumps(result['alive']), end='')
            sys.exit(0 if result['alive'] else 1)
        else:
            # For multiple devices, output results as JSON
            print(json.dumps(results_list), end='')
            # Exit with error code if any device failed
            if any(not r.get("alive", False) for r in results_list):
                sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required field in inventory: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
