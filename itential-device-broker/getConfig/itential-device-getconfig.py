#!/usr/bin/env python3

import argparse
import sys
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


DEVICE_COMMANDS = {
    'aruba': 'show running-config',
    'asa': 'show running-config',
    'bigip': 'show running-config',
    'eos': 'show running-config',
    'ios': 'show running-config',
    'iosxr': 'show running-config',
    'junos': 'show configuration',
    'nxos': 'show running-config',
    'sros': 'admin display-config'
}

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


def get_device_config(host, username, password, device_type, command=None, port=22, secret=None):
    if device_type not in DEVICE_TYPES:
        raise ValueError(f"Unsupported device type: {device_type}")
    
    netmiko_device_type = DEVICE_TYPES[device_type]
    default_command = DEVICE_COMMANDS[device_type]
    command_to_run = command if command else default_command
    
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
            output = connection.send_command(command_to_run)
            return output
    except NetmikoTimeoutException:
        raise Exception(f"Timeout connecting to {host}:{port}")
    except NetmikoAuthenticationException:
        raise Exception(f"Authentication failed for {host}")
    except Exception as e:
        raise Exception(f"Error connecting to {host}: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description='Show device configuration using netmiko',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Supported device types:
{', '.join(DEVICE_TYPES.keys())}

Default commands by device type:
''' + '\n'.join([f'  {k}: {v}' for k, v in DEVICE_COMMANDS.items()])
    )
    
    parser.add_argument('--host', required=True, help='Device IP address or hostname')
    parser.add_argument('--username', required=True, help='Username for device login')
    parser.add_argument('--password', required=True, help='Password for device login')
    parser.add_argument('--device_type', required=True, choices=list(DEVICE_TYPES.keys()),
                       help='Device type')
    parser.add_argument('-c', '--command', help='Custom command to run instead of default')
    parser.add_argument('-p', '--port', type=int, default=22, help='SSH port (default: 22)')
    parser.add_argument('-s', '--secret', help='Enable secret for privileged mode (Cisco devices)')
    
    args = parser.parse_args()
    
    try:
        output = get_device_config(
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


if __name__ == '__main__':
    main()