#!/usr/bin/env python3
"""
Dynamic Ansible Inventory Script
Reads JSON from stdin (if piped) or cache file and converts it to Ansible inventory format.

Usage:
    # From stdin
    cat inventory.json | python3 dynamic_inventory.py --list

    # From cache file
    python3 dynamic_inventory.py --list

    # Get specific host variables
    cat inventory.json | python3 dynamic_inventory.py --host hostname
"""

import json
import sys
import os
import argparse

# Cache file location
CACHE_FILE = '/tmp/ansible_inventory_cache.json'

# Map device types to Ansible network_os
DEVICE_TYPE_MAP = {
    'aruba': 'arubaos',
    'asa': 'asa',
    'bigip': 'bigip',
    'eos': 'eos',
    'ios': 'ios',
    'iosxr': 'iosxr',
    'junos': 'junos',
    'nxos': 'nxos',
    'sros': 'sros'
}

def build_inventory_from_data(data):
    """Build Ansible inventory from input data."""
    inventory = {
        "_meta": {
            "hostvars": {}
        },
        "all": {
            "hosts": [],
            "vars": {}
        }
    }

    if not data:
        return inventory

    nodes = data.get("inventory_nodes", [])

    for node in nodes:
        name = node.get("name")
        attributes = node.get("attributes", {})

        if not name:
            continue

        # Add host to 'all' group
        inventory["all"]["hosts"].append(name)

        # Build host variables
        hostvars = {}

        if 'itential_host' in attributes:
            hostvars['ansible_host'] = attributes['host']

        if 'itential_user' in attributes:
            hostvars['ansible_user'] = attributes['username']

        if 'itential_password' in attributes:
            hostvars['ansible_password'] = attributes['password']

        if 'itential_port' in attributes:
            hostvars['ansible_port'] = attributes['port']

        device_type = attributes.get('device_type') or attributes.get('itential_platform')
        if device_type:
            network_os = DEVICE_TYPE_MAP.get(device_type, device_type)
            hostvars['ansible_network_os'] = network_os
            hostvars['ansible_connection'] = 'ansible.netcommon.network_cli'

        if 'command' in attributes:
            hostvars['device_command'] = attributes['command']

        if 'options' in attributes:
            hostvars['device_options'] = attributes['options']

        inventory["_meta"]["hostvars"][name] = hostvars

    return inventory

def main():
    parser = argparse.ArgumentParser(description='Ansible Dynamic Inventory')
    parser.add_argument('--list', action='store_true', help='List all hosts')
    parser.add_argument('--host', help='Get variables for a specific host')
    args = parser.parse_args()

    # Try to load from stdin first (if data is piped in)
    data = None
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read()
            if stdin_data.strip():
                data = json.loads(stdin_data)
        except Exception as e:
            print(f"Warning: Could not parse stdin - {e}", file=sys.stderr)

    # Fall back to cache file if stdin was empty or failed
    if data is None and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache - {e}", file=sys.stderr)

    # Build inventory
    inventory = build_inventory_from_data(data)

    if args.list:
        print(json.dumps(inventory, indent=2))
    elif args.host:
        hostvars = inventory.get("_meta", {}).get("hostvars", {}).get(args.host, {})
        print(json.dumps(hostvars, indent=2))
    else:
        # Default: return list
        print(json.dumps(inventory, indent=2))

if __name__ == "__main__":
    main()
