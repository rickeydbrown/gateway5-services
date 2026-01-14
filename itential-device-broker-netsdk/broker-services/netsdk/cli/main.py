# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Command-line interface for NetSDK.

This module provides the CLI broker interface for NetSDK. It handles:
- Argument parsing and inventory loading (with stdin timeout support)
- Logging configuration and command dispatch
- Output formatting and error handling

Example:
    $ python -m netsdk.cli run-command -c "show version"
    $ cat inventory.json | python -m netsdk.cli get-config
    $ python -m netsdk.cli set-config -i @inventory.json -c "hostname router1"
"""

import argparse
import asyncio
import json
import sys

from netsdk.api import broker
from netsdk.api import inventory
from netsdk.cli.parser import create_parser
from netsdk.cli.parser import get_subparser
from netsdk.core.models import Inventory
from netsdk.core.responses import PingResponse
from netsdk.core.responses import RunCommandResponse
from netsdk.utils import logging
from netsdk.utils.schema import generate_schema


def _configure_logging(log_level: str | None) -> None:
    """Configure logging based on the provided log level.

    Args:
        log_level: The log level string (info, trace, debug, warning, error) or None
    """
    if log_level is None:
        return

    # Map string levels to logging module constants
    level_map = {
        "trace": logging.TRACE,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }

    level = level_map[log_level.lower()]
    logging.initialize()
    logging.set_level(level)


def _handle_decorator_schema(args_list: list[str]) -> int:
    """Handle --decorator flag for JSON schema generation.

    This function checks if --decorator is present in the arguments and, if so,
    generates and outputs the JSON schema for the specified command.

    Args:
        args_list: Command-line arguments list

    Returns:
        Exit code:
            - 0: Schema generated successfully
            - 1: Error (no command specified or unknown command)
            - None: --decorator not present or --help takes precedence
    """
    is_decorator = "--decorator" in args_list
    is_help = "-h" in args_list or "--help" in args_list

    if not is_decorator or is_help:
        return None

    # Extract the command name from args
    command_name = None
    for arg in args_list:
        if arg in ["run-command", "get-config", "set-config", "is-alive"]:
            command_name = arg
            break

    if not command_name:
        print("Error: No command specified with --decorator", file=sys.stderr)
        return 1

    parser = create_parser()
    subparser = get_subparser(parser, command_name)
    if not subparser:
        print(f"Error: Unknown command '{command_name}'", file=sys.stderr)
        return 1

    schema = generate_schema(subparser, command_name)
    print(json.dumps(schema, indent=2))
    return 0


def _load_inventory_from_args(inventory_arg: str | None) -> tuple:
    """Load inventory from command-line arguments.

    Args:
        inventory_arg: The inventory argument value (None, @file, or JSON string)

    Returns:
        Tuple of (inventory, exit_code). If exit_code is None, inventory
        loaded successfully. Otherwise, exit_code contains the error code and
        inventory is None.
    """
    try:
        if inventory_arg:
            # Load from JSON file or string
            inv = inventory.load(inventory_arg)
        else:
            # Load from stdin
            inv = inventory.load_from_stdin()
    except Exception as exc:
        if inventory_arg:
            source = (
                inventory_arg[1:]
                if inventory_arg.startswith("@")
                else "argument"
            )
        else:
            source = "stdin"
        print(f"Error reading inventory from {source}: {exc}", file=sys.stderr)
        return (None, 1)
    else:
        return (inv, None)


async def _dispatch_command(
    args: argparse.Namespace, inventory: Inventory
) -> RunCommandResponse | PingResponse:
    """Dispatch the appropriate command based on parsed arguments.

    Args:
        args: Parsed command-line arguments
        inventory: Loaded inventory object

    Returns:
        Command response (either RunCommandResponse or PingResponse)

    Raises:
        ValueError: If command validation fails
        KeyboardInterrupt: If user cancels operation
        Exception: For unexpected errors
    """
    result = None

    if args.command == "run-command":
        result = await broker.run_command(inventory, args.commands, args.timeout)

    elif args.command == "get-config":
        result = await broker.get_config(inventory, args.commands, args.timeout)

    elif args.command == "set-config":
        result = await broker.set_config(inventory, args.commands, args.timeout)

    elif args.command == "is-alive":
        result = await broker.is_alive(inventory, args.timeout)

    else:
        # Unknown command
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return (None, 1)

    return (result, 0)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Orchestrates the complete workflow: parses CLI arguments, configures logging,
    loads inventory from file/string/stdin (with timeout), and dispatches to the
    appropriate command handler (run-command, get-config, set-config, is-alive).

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code:
            - 0: Success
            - 1: Error (inventory loading, parsing, or command execution)
            - 130: User cancelled with KeyboardInterrupt
    """
    # Handle --decorator flag before parsing (bypass required argument checks)
    args_list = argv if argv is not None else sys.argv[1:]
    decorator_result = _handle_decorator_schema(args_list)
    if decorator_result is not None:
        return decorator_result

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args(argv)

    # Configure logging
    _configure_logging(args.log_level)

    # Load inventory
    inventory, error_code = _load_inventory_from_args(args.inventory)
    if error_code is not None:
        return error_code

    # Execute command
    try:
        result, error_code = asyncio.run(_dispatch_command(args, inventory))
        if error_code != 0:
            return error_code

        # Output result to stdout
        print(result.model_dump_json(exclude_none=True, indent=2))
        return 0  # noqa: TRY300

    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
