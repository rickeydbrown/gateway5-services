# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Network device handlers for managing driver lifecycle and command execution.

This module provides the core handler functionality that dispatches commands to
network devices through dynamically loaded drivers. It handles driver instantiation,
option mapping, and command result collection.

The handlers act as an intermediary between the high-level runner interface and
the low-level device drivers, managing the complexity of driver selection and
configuration.

Functions:
    run_command: Execute commands on a network device
    get_config: Retrieve configuration from a network device
    set_config: Send configuration commands to a network device
    is_alive: Check if a network device is reachable
"""

import asyncio
import keyword

from datetime import datetime
from datetime import timezone
from typing import Any

from netsdk.core import constants
from netsdk.core.exceptions import NetsdkError
from netsdk.core.models import Host
from netsdk.core.responses import CommandResult
from netsdk.core.responses import PingResult
from netsdk.drivers import MapFrom
from netsdk.drivers import loader
from netsdk.utils import logging

__all__ = ("get_config", "is_alive", "run_command", "set_config")

# Default timeout for driver operations (5 minutes)
DEFAULT_OPERATION_TIMEOUT = 300.0


async def _invoke_method(host: Host, name: str, *args: Any, **kwargs: Any) -> Any:
    """Invoke a driver method on a host.

    Args:
        host: The network device to invoke the method on
        name: The name of the driver method to invoke
        *args: Positional arguments to pass to the method
        **kwargs: Keyword arguments to pass to the method

    Returns:
        The result from the driver method

    Raises:
        NetsdkError: If the driver does not conform to the DriverSpec protocol
    """
    logging.info(f"using driver {host.driver}")

    driver_class = loader.driver_loader.load(host.driver)
    options_class = loader.options_loader.load(host.driver)

    options_kwargs = {}

    for field_name, fi in options_class.model_fields.items():
        value = None

        if hasattr(host.driver_options, field_name):
            value = getattr(host.driver_options, field_name)

        if value is None:
            for ele in fi.metadata:
                if isinstance(ele, MapFrom):
                    value = getattr(host, ele.name)

        if value is not None:
            options_kwargs[field_name] = value

    options = options_class(**options_kwargs)
    instance = driver_class(options)

    method = getattr(instance, name)

    return await method(*args, **kwargs)


async def _send_command(host: Host, commands: list[str]) -> list[CommandResult]:
    """Send CLI commands to a network device and return the output.

    Args:
        host: The network device to execute commands on
        commands: A list of commands to execute on the network device

    Returns:
        A list of CommandResult objects for each command executed
    """
    results = []

    try:
        start = datetime.now(timezone.utc)

        # Wrap with safety timeout
        timeout = getattr(host, "operation_timeout", DEFAULT_OPERATION_TIMEOUT)
        res = await asyncio.wait_for(
            _invoke_method(host, "send_commands", commands), timeout=timeout
        )

        # Validate driver response structure
        if not isinstance(res, list):
            msg = (
                f"driver '{host.driver}' returned invalid response type: "
                f"expected list, got {type(res).__name__}"
            )
            raise NetsdkError(msg)

        # Each result should be a (command, output) tuple with string types
        expected_tuple_size = 2
        for i, item in enumerate(res):
            if not isinstance(item, tuple) or len(item) != expected_tuple_size:
                msg = (
                    f"driver '{host.driver}' returned malformed response at index {i}: "
                    f"expected (str, str) tuple, got {type(item).__name__}"
                )
                raise NetsdkError(msg)

            command, output = item

            if not isinstance(command, str):
                msg = (
                    f"driver '{host.driver}' returned invalid command type "
                    f"at index {i}: expected str, got {type(command).__name__}"
                )
                raise NetsdkError(msg)

            if not isinstance(output, str):
                msg = (
                    f"driver '{host.driver}' returned invalid output type "
                    f"at index {i}: expected str, got {type(output).__name__}"
                )
                raise NetsdkError(msg)

        end = datetime.now(timezone.utc)
        elapsed = (end - start).total_seconds()

        for command, output in res:
            results.append(
                CommandResult(
                    name=host.name,
                    command=command,
                    output=output,
                    success=True,
                    host=host.host,
                    start=start.strftime("%Y-%m-%d %H:%M:%S"),
                    end=end.strftime("%Y-%m-%d %H:%M:%S"),
                    elapsed=f"{elapsed:.3f}s",
                )
            )

    except asyncio.CancelledError:
        # Re-raise immediately to allow proper cancellation propagation
        logging.debug(f"command execution cancelled on host {host.name}")
        raise

    except asyncio.TimeoutError as exc:
        # Operation timeout
        error_msg = f"operation timed out after {timeout}s"
        logging.error(f"timeout executing commands on host {host.name}")
        results.append(
            CommandResult(
                name=host.name,
                success=False,
                host=host.host,
                error=error_msg,
                error_type=type(exc).__name__,
            )
        )

    except NetsdkError as exc:
        # SDK-specific errors (connection, auth, driver issues)
        error_msg = str(exc)
        logging.exception(f"failed to execute commands on host {host.name}")
        results.append(
            CommandResult(
                name=host.name,
                success=False,
                host=host.host,
                error=error_msg,
                error_type=type(exc).__name__,
            )
        )

    except (OSError, TimeoutError, ConnectionError) as exc:
        # Network and connection errors
        error_msg = f"connection error: {exc}"
        logging.exception(f"connection failed for host {host.name}")
        results.append(
            CommandResult(
                name=host.name,
                success=False,
                host=host.host,
                error=error_msg,
                error_type=type(exc).__name__,
            )
        )

    except Exception as exc:
        # Unexpected errors - log with full context but don't crash parallel execution
        error_msg = f"unexpected error: {type(exc).__name__}: {exc}"
        logging.exception(
            f"unexpected error executing commands on host {host.name}: "
            f"{type(exc).__name__}"
        )
        results.append(
            CommandResult(
                name=host.name,
                success=False,
                host=host.host,
                error=error_msg,
                error_type=type(exc).__name__,
            )
        )

    return results


@logging.trace
async def run_command(host: Host, commands: list[str]) -> list[CommandResult]:
    """Send CLI commands to a network device and return the output.

    Args:
        host: The network device to execute commands on
        commands: A list of commands to execute on the network device

    Returns:
        A list of CommandResult objects for each command executed
    """
    return await _send_command(host, commands)


@logging.trace
async def get_config(
    host: Host, commands: list[str] | None = None
) -> list[CommandResult]:
    """Get configuration from a network device using platform-specific commands.

    Args:
        host: The network device to get configuration from
        commands: Optional list of commands to execute. When provided, the
            platform-specific command lookup from constants is skipped.

    Returns:
        A list of CommandResult objects for each command executed

    Raises:
        NetsdkError: If commands not provided and platform not defined or not supported
    """
    # If commands are provided, skip constants lookup
    if commands is not None:
        return await _send_command(host, commands)

    # Validate platform is specified
    if not host.platform:
        msg = (
            f"platform not specified for host '{host.name}'. "
            "Platform is required for get_config operation. "
            "Use run_command() with explicit commands instead."
        )
        raise NetsdkError(msg)

    # Normalize platform name to valid Python identifier
    # Replace hyphens and spaces with underscores, then uppercase
    platform_const = host.platform.upper().replace("-", "_").replace(" ", "_")

    # Validate it's a safe identifier (no dunders, no keywords)
    if (
        not platform_const.isidentifier()
        or platform_const.startswith("_")
        or keyword.iskeyword(platform_const.lower())
    ):
        msg = (
            f"invalid platform name '{host.platform}' for host '{host.name}'. "
            "Platform must be alphanumeric with underscores (no leading underscores)."
        )
        raise NetsdkError(msg)

    try:
        commands_tuple = getattr(constants, platform_const)
    except AttributeError as exc:
        # Get available platforms for helpful error message
        available = [name for name in dir(constants) if name.isupper()]
        msg = (
            f"platform '{host.platform}' is not supported for get_config operation. "
            f"Available platforms: {', '.join(available[:10])}... "
            f"(and {len(available) - 10} more). "
            "Use run_command() with explicit commands instead."
        )
        raise NetsdkError(msg) from exc

    # Convert tuple to list for run_command
    commands = list(commands_tuple)
    return await _send_command(host, commands)


async def _send_config(host: Host, commands: list[str]) -> list[CommandResult]:
    """Send configuration commands to a network device and return results.

    Args:
        host: The network device to configure
        commands: A list of configuration commands to execute

    Returns:
        A list containing a single CommandResult with the configuration output
    """
    results = []

    try:
        start = datetime.now(timezone.utc)

        # Wrap with safety timeout
        timeout = getattr(host, "operation_timeout", DEFAULT_OPERATION_TIMEOUT)
        output = await asyncio.wait_for(
            _invoke_method(host, "send_config", commands), timeout=timeout
        )

        # Validate driver response
        if not isinstance(output, str):
            msg = (
                f"driver '{host.driver}' returned invalid response type: "
                f"expected str, got {type(output).__name__}"
            )
            raise NetsdkError(msg)

        end = datetime.now(timezone.utc)
        elapsed = (end - start).total_seconds()

        # Create a single CommandResult with all config commands
        results.append(
            CommandResult(
                name=host.name,
                output=output,
                success=True,
                host=host.host,
                start=start.strftime("%Y-%m-%d %H:%M:%S"),
                end=end.strftime("%Y-%m-%d %H:%M:%S"),
                elapsed=f"{elapsed:.3f}s",
            )
        )

    except asyncio.CancelledError:
        # Re-raise immediately to allow proper cancellation propagation
        logging.debug(f"config send cancelled on host {host.name}")
        raise

    except asyncio.TimeoutError as exc:
        # Operation timeout
        error_msg = f"operation timed out after {timeout}s"
        logging.error(f"timeout sending config to host {host.name}")
        results.append(
            CommandResult(
                name=host.name,
                success=False,
                host=host.host,
                error=error_msg,
                error_type=type(exc).__name__,
            )
        )

    except NetsdkError as exc:
        # SDK-specific errors (connection, auth, driver issues)
        error_msg = str(exc)
        logging.exception(f"failed to send config to host {host.name}")
        results.append(
            CommandResult(
                name=host.name,
                success=False,
                host=host.host,
                error=error_msg,
                error_type=type(exc).__name__,
            )
        )

    except (OSError, TimeoutError, ConnectionError) as exc:
        # Network and connection errors
        error_msg = f"connection error: {exc}"
        logging.exception(f"connection failed for host {host.name}")
        results.append(
            CommandResult(
                name=host.name,
                success=False,
                host=host.host,
                error=error_msg,
                error_type=type(exc).__name__,
            )
        )

    except Exception as exc:
        # Unexpected errors - log with full context but don't crash parallel execution
        error_msg = f"unexpected error: {type(exc).__name__}: {exc}"
        logging.exception(
            f"unexpected error sending config to host {host.name}: {type(exc).__name__}"
        )
        results.append(
            CommandResult(
                name=host.name,
                success=False,
                host=host.host,
                error=error_msg,
                error_type=type(exc).__name__,
            )
        )

    return results


@logging.trace
async def set_config(host: Host, commands: list[str]) -> list[CommandResult]:
    """Send configuration commands to a network device.

    This function enters configuration mode, sends the configuration
    commands, and exits configuration mode automatically.

    Args:
        host: The network device to configure
        commands: A list of configuration commands to execute

    Returns:
        A list containing a single CommandResult with the configuration output

    Raises:
        NetsdkError: If connection or command execution fails
    """
    return await _send_config(host, commands)


@logging.trace
async def is_alive(host: Host) -> PingResult:
    """Check if a network device is reachable and optionally authenticated.

    This function attempts to connect to the device and authenticate.
    It returns a PingResult indicating whether the device is alive.

    Args:
        host: The network device to check

    Returns:
        A PingResult object with the alive status and timing information
    """
    try:
        start = datetime.now(timezone.utc)

        # Wrap with safety timeout
        timeout = getattr(host, "operation_timeout", DEFAULT_OPERATION_TIMEOUT)
        alive = await asyncio.wait_for(
            _invoke_method(host, "is_alive"), timeout=timeout
        )

        # Validate driver response
        if not isinstance(alive, bool):
            msg = (
                f"driver '{host.driver}' returned invalid response type: "
                f"expected bool, got {type(alive).__name__}"
            )
            raise NetsdkError(msg)

        end = datetime.now(timezone.utc)
        elapsed = (end - start).total_seconds()

        return PingResult(
            name=host.name,
            alive=alive,
            success=True,
            host=host.host,
            start=start.strftime("%Y-%m-%d %H:%M:%S"),
            end=end.strftime("%Y-%m-%d %H:%M:%S"),
            elapsed=f"{elapsed:.3f}s",
        )

    except asyncio.CancelledError:
        # Re-raise immediately to allow proper cancellation propagation
        logging.debug(f"alive check cancelled on host {host.name}")
        raise

    except asyncio.TimeoutError as exc:
        # Operation timeout
        error_msg = f"operation timed out after {timeout}s"
        logging.error(f"timeout checking alive status on host {host.name}")
        return PingResult(
            name=host.name,
            alive=False,
            success=False,
            host=host.host,
            error=error_msg,
            error_type=type(exc).__name__,
        )

    except NetsdkError as exc:
        # SDK-specific errors (connection, auth, driver issues)
        error_msg = str(exc)
        logging.exception(f"failed to check alive status on host {host.name}")
        return PingResult(
            name=host.name,
            alive=False,
            success=False,
            host=host.host,
            error=error_msg,
            error_type=type(exc).__name__,
        )

    except (OSError, TimeoutError, ConnectionError) as exc:
        # Network and connection errors
        error_msg = f"connection error: {exc}"
        logging.exception(f"connection failed for host {host.name}")
        return PingResult(
            name=host.name,
            alive=False,
            success=False,
            host=host.host,
            error=error_msg,
            error_type=type(exc).__name__,
        )

    except Exception as exc:
        # Unexpected errors - log with full context but don't crash parallel execution
        error_msg = f"unexpected error: {type(exc).__name__}: {exc}"
        logging.exception(
            f"unexpected error checking alive status on host {host.name}: "
            f"{type(exc).__name__}"
        )
        return PingResult(
            name=host.name,
            alive=False,
            success=False,
            host=host.host,
            error=error_msg,
            error_type=type(exc).__name__,
        )
