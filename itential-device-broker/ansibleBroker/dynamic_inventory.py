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
    'cisco_xr': 'iosxr',  # Map cisco_xr to iosxr for Ansible
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

        # Handle host - priority: ansible_host > itential_host > host
        if 'ansible_host' in attributes:
            hostvars['ansible_host'] = attributes['ansible_host']
        elif 'itential_host' in attributes:
            hostvars['ansible_host'] = attributes['itential_host']
        elif 'host' in attributes:
            hostvars['ansible_host'] = attributes['host']

        # Handle username - priority: ansible_user > itential_user > username
        if 'ansible_user' in attributes:
            hostvars['ansible_user'] = attributes['ansible_user']
        elif 'itential_user' in attributes:
            hostvars['ansible_user'] = attributes['itential_user']
        elif 'username' in attributes:
            hostvars['ansible_user'] = attributes['username']

        # Handle password - priority: ansible_password > itential_password > password
        if 'ansible_password' in attributes:
            hostvars['ansible_password'] = attributes['ansible_password']
        elif 'itential_password' in attributes:
            hostvars['ansible_password'] = attributes['itential_password']
        elif 'password' in attributes:
            hostvars['ansible_password'] = attributes['password']

        # Handle port - priority: ansible_port > itential_port > port
        if 'ansible_port' in attributes:
            hostvars['ansible_port'] = attributes['ansible_port']
        elif 'itential_port' in attributes:
            hostvars['ansible_port'] = attributes['itential_port']
        elif 'port' in attributes:
            hostvars['ansible_port'] = attributes['port']

        # Handle device type - priority: ansible_network_os > itential_platform > device_type > ostype
        if 'ansible_network_os' in attributes:
            hostvars['ansible_network_os'] = attributes['ansible_network_os']
        else:
            device_type = (attributes.get('itential_platform') or
                          attributes.get('device_type') or
                          attributes.get('ostype'))
            if device_type:
                network_os = DEVICE_TYPE_MAP.get(device_type, device_type)
                hostvars['ansible_network_os'] = network_os

        # Handle connection type - priority: ansible_connection > default
        if 'ansible_connection' in attributes:
            hostvars['ansible_connection'] = attributes['ansible_connection']
        elif 'ansible_network_os' in hostvars:
            hostvars['ansible_connection'] = 'ansible.netcommon.network_cli'

        # Handle driver
        if 'itential_driver' in attributes:
            hostvars['device_driver'] = attributes['itential_driver']

        # Handle command
        if 'command' in attributes:
            hostvars['device_command'] = attributes['command']

        # Handle options
        if 'options' in attributes:
            hostvars['device_options'] = attributes['options']

        inventory["_meta"]["hostvars"][name] = hostvars

        # Process tags to create Ansible groups
        tags = node.get("tags", [])
        for tag in tags:
            if tag not in inventory:
                inventory[tag] = {
                    "hosts": [],
                    "vars": {}
                }
            inventory[tag]["hosts"].append(name)

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
