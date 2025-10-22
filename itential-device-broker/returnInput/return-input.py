#!/usr/bin/env python3

import sys
import json


def main():
    try:
        # Read from stdin
        input_data = sys.stdin.read()

        # If no data from stdin, return empty object
        if not input_data or input_data.strip() == '':
            print(json.dumps({}, indent=2))
            return

        # Parse the input to validate it's valid JSON
        parsed_data = json.loads(input_data)

        # Return the input as formatted JSON
        print(json.dumps(parsed_data, indent=2))

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
