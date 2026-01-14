# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""NetSDK broker - Main library interface for network device automation.

This module provides the core API functions for executing commands, managing
configurations, and checking connectivity across network devices. It handles
parallel execution using asyncio.gather() and provides clean, type-safe interfaces.

The broker layer orchestrates parallel operations across inventories while the
handler layer manages individual device interactions.

Functions:
    run_command: Execute commands on devices in parallel
    get_config: Retrieve configuration from devices in parallel
    set_config: Send configuration commands to devices in parallel
    is_alive: Check device connectivity in parallel
"""

import asyncio

from collections.abc import Awaitable
from collections.abc import Callable
from functools import partial
from itertools import chain
from typing import TypeVar

from netsdk.core.models import Host
from netsdk.core.models import Inventory
from netsdk.core.responses import CommandResult
from netsdk.core.responses import PingResponse
from netsdk.core.responses import PingResult
from netsdk.core.responses import RunCommandResponse
from netsdk.executor import handlers
from netsdk.utils import logging

__all__ = (
    "get_config",
    "is_alive",
    "run_command",
    "set_config",
)

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
