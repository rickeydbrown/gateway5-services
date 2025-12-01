import sys
import json
import argparse

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

DEFAULT_CONNECTION_PARAMS = {
    "conn_timeout": 30,
    "auth_timeout": 30,
    "banner_timeout": 30,
    "timeout": 120,
    "global_delay_factor": 2,
    "fast_cli": False,
}

print("\n")
print("What we got in stdin")
# Read from stdin
stdin_data = sys.stdin.read()
print(stdin_data)

print("\nWhat we got in cli args\n")
print(sys.argv)

# Parse CLI arguments to get options
parser = argparse.ArgumentParser()
parser.add_argument('--options', help='JSON object with optional Netmiko connection parameters')
parser.add_argument('-c', '--command', help='Command to run')
args, unknown = parser.parse_known_args()

# Parse global options from CLI
global_options = None
if args.options:
    try:
        global_options = json.loads(args.options)
        print("\nParsed global options from CLI:")
        print(json.dumps(global_options, indent=2))
    except json.JSONDecodeError:
        print("\nCould not parse --options as JSON")

# Parse and show device parameters like they would be passed to ConnectHandler
print("\nDevice parameters for ConnectHandler:\n")
try:
    input_data = json.loads(stdin_data)

    # Handle both array format and object with "inventory_nodes" key
    if isinstance(input_data, list):
        devices = input_data
    elif isinstance(input_data, dict) and 'inventory_nodes' in input_data:
        devices = input_data['inventory_nodes']
    else:
        devices = []

    for device_info in devices:
        device_name = device_info.get('name', 'unknown')
        attributes = device_info.get('attributes', {})

        # Extract parameters
        host = attributes.get('host')
        username = attributes.get('username')
        password = attributes.get('password')
        device_type = attributes.get('device_type') or attributes.get('ostype')
        port = attributes.get('port', 22)
        secret = attributes.get('secret')

        # Use mapped device type if available, otherwise use incoming device_type directly
        netmiko_device_type = DEVICE_TYPES.get(device_type, device_type)

        # Build device connection dictionary with defaults
        device_params = {
            'device_type': netmiko_device_type,
            'host': host,
            'username': username,
            'password': password,
            'port': port,
        }

        # Apply default connection parameters
        device_params.update(DEFAULT_CONNECTION_PARAMS)

        # Priority 1: Device-level options from attributes
        device_options = attributes.get('options', {})
        if device_options:
            device_params.update(device_options)

        # Priority 2: Global options from command line
        if global_options:
            device_params.update(global_options)

        # Handle secret separately
        if secret:
            device_params['secret'] = secret

        print(f"Device: {device_name}")
        print(json.dumps(device_params, indent=2))
        print("")

except json.JSONDecodeError:
    print("Could not parse stdin as JSON")
except Exception as e:
    print(f"Error: {e}")
