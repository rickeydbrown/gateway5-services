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

    # Preprocess script code to fix common issues from unquoted arguments
    import re

    # Fix unquoted paths in function calls: os.listdir(/bin) -> os.listdir('/bin')
    # Pattern: function(/path) -> function('/path')
    script_code = re.sub(r'\((/[\w/.-]+)\)', r"('\1')", script_code)

    # Fix unquoted string literals with escape sequences: (\n) -> ("\n")
    # This handles cases like print(\n.join(...)) -> print("\n".join(...))
    script_code = re.sub(r'\(\\([ntr])\b', r'("\\\1"', script_code)

    # Fix unquoted dictionary keys and string values: {key: value} -> {'key': 'value'}
    # This is complex, so we'll handle common patterns

    # Pattern: {word: word, word: number} -> {'word': 'word', 'word': number}
    def fix_dict_quotes(match):
        dict_content = match.group(1)
        # First quote all keys: word: -> 'word':
        fixed = re.sub(r'(\w+):', r"'\1':", dict_content)
        # Then quote string values (words that are not numbers): : word -> : 'word'
        fixed = re.sub(r":\s*([a-zA-Z]\w*)(?=\s*[,}])", r": '\1'", fixed)
        return '{' + fixed + '}'

    script_code = re.sub(r'\{([^{}]+)\}', fix_dict_quotes, script_code)

    # Fix f-strings that lost their quotes: print(fResult: {var}) -> print(f'Result: {var}')
    # Pattern 1: print(f<text>: {<var>}) -> print(f'<text>: {<var>}')
    # Match: print(f followed by text with colon and curly braces, no quotes
    script_code = re.sub(r'print\(f([A-Za-z][^\'"\(\)]*:\s*\{[^}]+\})\)', r"print(f'\1')", script_code)

    # Pattern 2: print(f<text> {<var>}) -> print(f'<text> {<var>}') (without colon)
    # Match: print(f followed by text with space and curly braces, no quotes or colon
    script_code = re.sub(r'print\(f([A-Za-z][^\'"\(\):]*\s+\{[^}]+\})\)', r"print(f'\1')", script_code)

    # Fix escaped quotes that might have been introduced
    script_code = script_code.replace(r'\"', '"').replace(r"\'", "'")

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
