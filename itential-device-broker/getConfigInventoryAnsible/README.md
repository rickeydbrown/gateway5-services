# getConfigInventoryAnsible

Ansible-based service to execute commands on network devices using dynamic inventory from stdin.

## Overview

This service uses Ansible with a dynamic inventory script to execute commands on network devices. The inventory is provided via stdin in JSON format, converted to Ansible inventory format, and then used by an Ansible playbook to run commands on the devices.

## Components

1. **dynamic_inventory.py** - Dynamic inventory script that reads JSON from stdin and converts it to Ansible inventory format
2. **get_config.yml** - Ansible playbook that executes commands on network devices
3. **run_playbook.sh** - Wrapper script to simplify running the playbook with stdin input

## Requirements

- Python 3.6+
- Ansible 2.9+ with `ansible.netcommon` collection
- Network device access credentials

Install Ansible and required collections:
```bash
pip install ansible
ansible-galaxy collection install ansible.netcommon
```

## Input Format

The service expects JSON input via stdin with the following structure:

```json
{
  "inventory_nodes": [
    {
      "name": "device-name",
      "attributes": {
        "host": "10.0.0.1",
        "username": "admin",
        "password": "password",
        "device_type": "iosxr",
        "port": 22,
        "command": "show version"  (optional)
      }
    }
  ]
}
```

### Supported Device Types

- `aruba` → ansible_network_os: arubaos
- `asa` → ansible_network_os: asa
- `bigip` → ansible_network_os: bigip
- `eos` → ansible_network_os: eos
- `ios` → ansible_network_os: ios
- `iosxr` → ansible_network_os: iosxr
- `junos` → ansible_network_os: junos
- `nxos` → ansible_network_os: nxos
- `sros` → ansible_network_os: sros

## Usage

### Basic Usage

```bash
# With default command (show running-config)
cat input.json | ./run_playbook.sh

# With custom command
cat input.json | ./run_playbook.sh -c "show version"
```

### Direct Ansible Usage

```bash
# Test dynamic inventory
cat input.json | ./dynamic_inventory.py

# Run playbook directly
cat input.json | ansible-playbook -i ./dynamic_inventory.py get_config.yml

# With extra vars
cat input.json | ansible-playbook -i ./dynamic_inventory.py get_config.yml -e "device_command='show version'"
```

## Command Priority

1. **Device-specific command** - Command in device attributes (`attributes.command`)
2. **Global command** - Command passed via `-c` parameter
3. **Device-type default** - Default command based on `ansible_network_os`
4. **Fallback default** - `show running-config`

## Output

The playbook outputs the command results using Ansible's debug module. For production use, you may want to modify the playbook to format output as JSON or save to files.

## Testing

Run the test script to verify functionality:

```bash
./test.sh
```

This will:
1. Test the dynamic inventory conversion
2. Run the playbook with default command
3. Run the playbook with custom command

## Examples

### Single Device

```bash
echo '{
  "inventory_nodes": [{
    "name": "router1",
    "attributes": {
      "host": "10.0.0.1",
      "username": "admin",
      "password": "secret",
      "device_type": "iosxr"
    }
  }]
}' | ./run_playbook.sh
```

### Multiple Devices

```bash
cat multi_device_input.json | ./run_playbook.sh -c "show interfaces brief"
```

### Device with Custom Command

```bash
cat device_with_command.json | ./run_playbook.sh
```

## Notes

- Ansible uses SSH connection by default with `ansible.netcommon.network_cli`
- Passwords are passed in plaintext - consider using Ansible Vault for production
- The playbook runs commands serially by default - use `strategy: free` in playbook for parallel execution
- For large inventories, consider using `forks` parameter to control parallelism: `ansible-playbook -f 10 ...`
