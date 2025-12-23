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

import asyncio
import sys

from netsdk.api import broker
from netsdk.cli.parser import create_parser
from netsdk.utils import logging


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
    parser = create_parser()
    args = parser.parse_args(argv)

    # Configure logging if log level is specified
    _configure_logging(args.log_level)

    # Load inventory
    try:
        # Determine inventory source
        inventory_source = args.inventory if args.inventory else None
        from_stdin = inventory_source is None
        inventory = broker.load_inventory(inventory_source, from_stdin)
    except Exception as exc:
        if args.inventory:
            if args.inventory.startswith("@"):
                source = args.inventory[1:]
            else:
                source = "argument"
        else:
            source = "stdin"
        print(f"Error reading inventory from {source}: {exc}", file=sys.stderr)
        return 1

    # Execute the appropriate command with explicit arguments
    try:
        # Dispatch command execution and get result
        result = None
        if args.command == "run-command":
            result = asyncio.run(
                broker.run_command(inventory, args.commands, args.timeout)
            )

        elif args.command == "get-config":
            result = asyncio.run(
                broker.get_config(inventory, args.commands, args.timeout)
            )

        elif args.command == "set-config":
            result = asyncio.run(
                broker.set_config(inventory, args.commands, args.timeout)
            )

        elif args.command == "is-alive":
            result = asyncio.run(broker.is_alive(inventory, args.timeout))

        else:
            # Unknown command
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1

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
