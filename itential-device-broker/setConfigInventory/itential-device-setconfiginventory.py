#!/usr/bin/env python3

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


DEVICE_TYPES = {
    'aruba': 'aruba_os',
    'asa': 'cisco_asa',
    'bigip': 'f5_ltm',
    'eos': 'arista_eos',
    'ios': 'cisco_ios',
    'iosxr': 'cisco_xr',
    'junos': 'juniper_junos',
    'nxos': 'cisco_nxos',
    'sros': 'nokia_sros'
}

# Default connection parameters for reliability
DEFAULT_CONNECTION_PARAMS = {
    "conn_timeout": 30,
    "auth_timeout": 30,
    "banner_timeout": 30,
    "timeout": 120,
    "global_delay_factor": 2,
    "fast_cli": False,
}


def build_config_commands(config_changes, device_type):
    """
    Build configuration commands from the config changes array.

    Three scenarios:
    1. Add new config: parents + new (old empty) → Just add new
    2. Modify config: parents + old + new (both non-empty) → Just add new (overwrites old)
    3. Delete config: parents + old, new empty → Remove old with 'no' (or 'delete' for Junos)

    Args:
        config_changes: List of config change objects with parents, old, new
        device_type: Device type for vendor-specific command formatting

    Returns:
        List of command strings to send to device
    """
    commands = []

    # Determine if this is a Junos device (uses 'set' and 'delete' commands)
    is_junos = device_type in ('junos', 'juniper_junos')

    for change in config_changes:
        parents = change.get('parents', [])
        old_value = change.get('old', '')
        new_value = change.get('new', '')

        if is_junos:
            # Junos uses 'set' and 'delete' with full path in single command
            parent_path = ' '.join(parents) if parents else ''

            # If new exists, just set it (add or modify - overwrites old)
            if new_value:
                full_path = f"{parent_path} {new_value}".strip()
                # Only add 'set' prefix if not already present
                if not full_path.startswith('set '):
                    commands.append(f"set {full_path}")
                else:
                    commands.append(full_path)
            # If only old exists (delete scenario), delete it
            elif old_value:
                full_path = f"{parent_path} {old_value}".strip()
                # Only add 'delete' prefix if not already present
                if not full_path.startswith('delete '):
                    commands.append(f"delete {full_path}")
                else:
                    commands.append(full_path)
        else:
            # Cisco-style devices: Enter parent context, use 'no' for deletions only
            # Netmiko's send_config_set handles entering/exiting config mode automatically

            # Enter parent context(s) only if parents exist
            for parent in parents:
                commands.append(parent)

            # If new exists, just add it (add or modify - overwrites old)
            if new_value:
                commands.append(new_value)
            # If only old exists (delete scenario), remove it with 'no' prefix
            elif old_value:
                commands.append(f"no {old_value}")

    return commands


def set_device_config(device_name, attributes, config_changes, options=None, delay=0):
    """
    Apply configuration changes to a single device.

    Args:
        device_name: Name of the device
        attributes: Dictionary containing device connection parameters
        config_changes: List of configuration changes to apply
        options: Optional connection/session parameters to override defaults
        delay: Delay in seconds before connecting (for testing same device)

    Returns:
        Dictionary with device name, success status, changes applied, and output or error
    """
    # TESTING ONLY: Add delay to avoid hitting same device too quickly
    # TODO: Remove delay parameter in production
    if delay > 0:
        time.sleep(delay)

    try:
        # Extract parameters from attributes
        host = attributes.get('host')
        username = attributes.get('username')
        password = attributes.get('password')
        device_type = attributes.get('device_type') or attributes.get('ostype')
        port = attributes.get('port', 22)
        secret = attributes.get('secret')

        # Validate required parameters
        if not all([host, username, password, device_type]):
            return {
                'name': device_name,
                'success': False,
                'error': 'Missing required parameters (host, username, password, device_type/ostype)'
            }

        # Use mapped device type if available, otherwise use incoming device_type directly
        netmiko_device_type = DEVICE_TYPES.get(device_type, device_type)

        # Build device connection dictionary with defaults
        device = {
            'device_type': netmiko_device_type,
            'host': host,
            'username': username,
            'password': password,
            'port': port,
        }

        # Apply default connection parameters
        device.update(DEFAULT_CONNECTION_PARAMS)

        # Priority 1: Global options from command line
        if options:
            device.update(options)

        # Priority 2: Device-level options from attributes (highest priority)
        device_options = attributes.get('options', {})
        if device_options:
            device.update(device_options)

        # Handle secret separately (could come from attributes or options)
        if secret:
            device['secret'] = secret

        # Build configuration commands (pass netmiko_device_type for vendor-specific formatting)
        commands = build_config_commands(config_changes, netmiko_device_type)

        if not commands:
            return {
                'name': device_name,
                'success': False,
                'error': 'No configuration commands to execute'
            }

        with ConnectHandler(**device) as connection:
            # Enable privileged mode if needed
            if secret and netmiko_device_type in ['cisco_ios', 'cisco_nxos', 'cisco_asa']:
                connection.enable()

            # Send configuration commands
            output = connection.send_config_set(commands)

            # Manually commit for devices that require it
            if netmiko_device_type in ['cisco_xr', 'juniper_junos']:
                output += "\n" + connection.commit()

            # Build result with applied changes
            results = []
            for change in config_changes:
                results.append({
                    'result': True,
                    'parents': change.get('parents', []),
                    'old': change.get('old', ''),
                    'new': change.get('new', '')
                })

            return {
                'name': device_name,
                'success': True,
                'host': host,
                'changes': results,
                'output': output
            }

    except NetmikoTimeoutException:
        return {
            'name': device_name,
            'success': False,
            'error': f"Timeout connecting to {host}:{port}"
        }
    except NetmikoAuthenticationException:
        return {
            'name': device_name,
            'success': False,
            'error': f"Authentication failed for {host}"
        }
    except Exception as e:
        return {
            'name': device_name,
            'success': False,
            'error': f"Error connecting to {host}: {str(e)}"
        }


def process_devices(devices, config_changes, options=None, max_workers=10, delay=0):
    """
    Process multiple devices in parallel.

    Args:
        devices: List of device dictionaries with 'name' and 'attributes'
        config_changes: List of configuration changes to apply
        options: Optional connection parameters
        max_workers: Maximum number of parallel connections
        delay: Delay in seconds between connection attempts (for testing)

    Returns:
        List of results for all devices
    """
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks with staggered delays
        future_to_device = {}
        for i, device in enumerate(devices):
            # Apply incremental delay for testing multiple connections to same device
            device_delay = delay * i if delay > 0 else 0
            future = executor.submit(
                set_device_config,
                device['name'],
                device['attributes'],
                config_changes,
                options,
                device_delay
            )
            future_to_device[future] = device['name']

        # Collect results as they complete
        for future in as_completed(future_to_device):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                device_name = future_to_device[future]
                results.append({
                    'name': device_name,
                    'success': False,
                    'error': f"Unexpected error: {str(e)}"
                })

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Apply configuration changes to multiple devices from inventory (stdin)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Supported device types:
{', '.join(DEVICE_TYPES.keys())}

Config changes format (--config):
[
  {{
    "parents": ["interface Loopback 100"],
    "old": "",
    "new": "description Test Loopback"
  }},
  {{
    "parents": ["interface int2"],
    "old": "description Old",
    "new": ""
  }}
]

Options format (--options):
{{
  "session_log": "netmiko_session.log",
  "secret": "enable_secret",
  "global_delay_factor": 4,
  "timeout": 180,
  "verbose": true
}}

Input format (stdin):
{{
  "inventory_nodes": [
    {{
      "name": "device-name",
      "attributes": {{
        "host": "10.0.0.1",
        "username": "admin",
        "password": "password",
        "device_type": "iosxr",
        "port": 22
      }}
    }}
  ]
}}
'''
    )

    parser.add_argument('--config', required=True,
                       help='JSON array of configuration changes to apply')
    parser.add_argument('--options',
                       help='JSON object with optional Netmiko connection parameters')
    parser.add_argument('-w', '--workers', type=int, default=10,
                       help='Maximum number of parallel connections (default: 10)')
    parser.add_argument('-d', '--delay', type=float, default=0,
                       help='TESTING ONLY: Delay in seconds between connection attempts (default: 0, remove in production)')

    args = parser.parse_args()

    try:
        # Parse config changes
        config_changes = json.loads(args.config)
        if not isinstance(config_changes, list):
            print("Error: --config must be a JSON array", file=sys.stderr)
            sys.exit(1)

        # Parse options if provided
        options = None
        if args.options:
            options = json.loads(args.options)
            if not isinstance(options, dict):
                print("Error: --options must be a JSON object", file=sys.stderr)
                sys.exit(1)

        # Read device inventory from stdin
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            print("Error: No input provided on stdin", file=sys.stderr)
            sys.exit(1)

        input_data = json.loads(stdin_data)

        # Handle both array format and object with "inventory_nodes" key
        if isinstance(input_data, list):
            devices = input_data
        elif isinstance(input_data, dict) and 'inventory_nodes' in input_data:
            devices = input_data['inventory_nodes']
        else:
            print("Error: Input must be a JSON array of devices or an object with an 'inventory_nodes' key", file=sys.stderr)
            sys.exit(1)

        if not isinstance(devices, list):
            print("Error: Devices must be a JSON array", file=sys.stderr)
            sys.exit(1)

        if len(devices) == 0:
            print("Error: Device list is empty", file=sys.stderr)
            sys.exit(1)

        # Validate device structure
        for i, device in enumerate(devices):
            if not isinstance(device, dict):
                print(f"Error: Device at index {i} is not a dictionary", file=sys.stderr)
                sys.exit(1)
            if 'name' not in device:
                print(f"Error: Device at index {i} missing 'name' field", file=sys.stderr)
                sys.exit(1)
            if 'attributes' not in device:
                print(f"Error: Device at index {i} missing 'attributes' field", file=sys.stderr)
                sys.exit(1)

        # Process all devices
        results = process_devices(devices, config_changes, options, args.workers, args.delay)

        # For single device, output just the changes array
        if len(devices) == 1:
            result = results[0]
            if result['success']:
                print(json.dumps(result['changes']), end='')
                sys.exit(0)
            else:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
        else:
            # For multiple devices, output full results as JSON
            print(json.dumps(results), end='')
            # Exit with error code if any device failed
            if any(not result['success'] for result in results):
                sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
