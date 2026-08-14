#!/usr/bin/env python3
"""
Large-Data Payload Exercise Service

Exercises the proposed file-payload decorator pattern: instead of large
JSON blobs (pre-check results, dot1x session detail, running-config) being
passed inline through the decorator/gRPC payload, Gateway 5 would write
each one to a temp file and hand this script the path via an env var.

For each large entry, this script prefers the argparse value (pre-fix
behavior, data passed inline) and falls back to the env-var file (post-fix
behavior, data passed out-of-band), reporting which source was used - so
the same script works before and after the fix ships.

This script does no processing - it just proves the args and files came
through intact by returning them as-is.

Usage (pre-fix, inline args):
    ./large-data-test.py --target_device sw-access-42 --network_os ios \\
        --pre_check_result_json '{"checks": []}' \\
        --dot1x_detail_result_json '{"sessions": []}' \\
        --running_config_result_json '{"interfaces": []}'

Usage (post-fix, file-backed via env vars):
    export PRE_CHECK_RESULT_FILE=/tmp/pre_check.json
    export DOT1X_DETAIL_RESULT_FILE=/tmp/dot1x_detail.json
    export RUNNING_CONFIG_RESULT_FILE=/tmp/running_config.json
    ./large-data-test.py --target_device sw-access-42 --network_os ios --pre_check_success
"""

import argparse
import json
import os
import sys

LARGE_ENTRIES = {
    "pre_check_result": {"arg": "pre_check_result_json", "env_var": "PRE_CHECK_RESULT_FILE"},
    "dot1x_detail_result": {
        "arg": "dot1x_detail_result_json",
        "env_var": "DOT1X_DETAIL_RESULT_FILE",
    },
    "running_config_result": {
        "arg": "running_config_result_json",
        "env_var": "RUNNING_CONFIG_RESULT_FILE",
    },
}


def load_large_entry(name, arg_value, env_var):
    """Resolve a large entry from argparse (pre-fix) or an env-var file (post-fix).

    Returns the parsed contents, its size in bytes, and where it came from.
    """
    if arg_value:
        size_bytes = len(arg_value.encode("utf-8"))
        return json.loads(arg_value), size_bytes, "argparse"

    path = os.environ.get(env_var)
    if not path:
        raise RuntimeError(
            f"'{name}' was not passed via --{name}_json and '{env_var}' is not set"
        )
    if not os.path.isfile(path):
        raise RuntimeError(f"'{env_var}' points to a file that does not exist: {path}")
    size_bytes = os.path.getsize(path)
    with open(path, "r") as f:
        return json.load(f), size_bytes, f"env_file:{env_var}"


def main():
    parser = argparse.ArgumentParser(description="Large-data payload exercise")
    parser.add_argument("--target_device", required=True)
    parser.add_argument("--network_os", required=True)
    parser.add_argument("--pre_check_success", action="store_true")
    parser.add_argument("--pre_check_result_json")
    parser.add_argument("--dot1x_detail_result_json")
    parser.add_argument("--running_config_result_json")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    result = {
        "target_device": args.target_device,
        "network_os": args.network_os,
        "pre_check_success": args.pre_check_success,
    }

    try:
        for name, source_info in LARGE_ENTRIES.items():
            arg_value = getattr(args, source_info["arg"])
            value, size_bytes, source = load_large_entry(
                name, arg_value, source_info["env_var"]
            )
            result[name] = value
            result[f"{name}_size_bytes"] = size_bytes
            result[f"{name}_source"] = source
    except (RuntimeError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")

    sys.exit(0)


if __name__ == "__main__":
    main()
