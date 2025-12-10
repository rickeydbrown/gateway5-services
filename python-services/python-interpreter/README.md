# Python Interpreter Service

Execute Python code from command line arguments.

## Overview

This service allows you to execute arbitrary Python code passed as a command line argument. It captures stdout, stderr, and any errors, and can return results in either plain text or JSON format.

## Requirements

- Python 3.6+

## JSON Schema

The service includes JSON schemas for validation:

- **[input-schema.json](input-schema.json)**: Validates input parameters (script and format)
- **[output-schema.json](output-schema.json)**: Defines the structure of JSON format output

### Input Schema

```json
{
  "script": "string (required, min length 1)",
  "format": "string (optional, enum: ['json', 'text'], default: 'text')"
}
```

### Output Schema (JSON format only)

```json
{
  "success": "boolean (required)",
  "stdout": "string (required)",
  "stderr": "string (required)",
  "error": "string or null (required)",
  "traceback": "string (optional, only present on error)"
}
```

## Usage

### Basic Usage

```bash
./python-interpreter.py --script 'print("Hello, World!")'
```

### With JSON Output Format

```bash
./python-interpreter.py --script 'print("test")' --format json
```

## Parameters

- `--script` (required): Python code to execute as a string
- `--format` (optional): Output format, either `text` (default) or `json`

## Output Formats

### Text Format (Default)

In text format, the service outputs:
- **Success**: Prints stdout (and stderr to stderr)
- **Error**: Prints error message and traceback to stderr, exits with code 1

```bash
./python-interpreter.py --script "print('Hello')"
# Output: Hello
```

### JSON Format

In JSON format, the service always outputs a JSON object with:
- `success`: Boolean indicating if execution succeeded
- `stdout`: String containing captured stdout
- `stderr`: String containing captured stderr
- `error`: Error message (if failed)
- `traceback`: Full traceback (if failed)

```bash
./python-interpreter.py --script "print('Hello')" --format json
```

Output:
```json
{
  "success": true,
  "stdout": "Hello\n",
  "stderr": "",
  "error": null
}
```

## Examples

### Simple Print

```bash
./python-interpreter.py --script 'print("Hello, World!")'
```

### Math Calculation

```bash
./python-interpreter.py --script "result = 5 + 3 * 2; print(f'Result: {result}')"
```

### JSON Output

```bash
./python-interpreter.py --script "import json; print(json.dumps({'key': 'value'}))"
```

### Multi-line Script

```bash
./python-interpreter.py --script "
for i in range(3):
    print(f'Iteration {i}')
"
```

### Using Libraries

```bash
./python-interpreter.py --script "
import sys
import json
data = {'python_version': f'{sys.version_info.major}.{sys.version_info.minor}'}
print(json.dumps(data))
"
```

### Error Handling

```bash
./python-interpreter.py --script 'raise ValueError("Test error")' --format json
```

Output:
```json
{
  "success": false,
  "stdout": "",
  "stderr": "",
  "error": "Test error",
  "traceback": "Traceback (most recent call last):\n..."
}
```

## Testing

Run the test suite:

```bash
./test.sh
```

This will run various test scenarios including:
- Simple print statements
- Math calculations
- JSON output
- Loops and multi-line scripts
- Error handling
- Library imports

## Security Considerations

**WARNING**: This service executes arbitrary Python code. It should only be used in trusted environments.

- The service has access to all Python built-in functions
- It can import and use any installed Python packages
- It runs with the permissions of the user executing it
- Do not expose this service to untrusted users or networks

## Exit Codes

- `0`: Success
- `1`: Error during script execution

## Notes

- The script execution environment includes all Python built-ins
- Any imports must be done within the script code
- Stdout and stderr are captured separately
- In text format, only stdout is printed to stdout (stderr goes to stderr)
- In JSON format, both stdout and stderr are included in the response object
