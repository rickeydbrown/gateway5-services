#!/usr/bin/env python3

import argparse
import sys
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

# Device types that require explicit commit
COMMIT_REQUIRED = ['juniper_junos', 'cisco_xr']


def load_device_config(host, username, password, device_type, config_commands, port=22, secret=None, save_config=False):
    """
    Load configuration commands to a network device.

    Args:
        host: Device IP address or hostname
        username: Username for device login
        password: Password for device login
        device_type: Type of device (must be in DEVICE_TYPES)
        config_commands: List of configuration commands or string with newline-separated commands
        port: SSH port (default 22)
        secret: Enable secret for privileged mode (Cisco devices)
        save_config: Whether to save the configuration after loading (default False)

    Returns:
        Output from the configuration commands
    """
    if device_type not in DEVICE_TYPES:
        raise ValueError(f"Unsupported device type: {device_type}")

    if not config_commands:
        raise ValueError("Configuration commands are required")

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

    # Convert string with newlines to list if needed
    if isinstance(config_commands, str):
        config_commands = [cmd.strip() for cmd in config_commands.split('\n') if cmd.strip()]

    try:
        with ConnectHandler(**device) as connection:
            # Enable mode for Cisco devices if secret provided
            if secret and netmiko_device_type in ['cisco_ios', 'cisco_nxos', 'cisco_asa']:
                connection.enable()

            # Send configuration commands
            output = connection.send_config_set(config_commands)

            # Commit for devices that require it (Junos, IOS-XR)
            if netmiko_device_type in COMMIT_REQUIRED:
                commit_output = connection.commit()
                output += f"\n\n--- Commit Output ---\n{commit_output}"

            # Save configuration if requested
            if save_config:
                save_output = connection.save_config()
                output += f"\n\n--- Save Config Output ---\n{save_output}"

            return output

    except NetmikoTimeoutException:
        raise Exception(f"Timeout connecting to {host}:{port}")
    except NetmikoAuthenticationException:
        raise Exception(f"Authentication failed for {host}")
    except Exception as e:
        raise Exception(f"Error connecting to {host}: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description='Load configuration commands to a network device using netmiko',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Supported device types:
{', '.join(DEVICE_TYPES.keys())}

Configuration Input Methods:
  1. Use -c/--commands with semicolon-separated commands
  2. Use -f/--file to read commands from a file

Example usage:
  # Using inline commands
  python itential-device-loadconfig.py --host 192.168.1.1 --username admin --password pass123 --device_type ios --commands "interface gi0/1;description Test Port;no shutdown"

  # Using a configuration file
  python itential-device-loadconfig.py --host router.example.com --username admin --password pass123 --device_type junos --file config.txt

  # Save configuration after loading
  python itential-device-loadconfig.py --host 192.168.1.1 --username admin --password pass123 --device_type ios --commands "interface gi0/1;description Test" --save

Notes:
  - For Junos and IOS-XR devices, configuration is automatically committed
  - Use --save to write configuration to memory (copy run start equivalent)
  - Commands are automatically entered in configuration mode
'''
    )

    parser.add_argument('--host', required=True, help='Device IP address or hostname')
    parser.add_argument('--username', required=True, help='Username for device login')
    parser.add_argument('--password', required=True, help='Password for device login')
    parser.add_argument('--device_type', required=True, choices=list(DEVICE_TYPES.keys()),
                       help='Device type')

    # Configuration input options (mutually exclusive)
    config_group = parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument('-c', '--commands',
                             help='Configuration commands (semicolon-separated for multiple commands)')
    config_group.add_argument('-f', '--file',
                             help='File containing configuration commands (one per line)')

    parser.add_argument('-p', '--port', type=int, default=22, help='SSH port (default: 22)')
    parser.add_argument('-s', '--secret', help='Enable secret for privileged mode (Cisco devices)')
    parser.add_argument('--save', action='store_true',
                       help='Save configuration after loading (copy run start)')

    args = parser.parse_args()

    # Read configuration commands
    if args.file:
        try:
            with open(args.file, 'r') as f:
                config_commands = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"Error: Configuration file '{args.file}' not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file '{args.file}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Split commands by semicolon
        config_commands = [cmd.strip() for cmd in args.commands.split(';') if cmd.strip()]

    try:
        output = load_device_config(
            args.host,
            args.username,
            args.password,
            args.device_type,
            config_commands,
            args.port,
            args.secret,
            args.save
        )
        print(output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
