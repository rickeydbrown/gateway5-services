#!/usr/bin/env python3

import argparse
import sys
import json
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
    parser = argparse.ArgumentParser(
        description='Run a command on multiple network devices using netmiko',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Supported device types:
{', '.join(DEVICE_TYPES.keys())}

Example usage:
  # Single device (legacy mode)
  python itential-device-runcommand.py --host 192.168.1.1 --username admin --password pass123 --device_type ios --command "show version"

  # Multiple devices (new mode)
  python itential-device-runcommand.py --devices '[{{"host":"192.168.1.1","username":"admin","password":"pass123","device_type":"ios"}},{{"host":"192.168.1.2","username":"admin","password":"pass123","device_type":"ios"}}]' --command "show version"
'''
    )

    # Legacy single device arguments
    parser.add_argument('--host', help='Device IP address or hostname (legacy single device mode)')
    parser.add_argument('--username', help='Username for device login (legacy single device mode)')
    parser.add_argument('--password', help='Password for device login (legacy single device mode)')
    parser.add_argument('--device_type', choices=list(DEVICE_TYPES.keys()),
                       help='Device type (legacy single device mode)')
    parser.add_argument('-p', '--port', type=int, default=22, help='SSH port (default: 22, legacy single device mode)')
    parser.add_argument('-s', '--secret', help='Enable secret for privileged mode (Cisco devices, legacy single device mode)')

    # New multi-device arguments
    parser.add_argument('--devices', help='JSON array of devices to run command on')
    parser.add_argument('-c', '--command', required=True, help='Command to run on the device(s)')

    args = parser.parse_args()

    results = []

    try:
        # New multi-device mode
        if args.devices:
            devices = json.loads(args.devices)

            if not isinstance(devices, list) or len(devices) == 0:
                print("Error: --devices must be a non-empty JSON array", file=sys.stderr)
                sys.exit(1)

            for idx, device in enumerate(devices):
                host = device.get('host')
                username = device.get('username')
                password = device.get('password')
                device_type = device.get('device_type')
                port = device.get('port', 22)
                secret = device.get('secret')

                if not all([host, username, password, device_type]):
                    print(f"Error: Device {idx} missing required fields (host, username, password, device_type)", file=sys.stderr)
                    sys.exit(1)

                try:
                    output = run_device_command(
                        host,
                        username,
                        password,
                        device_type,
                        args.command,
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

        # Legacy single device mode
        elif args.host and args.username and args.password and args.device_type:
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

        else:
            print("Error: Either provide --devices (for multiple devices) or --host, --username, --password, --device_type (for single device)", file=sys.stderr)
            sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in --devices: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
