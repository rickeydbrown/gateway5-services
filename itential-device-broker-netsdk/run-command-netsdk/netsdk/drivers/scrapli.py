# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Scrapli driver implementation for NetSDK.

This module provides a driver that uses the scrapli library to connect to
network devices and execute commands. It supports multiple transport mechanisms
and provides comprehensive connection options.
"""

import asyncio
import warnings

from collections.abc import Callable
from typing import Annotated
from typing import Any

from pydantic import Field

from netsdk.core.exceptions import NetsdkError
from netsdk.utils import logging

try:
    import scrapli
except ImportError:
    msg = "missing scrapli library, please install it"
    raise NetsdkError(msg)

from netsdk.drivers import DriverOptionsBase
from netsdk.drivers import MapFrom

__all__ = ("Driver", "DriverOptions")

# Operation constants for connection error messages
_OP_RUN_COMMANDS = "send_commands"
_OP_SEND_CONFIG = "send_config"
_OP_CHECK_ALIVE = "is_alive"


class DriverOptions(DriverOptionsBase):
    """Scrapli connection options model.

    This model defines all available connection options for Scrapli.
    All fields are optional and will be passed to scrapli.Scrapli.
    """

    auth_bypass: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Bypass authentication for console/terminal connections that don't require "
                "username/password. When True, Scrapli will not attempt authentication, which "
                "is useful for direct console connections, connections through terminal servers, "
                "or pre-authenticated sessions. Set to False (default) for normal network "
                "connections that require authentication. Rarely needed for standard SSH/Telnet "
                "connections."
            ),
        ),
    ]

    auth_password: Annotated[
        str,
        Field(
            default=None,
            description=(
                "Password for authenticating to the network device. Used in conjunction with "
                "'auth_username' for password-based authentication. This is the password for "
                "the initial login, not the enable/privilege escalation password (use "
                "'auth_secondary' for that). Required if not using SSH key authentication. "
                "Note: Consider using SSH key authentication ('auth_private_key') for better "
                "security in production environments."
            ),
        ),
        MapFrom("password"),
    ]

    auth_private_key: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Path to an SSH private key file to use for authentication. This enables "
                "public key authentication instead of or in addition to password authentication. "
                "The path can be absolute or relative, and supports standard SSH key formats "
                "(RSA, DSA, ECDSA, Ed25519). Example: '/home/user/.ssh/network_devices_rsa' or "
                "'~/.ssh/custom_key'. If the key is encrypted, provide the passphrase via "
                "'auth_private_key_passphrase'. Only applicable for SSH-based transports."
            ),
        ),
    ]

    auth_private_key_passphrase: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Passphrase to decrypt an encrypted SSH private key. Required when using a "
                "password-protected SSH key file (specified via 'auth_private_key'). Leave "
                "empty or None if your SSH key is not encrypted. Using encrypted keys provides "
                "additional security by requiring both the key file and passphrase for "
                "authentication. Only applicable when 'auth_private_key' is specified."
            ),
        ),
    ]

    auth_secondary: Annotated[
        str,
        Field(
            default=None,
            description=(
                "Secondary password for privilege escalation (enable password). This is the "
                "password used when entering privileged/enable mode on devices that support "
                "privilege levels. On Cisco IOS and similar devices, this is the password "
                "prompted for by the 'enable' command. Only required when 'become' is True "
                "and the device requires an enable password. Not all platforms use secondary "
                "passwords for privilege escalation."
            ),
        ),
        MapFrom("become_password"),
    ]

    auth_strict_key: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Enable strict SSH host key checking. When True, the connection will fail if "
                "the host key is not in the known_hosts file or has changed, preventing "
                "potential man-in-the-middle attacks. When False (default), unknown host keys "
                "are automatically accepted. Recommended to set True in production environments "
                "for security. Requires proper host key management via 'ssh_known_hosts_file'. "
                "Only applicable for SSH-based transports."
            ),
        ),
    ]

    auth_username: Annotated[
        str,
        Field(
            default=None,
            description=(
                "Username for authenticating to the network device. This is the login account "
                "used to establish the initial connection to the device. For devices requiring "
                "privilege escalation (enable mode), this is typically the regular user account "
                "before escalation. This field is required unless using 'auth_bypass' for "
                "console connections or connections that don't require authentication."
            ),
        ),
        MapFrom("user"),
    ]

    become: Annotated[
        bool,
        Field(
            default=False,
            description=(
                "Whether to automatically enter privileged/enable mode after connecting to "
                "the device. When set to True, the driver will execute the platform-specific "
                "privilege escalation command (e.g., 'enable' on Cisco IOS) immediately after "
                "authentication. Requires 'auth_secondary' to be set if the device requires an "
                "enable password. This is commonly needed for configuration changes on Cisco "
                "IOS, Arista EOS, and similar network operating systems."
            ),
            exclude=True,
        ),
        MapFrom("become"),
    ]

    channel_lock: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Enable thread-safe locking for channel operations. When True, Scrapli uses "
                "threading locks to ensure only one operation at a time accesses the channel "
                "(connection). This prevents race conditions when multiple threads try to send "
                "commands simultaneously. Default is True. Set to False only if you're managing "
                "concurrency yourself or know you'll never have concurrent access. Recommended "
                "to leave enabled for multi-threaded applications."
            ),
        ),
    ]

    channel_log: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Path to a file where all channel activity (raw data sent/received) will be "
                "logged. Similar to Netmiko's session_log. When specified, Scrapli writes all "
                "raw communication data to this file, including commands, output, control "
                "characters, and timing. Extremely useful for debugging connection issues, "
                "understanding device behavior, and maintaining audit trails. Example: "
                "'/var/log/network/scrapli_channel.log'. Creates file if it doesn't exist."
            ),
        ),
    ]

    comms_ansi: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Enable processing of ANSI escape codes in device output. When True, Scrapli "
                "will strip ANSI color codes, cursor movement sequences, and other terminal "
                "control codes from device output. Useful for devices that send colorized output "
                "or use terminal features. Default is False. Set to True if device output contains "
                "garbled characters or escape sequences, or if you want clean text output without "
                "formatting codes."
            ),
        ),
    ]

    comms_prompt_pattern: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Regular expression pattern to match device CLI prompts. Scrapli uses this to "
                "detect when the device has finished sending output and is ready for the next "
                "command. Default patterns are provided for each platform, but you can override "
                "them for devices with non-standard prompts. Use raw strings (r'...') for regex "
                "patterns. Example: r'^[a-z0-9.\\-@/:]{1,63}[#>$]\\s*$'. Only modify if you're "
                "experiencing prompt detection issues."
            ),
        ),
    ]

    comms_return_char: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Character or sequence to send as line terminator after commands. Most devices "
                "use '\\n' (newline), which is the default. Some devices or connection types may "
                "require '\\r' (carriage return), '\\r\\n', or other sequences. Override only if "
                "experiencing issues with commands not being executed or device not responding. "
                "Incorrect values can cause commands to fail silently or hang."
            ),
        ),
    ]

    host: Annotated[
        str,
        Field(
            default=None,
            description=(
                "Hostname or IP address of the target network device. This is the primary "
                "connection parameter for establishing a connection. Supports both IPv4 addresses "
                "(e.g., '192.168.1.1') and hostnames that can be resolved via DNS (e.g., "
                "'router1.example.com'). IPv6 addresses are also supported by most transport types. "
                "This field is required for establishing a connection to the device."
            ),
        ),
        MapFrom("host"),
    ]

    logging_uid: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Unique identifier to include in Scrapli's internal log messages. Useful when "
                "running multiple concurrent connections and you need to distinguish log messages "
                "from different devices or sessions. The UID will be included in all log output "
                "for this connection. Example: 'router1-session-1' or 'dc1-core-switch'. Helpful "
                "for debugging and correlating log messages in multi-device automation scripts."
            ),
        ),
    ]

    on_close: Annotated[
        Callable[..., Any] | None,
        Field(
            default=None,
            description="Callable to execute on connection close",
        ),
    ]

    on_init: Annotated[
        Callable[..., Any] | None,
        Field(
            default=None,
            description="Callable to execute on initialization",
        ),
    ]

    on_open: Annotated[
        Callable[..., Any] | None,
        Field(
            default=None,
            description="Callable to execute on connection open",
        ),
    ]

    platform: Annotated[
        str,
        Field(
            default=None,
            description=(
                "Scrapli platform identifier specifying the network operating system. This "
                "determines which command patterns, prompts, and privilege levels Scrapli will "
                "use for device interaction. Supported platforms include: 'cisco_iosxe', "
                "'cisco_nxos', 'cisco_iosxr', 'arista_eos', 'juniper_junos', and others. "
                "This field is required and must match your device's network operating system. "
                "See Scrapli documentation for the complete list of supported platforms."
            ),
        ),
        MapFrom("platform"),
    ]

    port: Annotated[
        int,
        Field(
            default=None,
            description=(
                "TCP port number to connect to on the target device. Defaults to the standard "
                "port for the selected transport protocol (SSH: 22, Telnet: 23). Override this "
                "when connecting to devices with non-standard port configurations, when using "
                "port forwarding, or when devices are behind NAT/firewall with port translation. "
                "Must be between 1 and 65535."
            ),
        ),
        MapFrom("port"),
    ]

    ssh_config_file: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Path to an SSH config file to parse for connection settings. Scrapli can read "
                "OpenSSH config files to extract settings like ProxyCommand, IdentityFile, Port, "
                "and other SSH parameters. This allows you to leverage your existing SSH "
                "configuration for device connections. Default is typically '~/.ssh/config'. "
                "Set to False or empty string to disable SSH config file parsing. Useful for "
                "complex setups with jump hosts or per-host configurations. Only applicable "
                "for SSH-based transports."
            ),
        ),
    ]

    ssh_known_hosts_file: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Path to an SSH known_hosts file for host key verification. Used when "
                "'auth_strict_key' is True to verify device host keys. Follows the standard "
                "OpenSSH known_hosts format. Default is typically '~/.ssh/known_hosts'. You can "
                "specify a custom file to maintain a separate set of trusted host keys for "
                "network devices, isolating them from your personal SSH configuration. Only "
                "applicable for SSH-based transports."
            ),
        ),
    ]

    timeout_ops: Annotated[
        float | None,
        Field(
            default=None,
            description=(
                "Operations timeout in seconds for command execution and device responses. This "
                "is the maximum time to wait for a device to respond to commands and return to "
                "a prompt. Default is typically 30 seconds. Increase this for commands that take "
                "a long time to execute (e.g., 'show tech-support', large configurations, file "
                "transfers, routing table displays on large networks). This is the most commonly "
                "adjusted timeout value."
            ),
        ),
    ]

    timeout_socket: Annotated[
        float | None,
        Field(
            default=None,
            description=(
                "Socket connection timeout in seconds for establishing the initial TCP connection "
                "to the device. This controls how long to wait for the TCP handshake to complete "
                "before failing. Default is typically 15 seconds. Increase for slow or high-latency "
                "networks (e.g., satellite links, international connections), decrease for faster "
                "failure detection. This timeout only affects the initial connection phase, not "
                "authentication or command execution."
            ),
        ),
    ]

    timeout_transport: Annotated[
        float | None,
        Field(
            default=None,
            description=(
                "Transport-level timeout in seconds for transport-specific operations. This "
                "controls timeouts for SSH handshake, authentication negotiation, and other "
                "transport protocol operations. Default is typically 30 seconds. Increase for "
                "devices with slow authentication mechanisms (RADIUS/TACACS+ with network delays) "
                "or when connecting through high-latency networks. Different from 'timeout_ops' "
                "which controls command execution timeouts."
            ),
        ),
    ]

    transport: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "SSH/Telnet transport library to use for connections. Options include: 'system' "
                "(native OpenSSH, recommended for best performance and compatibility), 'paramiko' "
                "(pure Python SSH, good cross-platform compatibility), 'ssh2' (libssh2 bindings, "
                "high performance), 'telnet' (for Telnet connections), 'asyncssh' (async SSH, "
                "for async operations). Default is 'system' for SSH connections. Choose based on "
                "your requirements for performance, compatibility, and available system dependencies."
            ),
        ),
    ]

    transport_options: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            description=(
                "Dictionary of transport-specific options passed directly to the underlying "
                "transport library. Contents depend on the selected transport. For 'system' "
                "transport, you might specify SSH binary path or options. For 'paramiko', you "
                "might configure look_for_keys, compression, or SSH algorithms. This is an "
                "advanced parameter for fine-tuning transport behavior. Example: "
                "{'ssh_options': ['-o StrictHostKeyChecking=no']} for system transport."
            ),
        ),
    ]

    variant: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Platform variant for devices that have multiple sub-types or flavors within "
                "the same base platform. Some platforms have variations in command syntax, "
                "prompts, or behavior depending on hardware model, software version, or "
                "configuration mode. This allows you to specify the exact variant for more "
                "accurate device interaction. Consult platform-specific documentation to "
                "determine if a variant is needed for your specific device model."
            ),
        ),
    ]


class Driver:
    """Scrapli driver for executing commands on network devices.

    This driver uses the scrapli library to connect to network devices
    and execute commands. It wraps the synchronous scrapli API with async
    methods to integrate with the NetSDK async architecture.

    Attributes:
        options: Scrapli connection options configured for the device
    """

    def __init__(self, options: DriverOptions) -> None:
        """Initialize the Scrapli driver with connection options.

        Args:
            options: Scrapli connection options for the device
        """
        self.options = options

    def _with_connection(self, operation: str, callback: Callable[[Any], Any]) -> Any:
        """Execute a callback within a scrapli connection context.

        This method handles connection setup, privilege escalation, and error handling
        in a DRY manner for all scrapli operations.

        Args:
            operation: Description of the operation (for error messages)
            callback: Function to execute with the connection object

        Returns:
            The result from the callback function

        Raises:
            NetsdkError: If connection or operation fails
        """
        try:
            kwargs = self.options.model_dump(exclude_none=True)

            if self.options.become is False and "auth_secondary" in kwargs:
                del kwargs["auth_secondary"]

            logging.debug("scrapli driver options: %s", kwargs)

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with scrapli.Scrapli(**kwargs) as conn:
                    return callback(conn)

        except (
            scrapli.exceptions.ScrapliTimeout,
            scrapli.exceptions.ScrapliAuthenticationFailed,
        ) as exc:
            logging.exception(exc)
            msg = f"failed to {operation} on {self.options.host}"
            raise NetsdkError(msg) from exc

    def _execute_commands(self, commands: list[str]) -> list[tuple[str, str]]:
        """Execute commands synchronously using scrapli.

        Args:
            commands: A list of commands to execute

        Returns:
            A list of tuples (command, result) for each command

        Raises:
            NetsdkError: If connection or command execution fails
        """

        def callback(conn: Any) -> list[tuple[str, str]]:
            results = []
            for command in commands:
                resp = conn.send_command(command)
                results.append((command, resp.result))
            return results

        return self._with_connection(_OP_RUN_COMMANDS, callback)

    def _execute_config(self, commands: list[str]) -> str:
        """Execute configuration commands synchronously using scrapli.

        Args:
            commands: A list of configuration commands to execute

        Returns:
            The output from the configuration session

        Raises:
            NetsdkError: If connection or command execution fails
        """

        def callback(conn: Any) -> str:
            resp = conn.send_configs(commands)
            return resp.result

        return self._with_connection(_OP_SEND_CONFIG, callback)

    async def send_commands(
        self,
        commands: list[str],
    ) -> list[tuple[str, str]]:
        """Send commands to the remote device and return the output.

        Args:
            commands: A list of commands to execute

        Returns:
            A list of tuples (command, result) for each command

        Raises:
            NetsdkError: If connection or command execution fails
        """
        return await asyncio.to_thread(self._execute_commands, commands)

    async def send_config(self, commands: list[str]) -> str:
        """Send configuration commands to the remote device.

        This method enters configuration mode, sends the configuration
        commands, and exits configuration mode automatically.

        Args:
            commands: A list of configuration commands to execute

        Returns:
            The output from the configuration session

        Raises:
            NetsdkError: If connection or command execution fails
        """
        return await asyncio.to_thread(self._execute_config, commands)

    def _check_alive(self) -> bool:
        """Check if device is reachable synchronously.

        Returns:
            True if device is reachable and authenticated, False otherwise
        """
        try:
            self._with_connection(_OP_CHECK_ALIVE, lambda _: None)
        except (NetsdkError, Exception):
            return False
        else:
            return True

    async def is_alive(self) -> bool:
        """Check if the device is reachable and optionally authenticated.

        This method attempts to connect to the device and authenticate.
        It returns True if the connection and authentication are successful,
        False otherwise.

        Returns:
            True if device is reachable and authenticated, False otherwise
        """
        try:
            return await asyncio.to_thread(self._check_alive)
        except Exception:
            return False
