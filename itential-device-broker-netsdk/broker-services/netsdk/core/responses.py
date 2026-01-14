# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

# ruff: noqa: E501
"""Response models for network device operation results.

This module defines Pydantic models for representing the results of operations
on network devices. These models provide validation, serialization, and structured
access to operation results including command execution, configuration changes,
and connectivity checks.

All response models are immutable Pydantic BaseModel instances that can be easily
serialized to JSON for API responses, logging, or storage. They include timing
information, error details, and operation-specific output.

Classes:
    CommandResult: Result of a single command execution on one device
    RunCommandResponse: Collection of CommandResult objects from multiple devices
    PingResult: Result of connectivity/alive check on one device
    PingResponse: Collection of PingResult objects from multiple devices
"""

from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import RootModel

__all__ = ("CommandResult", "PingResponse", "PingResult", "RunCommandResponse")


class ResultBase(BaseModel):
    """Base class for result models with common timing and error fields.

    This base class provides shared fields used across all result types,
    including device identification, timing information, and error handling.
    All result models inherit from this class to ensure consistency.

    Attributes:
        name: Unique identifier/name of the device from the inventory
        host: Hostname or IP address used to connect to the device
        success: True if operation executed successfully, False if any error occurred
        start_time: ISO 8601 timestamp when operation started (YYYY-MM-DD HH:MM:SS)
        end_time: ISO 8601 timestamp when operation completed (YYYY-MM-DD HH:MM:SS)
        elapsed_time: Human-readable elapsed time string (e.g., "1.234s")
        error: Detailed error message if operation failed, None if successful
        error_type: Python exception type name if error occurred (e.g., "TimeoutError")
    """

    name: str = Field(
        description=(
            "Unique identifier for the device from the inventory. This corresponds "
            "to the 'name' field specified in the Host model or inventory definition. "
            "Used to identify which device this result belongs to when processing "
            "results from multiple devices. This field is always populated and matches "
            "the device name from the input inventory."
        )
    )

    host: str = Field(
        default=None,
        description=(
            "The hostname or IP address used to establish the connection to the device. "
            "This corresponds to the 'host' or 'itential_host' field from the Host model. "
            "Can be an IPv4 address (e.g., '192.168.1.1'), IPv6 address, or DNS hostname "
            "(e.g., 'router1.example.com'). This field reflects the actual connection target "
            "and is useful for logging, debugging, and correlating results with network "
            "topology. May be None for certain error conditions that occur before connection "
            "establishment."
        ),
    )

    success: bool = Field(
        default=True,
        description=(
            "Boolean indicator of operation success. True indicates the operation "
            "was successfully executed without errors. False indicates an error occurred "
            "at any stage (connection, authentication, command execution, or timeout). "
            "When False, the 'error' and 'error_type' fields contain details about the "
            "failure. This field allows quick filtering of successful vs failed operations "
            "without examining error fields."
        ),
    )

    start_time: str = Field(
        default=None,
        description=(
            "ISO 8601 formatted timestamp indicating when operation execution began. "
            "Format: 'YYYY-MM-DD HH:MM:SS' in UTC timezone (e.g., '2025-01-15 14:30:25'). "
            "Marks the moment when the SDK initiated the operation request, before "
            "any network communication. Use this for precise timing analysis, calculating "
            "total operation duration, or correlating events across multiple systems. May be "
            "None for certain early-stage errors (e.g., validation failures) that occur before "
            "execution begins. When present alongside 'end_time', these timestamps can be used to "
            "calculate operation duration independently of the 'elapsed_time' field."
        ),
    )

    end_time: str = Field(
        default=None,
        description=(
            "ISO 8601 formatted timestamp indicating when operation execution completed. "
            "Format: 'YYYY-MM-DD HH:MM:SS' in UTC timezone (e.g., '2025-01-15 14:30:27'). "
            "Marks the moment when the SDK received the final response or encountered an error, "
            "representing the end of the operation. The difference between 'end_time' and 'start_time' "
            "represents the total wall-clock time for the operation. May be None for certain "
            "error conditions or when execution was interrupted. Use this timestamp for audit "
            "logging, performance monitoring, or identifying when operations completed relative "
            "to other events in your system."
        ),
    )

    elapsed_time: str = Field(
        default=None,
        description=(
            "Human-readable elapsed time for the operation execution, formatted as a decimal "
            "number followed by 's' for seconds (e.g., '1.234s', '0.056s', '15.789s'). "
            "Calculated as the difference between 'end_time' and 'start_time' timestamps, representing "
            "total wall-clock duration including network latency, device processing time, and "
            "any driver overhead. This field provides an easy-to-read duration without requiring "
            "timestamp parsing. Use for performance monitoring, identifying slow operations, or "
            "displaying operation timing to users. May be None for errors that occur before "
            "timing begins or when execution was interrupted. Values less than 0.001s are "
            "typically displayed as '0.000s' due to formatting precision."
        ),
    )

    error: str | None = Field(
        default=None,
        description=(
            "Detailed human-readable error message when operation fails (success=False). "
            "None when execution succeeded (success=True). Contains a descriptive message "
            "explaining what went wrong, including context about the failure point (connection, "
            "authentication, timeout, command error, etc.). Messages follow the format "
            "'category: details' (e.g., 'connection error: Connection refused', 'operation timed "
            "out after 30s'). Use this field for error reporting, logging, and user-facing error "
            "messages. The message provides actionable information to help diagnose and resolve "
            "issues. For programmatic error handling, use 'error_type' to identify exception classes."
        ),
    )

    error_type: str | None = Field(
        default=None,
        description=(
            "Python exception class name when an error occurred during execution. None when "
            "execution succeeded (success=True). Contains the exception type name as a string "
            "(e.g., 'TimeoutError', 'ConnectionError', 'NetsdkError', 'OSError'). This field "
            "enables programmatic error handling by allowing code to check error types without "
            "parsing error messages. Use for error classification, metrics collection, or "
            "implementing type-specific error handling logic. Common types include: TimeoutError "
            "(operation timeout), ConnectionError (network connectivity), NetsdkError (SDK-specific "
            "errors), and OSError (system-level errors). Combine with 'error' field for complete "
            "error information."
        ),
    )


class DumpMixin:
    """Mixin that provides a dump() convenience method for Pydantic models.

    This mixin adds a simplified API for dumping Pydantic models to dictionaries
    or lists, wrapping the standard model_dump() method with a shorter name.
    """

    def dump(self, **kwargs: Any) -> dict[str, Any] | list[dict[str, Any]]:
        """Dump the model to a dictionary or list of dictionaries.

        This is a convenience method that wraps Pydantic's model_dump() method,
        providing a simpler API for serializing the model.

        Args:
            **kwargs: Additional keyword arguments to pass to model_dump(),
                such as exclude_none, exclude_unset, by_alias, etc.

        Returns:
            Dictionary representation for BaseModel instances, or list of
            dictionaries for RootModel instances

        Examples:
            >>> result.dump()
            {'name': 'router1', 'command': 'show version', ...}

            >>> result.dump(exclude_none=True)
            {'name': 'router1', 'command': 'show version', 'success': True}

            >>> response.dump()
            [{'name': 'router1', 'command': 'show version', ...}, ...]
        """
        return self.model_dump(**kwargs)


class CommandResult(DumpMixin, ResultBase):
    """Result of a single command execution on a network device.

    CommandResult encapsulates all information about executing a single command
    on a network device, including the command itself, its output, timing data,
    and any errors that occurred. Results can represent both successful and failed
    command executions.

    This model is used by run_command(), get_config(), and set_config() operations
    to return structured results that can be easily inspected, logged, or serialized.

    Attributes:
        name: Unique identifier/name of the device from the inventory
        command: The command string that was executed (e.g., "show version")
        output: Command output as returned by the device. Type depends on the
            command and driver - typically str for single commands, may be other
            types for structured output
        success: True if command executed successfully, False if any error occurred
        host: Hostname or IP address used to connect to the device
        start_time: ISO 8601 timestamp when command execution started (YYYY-MM-DD HH:MM:SS)
        end_time: ISO 8601 timestamp when command execution completed (YYYY-MM-DD HH:MM:SS)
        elapsed_time: Human-readable elapsed time string (e.g., "1.234s")
        error: Detailed error message if command failed, None if successful
        error_type: Python exception type name if error occurred (e.g., "TimeoutError")

    Examples:
        Successful command execution:
            >>> result = CommandResult(
            ...     name="router1",
            ...     command="show version",
            ...     output="Cisco IOS Software...",
            ...     success=True,
            ...     host="192.168.1.1",
            ...     start_time="2025-01-15 10:30:00",
            ...     end_time="2025-01-15 10:30:02",
            ...     elapsed_time="2.150s"
            ... )

        Failed command with error:
            >>> result = CommandResult(
            ...     name="router2",
            ...     command="show config",
            ...     success=False,
            ...     host="192.168.1.2",
            ...     error="connection error: Connection refused",
            ...     error_type="ConnectionError"
            ... )

        Accessing result data:
            >>> if result.success:
            ...     print(f"Output: {result.output}")
            ... else:
            ...     print(f"Error: {result.error}")

    Note:
        When success=False, the output field is typically None and error/error_type
        fields contain details about the failure. Timing fields (start_time/end_time/elapsed_time)
        may be None for certain error conditions like connection failures.
    """

    command: str = Field(
        default=None,
        description=(
            "The exact command string that was executed on the device. For single "
            "command operations, this contains the command text (e.g., 'show version', "
            "'show ip interface brief'). For configuration operations, this may contain "
            "the configuration command or a summary. This field is None when the result "
            "represents an error that occurred before command execution (e.g., connection "
            "failures). Use this field to identify which command produced the corresponding "
            "output, especially when executing multiple commands in sequence."
        ),
    )

    output: Any = Field(
        default=None,
        description=(
            "The raw output returned by the device after executing the command. "
            "The type and format depend on the driver and command executed. Typically "
            "a string containing the device's text response, but may be structured data "
            "(dict, list) for drivers that parse output. For successful executions, this "
            "contains the command results. For failed executions (success=False), this is "
            "typically None. The output preserves the device's original formatting including "
            "whitespace, newlines, and special characters. Use this field to access the "
            "actual command results for parsing, display, or further processing."
        ),
    )


class RunCommandResponse(DumpMixin, RootModel[list[CommandResult]]):
    """Collection of command execution results from multiple devices.

    RunCommandResponse is a Pydantic RootModel that wraps a list of CommandResult
    objects, providing validation and serialization capabilities. It's returned by
    run_command(), get_config(), and set_config() operations when executing commands
    across multiple devices in parallel.

    The response behaves like a list and can be iterated, indexed, and serialized
    to JSON. It contains one CommandResult per device, preserving the order of
    devices from the input inventory.

    Attributes:
        root: List of CommandResult objects, one per device

    Examples:
        Iterating over results:
            >>> response = await broker.run_command(inventory, ["show version"])
            >>> for result in response.root:
            ...     if result.success:
            ...         print(f"{result.name}: {result.output}")
            ...     else:
            ...         print(f"{result.name}: Error - {result.error}")

        Filtering successful results:
            >>> successful = [r for r in response.root if r.success]
            >>> failed = [r for r in response.root if not r.success]
            >>> print(f"Success: {len(successful)}, Failed: {len(failed)}")

        Getting dictionary representation:
            >>> data = response.dump(exclude_none=True)
            >>> print(f"Results: {len(data)}")

        Serializing to JSON:
            >>> import json
            >>> json_output = response.model_dump_json(indent=2)

    Note:
        The response includes results for all devices, even those that failed.
        Check the success field on each CommandResult to determine if the
        command executed successfully on that device.
    """

    root: list[CommandResult]


class PingResult(DumpMixin, ResultBase):
    """Result of a connectivity/alive check on a network device.

    PingResult encapsulates the outcome of checking whether a network device is
    reachable and can be authenticated. Unlike ICMP ping, this check attempts to
    establish a full connection and authenticate to the device using the configured
    driver and credentials.

    This model is used by the is_alive() operation to return structured results
    indicating device reachability, authentication success, and any errors encountered.

    Attributes:
        name: Unique identifier/name of the device from the inventory
        alive: True if device is reachable and authentication succeeded,
            False otherwise
        success: True if check completed without throwing exceptions,
            False if check failed
        host: Hostname or IP address used to connect to the device
        start_time: ISO 8601 timestamp when check started (YYYY-MM-DD HH:MM:SS)
        end_time: ISO 8601 timestamp when check completed (YYYY-MM-DD HH:MM:SS)
        elapsed_time: Human-readable elapsed time string (e.g., "0.523s")
        error: Detailed error message if check failed, None if successful
        error_type: Python exception type name if error occurred (e.g., "TimeoutError")

    Examples:
        Successful alive check:
            >>> result = PingResult(
            ...     name="router1",
            ...     alive=True,
            ...     success=True,
            ...     host="192.168.1.1",
            ...     start_time="2025-01-15 10:30:00",
            ...     end_time="2025-01-15 10:30:01",
            ...     elapsed_time="0.523s"
            ... )

        Failed check with authentication error:
            >>> result = PingResult(
            ...     name="router2",
            ...     alive=False,
            ...     success=False,
            ...     host="192.168.1.2",
            ...     error="connection error: Authentication failed",
            ...     error_type="NetsdkError"
            ... )

        Checking device status:
            >>> if result.alive:
            ...     print(f"{result.name} is reachable")
            ... else:
            ...     print(f"{result.name} is not reachable: {result.error}")

    Note:
        The alive field indicates successful connection and authentication, while
        success indicates the check operation itself completed. A device can be
        unreachable (alive=False) but the check still succeeds (success=True) by
        catching and handling connection errors gracefully.
    """

    alive: bool = Field(
        default=False,
        description=(
            "Boolean indicator of device reachability and authentication success. "
            "True indicates the SDK was able to establish a network connection to the "
            "device, successfully authenticate using the provided credentials, and verify "
            "the session is functional. False indicates the device is unreachable, "
            "authentication failed, or the connection could not be established. This "
            "differs from ICMP ping - it represents full application-layer connectivity "
            "including authentication. Use this field to determine if a device is ready "
            "for command execution. Note that alive=False with success=True indicates "
            "the check operation succeeded but found the device unreachable - this is "
            "normal behavior for offline devices and should not be treated as an error "
            "in your monitoring logic."
        ),
    )


class PingResponse(DumpMixin, RootModel[list[PingResult]]):
    """Collection of connectivity check results from multiple devices.

    PingResponse is a Pydantic RootModel that wraps a list of PingResult objects,
    providing validation and serialization capabilities. It's returned by the
    is_alive() operation when checking connectivity and authentication across
    multiple devices in parallel.

    The response behaves like a list and can be iterated, indexed, and serialized
    to JSON. It contains one PingResult per device, preserving the order of devices
    from the input inventory.

    Attributes:
        root: List of PingResult objects, one per device

    Examples:
        Checking multiple devices:
            >>> response = await broker.is_alive(inventory)
            >>> for result in response.root:
            ...     status = "UP" if result.alive else "DOWN"
            ...     print(f"{result.name}: {status}")

        Counting reachable devices:
            >>> alive_count = sum(1 for r in response.root if r.alive)
            >>> total = len(response.root)
            >>> print(f"Reachable: {alive_count}/{total}")

        Finding failed checks:
            >>> failures = [r for r in response.root if not r.alive]
            >>> for failure in failures:
            ...     print(f"{failure.name}: {failure.error}")

        Getting dictionary representation:
            >>> data = response.dump(exclude_none=True)
            >>> alive_count = sum(1 for r in data if r["alive"])

        Serializing to JSON:
            >>> json_output = response.model_dump_json(indent=2)

    Note:
        The response includes results for all devices, even those that are
        unreachable. Check the alive field on each PingResult to determine
        device reachability status.
    """

    root: list[PingResult]
