# runCommandInventory Service

Execute commands on network devices using inventory from stdin and command from CLI.

## Features

- Reads device inventory from stdin (supports `inventory_nodes` format)
- Command specified via CLI argument (required)
- Supports multiple devices in parallel
- Configurable Netmiko connection parameters
- Command priority: device attribute > CLI parameter

## Usage

### Basic Example

```bash
cat test_input.json | ./itential-device-runcommandinventory.py \
  -c "show version"
```

### With Custom Options

```bash
cat test_input.json | ./itential-device-runcommandinventory.py \
  -c "show ip interface brief" \
  --options '{"global_delay_factor": 4, "timeout": 180}'
```

### Multiple Devices

```bash
cat test_input.json | ./itential-device-runcommandinventory.py \
  -c "show running-config"
```

## Device Input Format

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
        "port": 22
      }
    }
  ]
}
```

## Command Priority

1. **Device-level command** (in `attributes.command` or `attributes.cmd`)
2. **CLI command** (via `-c` or `--command` parameter)

If a device has its own command in attributes, that takes priority over the global CLI command.

## Options Priority

1. **Device-level options** (in `attributes.options`)
2. **Global options** (via `--options` CLI parameter)
3. **Script defaults**

## Testing

Run the test script:
```bash
./test.sh
```

Or test manually:
```bash
cat test_input.json | ./itential-device-runcommandinventory.py \
  -c "show version"
```

## Supported Device Types

Supports all Netmiko device types. Common mappings include:
- `aruba` → aruba_os
- `asa` → cisco_asa
- `bigip` → f5_ltm
- `eos` → arista_eos
- `ios` → cisco_ios
- `iosxr` → cisco_xr
- `junos` → juniper_junos
- `nxos` → cisco_nxos
- `sros` → nokia_sros

If the device type is not in the mapping, it will be passed directly to Netmiko (e.g., `cisco_ios_telnet`, `hp_comware`, etc.).

## Output

**Single device:**
Plain text output of the command (no JSON wrapping)

**Multiple devices:**
JSON array with results for each device:
```json
[
  {
    "name": "device1",
    "success": true,
    "output": "...",
    "host": "10.0.0.1"
  }
]
```

## Error Handling

- Exit code 0: Success
- Exit code 1: Failure
- Errors printed to stderr
