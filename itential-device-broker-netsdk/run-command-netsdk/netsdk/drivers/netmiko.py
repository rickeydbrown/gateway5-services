# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Netmiko driver implementation for NetSDK.

This module provides a driver that uses the netmiko library to connect to
network devices and execute commands. Netmiko is a popular multi-vendor
SSH library that supports a wide range of network device types.

The driver wraps netmiko's ConnectHandler to provide async compatibility
with the NetSDK architecture.

Classes:
    DriverOptions: Pydantic model for netmiko connection options
    Driver: Netmiko driver implementation

Raises:
    NetsdkError: If netmiko library is not installed
"""

import asyncio
import warnings

from typing import Annotated
from typing import Any

from pydantic import Field

from netsdk.core.exceptions import NetsdkError
from netsdk.drivers import DriverOptionsBase
from netsdk.drivers import MapFrom
from netsdk.utils import logging

try:
    import netmiko
except ImportError:
    raise NetsdkError("missing netmiko library, please install it")  # noqa: TRY003


class DriverOptions(DriverOptionsBase):
    """Netmiko connection options model.

    This model defines all available connection options for Netmiko.
    All fields are optional and will be passed to netmiko.ConnectHandler.
    """

    allow_agent: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Allow connection to SSH agent for key authentication. When True (default), "
                "Paramiko will attempt to connect to the local SSH agent (ssh-agent) to retrieve "
                "available SSH keys. Set to False to prevent agent access, forcing authentication "
                "via password or explicitly specified keys only. Useful in containerized "
                "environments or when you want to ensure only specific keys are used."
            ),
        ),
    ]

    allow_auto_change: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Allow Netmiko to automatically detect and switch to a different device type if "
                "the initial device_type is incorrect. This feature uses auto-detection to identify "
                "the actual device type after connection. Useful in environments where you're not "
                "certain of the exact device type, but may have performance implications. Set to "
                "False for more predictable behavior and faster connections when you know the "
                "device type."
            ),
        ),
    ]

    alt_host_keys: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Use an alternative host keys file instead of the system default. When True, "
                "you must also specify 'alt_key_file' to point to your custom known_hosts file. "
                "Useful when you want to maintain a separate set of trusted host keys for "
                "network devices, isolating them from your personal SSH host keys."
            ),
        ),
    ]

    alt_key_file: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Path to an alternative known_hosts file for host key verification. Must be "
                "used with 'alt_host_keys=True'. This allows you to maintain a custom known_hosts "
                "file specifically for network devices. Format follows the standard OpenSSH "
                "known_hosts format. Example: '/etc/network/device_known_hosts' or "
                "'~/.ssh/network_devices_known_hosts'."
            ),
        ),
    ]

    auth_timeout: Annotated[
        float | None,
        Field(
            default=30,
            description=(
                "Maximum time in seconds to wait for authentication to complete. This includes "
                "the time to send credentials and receive the post-authentication prompt. "
                "Defaults to 30 seconds. Increase for devices with slow authentication processes "
                "(e.g., RADIUS/TACACS+ authentication with retries) or slow banner displays."
            ),
        ),
    ]

    auto_connect: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Automatically establish the SSH connection when the ConnectHandler object is "
                "instantiated. When True (default), connection happens immediately during object "
                "creation. When False, you must manually call the connect() method. Setting to "
                "False allows you to configure additional parameters before connecting or to "
                "handle connection in a try-except block separately from object creation."
            ),
        ),
    ]

    banner_timeout: Annotated[
        float | None,
        Field(
            default=None,
            description=(
                "Maximum time in seconds to wait for the login banner to be received after "
                "connection establishment. Some devices display lengthy banners (legal notices, "
                "MOTD) before the login prompt. Defaults to a device-specific value (typically "
                "15 seconds). Increase if connecting to devices with very long banners or slow "
                "terminal responses."
            ),
        ),
    ]

    become: Annotated[
        bool,
        Field(
            default=None,
            description=(
                "Whether to automatically enter privileged/enable mode after connecting to "
                "the device. When set to True, the driver will execute the enable command "
                "(e.g., 'enable' on Cisco devices) immediately after authentication. Requires "
                "'secret' to be set if the device requires an enable password. This is commonly "
                "needed for configuration changes on Cisco IOS, Arista EOS, and similar devices."
            ),
            exclude=True,
        ),
        MapFrom("become"),
    ]

    conn_timeout: Annotated[
        float | None,
        Field(
            default=30,
            description=(
                "TCP connection timeout in seconds for establishing the initial socket connection "
                "to the device. This is how long to wait for the TCP handshake to complete. "
                "Defaults to 30 seconds. Increase for slow or high-latency networks, decrease "
                "for faster failure detection. Note: This only controls the socket connection "
                "phase, not authentication or command execution."
            ),
        ),
    ]

    default_enter: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Default character sequence to use as line terminator when sending commands. "
                "Netmiko normally uses '\\n' (newline), but some devices or protocols may require "
                "different terminators like '\\r\\n' (carriage return + newline) or '\\r' alone. "
                "Override this only if you're experiencing command execution issues related to "
                "line endings. Most users should leave this at the default."
            ),
        ),
    ]

    delay_factor_compat: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Enable compatibility mode for delay_factor behavior from older Netmiko versions. "
                "Controls how delay_factor multipliers are applied to timeouts. Set to True for "
                "backward compatibility with scripts written for older Netmiko versions. New "
                "code should leave this at default (False) to use current timing behavior."
            ),
        ),
    ]

    device_type: Annotated[
        str,
        Field(
            default=None,
            description=(
                "Netmiko device type identifier specifying the network operating system and "
                "connection method. This determines which command patterns, prompts, and "
                "behaviors Netmiko will use. Examples: 'cisco_ios', 'cisco_nxos', 'arista_eos', "
                "'juniper_junos', 'hp_procurve'. See Netmiko documentation for the complete list "
                "of supported device types. This field is required and must match your device's OS."
            ),
        ),
        MapFrom("platform"),
    ]

    disable_lf_normalization: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Disable automatic line feed (LF) normalization in device output. By default, "
                "Netmiko normalizes different line ending styles (CRLF, LF, CR) to a consistent "
                "format. Set to True if you need the raw output exactly as received from the "
                "device, including original line endings. Useful for binary data or when parsing "
                "output that's sensitive to line ending characters."
            ),
        ),
    ]

    disable_sha2_fix: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Disable the SHA2 algorithm fix for older devices. Netmiko includes workarounds "
                "for devices that don't properly support SHA2 algorithms. Set to True to disable "
                "this fix if it's causing issues or if your device properly supports SHA2. "
                "Typically only needed for troubleshooting connection problems with specific "
                "device models."
            ),
        ),
    ]

    disabled_algorithms: Annotated[
        dict | None,
        Field(
            default=None,
            description=(
                "Dictionary of SSH algorithm types to disable during connection negotiation. "
                "Useful when connecting to older devices that don't support modern algorithms "
                "or when you need to disable specific algorithms for security/compatibility "
                "reasons. Keys can include: 'pubkeys', 'kex', 'ciphers', 'macs', 'compression'. "
                "Example: {'pubkeys': ['rsa-sha2-256', 'rsa-sha2-512'], 'kex': ['diffie-hellman-group1-sha1']}"
            ),
        ),
    ]

    enable_fast_mode: Annotated[
        bool,
        Field(
            default=True,
            description=(
                "Use send_command_timing for faster command execution. "
                "This skips pattern matching and is 20-30% faster for most devices. "
                "Set to False for interactive commands that need pattern detection."
            ),
            exclude=True,
        ),
    ]

    encoding: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Character encoding to use for SSH session data. Default is 'utf-8' for most "
                "devices. Some older devices or devices with specific regional configurations "
                "may require different encodings like 'latin-1', 'ascii', or 'cp850'. Incorrect "
                "encoding can cause garbled characters in device output, especially for non-ASCII "
                "characters. Change only if you're seeing character encoding issues."
            ),
        ),
    ]

    fast_cli: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Enable Netmiko's fast_cli mode for improved performance. When True, Netmiko "
                "reduces delays between operations and uses more aggressive timing. Can "
                "significantly speed up operations on capable devices but may cause issues with "
                "slower devices or high-latency connections. Set to False for more reliable but "
                "slower operation. Default behavior varies by device type."
            ),
        ),
    ]

    global_cmd_verify: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Enable global command echo verification for configuration commands. When True, "
                "Netmiko verifies that each configuration command was echoed back by the device, "
                "providing confirmation that the command was entered correctly. This adds "
                "reliability but increases execution time. Set to False to skip verification "
                "for faster operations when you trust the connection quality."
            ),
        ),
    ]

    global_delay_factor: Annotated[
        float | None,
        Field(
            default=None,
            description=(
                "Global multiplier applied to all internal delays in Netmiko operations. Default "
                "is 1.0. Increase this value (e.g., 2.0 or 3.0) when working with slow devices, "
                "high-latency connections, or devices that need more time to process commands. "
                "Decrease it (e.g., 0.5) for faster devices to speed up operations. Affects "
                "timeouts for reading device responses and waiting for prompts."
            ),
        ),
    ]

    host: Annotated[
        str,
        Field(
            default=None,
            description=(
                "Hostname or IP address of the target network device. This is the primary "
                "connection parameter and is preferred over 'ip'. Supports both IPv4 addresses "
                "(e.g., '192.168.1.1') and hostnames that can be resolved via DNS "
                "(e.g., 'router1.example.com'). This field is required for establishing a connection."
            ),
        ),
        MapFrom("host"),
    ]

    ip: Annotated[
        str,
        Field(
            default=None,
            description=(
                "IP address of the target network device. Note: if both 'ip' and 'host' "
                "are specified, 'host' will be used and a warning will be issued. Use 'host' "
                "for consistency across different connection methods."
            ),
        ),
    ]

    keepalive: Annotated[
        int | None,
        Field(
            default=None,
            description=(
                "TCP keepalive interval in seconds. When set to a positive value, enables TCP "
                "keepalive packets to keep the SSH session alive through firewalls and prevent "
                "idle connection timeouts. Recommended for long-running sessions or when "
                "connecting through firewalls with idle timeouts. Typically set to 30-60 seconds. "
                "Set to 0 to disable keepalive."
            ),
        ),
    ]

    key_file: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Path to a specific SSH private key file to use for authentication. Use this to "
                "specify a non-default key location. The path can be absolute or relative. "
                "Common formats include RSA, DSA, ECDSA, and Ed25519 keys. Example: "
                "'/home/user/.ssh/network_devices_rsa' or '~/.ssh/custom_key'. If the key is "
                "encrypted, provide the passphrase via the 'passphrase' parameter."
            ),
        ),
    ]

    passphrase: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Passphrase to decrypt an encrypted SSH private key. Required when using a "
                "password-protected SSH key file (specified via 'key_file' or 'pkey'). Leave "
                "empty or None if your SSH key is not encrypted. Note: Using encrypted keys "
                "provides additional security if the key file is compromised."
            ),
        ),
    ]

    password: Annotated[
        str,
        Field(
            default=None,
            description=(
                "Password for authenticating to the network device. Used in conjunction with "
                "'username' for password-based authentication. This is the password for the "
                "initial login, not the enable/privilege escalation password (use 'secret' "
                "for that). Note: Consider using SSH key authentication instead for better "
                "security. Required if not using key-based authentication."
            ),
        ),
        MapFrom("password"),
    ]

    pkey: Annotated[
        Any | None,
        Field(
            default=None,
            description=(
                "Pre-loaded SSH private key object (Paramiko PKey object) to use for "
                "authentication. This is an advanced option for programmatic use when you've "
                "already loaded a key into memory. Typically, you would use 'key_file' instead "
                "to specify a key file path. This parameter accepts any Paramiko key type "
                "(RSAKey, DSSKey, ECDSAKey, Ed25519Key)."
            ),
        ),
    ]

    port: Annotated[
        int,
        Field(
            default=None,
            description=(
                "TCP port number to connect to on the target device. Defaults to the standard "
                "port for the connection protocol (SSH: 22, Telnet: 23). Override this when "
                "connecting to devices with non-standard port configurations or when using "
                "port forwarding."
            ),
        ),
        MapFrom("port"),
    ]

    read_timeout_override: Annotated[
        float | None,
        Field(
            default=None,
            description=(
                "Override the default read timeout for specific operations. When set, this value "
                "overrides 'session_timeout' for all read operations. Useful for globally "
                "adjusting read behavior without changing session_timeout. Measured in seconds. "
                "Use with caution as it affects all read operations uniformly."
            ),
        ),
    ]

    response_return: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Character sequence that indicates the end of a device response. Used by Netmiko "
                "to determine when the device has finished sending output. Typically '\\n' "
                "(newline) for most devices. Override only for devices with non-standard "
                "response formatting. Incorrect values can cause commands to hang or return "
                "incomplete output."
            ),
        ),
    ]

    secret: Annotated[
        str,
        Field(
            default=None,
            description=(
                "Enable password for privilege escalation (privileged/enable mode). This is "
                "the password used when entering enable mode on devices that support privilege "
                "levels. On Cisco IOS and similar devices, this is the password prompted for "
                "by the 'enable' command. Only used when 'become' is set to True. Note: This "
                "is different from the login password ('password')."
            ),
        ),
        MapFrom("become_password"),
    ]

    serial_settings: Annotated[
        dict | None,
        Field(
            default=None,
            description=(
                "Configuration dictionary for serial (console) port connections. Used when "
                "connecting via serial cable instead of network. Typical keys include: 'port' "
                "(e.g., '/dev/ttyUSB0' or 'COM1'), 'baudrate' (e.g., 9600), 'bytesize', 'parity', "
                "'stopbits'. Example: {'port': '/dev/ttyUSB0', 'baudrate': 9600}. Only relevant "
                "when 'device_type' ends with '_serial' (e.g., 'cisco_ios_serial')."
            ),
        ),
    ]

    session_log: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Path to a file where all session activity will be logged. When specified, "
                "Netmiko writes all data sent to and received from the device to this file. "
                "Extremely useful for debugging connection issues, understanding device behavior, "
                "and maintaining audit trails. The log includes commands, responses, control "
                "characters, and timing information. Example: '/var/log/network/device_session.log'. "
                "Use with 'session_log_record_writes' and 'session_log_file_mode' for fine control."
            ),
        ),
    ]

    session_log_file_mode: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "File opening mode for the session log. Options are 'write' (default, overwrites "
                "existing file) or 'append' (adds to existing file). Use 'append' when you want "
                "to maintain a continuous log across multiple script runs or when connecting to "
                "the same device multiple times. Use 'write' to start fresh each time. Only "
                "relevant when 'session_log' is specified."
            ),
        ),
    ]

    session_log_record_writes: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Control whether write operations (commands sent to device) are included in the "
                "session log. When True, both reads (device output) and writes (commands sent) "
                "are logged. When False, only device output is logged. Requires 'session_log' "
                "to be set. Setting to False can be useful when you want to log only device "
                "responses without cluttering the log with your commands."
            ),
        ),
    ]

    session_timeout: Annotated[
        float | None,
        Field(
            default=60,
            description=(
                "Maximum time in seconds to wait for read operations during command execution. "
                "This controls how long Netmiko waits for the device to respond to commands. "
                "Defaults to 60 seconds. Increase this for commands that take a long time to "
                "complete (e.g., large show tech-support outputs, file transfers). Applies to "
                "reading channel output during normal operations."
            ),
        ),
    ]

    sock: Annotated[
        Any | None,
        Field(
            default=None,
            description=(
                "Pre-established socket object to use for the connection. This is an advanced "
                "parameter for programmatic use when you've already created a socket connection "
                "(e.g., through a proxy or jump host). When provided, Netmiko will use this "
                "socket instead of creating a new one. Typically used with SSH ProxyCommand or "
                "custom connection routing. Most users should leave this unset."
            ),
        ),
    ]

    sock_telnet: Annotated[
        Any | None,
        Field(
            default=None,
            description=(
                "Pre-established Telnet socket object for Telnet connections. Similar to 'sock' "
                "but specifically for Telnet protocol connections. Used in advanced scenarios "
                "where you need custom Telnet socket handling or connection routing through "
                "intermediary devices. Rarely needed for standard operations."
            ),
        ),
    ]

    ssh_config_file: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Path to an SSH config file to parse for connection settings. Netmiko can read "
                "OpenSSH config files to extract settings like ProxyCommand, IdentityFile, Port, "
                "etc. This allows you to leverage your existing SSH configuration for device "
                "connections. Default is '~/.ssh/config'. Set to False to disable SSH config "
                "file parsing. Useful for complex SSH setups with jump hosts or specific per-host "
                "configurations."
            ),
        ),
    ]

    ssh_strict: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Enable strict SSH host key checking. When False (typical default), new host "
                "keys are automatically accepted. When True, connection will fail if the host "
                "key is not in the known_hosts file or has changed. Recommended for production "
                "environments to prevent man-in-the-middle attacks. Requires proper host key "
                "management via 'system_host_keys' or 'alt_host_keys'."
            ),
        ),
    ]

    system_host_keys: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Load and use the system's known_hosts file for host key verification. When True, "
                "Netmiko will load keys from the default system location (typically ~/.ssh/known_hosts). "
                "This is used in conjunction with 'ssh_strict' to verify host identity. Set to False "
                "if you're managing host keys separately or want to bypass host key checking "
                "(not recommended for production)."
            ),
        ),
    ]

    use_keys: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Enable SSH key-based authentication. When set to True, Netmiko will attempt to "
                "use SSH keys for authentication instead of or in addition to password "
                "authentication. If SSH keys are available via ssh-agent or in default locations "
                "(~/.ssh/id_rsa, ~/.ssh/id_dsa), they will be tried automatically. Set to False "
                "to explicitly disable key authentication and use only password authentication."
            ),
        ),
    ]

    username: Annotated[
        str,
        Field(
            default=None,
            description=(
                "Username for authenticating to the network device. This is the login account "
                "used to establish the initial connection. For devices requiring privilege "
                "escalation (enable mode), this is typically the regular user account before "
                "escalation. This field is required for password-based authentication."
            ),
        ),
        MapFrom("user"),
    ]

    verbose: Annotated[
        bool | None,
        Field(
            default=None,
            description=(
                "Enable verbose output for debugging purposes. When set to True, Netmiko will "
                "print detailed information about the connection process, commands executed, and "
                "responses received. Useful for troubleshooting connection issues or understanding "
                "device behavior. Not recommended for production use as it can produce large "
                "amounts of output."
            ),
        ),
    ]


class Driver:
    """Netmiko driver for executing commands on network devices.

    This driver uses the netmiko library to connect to network devices
    via SSH and execute commands. It provides comprehensive support for
    various network operating systems and connection options.

    The driver implements the DriverSpec protocol and provides async-compatible
    methods by wrapping netmiko's synchronous operations.

    Attributes:
        options: Netmiko connection options configured for the device

    Example:
        options = DriverOptions(
            host="192.168.1.1",
            username="admin",
            password="admin",
            device_type="cisco_ios",
        )
        driver = Driver(options)
        results = await driver.send_commands(["show version"])
    """

    def __init__(self, options: DriverOptions) -> None:
        """Initialize the Netmiko driver with connection options.

        Args:
            options: Netmiko connection options for the device
        """
        self.options: DriverOptionsBase = options

    def _prepare_kwargs(self) -> dict[str, Any]:
        """Prepare connection kwargs from options.

        Handles the case where both 'ip' and 'host' are set by preferring
        'host' and issuing a warning.

        Returns:
            Dictionary of connection parameters for netmiko.ConnectHandler
        """
        kwargs = self.options.model_dump(exclude_none=True)
        logging.debug("netmiko driver options: %s", kwargs)

        if all((kwargs.get("host") is not None, kwargs.get("ip") is not None)):
            warnings.warn(
                "Both `ip` and `host` drivers option set, using `host`", stacklevel=3
            )
            del kwargs["ip"]

        return kwargs

    def _enter_enable_mode(self, conn: Any) -> None:
        """Enter enable/privileged mode if required.

        Args:
            conn: Active netmiko connection object
        """
        if self.options.become is not None:
            logging.debug(f"Entering privilege mode for host {self.options.host}")
            conn.enable()

    def _execute_commands_sync(
        self, kwargs: dict[str, Any], commands: list[str]
    ) -> list[tuple[str, str]]:
        """Execute commands synchronously (to be run in thread pool).

        This method performs synchronous I/O operations and should be
        called via asyncio.to_thread() to avoid blocking the event loop.

        Uses send_command_timing() for better performance when enable_fast_mode
        is True, or send_command() for interactive commands when False.

        Args:
            kwargs: Connection parameters for netmiko.ConnectHandler
            commands: List of commands to execute

        Returns:
            List of tuples (command, output) for each command

        Raises:
            NetsdkError: If connection or command execution fails
        """
        results = []

        with netmiko.ConnectHandler(**kwargs) as conn:
            self._enter_enable_mode(conn)

            for command in commands:
                if self.options.enable_fast_mode:
                    # Use send_command_timing for 20-30% better performance
                    # This skips pattern matching and returns after a fixed delay
                    resp = conn.send_command_timing(command)
                else:
                    # Use send_command for interactive commands that need
                    # pattern detection
                    resp = conn.send_command(command)
                results.append((command, resp))

        return results

    def _execute_config_sync(
        self, kwargs: dict[str, Any], commands: list[str], commit: bool
    ) -> str:
        """Execute configuration commands synchronously (to be run in thread pool).

        This method performs synchronous I/O operations and should be
        called via asyncio.to_thread() to avoid blocking the event loop.

        Args:
            kwargs: Connection parameters for netmiko.ConnectHandler
            commands: List of configuration commands to execute
            commit: Whether to commit the configuration changes

        Returns:
            The output from the configuration session

        Raises:
            NetsdkError: If connection or command execution fails
        """
        with netmiko.ConnectHandler(**kwargs) as conn:
            self._enter_enable_mode(conn)

            output = conn.send_config_set(commands, cmd_verify=False)

            if commit:
                output += conn.commit()

            return output

    async def send_commands(self, commands: list[str]) -> list[tuple[str, str]]:
        """Sends commands to the remote device and returns the output.

        Args:
            commands: A list of commands to execute

        Returns:
            A list of tuples (command, result) for each command

        Raises:
            NetsdkError: If connection or command execution fails
        """
        try:
            kwargs = self._prepare_kwargs()

            # Run blocking I/O in thread pool to avoid blocking event loop
            return await asyncio.to_thread(
                self._execute_commands_sync, kwargs, commands
            )

        except (
            netmiko.NetmikoTimeoutException,
            netmiko.NetmikoAuthenticationException,
        ) as exc:
            logging.exception(exc)
            msg = (
                f"failed to run commands on {self.options.host}: "
                f"{type(exc).__name__}: {exc}"
            )
            raise NetsdkError(msg) from exc

    async def send_config(self, commands: list[str], *, commit: bool = False) -> str:
        """Send configuration commands to the remote device.

        This method enters configuration mode, sends the configuration
        commands, and exits configuration mode automatically.

        Args:
            commands: A list of configuration commands to execute
            commit: Whether to commit the configuration changes (default: False)

        Returns:
            The output from the configuration session

        Raises:
            NetsdkError: If connection or command execution fails
        """
        try:
            kwargs = self._prepare_kwargs()

            # Run blocking I/O in thread pool to avoid blocking event loop
            return await asyncio.to_thread(
                self._execute_config_sync, kwargs, commands, commit
            )

        except (
            netmiko.NetmikoTimeoutException,
            netmiko.NetmikoAuthenticationException,
        ) as exc:
            logging.exception(exc)
            msg = (
                f"failed to send config to {self.options.host}: "
                f"{type(exc).__name__}: {exc}"
            )
            raise NetsdkError(msg) from exc

    def _check_alive_sync(self, kwargs: dict[str, Any]) -> bool:
        """Check if device is reachable synchronously (to be run in thread pool).

        This method performs synchronous I/O operations and should be
        called via asyncio.to_thread() to avoid blocking the event loop.

        Args:
            kwargs: Connection parameters for netmiko.ConnectHandler

        Returns:
            True if device is reachable and authenticated, False otherwise
        """
        try:
            with netmiko.ConnectHandler(**kwargs) as conn:
                self._enter_enable_mode(conn)
                return True
        except (
            netmiko.NetmikoTimeoutException,
            netmiko.NetmikoAuthenticationException,
            Exception,
        ):
            return False

    async def is_alive(self) -> bool:
        """Check if the device is reachable and optionally authenticated.

        This method attempts to connect to the device and authenticate.
        It returns True if the connection and authentication are successful,
        False otherwise.

        Returns:
            True if device is reachable and authenticated, False otherwise
        """
        try:
            kwargs = self._prepare_kwargs()

            # Run blocking I/O in thread pool to avoid blocking event loop
            return await asyncio.to_thread(self._check_alive_sync, kwargs)

        except Exception:
            return False
