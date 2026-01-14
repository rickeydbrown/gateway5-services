# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Command-line argument parser for NetSDK.

This module defines the argument parser structure for the NetSDK CLI broker,
including all subcommands (run-command, get-config, set-config, is-alive) and
their common arguments (inventory, timeout, log-level).
"""

import argparse


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common arguments shared across subcommands.

    Args:
        parser: The ArgumentParser or subparser to add arguments to
    """
    parser.add_argument(
        "--decorator",
        action="store_true",
        default=False,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-i",
        "--inventory",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to inventory file (JSON format)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Timeout in seconds for each host operation",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        default=None,
        choices=["info", "trace", "debug", "warning", "error"],
        metavar="LEVEL",
        help="Set logging level (info, trace, debug, warning, error)",
    )


def _add_run_command_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add run-command subcommand parser.

    Args:
        subparsers: The subparsers action object to add the parser to
    """
    parser = subparsers.add_parser(
        "run-command",
        help="Execute commands on network devices",
        description="Execute one or more commands on all devices in the inventory",
    )
    parser.add_argument(
        "-c",
        "--command",
        action="append",
        required=True,
        dest="commands",
        metavar="CMD",
        help="Command to execute (can be specified multiple times)",
    )
    _add_common_arguments(parser)


def _add_get_config_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add get-config subcommand parser.

    Args:
        subparsers: The subparsers action object to add the parser to
    """
    parser = subparsers.add_parser(
        "get-config",
        help="Retrieve configuration from network devices",
        description="Get running configuration from all devices in the inventory",
    )
    parser.add_argument(
        "-c",
        "--command",
        action="append",
        default=None,
        dest="commands",
        metavar="CMD",
        help="Command to execute (can be specified multiple times)",
    )
    _add_common_arguments(parser)


def _add_set_config_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add set-config subcommand parser.

    Args:
        subparsers: The subparsers action object to add the parser to
    """
    parser = subparsers.add_parser(
        "set-config",
        help="Send configuration commands to network devices",
        description="Send configuration commands to all devices in the inventory",
    )
    parser.add_argument(
        "-c",
        "--command",
        action="append",
        required=True,
        dest="commands",
        metavar="CMD",
        help="Configuration command to send (can be specified multiple times)",
    )
    _add_common_arguments(parser)


def _add_is_alive_parser(subparsers: argparse._SubParsersAction) -> None:
    """Add is-alive subcommand parser.

    Args:
        subparsers: The subparsers action object to add the parser to
    """
    parser = subparsers.add_parser(
        "is-alive",
        help="Check if network devices are reachable",
        description="Check connectivity to all devices in the inventory",
    )
    _add_common_arguments(parser)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser with subcommands.

    Creates the main ArgumentParser with four subcommands for network operations:
    - run-command: Execute show commands on devices
    - get-config: Retrieve running configuration
    - set-config: Apply configuration commands
    - is-alive: Check device connectivity

    All subcommands support common arguments: -i/--inventory, -t/--timeout,
    and -l/--log-level.

    Returns:
        Configured ArgumentParser instance with all subcommands
    """
    parser = argparse.ArgumentParser(
        prog="netsdk",
        description="NetSDK - Unified network device management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    # Create subparsers for each operation
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands",
    )

    # Add all subcommand parsers
    _add_run_command_parser(subparsers)
    _add_get_config_parser(subparsers)
    _add_set_config_parser(subparsers)
    _add_is_alive_parser(subparsers)

    return parser


def get_subparser(
    parser: argparse.ArgumentParser, command_name: str
) -> argparse.ArgumentParser | None:
    """Get a specific subparser by command name.

    Args:
        parser: The main ArgumentParser instance
        command_name: The name of the subcommand to retrieve

    Returns:
        The subparser for the specified command, or None if not found
    """
    # Find the subparsers action
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            # Return the specific subparser
            return action.choices.get(command_name)
    return None
