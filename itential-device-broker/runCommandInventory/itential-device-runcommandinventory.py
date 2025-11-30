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


def run_device_command(device_name, attributes, command, options=None, delay=0):
    """
    Execute a command on a single device.

    Args:
        device_name: Name of the device
        attributes: Dictionary containing device connection parameters
        command: Command to execute (required)
        options: Optional connection/session parameters to override defaults
        delay: Delay in seconds before connecting (for testing same device)

    Returns:
        Dictionary with device name, success status, and output or error
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

        # Command priority: 1) device attribute, 2) parameter
        device_command = attributes.get('command') or attributes.get('cmd')
        command_to_run = device_command or command

        # Validate required parameters
        if not all([host, username, password, device_type]):
            return {
                'name': device_name,
                'success': False,
                'error': 'Missing required parameters (host, username, password, device_type/ostype)'
            }

        if not command_to_run:
            return {
                'name': device_name,
                'success': False,
                'error': 'Command is required'
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

        # Priority 1: Device-level options from attributes
        device_options = attributes.get('options', {})
        if device_options:
            device.update(device_options)

        # Priority 2: Global options from command line
        if options:
            device.update(options)

        # Handle secret separately (could come from attributes or options)
        if secret:
            device['secret'] = secret

        with ConnectHandler(**device) as connection:
            # Enable privileged mode if needed
            if secret and netmiko_device_type in ['cisco_ios', 'cisco_nxos', 'cisco_asa']:
                connection.enable()

            output = connection.send_command(command_to_run)

            return {
                'name': device_name,
                'success': True,
                'output': output,
                'host': host
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


def process_devices(devices, command, options=None, max_workers=10, delay=0):
    """
    Process multiple devices in parallel.

    Args:
        devices: List of device dictionaries with 'name' and 'attributes'
        command: Command to execute on all devices
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
                run_device_command,
                device['name'],
                device['attributes'],
                command,
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
        description='Run commands on multiple devices from inventory (stdin)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Supported device types:
Common mappings: {', '.join(DEVICE_TYPES.keys())}
Note: Any Netmiko device type can be used. If not in the mapping above,
      it will be passed directly to Netmiko (e.g., cisco_ios_telnet, hp_comware, etc.)

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

    parser.add_argument('-c', '--command', required=True,
                       help='Command to run on all devices')
    parser.add_argument('--options',
                       help='JSON object with optional Netmiko connection parameters')
    parser.add_argument('-w', '--workers', type=int, default=10,
                       help='Maximum number of parallel connections (default: 10)')
    parser.add_argument('-d', '--delay', type=float, default=0,
                       help='TESTING ONLY: Delay in seconds between connection attempts (default: 0, remove in production)')

    args = parser.parse_args()

    try:
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
        results = process_devices(devices, args.command, options, args.workers, args.delay)

        # For single device, output just the command output (like runCommand)
        if len(devices) == 1:
            result = results[0]
            if result['success']:
                print(result['output'], end='')
                sys.exit(0)
            else:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
        else:
            # For multiple devices, output results as JSON
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
