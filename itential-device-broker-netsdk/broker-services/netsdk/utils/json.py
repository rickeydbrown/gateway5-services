# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""JSON serialization and deserialization utilities for the Itential Python SDK.

This module provides wrapper functions for JSON encoding and decoding operations
with comprehensive error handling. All JSON operations raise SDK-specific
exceptions and log errors for debugging.

Functions
---------
loads:
    Parse a JSON formatted string into a Python dict or list object.
    Wraps json.loads() with error handling and logging.

dumps:
    Convert a Python dict or list object into a JSON formatted string.
    Wraps json.dumps() with error handling and logging.

Error Handling
--------------
All functions in this module raise SerializationError exceptions for JSON
parsing and encoding failures. This provides consistent error handling across
the SDK and makes it easier to catch and handle JSON-related errors.

Common error scenarios:

Deserialization errors (loads):
    - Malformed JSON syntax (missing brackets, quotes, commas)
    - Invalid JSON structure
    - Unexpected end of JSON input
    - Invalid escape sequences
    - Invalid Unicode characters

Serialization errors (dumps):
    - Non-serializable Python objects (datetime, custom classes)
    - Circular references in data structures
    - Invalid data types for JSON encoding
    - Encoding errors

Logging
-------
All JSON operations are logged at ERROR level when failures occur, with full
exception details including tracebacks. This helps with debugging JSON parsing
and serialization issues in production.

Examples
--------
Parsing JSON strings::

    from ipsdk import jsonutils
    from ipsdk.exceptions import SerializationError

    # Parse valid JSON
    data = jsonutils.loads('{"name": "workflow1", "enabled": true}')
    print(data["name"])  # "workflow1"

    # Parse JSON array
    items = jsonutils.loads('[1, 2, 3, 4, 5]')
    print(len(items))  # 5

    # Handle parsing errors
    try:
        invalid = jsonutils.loads('{"invalid": json}')
    except SerializationError as e:
        print(f"Failed to parse JSON: {e}")

Converting to JSON strings::

    from ipsdk import jsonutils
    from ipsdk.exceptions import SerializationError

    # Serialize dict to JSON
    data = {"name": "workflow1", "enabled": True}
    json_str = jsonutils.dumps(data)
    print(json_str)  # '{"name": "workflow1", "enabled": true}'

    # Serialize list to JSON
    items = [1, 2, 3, 4, 5]
    json_str = jsonutils.dumps(items)
    print(json_str)  # '[1, 2, 3, 4, 5]'

    # Handle serialization errors
    import datetime
    try:
        invalid = jsonutils.dumps({"date": datetime.datetime.now()})
    except SerializationError as e:
        print(f"Failed to serialize: {e}")

Response parsing::

    from ipsdk import platform_factory
    from ipsdk import jsonutils

    platform = platform_factory()
    response = platform.get("/api/v2.0/workflows")

    # Response.json() uses jsonutils internally
    # But you can also parse response text manually
    try:
        data = jsonutils.loads(response.text)
        print(f"Found {len(data)} workflows")
    except SerializationError as e:
        print(f"Invalid JSON response: {e}")
"""

import json

from netsdk.core import exceptions
from netsdk.utils import logging


@logging.trace
def loads(s: str) -> dict | list:
    """Convert a JSON formatted string to a dict or list object

    Args:
        s (str): The JSON object represented as a string

    Returns:
        A dict or list object
    """
    try:
        return json.loads(s)
    except json.JSONDecodeError as exc:
        logging.exception(exc)
        raise exceptions.SerializationError(f"Failed to parse JSON: {exc!s}")
    except Exception as exc:
        logging.exception(exc)
        raise exceptions.SerializationError(f"Unexpected error parsing JSON: {exc!s}")


@logging.trace
def dumps(o: dict | list) -> str:
    """Convert a dict or list to a JSON string

    Args:
        o (list, dict): The list or dict object to dump to a string

    Returns:
        A JSON string representation
    """
    try:
        return json.dumps(o)
    except (TypeError, ValueError) as exc:
        logging.exception(exc)
        raise exceptions.SerializationError(
            f"Failed to serialize object to JSON: {exc!s}"
        )
    except Exception as exc:
        logging.exception(exc)
        raise exceptions.SerializationError(
            f"Unexpected error serializing JSON: {exc!s}"
        )
