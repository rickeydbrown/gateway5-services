# NetSDK Broker Services

This directory contains a portable implementation of netsdk with multiple brokered services that can be cloned and run on any system.

## Directory Structure

```
broker-services/
├── netsdk/                  # Complete netsdk package (copied from source)
├── is-alive-netsdk.py       # Check if devices are alive/reachable
├── get-config-netsdk.py     # Get configuration from devices
├── run-command-netsdk.py    # Run commands on devices
├── inventory.json           # Device inventory (edit with your devices)
├── requirements.txt         # Dependencies needed for netsdk
└── README.md                # This file
```

## Setup on Any System

1. Clone this repository
2. Install dependencies:
   ```bash
   cd itential-device-broker-netsdk/broker-services
   pip install -r requirements.txt
   ```

## Available Services

### 1. is-alive-netsdk.py - Check Device Connectivity

Checks if network devices are alive/reachable by verifying SSH connectivity and authentication.

```bash
# Check if devices are alive
cat inventory.json | python3 is-alive-netsdk.py

# With file input
python3 is-alive-netsdk.py -f inventory.json

# Suppress log messages (show only result)
cat inventory.json | python3 is-alive-netsdk.py --log-level ERROR

# Output for single device: true or false
# Output for multiple devices: JSON array with name, alive, and host fields
```

### 2. get-config-netsdk.py - Get Device Configuration

Retrieves configuration from network devices using platform-specific default commands.

```bash
# Get config using platform defaults (e.g., "show running-config" for Cisco)
cat inventory.json | python3 get-config-netsdk.py

# Get config with custom command
cat inventory.json | python3 get-config-netsdk.py -c "show running-config"

# Multiple commands
cat inventory.json | python3 get-config-netsdk.py -c "show running-config" -c "show startup-config"

# From file input
python3 get-config-netsdk.py -f inventory.json

# With different log level
cat inventory.json | python3 get-config-netsdk.py --log-level DEBUG

# Output for single device: Just the configuration text
# Output for multiple devices: JSON array with name, success, output, and host fields
```

### 3. run-command-netsdk.py - Run Commands on Devices

Executes commands on network devices and returns the output.

```bash
# Single command
cat inventory.json | python3 run-command-netsdk.py -c "show version"

# Multiple commands
cat inventory.json | python3 run-command-netsdk.py -c "show version" -c "show ip interface brief"

# From file input
python3 run-command-netsdk.py -c "show version" -f inventory.json

# With different log level
cat inventory.json | python3 run-command-netsdk.py -c "show version" --log-level DEBUG

# Redirect stdin
python3 run-command-netsdk.py -c "show version" < inventory.json
```

## Inventory File Format

The inventory file defines the devices to connect to:

```json
{
    "inventory_nodes": [
        {
            "name": "my-router",
            "attributes": {
                "itential_host": "192.168.1.1",
                "itential_user": "admin",
                "itential_password": "admin",
                "itential_platform": "cisco_ios",
                "itential_port": 22,
                "itential_driver": "netmiko"
            }
        }
    ]
}
```

### Supported Attributes

- `itential_host`: Device IP address or hostname (required)
- `itential_user`: SSH username (required)
- `itential_password`: SSH password (required)
- `itential_platform`: Device platform (e.g., `cisco_ios`, `arista_eos`, `juniper_junos`)
- `itential_port`: SSH port (default: 22)
- `itential_driver`: Driver to use (`netmiko` or `scrapli`)
- `itential_become`: Enable privilege escalation (optional, boolean)
- `itential_become_password`: Password for privilege escalation (optional)
- `itential_driver_options`: Driver-specific options (optional, see below)

### Driver Options

For advanced configuration, use `itential_driver_options` to pass driver-specific settings:

#### Scrapli with SSH Host Key Verification Disabled (Paramiko Transport - Recommended)

```json
{
    "itential_driver": "scrapli",
    "itential_driver_options": {
        "scrapli": {
            "auth_strict_key": false,
            "transport": "paramiko"
        }
    }
}
```

#### Scrapli with SSH Host Key Verification Disabled (System Transport)

```json
{
    "itential_driver": "scrapli",
    "itential_driver_options": {
        "scrapli": {
            "auth_strict_key": false,
            "transport": "system",
            "transport_options": {
                "ssh_options": ["-o StrictHostKeyChecking=no", "-o UserKnownHostsFile=/dev/null"]
            }
        }
    }
}
```

#### Netmiko with SSH Host Key Verification Disabled

```json
{
    "itential_driver": "netmiko",
    "itential_driver_options": {
        "netmiko": {
            "ssh_strict": false,
            "system_host_keys": false
        }
    }
}
```

#### Netmiko with Fast CLI Mode

```json
{
    "itential_driver": "netmiko",
    "itential_driver_options": {
        "netmiko": {
            "fast_cli": true,
            "global_delay_factor": 0.5
        }
    }
}
```

## Using netsdk in Your Own Scripts

The netsdk package is included directly in this directory. To use it in your scripts:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add this directory to Python path
script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(script_dir))

# Now you can import netsdk
from netsdk.core.models import DeviceConnection, DeviceCredentials
from netsdk.executor import broker

# Your code here...
```

## Requirements

- Python 3.10+
- netmiko >= 4.6.0
- pydantic >= 2.0.0
- scrapli >= 2025.1.30

All dependencies are listed in `requirements.txt`.

## Notes

- The netsdk package is completely self-contained in this directory
- No need to clone multiple repositories
- Works on any system after installing dependencies
- Version: 0.0.1.dev+c001b0c (updated 2026-01-14)
