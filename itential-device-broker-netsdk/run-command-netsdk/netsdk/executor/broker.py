# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""NetSDK broker - Main library interface for network device automation.

This module provides the core API functions for executing commands, managing
configurations, and checking connectivity across network devices. It handles
parallel execution using asyncio.gather() and provides clean, type-safe interfaces
for both batch and streaming operations.

The broker layer orchestrates parallel operations across inventories while the
handler layer manages individual device interactions.

Functions:
    run_command: Execute commands on devices in parallel
    run_command_streaming: Stream command results as they complete
    get_config: Retrieve configuration from devices in parallel
    get_config_streaming: Stream config results as they complete
    set_config: Send configuration commands to devices in parallel
    set_config_streaming: Stream config results as they complete
    is_alive: Check device connectivity in parallel
    is_alive_streaming: Stream connectivity results as they complete
    load_inventory: Load inventory from file, string, or stdin
"""

import asyncio
import sys

from collections.abc import AsyncIterator
from collections.abc import Awaitable
from collections.abc import Callable
from functools import partial
from itertools import chain
from pathlib import Path
from typing import TypeVar

from netsdk.core.models import Host
from netsdk.core.models import Inventory
from netsdk.core.responses import CommandResult
from netsdk.core.responses import PingResponse
from netsdk.core.responses import PingResult
from netsdk.core.responses import RunCommandResponse
from netsdk.executor import handlers
from netsdk.utils import logging
from netsdk.utils.json import loads

__all__ = (
    "STDIN_TIMEOUT",
    "get_config",
    "get_config_streaming",
    "is_alive",
    "is_alive_streaming",
    "load_inventory",
    "main",
    "run_command",
    "run_command_streaming",
    "set_config",
    "set_config_streaming",
)

# Default timeout for reading inventory from stdin (in seconds)
STDIN_TIMEOUT = 10.0

T = TypeVar("T")


def _create_command_timeout_result(
    host: Host, timeout_val: float, operation_name: str
) -> list[CommandResult]:
    """Create timeout result for command operations.

    Args:
        host: The host that timed out
        timeout_val: The timeout value in seconds
        operation_name: Name of the operation that timed out

    Returns:
        List containing a single CommandResult indicating timeout
    """
    return [
        CommandResult(
            name=host.name,
            success=False,
            host=host.host,
            error=f"{operation_name} timed out after {timeout_val}s",
            error_type="TimeoutError",
        )
    ]


def _create_ping_timeout_result(
    host: Host, timeout_val: float, operation_name: str
) -> PingResult:
    """Create timeout result for ping operations.

    Args:
        host: The host that timed out
        timeout_val: The timeout value in seconds
        operation_name: Name of the operation that timed out

    Returns:
        PingResult indicating timeout
    """
    return PingResult(
        name=host.name,
        alive=False,
        success=False,
        host=host.host,
        error=f"{operation_name} timed out after {timeout_val}s",
        error_type="TimeoutError",
    )


async def _with_timeout(
    host: Host,
    operation: Callable[[Host], Awaitable[T]],
    timeout: float | None,
    create_timeout_result: Callable[[Host, float, str], T],
) -> T:
    """Execute an operation with optional timeout.

    Args:
        host: The host to operate on
        operation: The async operation to execute
        timeout: Optional timeout in seconds
        create_timeout_result: Function to create timeout result

    Returns:
        Result from operation or timeout result
    """
    try:
        if timeout is not None:
            return await asyncio.wait_for(operation(host), timeout=timeout)
        return await operation(host)

    except asyncio.TimeoutError:
        # Get operation name, handling both functions and functools.partial
        if hasattr(operation, "__name__"):
            operation_name = operation.__name__.replace("_", " ")
        elif hasattr(operation, "func"):
            operation_name = operation.func.__name__.replace("_", " ")
        else:
            operation_name = "operation"
        logging.error(f"timeout {operation_name} on host {host.name}")
        return create_timeout_result(host, timeout, operation_name)


async def _read_stdin_with_timeout(timeout: float = STDIN_TIMEOUT) -> str:
    """Read from stdin with a timeout.

    Args:
        timeout: Timeout in seconds for reading from stdin

    Returns:
        Content read from stdin

    Raises:
        asyncio.TimeoutError: If reading from stdin exceeds the timeout
    """
    return await asyncio.wait_for(asyncio.to_thread(sys.stdin.read), timeout=timeout)


async def run_command(
    inventory: Inventory,
    commands: list[str],
    timeout: float | None = None,
) -> RunCommandResponse:
    """Execute commands on all hosts in the inventory in parallel.

    Args:
        inventory: The inventory of network devices to execute commands on
        commands: A list of commands to execute on each network device
        timeout: Optional timeout in seconds for each host operation.
            If None, no timeout is applied.

    Returns:
        A RunCommandResponse containing flattened CommandResult objects from all hosts

    Raises:
        ValueError: If commands list is empty, inventory is None, or inventory is empty
    """
    if not commands:
        raise ValueError("commands list cannot be empty")

    if inventory is None:
        raise ValueError("inventory cannot be None")

    if len(inventory) == 0:
        raise ValueError("inventory is empty, no hosts to execute commands on")

    # Create tasks for each host
    # Using functools.partial for clearer intent and safer capture
    tasks = [
        _with_timeout(
            host,
            partial(handlers.run_command, commands=commands),
            timeout,
            _create_command_timeout_result,
        )
        for host in inventory
    ]

    # Run all tasks in parallel and collect results
    logging.info(
        f"running {len(commands)} command(s) on {len(inventory)} hosts in parallel"
    )

    results = await asyncio.gather(*tasks)

    # Flatten the nested list structure using itertools.chain
    flattened = list(chain.from_iterable(results))

    return RunCommandResponse(flattened)


async def get_config(
    inventory: Inventory,
    commands: list[str] | None = None,
    timeout: float | None = None,
) -> RunCommandResponse:
    """Get configuration from network devices in parallel.

    Args:
        inventory: The inventory of network devices to get configuration from
        commands: Optional list of commands to execute. When provided, the
            platform-specific command lookup from constants is skipped for all hosts.
        timeout: Optional timeout in seconds for each host operation.
            If None, no timeout is applied.

    Returns:
        A RunCommandResponse containing CommandResult objects from all hosts

    Raises:
        ValueError: If inventory is None or inventory is empty
    """
    if inventory is None:
        raise ValueError("inventory cannot be None")

    if len(inventory) == 0:
        raise ValueError("inventory is empty, no hosts to get configuration from")

    # Create tasks for each host
    tasks = [
        _with_timeout(
            host,
            partial(handlers.get_config, commands=commands),
            timeout,
            _create_command_timeout_result,
        )
        for host in inventory
    ]

    # Run all tasks in parallel and collect results
    logging.info(f"getting config from {len(inventory)} hosts in parallel")

    results = await asyncio.gather(*tasks)

    # Flatten the nested list structure using itertools.chain
    flattened = list(chain.from_iterable(results))

    return RunCommandResponse(flattened)


async def set_config(
    inventory: Inventory,
    commands: list[str],
    timeout: float | None = None,
) -> RunCommandResponse:
    """Send configuration commands to all hosts in the inventory in parallel.

    Args:
        inventory: The inventory of network devices to configure
        commands: A list of configuration commands to execute on each device
        timeout: Optional timeout in seconds for each host operation.
            If None, no timeout is applied.

    Returns:
        A RunCommandResponse containing CommandResult objects from all hosts

    Raises:
        ValueError: If commands list is empty, inventory is None, or inventory is empty
    """
    if not commands:
        raise ValueError("commands list cannot be empty")

    if inventory is None:
        raise ValueError("inventory cannot be None")

    if len(inventory) == 0:
        raise ValueError("inventory is empty, no hosts to send configuration to")

    # Create tasks for each host
    # Using functools.partial for clearer intent and safer capture
    tasks = [
        _with_timeout(
            host,
            partial(handlers.set_config, commands=commands),
            timeout,
            _create_command_timeout_result,
        )
        for host in inventory
    ]

    # Run all tasks in parallel and collect results
    logging.info(
        f"sending {len(commands)} config command(s) to "
        f"{len(inventory)} hosts in parallel"
    )

    results = await asyncio.gather(*tasks)

    # Flatten the nested list structure using itertools.chain
    flattened = list(chain.from_iterable(results))

    return RunCommandResponse(flattened)


async def is_alive(
    inventory: Inventory,
    timeout: float | None = None,
) -> PingResponse:
    """Check if network devices are reachable in parallel.

    Args:
        inventory: The inventory of network devices to check
        timeout: Optional timeout in seconds for each host operation.
            If None, no timeout is applied.

    Returns:
        A PingResponse containing PingResult objects for all hosts

    Raises:
        ValueError: If inventory is None or inventory is empty
    """
    if inventory is None:
        raise ValueError("inventory cannot be None")

    if len(inventory) == 0:
        raise ValueError("inventory is empty, no hosts to check alive status")

    # Create tasks for each host
    tasks = [
        _with_timeout(
            host,
            handlers.is_alive,
            timeout,
            _create_ping_timeout_result,
        )
        for host in inventory
    ]

    # Run all tasks in parallel and collect results
    logging.info(f"checking alive status for {len(inventory)} hosts in parallel")

    results = await asyncio.gather(*tasks)

    return PingResponse(results)


def load_inventory(
    inventory_source: str | None = None,
    from_stdin: bool = False,
    stdin_timeout: float = STDIN_TIMEOUT,
) -> Inventory:
    """Load inventory from file, JSON string, or stdin.

    Args:
        inventory_source: Inventory source - can be:
            - Path to file (prefixed with @, e.g., "@inventory.json")
            - Direct JSON string
            - None (will read from stdin if from_stdin=True)
        from_stdin: If True and inventory_source is None, read from stdin
        stdin_timeout: Timeout in seconds for reading from stdin (default: 30.0)

    Returns:
        Inventory instance containing hosts

    Raises:
        FileNotFoundError: If inventory file does not exist
        ValueError: If inventory_source is None and from_stdin is False, or if
            inventory data structure is invalid
        asyncio.TimeoutError: If reading from stdin exceeds the timeout
        Exception: If inventory data cannot be parsed
    """
    if inventory_source:
        if inventory_source.startswith("@"):
            # Read from inventory file (strip @ prefix)
            inventory_path = Path(inventory_source[1:])
            if not inventory_path.exists():
                msg = f"Inventory file not found: {inventory_source[1:]}"
                raise FileNotFoundError(msg)
            data = loads(inventory_path.read_text())
        else:
            # Parse as direct JSON string
            data = loads(inventory_source)
    elif from_stdin:
        # Read from stdin with timeout
        stdin_data = asyncio.run(_read_stdin_with_timeout(stdin_timeout))
        data = loads(stdin_data)
    else:
        msg = "inventory_source must be provided or from_stdin must be True"
        raise ValueError(msg)

    # Validate top-level structure
    if not isinstance(data, dict):
        msg = (
            f"Inventory must be a JSON object, got {type(data).__name__}. "
            "Expected format: {'inventory_nodes': [...]}"
        )
        raise TypeError(msg)

    if "inventory_nodes" not in data:
        msg = (
            "Inventory missing required field 'inventory_nodes'. "
            "Expected format: {'inventory_nodes': [...]}"
        )
        raise ValueError(msg)

    inventory_nodes = data["inventory_nodes"]
    if not isinstance(inventory_nodes, list):
        msg = (
            f"'inventory_nodes' must be a list, got {type(inventory_nodes).__name__}. "
            "Expected format: {'inventory_nodes': [...]}"
        )
        raise TypeError(msg)

    return Inventory(inventory_nodes)


# Streaming API functions that yield results as they complete


async def run_command_streaming(
    inventory: Inventory,
    commands: list[str],
    timeout: float | None = None,
) -> AsyncIterator[list[CommandResult]]:
    """Execute commands on hosts and yield results as they complete.

    This streaming version yields CommandResult objects as soon as each host completes,
    rather than waiting for all hosts to finish. Useful for providing real-time feedback
    in interactive applications or processing results incrementally.

    Args:
        inventory: The inventory of network devices to execute commands on
        commands: A list of commands to execute on each network device
        timeout: Optional timeout in seconds for each host operation

    Yields:
        list[CommandResult]: Results for each host as they complete

    Raises:
        ValueError: If commands list is empty, inventory is None, or inventory is empty
    """
    if not commands:
        raise ValueError("commands list cannot be empty")

    if inventory is None:
        raise ValueError("inventory cannot be None")

    if len(inventory) == 0:
        raise ValueError("inventory is empty, no hosts to execute commands on")

    logging.info(f"streaming {len(commands)} command(s) to {len(inventory)} hosts")

    # Create tasks for each host
    tasks = {
        asyncio.create_task(
            _with_timeout(
                host,
                partial(handlers.run_command, commands=commands),
                timeout,
                _create_command_timeout_result,
            )
        ): host
        for host in inventory
    }

    # Yield results as they complete
    for coro in asyncio.as_completed(tasks.keys()):
        try:
            result = await coro
            yield result
        except Exception as exc:  # noqa: PERF203
            # Log error but continue processing other hosts
            host = tasks[coro]
            logging.exception(f"error processing host {host.name}: {exc}")


async def get_config_streaming(
    inventory: Inventory,
    commands: list[str] | None = None,
    timeout: float | None = None,
) -> AsyncIterator[list[CommandResult]]:
    """Get configuration from devices and yield results as they complete.

    This streaming version yields CommandResult objects as soon as each host completes,
    rather than waiting for all hosts to finish.

    Args:
        inventory: The inventory of network devices to get configuration from
        commands: Optional list of commands to execute. When provided, the
            platform-specific command lookup from constants is skipped for all hosts.
        timeout: Optional timeout in seconds for each host operation

    Yields:
        list[CommandResult]: Results for each host as they complete

    Raises:
        ValueError: If inventory is None or inventory is empty
    """
    if inventory is None:
        raise ValueError("inventory cannot be None")

    if len(inventory) == 0:
        raise ValueError("inventory is empty, no hosts to get configuration from")

    logging.info(f"streaming config from {len(inventory)} hosts")

    # Create tasks for each host
    tasks = {
        asyncio.create_task(
            _with_timeout(
                host,
                partial(handlers.get_config, commands=commands),
                timeout,
                _create_command_timeout_result,
            )
        ): host
        for host in inventory
    }

    # Yield results as they complete
    for coro in asyncio.as_completed(tasks.keys()):
        try:
            result = await coro
            yield result
        except Exception as exc:  # noqa: PERF203
            # Log error but continue processing other hosts
            host = tasks[coro]
            logging.exception(f"error processing host {host.name}: {exc}")


async def set_config_streaming(
    inventory: Inventory,
    commands: list[str],
    timeout: float | None = None,
) -> AsyncIterator[list[CommandResult]]:
    """Send configuration commands to devices and yield results as they complete.

    This streaming version yields CommandResult objects as soon as each host completes,
    rather than waiting for all hosts to finish.

    Args:
        inventory: The inventory of network devices to configure
        commands: A list of configuration commands to execute on each device
        timeout: Optional timeout in seconds for each host operation

    Yields:
        list[CommandResult]: Results for each host as they complete

    Raises:
        ValueError: If commands list is empty, inventory is None, or inventory is empty
    """
    if not commands:
        raise ValueError("commands list cannot be empty")

    if inventory is None:
        raise ValueError("inventory cannot be None")

    if len(inventory) == 0:
        raise ValueError("inventory is empty, no hosts to send configuration to")

    logging.info(
        f"streaming {len(commands)} config command(s) to {len(inventory)} hosts"
    )

    # Create tasks for each host
    tasks = {
        asyncio.create_task(
            _with_timeout(
                host,
                partial(handlers.set_config, commands=commands),
                timeout,
                _create_command_timeout_result,
            )
        ): host
        for host in inventory
    }

    # Yield results as they complete
    for coro in asyncio.as_completed(tasks.keys()):
        try:
            result = await coro
            yield result
        except Exception as exc:  # noqa: PERF203
            # Log error but continue processing other hosts
            host = tasks[coro]
            logging.exception(f"error processing host {host.name}: {exc}")


async def is_alive_streaming(
    inventory: Inventory,
    timeout: float | None = None,
) -> AsyncIterator[PingResult]:
    """Check if devices are alive and yield results as they complete.

    This streaming version yields PingResult objects as soon as each host completes,
    rather than waiting for all hosts to finish.

    Args:
        inventory: The inventory of network devices to check
        timeout: Optional timeout in seconds for each host operation

    Yields:
        PingResult: Result for each host as they complete

    Raises:
        ValueError: If inventory is None or inventory is empty
    """
    if inventory is None:
        raise ValueError("inventory cannot be None")

    if len(inventory) == 0:
        raise ValueError("inventory is empty, no hosts to check alive status")

    logging.info(f"streaming alive check for {len(inventory)} hosts")

    # Create tasks for each host
    tasks = {
        asyncio.create_task(
            _with_timeout(
                host,
                handlers.is_alive,
                timeout,
                _create_ping_timeout_result,
            )
        ): host
        for host in inventory
    }

    # Yield results as they complete
    for coro in asyncio.as_completed(tasks.keys()):
        try:
            result = await coro
            yield result
        except Exception as exc:  # noqa: PERF203
            # Log error but continue processing other hosts
            host = tasks[coro]
            logging.exception(f"error processing host {host.name}: {exc}")


# Import main from cli for backward compatibility (tests use broker.main)
# This import is at the end to avoid circular import issues
from netsdk.cli.main import main  # noqa: E402

# Support running as a module
if __name__ == "__main__":
    import sys

    sys.exit(main())
