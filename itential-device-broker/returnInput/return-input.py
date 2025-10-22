#!/usr/bin/env python3

import argparse
import sys
import json


def main():
    parser = argparse.ArgumentParser(
        description='Return input data as-is - useful for testing and debugging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example usage:
  python return-input.py --input '{"message":"Hello, World!"}'
  python return-input.py --input '{"data":{"name":"test","value":123}}'
'''
    )

    parser.add_argument('--input', required=True, help='JSON input data to return')

    args = parser.parse_args()

    try:
        # Parse the input to validate it's valid JSON
        input_data = json.loads(args.input)

        # Return the input as formatted JSON
        print(json.dumps(input_data, indent=2))

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
