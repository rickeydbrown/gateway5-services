# isAliveInventory Service

Check if network devices are alive by executing version commands using inventory from stdin.

## Features

- Reads device inventory from stdin (supports `inventory_nodes` format)
- Device-specific default commands (e.g., `show sys version` for BigIP)
- Optional custom command via CLI argument
- Supports multiple devices in parallel
- Configurable Netmiko connection parameters
- Command priority: device attribute > CLI parameter > device-specific default

## Usage

### Basic Example (uses defaults)

```bash
cat test_input.json | ./itential-device-isaliveinventory.py
```

### With Custom Command

```bash
cat test_input.json | ./itential-device-isaliveinventory.py \
  -c "show hostname"
```

### With Custom Options

```bash
cat test_input.json | ./itential-device-isaliveinventory.py \
  --options '{"global_delay_factor": 4, "timeout": 180}'
```

## Default Commands by Device Type

- **Most devices**: `show version`
  - aruba, asa, eos, ios, iosxr, junos, nxos, sros
- **BigIP (F5)**: `show sys version`

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
3. **Device-specific default** (e.g., `show version` or `show sys version`)

## Options Priority

1. **Device-level options** (in `attributes.options`) - **Highest priority**
2. **Global options** (via `--options` CLI parameter)
3. **Script defaults** - Lowest priority

## Testing

Run the test script:
```bash
./test.sh
```

Or test manually:
```bash
cat test_input.json | ./itential-device-isaliveinventory.py
```

## Supported Device Types

Supports all Netmiko device types. Common mappings include:
- `aruba` → aruba_os
- `asa` → cisco_asa
- `bigip` → f5_ltm (uses `show sys version` by default)
- `eos` → arista_eos
- `ios` → cisco_ios
- `iosxr` → cisco_xr
- `junos` → juniper_junos
- `nxos` → cisco_nxos
- `sros` → nokia_sros

If the device type is not in the mapping, it will be passed directly to Netmiko (e.g., `cisco_ios_telnet`, `hp_comware`, etc.).

## Output

**Single device:**
Boolean value: `true` if device is alive, `false` if not
```
true
```

**Multiple devices:**
JSON array with alive status for each device:
```json
[
  {
    "name": "device1",
    "alive": true,
    "host": "10.0.0.1"
  },
  {
    "name": "device2",
    "alive": false,
    "error": "Timeout connecting to 10.0.0.2:22"
  }
]
```

## Error Handling

- Exit code 0: Success
- Exit code 1: Failure
- Errors printed to stderr
