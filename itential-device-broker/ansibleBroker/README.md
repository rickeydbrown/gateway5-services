# Ansible Broker for Itential Gateway5

Ansible-based service to interact with network devices using dynamic inventory from stdin.

## Overview

This service uses Ansible with a dynamic inventory script to interact with network devices. The inventory is provided via stdin in JSON format, converted to Ansible inventory format with proper host variables, and then used by Ansible playbooks to perform operations on the devices.

## Components

1. **dynamic_inventory.py** - Dynamic inventory script that reads JSON from stdin and converts it to Ansible inventory format with proper host variables
2. **get_config_playbook.yml** - Retrieves device configuration (replaces get_config Python script)
3. **is_alive_playbook.yml** - Checks device connectivity (replaces is_alive Python script)
4. **run_command_playbook.yml** - Executes arbitrary CLI commands on devices
5. **library/get_config_output.py** - Custom Ansible module to extract and clean configuration output
6. **callback_plugins/itential_output.py** - Custom callback plugin for clean output formatting
7. **ansible.cfg** - Ansible configuration file specifying custom plugins and settings

## Requirements

- Python 3.6+
- Ansible 2.9+ with required collections (see requirements.yml)
- Network device access credentials

Install Ansible and required dependencies:
```bash
# Install Python packages
pip install -r requirements.txt

# Install Ansible collections
ansible-galaxy collection install -r requirements.yml
```

## How It Works: Dynamic Inventory and Host Variables

The `dynamic_inventory.py` script is the bridge between Itential Gateway and Ansible. It reads JSON from stdin and converts device attributes into Ansible host variables that the playbooks use for authentication and connection.

### Input Format

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
        "command": "show version"
      }
    }
  ]
}
```

### Host Variable Mapping

The dynamic inventory script converts device attributes into Ansible host variables with the following priority order:

| Purpose | Priority Order (highest to lowest) | Result Ansible Variable |
|---------|-------------------------------------|------------------------|
| **Hostname/IP** | `ansible_host` → `itential_host` → `host` | `ansible_host` |
| **Username** | `ansible_user` → `itential_user` → `username` | `ansible_user` |
| **Password** | `ansible_password` → `itential_password` → `password` | `ansible_password` |
| **Port** | `ansible_port` → `itential_port` → `port` | `ansible_port` |
| **Device OS** | `ansible_network_os` → `itential_platform` → `device_type` → `ostype` | `ansible_network_os` |
| **Command** | `command` | `device_command` |
| **Options** | `options` | `device_options` |

### Supported Device Types

The script maps device types to Ansible network OS values:

| Device Type | Ansible Network OS | Collection Required |
|-------------|-------------------|---------------------|
| `ios` | `ios` | cisco.ios |
| `iosxr` / `cisco_xr` | `iosxr` | cisco.iosxr |
| `asa` | `asa` | cisco.asa |
| `nxos` | `nxos` | cisco.nxos |
| `eos` | `eos` | arista.eos |
| `junos` | `junos` | junipernetworks.junos |
| `bigip` | `bigip` | f5networks.f5_modules |
| `sros` | `sros` | nokia.sros (commented out - not available) |
| `aruba` | `arubaos` | arubanetworks.aoscx (commented out - not available) |

## Playbook Details

All playbooks use the same host variables set by the dynamic inventory script to connect to devices.

### 1. get_config_playbook.yml - Retrieve Device Configuration

**Purpose**: Retrieves device configuration (running-config or equivalent)

**How it works**:
1. Uses `ansible_network_os` host variable to determine device platform
2. Executes platform-specific command module (e.g., `cisco.iosxr.iosxr_command`)
3. Uses `device_command` host variable if set, otherwise defaults to:
   - IOS/IOS-XR: `show running-config`
   - Junos: `show configuration`
   - Other platforms: `show running-config`
4. Passes results to custom `get_config_output` module to clean output
5. Custom callback plugin outputs only the clean configuration data

**Authentication**: Uses `ansible_host`, `ansible_user`, `ansible_password`, `ansible_port`

**Usage**:
```bash
# Default command (show running-config)
cat input.json | ansible-playbook -i ./dynamic_inventory.py get_config_playbook.yml

# Custom command via extra vars
cat input.json | ansible-playbook -i ./dynamic_inventory.py get_config_playbook.yml -e "config_command='show startup-config'"

# Custom command in device attributes
echo '{
  "inventory_nodes": [{
    "name": "router1",
    "attributes": {
      "host": "10.0.0.1",
      "username": "admin",
      "password": "secret",
      "device_type": "iosxr",
      "command": "show configuration"
    }
  }]
}' | ansible-playbook -i ./dynamic_inventory.py get_config_playbook.yml
```

**Output**: Clean configuration text without Ansible JSON wrapper or "Building configuration..." prefixes

### 2. is_alive_playbook.yml - Check Device Connectivity

**Purpose**: Determines if a device is reachable and responsive

**How it works**:
1. Uses `ansible_network_os` host variable to determine device platform
2. Executes `show version` command using platform-specific module
3. If command succeeds, sets `device_alive` fact to `true`
4. Custom callback plugin outputs just `true` or `false` (no newline)
5. Most platforms have `ignore_errors: yes` to handle connection failures gracefully
6. IOS-XR intentionally lacks `ignore_errors` to fail fast on connection issues

**Authentication**: Uses `ansible_host`, `ansible_user`, `ansible_password`, `ansible_port`

**Usage**:
```bash
cat input.json | ansible-playbook -i ./dynamic_inventory.py is_alive_playbook.yml
```

**Output**: `true` or `false` (without trailing newline to match Python script behavior)

### 3. run_command_playbook.yml - Execute CLI Commands

**Purpose**: Executes arbitrary CLI commands on network devices

**How it works**:
1. Uses `ansible_network_os` host variable to determine device platform
2. Requires `device_command` host variable (from `command` attribute) or `command` extra var
3. Fails if no command is provided
4. Executes command using platform-specific module (e.g., `cisco.ios.ios_command`)
5. Custom callback plugin captures stdout and outputs command results

**Authentication**: Uses `ansible_host`, `ansible_user`, `ansible_password`, `ansible_port`

**Usage**:
```bash
# Command in device attributes
echo '{
  "inventory_nodes": [{
    "name": "router1",
    "attributes": {
      "host": "10.0.0.1",
      "username": "admin",
      "password": "secret",
      "device_type": "iosxr",
      "command": "show interfaces brief"
    }
  }]
}' | ansible-playbook -i ./dynamic_inventory.py run_command_playbook.yml

# Command via extra vars
cat input.json | ansible-playbook -i ./dynamic_inventory.py run_command_playbook.yml -e "command='show version'"
```

**Output**: Command output (stdout from the network device)

## Custom Callback Plugin

The `itential_output.py` callback plugin provides clean output formatting for Itential Gateway integration:

**Output Priority**:
1. **config_data** - If present, outputs configuration from get_config_playbook.yml
2. **command_result** - If present, outputs command stdout from run_command_playbook.yml
3. **device_alive** - If present, outputs `true`/`false` from is_alive_playbook.yml
4. **Fallback** - For is_alive, checks playbook stats and outputs `true` if no failures, `false` otherwise

**Key Features**:
- Suppresses Ansible's default JSON/YAML output
- Outputs raw text for config and command results
- Outputs boolean without newline for is_alive (matches Python script behavior)
- Configured in ansible.cfg: `stdout_callback = itential_output`

## Examples

### Example 1: Check Device Connectivity
```bash
cat <<EOF | ansible-playbook -i ./dynamic_inventory.py is_alive_playbook.yml
{
  "inventory_nodes": [{
    "name": "router1",
    "attributes": {
      "host": "10.0.0.1",
      "username": "admin",
      "password": "secret",
      "device_type": "iosxr"
    }
  }]
}
EOF
```
Output: `true` (or `false` if unreachable)

### Example 2: Get Device Configuration
```bash
cat <<EOF | ansible-playbook -i ./dynamic_inventory.py get_config_playbook.yml
{
  "inventory_nodes": [{
    "name": "switch1",
    "attributes": {
      "host": "10.0.0.2",
      "username": "admin",
      "password": "secret",
      "device_type": "ios"
    }
  }]
}
EOF
```
Output: Clean running-config text

### Example 3: Run Custom Command
```bash
cat <<EOF | ansible-playbook -i ./dynamic_inventory.py run_command_playbook.yml
{
  "inventory_nodes": [{
    "name": "router1",
    "attributes": {
      "host": "10.0.0.1",
      "username": "admin",
      "password": "secret",
      "device_type": "iosxr",
      "command": "show bgp summary"
    }
  }]
}
EOF
```
Output: BGP summary output from device

### Example 4: Multiple Devices
```bash
cat <<EOF | ansible-playbook -i ./dynamic_inventory.py is_alive_playbook.yml
{
  "inventory_nodes": [
    {
      "name": "router1",
      "attributes": {
        "host": "10.0.0.1",
        "username": "admin",
        "password": "secret",
        "device_type": "iosxr"
      }
    },
    {
      "name": "switch1",
      "attributes": {
        "host": "10.0.0.2",
        "username": "admin",
        "password": "secret",
        "device_type": "ios"
      }
    }
  ]
}
EOF
```

### Example 5: Using Pre-configured Ansible Variables
```bash
# You can pass native Ansible variables directly
cat <<EOF | ansible-playbook -i ./dynamic_inventory.py get_config_playbook.yml
{
  "inventory_nodes": [{
    "name": "router1",
    "attributes": {
      "ansible_host": "10.0.0.1",
      "ansible_user": "admin",
      "ansible_password": "secret",
      "ansible_network_os": "iosxr",
      "ansible_port": 22
    }
  }]
}
EOF
```

## Connection Details

All playbooks use these Ansible connection settings (configured automatically by dynamic_inventory.py):

- **Connection Type**: `ansible.netcommon.network_cli` (SSH-based network CLI connection)
- **Connection Variables**:
  - `ansible_host` - Device IP or hostname
  - `ansible_user` - SSH username
  - `ansible_password` - SSH password
  - `ansible_port` - SSH port (default: 22)
  - `ansible_network_os` - Network OS type (determines which command module to use)

**Additional Settings** (from ansible.cfg):
- `host_key_checking = False` - Disables SSH host key verification
- `command_timeout = 30` - Commands timeout after 30 seconds
- `connect_timeout = 30` - Connection attempts timeout after 30 seconds
- `interpreter_python = auto_silent` - Automatically detects Python interpreter

## Notes

- Passwords are passed in plaintext - consider using Ansible Vault for production
- The playbooks run commands serially by default
- For large inventories, use `forks` parameter for parallelism: `ansible-playbook -f 10 ...`
- SR OS and Aruba device types are commented out due to unavailable Ansible collections
- Custom callback plugin ensures output format matches original Python scripts for Gateway compatibility

## Troubleshooting

### Device reported as NOT ALIVE but can get config
- Check that `is_alive_playbook.yml` outputs exactly `true` or `false` with no trailing newline
- Verify callback plugin is loaded: `ansible-playbook --version` should show callback plugins path
- Check stderr for DEBUG messages from callback plugin

### "Building configuration..." appears in config output
- Ensure `get_config_output` module is in the `library/` directory
- Check that callback plugin is capturing `config_data` field
- Verify platform detection is working (check `ansible_network_os` value)

### Module not found errors
- Install required collections: `ansible-galaxy collection install -r requirements.yml`
- For SR OS/Aruba devices, uncomment and install appropriate collections
- Verify collection installation: `ansible-galaxy collection list`

### Connection timeout errors
- Increase timeout values in ansible.cfg `[persistent_connection]` section
- Verify network connectivity to devices
- Check firewall rules for SSH access
