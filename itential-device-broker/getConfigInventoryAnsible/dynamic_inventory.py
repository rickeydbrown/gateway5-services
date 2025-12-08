#!/usr/bin/env python3
"""
Dynamic Ansible Inventory Script
Reads JSON from stdin and converts it to Ansible inventory format.

Input format:
{
    "inventory_nodes": [
        {
            "name": "host-name",
            "attributes": {
                "host": "10.0.0.1",
                "username": "admin",
                "password": "password",
                "device_type": "iosxr",
                "port": 22,
                "command": "show running-config"  (optional)
            }
        }
    ]
}

Output: Ansible dynamic inventory JSON format
"""

import json
import sys

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

def read_stdin():
    """Read JSON data from stdin."""
    try:
        data = json.load(sys.stdin)
        return data
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading stdin: {e}", file=sys.stderr)
        sys.exit(1)

def build_inventory(data):
    """
    Convert input data to Ansible dynamic inventory format.

    Returns a dictionary with the structure:
    {
        "_meta": {
            "hostvars": {
                "hostname": { "var": "value", ... }
            }
        },
        "all": {
            "hosts": ["host1", "host2", ...],
            "vars": {}
        }
    }
    """
    inventory = {
        "_meta": {
            "hostvars": {}
        },
        "all": {
            "hosts": [],
            "vars": {}
        }
    }

    # Process inventory nodes
    nodes = data.get("inventory_nodes", [])

    for node in nodes:
        name = node.get("name")
        attributes = node.get("attributes", {})

        if not name:
            print("Warning: Node missing 'name' field, skipping", file=sys.stderr)
            continue

        # Add host to 'all' group
        inventory["all"]["hosts"].append(name)

        # Build host variables
        hostvars = {}

        # Map attributes to Ansible variables
        if 'host' in attributes:
            hostvars['ansible_host'] = attributes['host']

        if 'username' in attributes:
            hostvars['ansible_user'] = attributes['username']

        if 'password' in attributes:
            hostvars['ansible_password'] = attributes['password']

        if 'port' in attributes:
            hostvars['ansible_port'] = attributes['port']

        # Map device_type to ansible_network_os
        device_type = attributes.get('device_type') or attributes.get('ostype')
        if device_type:
            network_os = DEVICE_TYPE_MAP.get(device_type, device_type)
            hostvars['ansible_network_os'] = network_os
            hostvars['ansible_connection'] = 'ansible.netcommon.network_cli'

        # Pass through command if specified
        if 'command' in attributes:
            hostvars['device_command'] = attributes['command']

        # Pass through any options
        if 'options' in attributes:
            hostvars['device_options'] = attributes['options']

        # Add host variables to inventory
        inventory["_meta"]["hostvars"][name] = hostvars

    return inventory

def main():
    # Read from stdin and build inventory
    data = read_stdin()
    inventory = build_inventory(data)
    print(json.dumps(inventory, indent=2))

if __name__ == "__main__":
    main()
