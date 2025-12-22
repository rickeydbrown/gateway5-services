# Run Command with NetSDK

This directory contains a portable implementation of netsdk that can be cloned and run on any system.

## Directory Structure

```
run-command-netsdk/
├── netsdk/                  # Complete netsdk package (copied from source)
├── run-command-netsdk.py    # Main script to run commands on devices
├── inventory.json           # Device inventory (edit with your devices)
├── requirements.txt         # Dependencies needed for netsdk
└── README.md               # This file
```

## Setup on Any System

1. Clone this repository
2. Install dependencies:
   ```bash
   cd itential-device-broker-netsdk/run-command-netsdk
   pip install -r requirements.txt
   ```

## Usage

The script reads inventory from stdin and commands from command-line arguments:

```bash
# Single command from stdin
cat inventory.json | python3 run-command-netsdk.py -c "show version"

# Multiple commands
cat inventory.json | python3 run-command-netsdk.py -c "show version" -c "show ip interface brief"

# From file instead of stdin
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
- Version: 0.0.1.dev7+f05b1b3
