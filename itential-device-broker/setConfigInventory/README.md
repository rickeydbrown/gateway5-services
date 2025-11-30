# setConfigInventory Service

Apply configuration changes to network devices using Netmiko.

## Features

- Reads device inventory from stdin (supports `inventory_nodes` format)
- Applies configuration changes via `send_config_set()`
- Supports multiple devices in parallel
- Auto-commit for IOS-XR and Junos devices
- Configurable Netmiko connection parameters
- Vendor-specific command formatting (Cisco vs Junos)

## Usage

### Basic Example

```bash
cat test_input.json | ./itential-device-setconfiginventory.py \
  --config '[
    {
      "parents": ["interface Loopback100"],
      "old": "",
      "new": "description Test Interface"
    }
  ]'
```

### With Custom Options

```bash
cat test_input.json | ./itential-device-setconfiginventory.py \
  --config "$(cat test_config_changes.json)" \
  --options '{"global_delay_factor": 4, "timeout": 180}'
```

### Multiple Changes

```bash
cat test_input.json | ./itential-device-setconfiginventory.py \
  --config "$(cat test_multiple_changes.json)"
```

## Configuration Change Format

Each change object has:
- `parents`: Array of parent contexts (e.g., `["interface Loopback100"]`)
- `old`: Old configuration line (empty string if adding new)
- `new`: New configuration line (empty string if deleting)

### Examples

**Add new config:**
```json
{
  "parents": ["interface Loopback100"],
  "old": "",
  "new": "description New Interface"
}
```

**Modify existing config:**
```json
{
  "parents": ["interface Loopback100"],
  "old": "description Old",
  "new": "description Updated"
}
```

**Delete config:**
```json
{
  "parents": ["interface Loopback100"],
  "old": "shutdown",
  "new": ""
}
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

## Options Priority

1. **Device-level options** (in `attributes.options`)
2. **Global options** (via `--options` CLI parameter)
3. **Script defaults**

## Testing

Run the test script:
```bash
./test.sh
```

Or test individual files:
```bash
cat test_input.json | ./itential-device-setconfiginventory.py \
  --config "$(cat test_config_changes.json)"
```

## Supported Device Types

- Cisco IOS
- Cisco IOS-XR (auto-commit enabled)
- Cisco NX-OS
- Cisco ASA
- Juniper JunOS (auto-commit enabled)
- Arista EOS
- Aruba
- F5 BigIP
- Nokia SR OS

## Output

**Single device:**
```json
[
  {
    "result": true,
    "parents": ["interface Loopback100"],
    "old": "",
    "new": "description Test"
  }
]
```

**Multiple devices:**
Full results array with success/error status for each device.

## Error Handling

- Exit code 0: Success
- Exit code 1: Failure
- Errors printed to stderr
