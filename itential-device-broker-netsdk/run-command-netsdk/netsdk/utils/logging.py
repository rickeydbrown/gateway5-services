# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

from __future__ import annotations

r"""Comprehensive logging system for the Itential Python SDK.

This module provides a full-featured logging implementation with support for
custom log levels, function tracing, and sensitive data filtering.

Features:
    - Extended logging levels:
        - TRACE (5) - For detailed function invocation tracing
        - FATAL (90) - For fatal errors that exit the application
        - NONE (100) - To disable all logging output
    - Convenience functions for all log levels: debug(), info(), warning(),
      error(), critical(), fatal(), exception(), trace()
    - Configuration functions:
        - set_level() - Set logging level with optional httpx/httpcore control
        - initialize() - Reset and initialize logging handlers
        - get_logger() - Get the main application logger
    - Sensitive data filtering:
        - enable_sensitive_data_filtering() - Enable PII/credential redaction
        - disable_sensitive_data_filtering() - Disable filtering
        - configure_sensitive_data_patterns() - Add custom patterns
        - add_sensitive_data_pattern() - Add individual pattern
        - remove_sensitive_data_pattern() - Remove pattern
        - get_sensitive_data_patterns() - List configured patterns
    - httpx/httpcore logging control via propagate parameter
    - Automatic initialization with stderr handler

Logging Levels:
    NOTSET (0), TRACE (5), DEBUG (10), INFO (20), WARNING (30), ERROR (40),
    CRITICAL (50), FATAL (90), NONE (100)

Example:
    Basic usage with console logging::

        from ipsdk import logging

        # Set logging level
        logging.set_level(logging.INFO)

        # Log messages at different levels
        logging.info("Application started")
        logging.warning("Configuration file not found, using defaults")
        logging.error("An error occurred")

    Function tracing for debugging::

        from ipsdk import logging

        # Enable TRACE level for detailed function tracing
        logging.set_level(logging.TRACE)

        @logging.trace
        def process_data(data):
            # ... function implementation
            return result

        # Calling process_data will log:
        # "→ module.process_data" on entry
        # "← module.process_data (1.23ms)" on exit

    Fatal errors that exit the application::

        from ipsdk import logging

        if critical_error:
            logging.fatal("Critical failure, cannot continue")
            # This will log at FATAL level, print to console, and exit with code 1

    Sensitive data filtering::

        from ipsdk import logging

        # Enable sensitive data filtering
        logging.enable_sensitive_data_filtering()

        # Add custom pattern for SSN
        logging.add_sensitive_data_pattern(
            "ssn",
            r"(?:SSN|social[_-]?security):\s*(\d{3}-\d{2}-\d{4})"
        )

        # Log messages will automatically redact sensitive data
        logging.info("User credentials: api_key=secret123456789012345")
        # Output: "User credentials: [REDACTED_API_KEY]"

    Controlling httpx/httpcore logging::

        from ipsdk import logging

        # Enable httpx logging along with application logging
        logging.set_level(logging.DEBUG, propagate=True)

    Disabling all logging::

        from ipsdk import logging

        # Set to NONE to disable all log output
        logging.set_level(logging.NONE)
"""

import contextlib  # noqa: E402
import inspect  # noqa: E402
import logging  # noqa: E402
import sys  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402

from collections.abc import Callable  # noqa: E402
from functools import cache  # noqa: E402
from functools import partial  # noqa: E402
from functools import wraps  # noqa: E402
from typing import Any  # noqa: E402
from typing import TypeVar  # noqa: E402

from netsdk import metadata  # noqa: E402
from netsdk.utils import heuristics  # noqa: E402

logging_message_format = "%(asctime)s: [%(name)s] %(levelname)s: %(message)s"

# Add the FATAL logging level
logging.FATAL = 90  # type: ignore[misc]
logging.addLevelName(logging.FATAL, "FATAL")

logging.NONE = logging.FATAL + 10
logging.addLevelName(logging.NONE, "NONE")

logging.TRACE = 5
logging.addLevelName(logging.TRACE, "TRACE")

# Logging level constants that wrap stdlib logging module constants
NOTSET = logging.NOTSET
TRACE = logging.TRACE
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
FATAL = logging.FATAL
NONE = logging.NONE

# Set initial log level to NONE (disabled)
logging.getLogger(metadata.name).setLevel(NONE)

# Thread-safe configuration for sensitive data filtering
_filtering_lock = threading.RLock()
_sensitive_data_filtering_enabled = True


def log(lvl: int, msg: str, *args: Any) -> None:
    """Send the log message with the specified level.

    This function will send the log message to the logger with the specified
    logging level. If sensitive data filtering is enabled, the message will
    be scanned and any sensitive information (such as API keys, passwords,
    tokens) will be redacted before logging.

    This function should not be directly invoked. Use one of the convenience
    functions (debug, info, warning, error, critical, fatal) to send a log
    message with a given level.

    This function is thread-safe. The sensitive data filtering check is
    protected by a reentrant lock to prevent race conditions.

    Args:
        lvl (int): The logging level of the message.
        msg (str): The message to write to the logger. Can contain format
            specifiers (e.g., %s, %d) if args are provided.
        *args: Arguments to format into the message. Dictionary arguments
            will be sanitized before formatting.

    Returns:
        None

    Raises:
        None
    """
    # Apply sensitive data filtering if enabled (thread-safe)
    with _filtering_lock:
        if _sensitive_data_filtering_enabled:
            # Sanitize any dictionary arguments before formatting
            if args:
                sanitized_args = []
                for arg in args:
                    if isinstance(arg, dict):
                        sanitized_args.append(heuristics.sanitize_dict(arg))
                    else:
                        sanitized_args.append(arg)
                args = tuple(sanitized_args)

            # Format the message if args are provided
            # If formatting fails, fall back to unformatted message
            if args:
                with contextlib.suppress(TypeError, ValueError):
                    msg = msg % args

            # Scan and redact the final formatted message
            msg = heuristics.scan_and_redact(msg)
        elif args:
            # No filtering, but still need to format if args provided
            with contextlib.suppress(TypeError, ValueError):
                msg = msg % args

    logging.getLogger(metadata.name).log(lvl, msg)


# Convenience functions for different logging levels
debug = partial(log, logging.DEBUG)
info = partial(log, logging.INFO)
warning = partial(log, logging.WARNING)
error = partial(log, logging.ERROR)
critical = partial(log, logging.CRITICAL)


T = TypeVar("T", bound=Callable[..., Any])


def trace(f: T) -> T:
    """Decorator to automatically trace function invocations.

    This decorator logs trace-level messages at function entry and exit,
    automatically extracting module and qualified name information from
    the function object. Useful for detailed debugging and execution flow
    tracking.

    The decorator works with both synchronous and asynchronous functions,
    logging entry with '→' and exit with '←' symbols. Exit logs include
    the execution time in milliseconds.

    Args:
        f (Callable): The function to wrap with tracing

    Returns:
        Callable: The wrapped function with tracing enabled

    Raises:
        None

    Example:
        @trace
        def process_data(data):
            # Function implementation
            return result

        # Logs: "→ module.process_data" on entry
        # Logs: "← module.process_data (1.23ms)" on exit
    """
    func_name = f"{f.__module__}.{f.__qualname__}"

    if inspect.iscoroutinefunction(f):

        @wraps(f)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            log(logging.TRACE, f"→ {func_name}")
            try:
                result = await f(*args, **kwargs)
            except Exception:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                log(logging.TRACE, f"← {func_name} (exception, {elapsed_ms:.2f}ms)")
                raise
            else:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                log(logging.TRACE, f"← {func_name} ({elapsed_ms:.2f}ms)")
                return result

        return async_wrapper  # type: ignore[return-value]

    @wraps(f)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        log(logging.TRACE, f"→ {func_name}")
        try:
            result = f(*args, **kwargs)
        except Exception:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            log(logging.TRACE, f"← {func_name} (exception, {elapsed_ms:.2f}ms)")
            raise
        else:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            log(logging.TRACE, f"← {func_name} ({elapsed_ms:.2f}ms)")
            return result

    return sync_wrapper  # type: ignore[return-value]


def exception(exc: str | Exception) -> None:
    """Log an exception error with full traceback.

    This function logs an exception at ERROR level, including the full
    traceback information to help with debugging. The traceback shows
    the complete call stack from where the exception was raised.

    Args:
        exc: Either an Exception object or a string message. If a string is
            provided, the current exception from sys.exc_info() will be used.

    Returns:
        None

    Raises:
        None
    """
    # If a string message is provided, get the current exception from context
    if isinstance(exc, str):
        exc_type, exc_value, exc_tb = sys.exc_info()
        if exc_value is not None:
            # Log the message first, then the exception
            log(logging.ERROR, exc)
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
            tb_text = "".join(tb_lines)
            log(logging.ERROR, tb_text)
        else:
            # No exception in context, just log the message
            log(logging.ERROR, exc)
    else:
        # Format the exception with full traceback
        tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        tb_text = "".join(tb_lines)
        log(logging.ERROR, tb_text)


def fatal(msg: str) -> None:
    """Log a fatal error and exit the application.

    A fatal error will log the message using level 90 (FATAL) and print
    an error message to stderr. It will then exit the application with
    return code 1.

    Args:
        msg (str): The message to print.

    Returns:
        None

    Raises:
        SystemExit: Always raised with exit code 1 after logging the fatal error.
    """
    log(logging.FATAL, msg)
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


@cache
def _get_loggers() -> set[logging.Logger]:
    """Get all relevant loggers for the application.

    Retrieves loggers that belong to the Itential MCP application and its
    dependencies (ipsdk, FastMCP). Results are cached to improve performance
    on subsequent calls.

    This function is thread-safe. It creates a snapshot of logger names before
    iteration to prevent issues if the logger dictionary is modified by other
    threads during iteration.

    Note:
        The cached result may not immediately reflect loggers created after
        the first call. Call _get_loggers.cache_clear() to force a refresh
        if needed.

    Returns:
        set[logging.Logger]: Set of logger instances for the application
            and dependencies.
    """
    loggers = set()
    # Create a snapshot of logger names to prevent race conditions during iteration
    logger_names = list(logging.Logger.manager.loggerDict.keys())
    for name in logger_names:
        if name.startswith((metadata.name, "httpx")):
            loggers.add(logging.getLogger(name))
    return loggers


def get_logger() -> logging.Logger:
    """Get the main application logger.

    Args:
        None

    Returns:
        logging.Logger: The logger instance for the ipsdk application.

    Raises:
        None
    """
    return logging.getLogger(metadata.name)


def set_level(lvl: int | str, *, propagate: bool = False) -> None:
    """Set logging level for all loggers in the current Python process.

    Args:
        lvl (int | str): Logging level (e.g., logging.INFO, logging.DEBUG, or "NONE").
            This is a required argument. Can be an integer level or the string "NONE"
            to disable all logging.
        propagate (bool): Setting this value to True will also turn on
            logging for httpx and httpcore. Defaults to False.

    Returns:
        None

    Raises:
        TypeError: If lvl is a string other than "NONE".
    """
    logger = get_logger()

    # Convert string "NONE" to NONE constant
    if isinstance(lvl, str):
        if lvl == "NONE":
            lvl = NONE
        else:
            raise TypeError(  # noqa: TRY003
                f"Invalid level string: {lvl}. Only 'NONE' is supported as a string."
            )

    logger.setLevel(lvl)
    logger.propagate = False

    logger.log(logging.INFO, "%s version %s", metadata.name, metadata.version)
    logger.log(logging.INFO, "Logging level set to %s", lvl)

    if propagate is True:
        # Clear cache to ensure we get all current loggers including httpx
        _get_loggers.cache_clear()
        for logger in _get_loggers():
            logger.setLevel(lvl)


def enable_sensitive_data_filtering() -> None:
    """Enable sensitive data filtering in log messages.

    When enabled, log messages will be scanned for potentially sensitive
    information (such as passwords, tokens, API keys) and redacted before
    being written to the log output.

    This function is thread-safe.

    Returns:
        None

    Raises:
        None
    """
    global _sensitive_data_filtering_enabled  # noqa: PLW0603
    with _filtering_lock:
        _sensitive_data_filtering_enabled = True


def disable_sensitive_data_filtering() -> None:
    """Disable sensitive data filtering in log messages.

    When disabled, log messages will be written as-is without scanning
    for sensitive information. Use with caution in production environments
    as this may expose sensitive data in log files.

    This function is thread-safe.

    Returns:
        None

    Raises:
        None
    """
    global _sensitive_data_filtering_enabled  # noqa: PLW0603
    with _filtering_lock:
        _sensitive_data_filtering_enabled = False


def is_sensitive_data_filtering_enabled() -> bool:
    """Check if sensitive data filtering is currently enabled.

    Returns the current state of sensitive data filtering to determine
    if log messages are being scanned and redacted.

    This function is thread-safe.

    Returns:
        bool: True if filtering is enabled, False otherwise

    Raises:
        None
    """
    with _filtering_lock:
        return _sensitive_data_filtering_enabled


def configure_sensitive_data_patterns(
    custom_patterns: dict[str, str | None] | None = None,
) -> None:
    """Configure custom patterns for sensitive data detection.

    Allows configuration of custom regular expression patterns to identify
    and redact sensitive information in log messages. Each pattern should
    match sensitive data that needs to be protected.

    Args:
        custom_patterns (dict[str, str | None]): Dictionary of custom regex
            patterns to add to the sensitive data scanner. Keys are pattern
            names (for identification) and values are regex patterns to match
            sensitive data. If None, no patterns are added

    Returns:
        None

    Raises:
        re.error: If any of the custom patterns are invalid regex expressions
    """
    heuristics.configure_scanner(custom_patterns)


def get_sensitive_data_patterns() -> list[str]:
    """Get a list of all sensitive data patterns currently configured.

    Returns the names of all patterns currently registered with the sensitive
    data scanner for identifying and redacting sensitive information.

    Args:
        None

    Returns:
        list[str]: List of pattern names that are being scanned for

    Raises:
        None
    """
    return heuristics.get_scanner().list_patterns()


def add_sensitive_data_pattern(name: str, pattern: str) -> None:
    """Add a new sensitive data pattern to scan for.

    Registers a new regular expression pattern with the sensitive data scanner.
    The pattern will be used to identify and redact matching sensitive information
    in log messages when filtering is enabled.

    Args:
        name (str): Unique name for the pattern, used for identification and
            later removal if needed
        pattern (str): Regular expression pattern to match sensitive data

    Returns:
        None

    Raises:
        re.error: If the regex pattern is invalid or malformed
    """
    heuristics.get_scanner().add_pattern(name, pattern)


def remove_sensitive_data_pattern(name: str) -> bool:
    """Remove a sensitive data pattern from scanning.

    Unregisters a previously added sensitive data pattern from the scanner.
    After removal, the pattern will no longer be used to identify and
    redact sensitive information in log messages.

    Args:
        name (str): Name of the pattern to remove (as provided when the
            pattern was added)

    Returns:
        bool: True if the pattern was found and removed, False if the
            pattern name didn't exist in the scanner

    Raises:
        None
    """
    return heuristics.get_scanner().remove_pattern(name)


def initialize() -> None:
    """Initialize logging configuration for the application.

    Resets all managed loggers by removing their existing handlers and
    replacing them with a standard StreamHandler that writes to stderr.
    This ensures consistent logging configuration across all related loggers.

    Warning:
        This function is NOT thread-safe. It should only be called during
        application startup before any logging activity begins. Calling this
        function while other threads are actively logging may result in lost
        log messages or exceptions.

    Returns:
        None

    Raises:
        None
    """
    # Clear cache to ensure we get all current loggers
    _get_loggers.cache_clear()

    for logger in _get_loggers():
        handlers = logger.handlers[:]

        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()

        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(logging.Formatter(logging_message_format))

        logger.addHandler(stream_handler)
        logger.setLevel(NONE)
        logger.propagate = False
