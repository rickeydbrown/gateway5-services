#!/usr/bin/env python3

import sys
import json
import argparse
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


def run_device_command(host, username, password, device_type, command, port=22, secret=None):
    if device_type not in DEVICE_TYPES:
        raise ValueError(f"Unsupported device type: {device_type}")

    if not command:
        raise ValueError("Command is required")

    netmiko_device_type = DEVICE_TYPES[device_type]

    device = {
        'device_type': netmiko_device_type,
        'host': host,
        'username': username,
        'password': password,
        'port': port,
    }

    if secret:
        device['secret'] = secret

    try:
        with ConnectHandler(**device) as connection:
            if secret and netmiko_device_type in ['cisco_ios', 'cisco_nxos', 'cisco_asa']:
                connection.enable()
            output = connection.send_command(command)
            return output
    except NetmikoTimeoutException:
        raise Exception(f"Timeout connecting to {host}:{port}")
    except NetmikoAuthenticationException:
        raise Exception(f"Authentication failed for {host}")
    except Exception as e:
        raise Exception(f"Error connecting to {host}: {str(e)}")


def main():
    # Check if we have command-line arguments (legacy mode) or stdin (new mode)
    # If we have recognized arguments, use legacy mode
    if len(sys.argv) > 1 and any(arg.startswith('--') for arg in sys.argv[1:]):
        # Legacy command-line argument mode
        parser = argparse.ArgumentParser(
            description='Run a command on a network device using netmiko',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument('--host', required=True, help='Device IP address or hostname')
        parser.add_argument('--username', required=True, help='Username for device login')
        parser.add_argument('--password', required=True, help='Password for device login')
        parser.add_argument('--device_type', required=True, choices=list(DEVICE_TYPES.keys()),
                           help='Device type')
        parser.add_argument('--command', required=True, help='Command to run on the device')
        parser.add_argument('--port', type=int, default=22, help='SSH port (default: 22)')
        parser.add_argument('--secret', help='Enable secret for privileged mode (Cisco devices)')

        # Ignore unknown arguments (like clusterId, ostype, etc.)
        args, _ = parser.parse_known_args()

        try:
            output = run_device_command(
                args.host,
                args.username,
                args.password,
                args.device_type,
                args.command,
                args.port,
                args.secret
            )
            print(output)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        # New stdin-based array mode
        try:
            input_data = sys.stdin.read()

            if not input_data or input_data.strip() == '':
                print(json.dumps({"error": "No input provided"}, indent=2), file=sys.stderr)
                sys.exit(1)

            # Parse the input JSON
            data = json.loads(input_data)

            # Extract arrays
            hosts = data.get('host', [])
            usernames = data.get('username', [])
            passwords = data.get('password', [])
            device_types = data.get('device_type', [])
            ports = data.get('port', [])
            secrets = data.get('secret', [])
            command = data.get('command', '')

            # Validate inputs
            if not all([hosts, usernames, passwords, device_types, command]):
                print(json.dumps({"error": "Missing required fields: host, username, password, device_type, command"}, indent=2), file=sys.stderr)
                sys.exit(1)

            # Ensure all arrays are the same length
            num_devices = len(hosts)
            if not all(len(arr) == num_devices for arr in [usernames, passwords, device_types]):
                print(json.dumps({"error": "host, username, password, and device_type arrays must be the same length"}, indent=2), file=sys.stderr)
                sys.exit(1)

            # Pad ports and secrets arrays if needed
            if len(ports) < num_devices:
                ports.extend([22] * (num_devices - len(ports)))
            if len(secrets) < num_devices:
                secrets.extend([None] * (num_devices - len(secrets)))

            results = []

            # Process each device
            for idx in range(num_devices):
                host = hosts[idx]
                username = usernames[idx]
                password = passwords[idx]
                device_type = device_types[idx]
                port = ports[idx] if idx < len(ports) else 22
                secret = secrets[idx] if idx < len(secrets) else None

                try:
                    output = run_device_command(
                        host,
                        username,
                        password,
                        device_type,
                        command,
                        port,
                        secret
                    )
                    results.append({
                        "host": host,
                        "success": True,
                        "output": output
                    })
                except Exception as e:
                    results.append({
                        "host": host,
                        "success": False,
                        "error": str(e)
                    })

            print(json.dumps(results, indent=2))

        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid JSON input: {str(e)}"}, indent=2), file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(json.dumps({"error": str(e)}, indent=2), file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
