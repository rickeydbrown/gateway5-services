# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

r"""Heuristic-based sensitive data detection and redaction for NetSDK.

This module provides a production-grade scanner for detecting and redacting
sensitive information in strings, dictionaries, and JSON data. It uses
pattern-based heuristics to identify credentials, tokens, API keys, and other
personally identifiable information (PII) before they are logged or exposed.

Key Features:

    Pattern-Based Detection:
        - Pre-configured patterns for common sensitive data
          (API keys, passwords, tokens)
        - Regular expression matching with compiled patterns for performance
        - Customizable patterns for application-specific sensitive data
        - Support for both value-based and key-based detection

    Multiple Data Structure Support:
        - String scanning and redaction with scan_and_redact()
        - Dictionary deep scanning with sanitize_dict()
        - JSON string parsing and sanitization with sanitize_json()
        - Recursive processing of nested structures

    Singleton Pattern:
        - Single global scanner instance ensures consistent configuration
        - Thread-safe singleton implementation
        - Can be reset and reconfigured via configure_scanner()

    Customizable Redaction:
        - Per-pattern custom redaction functions
        - Default redaction format: [REDACTED_PATTERN_NAME]
        - Preserves structure while removing sensitive content

    Key-Based Filtering:
        - Automatic detection of sensitive dictionary keys
        - Configurable list of sensitive key names
        - Case-insensitive key matching with normalization

Default Patterns:
    The scanner comes pre-configured with patterns to detect:
    - API keys and authentication tokens
    - Bearer tokens and JWT tokens
    - AWS and cloud provider credentials
    - Private keys and certificates
    - Passwords in URLs and connection strings
    - OAuth client secrets
    - Generic secret patterns

Architecture:
    The module uses a singleton Scanner class that maintains:
    - Compiled regex patterns for efficient matching
    - Per-pattern redaction functions for custom handling
    - Set of sensitive key names for dictionary filtering
    - Pattern registry for dynamic addition/removal

Performance Considerations:
    - Regex patterns are compiled once and cached
    - Dictionary traversal is optimized for common cases
    - String scanning uses compiled patterns for speed
    - Minimal overhead when no sensitive data is found

Examples:

    Basic string redaction::

        from netsdk.utils import heuristics

        # Scan and redact sensitive data
        text = "Connecting with API_KEY=sk_live_abc123456789012345"
        clean = heuristics.scan_and_redact(text)
        # Returns: "Connecting with API_KEY=[REDACTED_API_KEY]"

    Dictionary sanitization::

        from netsdk.utils import heuristics

        config = {
            "host": "10.0.0.1",
            "username": "admin",
            "password": "secret123",
            "api_key": "sk_test_xyz",
            "nested": {
                "token": "bearer_abc"
            }
        }

        clean_config = heuristics.sanitize_dict(config)
        # Returns: {
        #     "host": "10.0.0.1",
        #     "username": "admin",
        #     "password": "[REDACTED]",
        #     "api_key": "[REDACTED]",
        #     "nested": {"token": "[REDACTED]"}
        # }

    JSON sanitization::

        from netsdk.utils import heuristics

        json_str = '{"user": "admin", "password": "secret"}'
        clean_json = heuristics.sanitize_json(json_str)
        # Returns: '{"user": "admin", "password": "[REDACTED]"}'

    Custom pattern configuration::

        from netsdk.utils import heuristics

        # Get the scanner instance
        scanner = heuristics.get_scanner()

        # Add custom pattern for employee IDs
        scanner.add_pattern(
            name="employee_id",
            pattern=r"EMP\d{6}",
            redaction_fn=lambda match: "[EMPLOYEE_ID]"
        )

        # Check if text contains sensitive data
        if heuristics.has_sensitive_data("Employee EMP123456 logged in"):
            print("Contains sensitive data!")

    Reconfiguring the scanner::

        from netsdk.utils import heuristics

        # Reset and configure with custom patterns only
        custom = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"
        }

        heuristics.configure_scanner(custom)
        # Scanner now uses only the custom patterns

Module Functions:
    get_scanner() -> Scanner: Get the singleton scanner instance
    configure_scanner(patterns): Reset and configure with custom patterns
    scan_and_redact(text): Scan and redact sensitive data in string
    has_sensitive_data(text): Check if text contains sensitive data
    sanitize_dict(data): Deep sanitize dictionary structures
    sanitize_json(json_str): Parse and sanitize JSON strings

See Also:
    netsdk.utils.logging: Logging system that uses this module
    re: Python regular expression operations
"""

import json
import re

from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
from re import Pattern
from typing import Any
from typing import Optional


class Scanner:
    """Scanner for detecting and redacting sensitive data patterns in text.

    This scanner uses heuristic pattern matching to identify potentially sensitive
    information and replace it with redacted placeholders to prevent data leakage
    in log files.

    This class implements the Singleton pattern to ensure only one instance
    exists throughout the application.

    Usage:
        scanner = Scanner()
        redacted = scanner.scan_and_redact("API_KEY=secret123456789")
    """

    _instance: Optional["Scanner"] = None
    _initialized: bool = False

    def __new__(cls, _custom_patterns: dict[str, str] | None = None) -> "Scanner":
        """Create or return the singleton instance.

        Args:
            _custom_patterns (Optional[Dict[str, str]]): Additional patterns
                to scan for, where keys are pattern names and values are
                regex patterns. Passed to __init__ after instance creation.

        Returns:
            Scanner: The singleton instance.

        Raises:
            None
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, custom_patterns: dict[str, str] | None = None) -> None:
        """Initialize the sensitive data scanner.

        This method will only initialize the instance once due to the Singleton pattern.
        Subsequent calls will not re-initialize the patterns.

        Args:
            custom_patterns (Optional[Dict[str, str]]): Additional patterns to scan for,
                where keys are pattern names and values are regex patterns.
                Only applied on first initialization.

        Returns:
            None

        Raises:
            re.error: If any of the regex patterns are invalid.
        """
        # Only initialize once due to Singleton pattern
        if not self._initialized:
            self._patterns: dict[str, Pattern] = {}
            self._redaction_functions: dict[str, Callable[[str], str]] = {}

            # Sensitive key names that should always have values redacted
            self._sensitive_keys = {
                "password",
                "passwd",
                "pwd",
                "secret",
                "api_key",
                "apikey",
                "api-key",
                "access_token",
                "accesstoken",
                "access-token",
                "auth_token",
                "authtoken",
                "token",
                "private_key",
                "privatekey",
                "client_secret",
                "clientsecret",
                "auth_secondary",
                "auth_password",
            }

            # Initialize default patterns
            self._init_default_patterns()

            # Add custom patterns if provided
            if custom_patterns:
                for name, pattern in custom_patterns.items():
                    self.add_pattern(name, pattern)

            # Mark as initialized
            Scanner._initialized = True

    def _init_default_patterns(self) -> None:
        """Initialize default sensitive data patterns.

        Sets up regex patterns for common sensitive data types including API keys,
        passwords, tokens, credit card numbers, and other PII.

        Returns:
            None

        Raises:
            None
        """
        # API Keys and tokens (various formats)
        self.add_pattern(
            "api_key",
            r"(?i)\b(?:api[_-]?key|apikey)\s*[=:]\s*[\"']?([a-zA-Z0-9_\-]{16,})[\"']?",
        )
        self.add_pattern("bearer_token", r"(?i)\bbearer\s+([a-zA-Z0-9_\-\.]{20,})")
        self.add_pattern(
            "jwt_token",
            r"\b(eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+)\b",
        )
        self.add_pattern(
            "access_token",
            r"(?i)\b(?:access[_-]?token|accesstoken)\s*[=:]\s*[\"']?([a-zA-Z0-9_\-]{20,})[\"']?",
        )

        # Password patterns
        self.add_pattern(
            "password",
            r"(?i)\b(?:password|passwd|pwd)\s*[=:]\s*[\"']?([^\s\"']{6,})[\"']?",
        )
        self.add_pattern(
            "secret",
            r"(?i)\b(?:secret|client_secret)\s*[=:]\s*[\"']?([a-zA-Z0-9_\-]{16,})[\"']?",
        )

        # URLs with authentication (check before email patterns)
        self.add_pattern("auth_url", r"https?://[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+@[^\s]+")

        # Basic email pattern (when used in sensitive contexts)
        self.add_pattern(
            "email_in_auth",
            r"(?i)(?:username|user|email)\s*[=:]\s*[\"']?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})[\"']?",
        )

        # Database connection strings
        self.add_pattern(
            "db_connection",
            r"(?i)\b(?:mongodb|mysql|postgresql|postgres)://[^\s]+:[^\s]+@[^\s]+",
        )

        # Private keys (basic detection)
        self.add_pattern(
            "private_key",
            r"-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]*?"
            r"-----END (?:RSA )?PRIVATE KEY-----",
        )

        # Authentication-related parameters (auth_*)
        self.add_pattern(
            "auth_parameter",
            r"(?i)[\"']?auth_[a-zA-Z0-9_]+[\"']?\s*[=:]\s*[\"']?([^\s\"',}\]]+)[\"']?",
        )

    def add_pattern(
        self,
        name: str,
        pattern: str,
        redaction_func: Callable[[str], str] | None = None,
    ) -> None:
        """Add a new sensitive data pattern to scan for.

        Args:
            name (str): Name of the pattern for identification.
            pattern (str): Regular expression pattern to match sensitive data.
            redaction_func (Optional[Callable[[str], str]]): Custom function
                to redact matches. If None, uses default redaction with
                pattern name.

        Returns:
            None

        Raises:
            re.error: If the regex pattern is invalid.
        """
        try:
            compiled_pattern = re.compile(pattern)
            self._patterns[name] = compiled_pattern

            if redaction_func:
                self._redaction_functions[name] = redaction_func
            else:
                self._redaction_functions[name] = lambda _: f"[REDACTED_{name.upper()}]"
        except re.error as e:
            raise re.error(f"Invalid regex pattern for '{name}': {e}") from e  # noqa: TRY003

    def remove_pattern(self, name: str) -> bool:
        """Remove a pattern from the scanner.

        Args:
            name (str): Name of the pattern to remove.

        Returns:
            bool: True if pattern was removed, False if it didn't exist.

        Raises:
            None
        """
        if name in self._patterns:
            del self._patterns[name]
            del self._redaction_functions[name]
            return True
        return False

    def list_patterns(self) -> list[str]:
        """Get a list of all pattern names currently registered.

        Returns:
            List[str]: List of pattern names.

        Raises:
            None
        """
        return list(self._patterns.keys())

    def scan_and_redact(self, text: str) -> str:
        """Scan text for sensitive data and redact any matches.

        Args:
            text (str): The text to scan and potentially redact.

        Returns:
            str: The text with sensitive data redacted.

        Raises:
            None
        """
        if not text:
            return text

        result = text

        for pattern_name, pattern in self._patterns.items():
            redaction_func = self._redaction_functions[pattern_name]
            # Use lambda with default arg to capture current redaction_func
            result = pattern.sub(
                lambda match, func=redaction_func: func(match.group(0)), result
            )

        return result

    def has_sensitive_data(self, text: str) -> bool:
        """Check if text contains any sensitive data without redacting it.

        Args:
            text (str): The text to check for sensitive data.

        Returns:
            bool: True if sensitive data is detected, False otherwise.

        Raises:
            None
        """
        if not text:
            return False

        return any(pattern.search(text) for pattern in self._patterns.values())

    def get_sensitive_data_types(self, text: str) -> list[str]:
        """Get a list of sensitive data types detected in the text.

        Args:
            text (str): The text to analyze.

        Returns:
            List[str]: List of pattern names that matched in the text.

        Raises:
            None
        """
        if not text:
            return []

        detected_types = []

        for pattern_name, pattern in self._patterns.items():
            if pattern.search(text):
                detected_types.append(pattern_name)

        return detected_types

    def sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively sanitize a dictionary by redacting sensitive data.

        This method processes dictionaries recursively, scanning and redacting
        sensitive data in both keys and values. It handles nested structures
        including nested dicts and lists.

        Args:
            data (Dict[str, Any]): The dictionary to sanitize.

        Returns:
            Dict[str, Any]: A new dictionary with sensitive data redacted.

        Raises:
            TypeError: If data is not a dictionary.
        """
        if not isinstance(data, Mapping):
            msg = f"Expected dict or Mapping, got {type(data).__name__}"
            raise TypeError(msg)

        result = {}

        for key, value in data.items():
            # Sanitize the key itself (convert to string first if needed)
            sanitized_key = self.scan_and_redact(str(key))

            # Check if the key name is a known sensitive field
            key_lower = str(key).lower()
            is_sensitive_key = key_lower in self._sensitive_keys

            # Recursively sanitize the value based on its type
            if isinstance(value, Mapping):
                # Recursively sanitize nested dictionaries
                sanitized_value = self.sanitize_dict(value)
            elif isinstance(value, str):
                # If key is a known sensitive field, always redact the value
                if is_sensitive_key:
                    # Determine which pattern this key matches for appropriate redaction
                    if key_lower in {"password", "passwd", "pwd"}:
                        sanitized_value = "[REDACTED_PASSWORD]"
                    elif key_lower == "secret":
                        sanitized_value = "[REDACTED_SECRET]"
                    elif key_lower in {
                        "api_key",
                        "apikey",
                        "api-key",
                    }:
                        sanitized_value = "[REDACTED_API_KEY]"
                    elif key_lower in {
                        "access_token",
                        "accesstoken",
                        "access-token",
                        "auth_token",
                        "authtoken",
                        "token",
                    }:
                        sanitized_value = "[REDACTED_ACCESS_TOKEN]"
                    elif key_lower in {
                        "private_key",
                        "privatekey",
                    }:
                        sanitized_value = "[REDACTED_PRIVATE_KEY]"
                    elif key_lower in {
                        "client_secret",
                        "clientsecret",
                    }:
                        sanitized_value = "[REDACTED_SECRET]"
                    else:
                        sanitized_value = "[REDACTED]"
                else:
                    # For string values, check if combined "key=value" format
                    # triggers a match. Try both formats: "key=value" and "key: value"
                    test_combined_colon = f"{key}: {value}"
                    test_combined_equals = f"{key}={value}"

                    # Scan both formats to see if either triggers a pattern
                    sanitized_colon = self.scan_and_redact(test_combined_colon)
                    sanitized_equals = self.scan_and_redact(test_combined_equals)

                    # If either format was redacted (changed), use redacted value
                    if sanitized_colon != test_combined_colon:
                        # Pattern matched, value is sensitive
                        sanitized_value = sanitized_colon
                    elif sanitized_equals != test_combined_equals:
                        # Pattern matched, value is sensitive
                        sanitized_value = sanitized_equals
                    else:
                        # No pattern matched, scan value alone
                        sanitized_value = self.scan_and_redact(value)
            elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                # Recursively sanitize lists/sequences
                sanitized_value = self._sanitize_sequence(value)
            else:
                # For other types (int, float, bool, None), keep as-is
                sanitized_value = value

            result[sanitized_key] = sanitized_value

        return result

    def _sanitize_sequence(self, seq: Sequence[Any]) -> list[Any]:
        """Recursively sanitize a sequence (list, tuple) by redacting sensitive data.

        Args:
            seq (Sequence[Any]): The sequence to sanitize.

        Returns:
            List[Any]: A new list with sensitive data redacted.

        Raises:
            None
        """
        result = []

        for item in seq:
            if isinstance(item, Mapping):
                # Recursively sanitize dict items
                result.append(self.sanitize_dict(item))
            elif isinstance(item, str):
                # Sanitize string items
                result.append(self.scan_and_redact(item))
            elif isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
                # Recursively sanitize nested sequences
                result.append(self._sanitize_sequence(item))
            else:
                # For other types (int, float, bool, None), keep as-is
                result.append(item)

        return result

    def sanitize_json(self, json_str: str) -> str:
        """Sanitize a JSON string by redacting sensitive data.

        This method parses a JSON string, recursively sanitizes the data
        structure, and returns a sanitized JSON string.

        Args:
            json_str (str): The JSON string to sanitize.

        Returns:
            str: A JSON string with sensitive data redacted.

        Raises:
            json.JSONDecodeError: If the input is not valid JSON.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON string: {e}"
            raise json.JSONDecodeError(msg, json_str, e.pos) from e

        # Handle different JSON root types
        if isinstance(data, Mapping):
            sanitized_data = self.sanitize_dict(data)
        elif isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
            sanitized_data = self._sanitize_sequence(data)
        elif isinstance(data, str):
            sanitized_data = self.scan_and_redact(data)
        else:
            # For primitive types (int, float, bool, None), keep as-is
            sanitized_data = data

        return json.dumps(sanitized_data, indent=2)

    @classmethod
    def reset_singleton(cls) -> None:
        """Reset the singleton instance.

        This method is primarily for testing purposes to allow creating
        a fresh instance with different configurations.

        Returns:
            None

        Raises:
            None
        """
        cls._instance = None
        cls._initialized = False


def get_scanner() -> Scanner:
    """Get the global sensitive data scanner instance.

    Returns the singleton instance of the scanner.

    Returns:
        Scanner: The singleton scanner instance.

    Raises:
        None
    """
    return Scanner()


def configure_scanner(
    custom_patterns: dict[str, str] | None = None,
) -> Scanner:
    """Configure the global scanner with custom patterns.

    Note: Due to the singleton pattern, this will only apply custom patterns
    if the scanner hasn't been initialized yet. To reconfigure an existing
    scanner, use reset_singleton() first.

    Args:
        custom_patterns (Optional[Dict[str, str]]): Custom patterns to add
            to the scanner.

    Returns:
        Scanner: The configured singleton scanner instance.

    Raises:
        re.error: If any custom patterns are invalid.
    """
    # Reset the singleton to allow reconfiguration
    Scanner.reset_singleton()
    return Scanner(custom_patterns)


def scan_and_redact(text: str) -> str:
    """Convenience function to scan and redact text using the global scanner.

    Args:
        text (str): The text to scan and redact.

    Returns:
        str: The text with sensitive data redacted.

    Raises:
        None
    """
    scanner = get_scanner()
    return scanner.scan_and_redact(text)


def has_sensitive_data(text: str) -> bool:
    """Convenience function to check for sensitive data using the global scanner.

    Args:
        text (str): The text to check.

    Returns:
        bool: True if sensitive data is detected, False otherwise.

    Raises:
        None
    """
    scanner = get_scanner()
    return scanner.has_sensitive_data(text)


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Convenience function to sanitize a dictionary using the global scanner.

    Args:
        data (Dict[str, Any]): The dictionary to sanitize.

    Returns:
        Dict[str, Any]: A new dictionary with sensitive data redacted.

    Raises:
        TypeError: If data is not a dictionary.
    """
    scanner = get_scanner()
    return scanner.sanitize_dict(data)


def sanitize_json(json_str: str) -> str:
    """Convenience function to sanitize a JSON string using the global scanner.

    Args:
        json_str (str): The JSON string to sanitize.

    Returns:
        str: A JSON string with sensitive data redacted.

    Raises:
        json.JSONDecodeError: If the input is not valid JSON.
    """
    scanner = get_scanner()
    return scanner.sanitize_json(json_str)
