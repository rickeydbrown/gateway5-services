#!/usr/bin/env python3
"""
Python Interpreter Service
Executes Python code passed as a command line argument.

Usage:
    ./python-interpreter.py --script "print('Hello, World!')"
    ./python-interpreter.py --script "import json; print(json.dumps({'key': 'value'}))"
"""

import sys
import argparse
import json
from io import StringIO
import traceback

def execute_script(script_code):
    """
    Execute Python code and capture output.

    Args:
        script_code: String containing Python code to execute

    Returns:
        Dictionary with success status, output, and any errors
    """
    # Redirect stdout and stderr to capture output
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    stdout_capture = StringIO()
    stderr_capture = StringIO()

    sys.stdout = stdout_capture
    sys.stderr = stderr_capture

    result = {
        'success': True,
        'stdout': '',
        'stderr': '',
        'error': None
    }

    try:
        # Execute the script
        exec(script_code, {'__builtins__': __builtins__})

        # Capture output
        result['stdout'] = stdout_capture.getvalue()
        result['stderr'] = stderr_capture.getvalue()

    except Exception as e:
        result['success'] = False
        result['error'] = str(e)
        result['traceback'] = traceback.format_exc()
        result['stderr'] = stderr_capture.getvalue()

    finally:
        # Restore stdout and stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return result

def main():
    parser = argparse.ArgumentParser(
        description='Execute Python code from command line argument'
    )
    parser.add_argument(
        '--script',
        required=False,
        help='Python code to execute'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )

    # Use parse_known_args to capture remaining arguments
    args, remaining = parser.parse_known_args()

    # Build script from --script and any remaining arguments
    if args.script:
        # If there are remaining arguments, they're part of the script that got split
        if remaining:
            script_code = args.script + ' ' + ' '.join(remaining)
        else:
            script_code = args.script
    else:
        print("Error: --script argument is required", file=sys.stderr)
        sys.exit(1)

    # Execute the script
    result = execute_script(script_code)

    # Output results
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        # Text format - just print stdout or error
        if result['success']:
            if result['stdout']:
                print(result['stdout'], end='')
            if result['stderr']:
                print(result['stderr'], end='', file=sys.stderr)
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            if result.get('traceback'):
                print(result['traceback'], file=sys.stderr)

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main()
