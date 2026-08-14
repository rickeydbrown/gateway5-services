#!/usr/bin/env python3
"""
Large-Data Payload Exercise Service

Exercises the proposed file-payload decorator pattern: instead of large
JSON blobs (pre-check results, dot1x session detail, running-config) being
passed inline through the decorator/gRPC payload, Gateway 5 would write
each one to a temp file and hand this script the path via an env var.

This script does no processing - it just proves the args and files came
through intact by returning them as-is.

Usage:
    export PRE_CHECK_RESULT_FILE=/tmp/pre_check.json
    export DOT1X_DETAIL_RESULT_FILE=/tmp/dot1x_detail.json
    export RUNNING_CONFIG_RESULT_FILE=/tmp/running_config.json
    ./large-data-test.py --target-device sw-access-42 --network-os ios --pre-check-success
"""

import argparse
import json
import os
import sys

FILE_ENV_VARS = {
    "pre_check_result": "PRE_CHECK_RESULT_FILE",
    "dot1x_detail_result": "DOT1X_DETAIL_RESULT_FILE",
    "running_config_result": "RUNNING_CONFIG_RESULT_FILE",
}


def load_payload_file(env_var):
    """Load and parse a JSON file whose path was handed to us via env_var.

    Returns the parsed contents along with the file's size in bytes.
    """
    path = os.environ.get(env_var)
    if not path:
        raise RuntimeError(f"required environment variable '{env_var}' is not set")
    if not os.path.isfile(path):
        raise RuntimeError(f"'{env_var}' points to a file that does not exist: {path}")
    size_bytes = os.path.getsize(path)
    with open(path, "r") as f:
        return json.load(f), size_bytes


def main():
    parser = argparse.ArgumentParser(description="Large-data payload exercise")
    parser.add_argument("--target-device", required=True)
    parser.add_argument("--network-os", required=True)
    parser.add_argument("--pre-check-success", action="store_true")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    try:
        pre_check_result, pre_check_size = load_payload_file(FILE_ENV_VARS["pre_check_result"])
        dot1x_detail_result, dot1x_detail_size = load_payload_file(
            FILE_ENV_VARS["dot1x_detail_result"]
        )
        running_config_result, running_config_size = load_payload_file(
            FILE_ENV_VARS["running_config_result"]
        )
    except (RuntimeError, json.JSONDecodeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = {
        "target_device": args.target_device,
        "network_os": args.network_os,
        "pre_check_success": args.pre_check_success,
        "pre_check_result": pre_check_result,
        "pre_check_result_size_bytes": pre_check_size,
        "dot1x_detail_result": dot1x_detail_result,
        "dot1x_detail_result_size_bytes": dot1x_detail_size,
        "running_config_result": running_config_result,
        "running_config_result_size_bytes": running_config_size,
    }

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")

    sys.exit(0)


if __name__ == "__main__":
    main()
