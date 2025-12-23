# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Driver interface definitions and base classes for NetSDK.

This module defines the core interfaces and base classes that all NetSDK
drivers must implement or extend to integrate with the framework. It provides
a plugin architecture that allows NetSDK to support multiple backend libraries
(like netmiko and scrapli) through a consistent, unified interface.

Architecture:
    The driver system uses a three-component design:

    1. MapFrom: Named tuple providing metadata for automatic field mapping
       between Host model fields and driver-specific option fields

    2. DriverOptionsBase: Base Pydantic model that all driver option classes
       must inherit from, providing immutability and strict validation

    3. DriverSpec: Runtime-checkable Protocol that defines the required methods
       all driver implementations must provide for compatibility

Usage:
    Driver implementations should:
    - Define an Options class inheriting from DriverOptionsBase
    - Implement the DriverSpec protocol methods (send_commands, send_config, is_alive)
    - Use MapFrom metadata to map Host fields to driver-specific option fields
    - Register via entry points in pyproject.toml for automatic discovery

Example:
    class MyDriverOptions(DriverOptionsBase):
        username: str = Field(default=None, metadata=[MapFrom("user")])
        password: str = Field(default=None, metadata=[MapFrom("password")])

    class MyDriver:
        options: MyDriverOptions

        async def send_commands(self, commands: list[str]) -> list[tuple[str, str]]:
            # Implementation here
            pass

Classes:
    DriverOptionsBase: Base Pydantic model for driver options with strict validation
    DriverSpec: Protocol defining the required driver interface

Named Tuples:
    MapFrom: Metadata for automatic field mapping from Host to driver options

See Also:
    netsdk.drivers.netmiko: Reference netmiko driver implementation
    netsdk.drivers.scrapli: Reference scrapli driver implementation
"""

from __future__ import annotations

from collections import namedtuple
from typing import TYPE_CHECKING
from typing import Protocol
from typing import runtime_checkable

from pydantic import BaseModel
from pydantic import ConfigDict

if TYPE_CHECKING:
    from netsdk.core.models import Host as Host

MapFrom = namedtuple("MapFrom", ("name",))
"""Metadata for mapping Host model fields to driver option fields.

MapFrom is a named tuple used as Pydantic field metadata to enable automatic
field mapping. When a driver option field is not explicitly provided, the
framework will check if MapFrom metadata exists and automatically populate
the driver option field from the corresponding Host model field.

This mechanism enables a clean separation between the generic Host model
and driver-specific option classes while maintaining convenience and
reducing boilerplate code.

Attributes:
    name (str): The name of the field in the Host model to map from

Behavior:
    - If the driver option field has an explicit value, MapFrom is ignored
    - If the driver option field is None/unset, the value is copied from Host.{name}
    - If the Host field doesn't exist or is None, the driver option remains None
    - Mapping occurs during inventory initialization when creating driver options

Example:
    class DriverOptions(DriverOptionsBase):
        username: Annotated[
            str | None,
            Field(default=None, description="Authentication username"),
            MapFrom("user"),  # Maps from host.user if username not explicitly set
        ] = None

        hostname: Annotated[
            str | None,
            Field(default=None, description="Device hostname or IP"),
            MapFrom("host"),  # Maps from host.host if hostname not provided
        ] = None

    # When creating inventory:
    # If host.user="admin" and username is not set, username will be "admin"
    # If username="root" is explicitly set, it overrides the mapping

See Also:
    netsdk.core.models.Host: The Host model containing source fields
    netsdk.core.models.Inventory: Handles the mapping during initialization
"""


class DriverOptionsBase(BaseModel):
    """Base class for driver-specific connection options.

    All driver option classes must inherit from this base class, which provides
    common Pydantic configuration for validation, immutability, and type safety.
    This ensures consistent behavior across all driver implementations.

    The model enforces strict validation by forbidding extra fields and making
    instances immutable after creation. This prevents runtime errors from typos
    in field names and ensures thread-safe usage of option objects.

    Configuration:
        extra="forbid": Reject any fields not explicitly defined in the model,
            catching typos and invalid configuration early

        frozen=True: Make instances immutable after creation, ensuring thread
            safety and preventing accidental modification

    Usage:
        All driver option classes should inherit from this base:

        class NetmikoOptions(DriverOptionsBase):
            username: str | None = None
            password: str | None = None
            timeout: int = 30

    Attributes:
        model_config (ConfigDict): Pydantic model configuration

    Example:
        # Creating driver options
        options = NetmikoOptions(username="admin", password="secret")

        # Attempting to set undefined field raises error
        # options = NetmikoOptions(invalid_field="value")  # Raises ValidationError

        # Attempting to modify after creation raises error
        # options.username = "different"  # Raises ValidationError

    Notes:
        - Subclasses automatically inherit the frozen and extra="forbid" config
        - Use Field() with MapFrom metadata to enable automatic field mapping
        - All fields should have type hints for proper validation
        - Use str | None for optional string fields, not Optional[str]

    See Also:
        netsdk.drivers.netmiko: Example netmiko driver options implementation
        netsdk.drivers.scrapli: Example scrapli driver options implementation
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


@runtime_checkable
class DriverSpec(Protocol):
    """Protocol defining the interface for network device drivers.

    This protocol specifies the required interface that all NetSDK driver
    implementations must provide. It uses Python's structural subtyping
    (Protocol) to enable runtime verification of driver compatibility
    without requiring explicit inheritance.

    The protocol is marked as runtime_checkable, allowing isinstance() and
    issubclass() checks to verify that dynamically loaded driver classes
    conform to the expected interface. This is essential for the plugin
    architecture where drivers are loaded at runtime via entry points.

    All methods are async to support non-blocking I/O operations when
    communicating with network devices, enabling efficient concurrent
    execution across multiple devices.

    Attributes:
        options (DriverOptionsBase): Instance of driver-specific options
            containing connection parameters and driver configuration

    Methods:
        send_commands: Execute show/display commands and return output
        send_config: Send configuration commands with optional commit
        is_alive: Verify device connectivity and authentication

    Usage:
        Implement this protocol in your driver class:

        class MyDriver:
            def __init__(self, host: Host, options: MyDriverOptions):
                self.host = host
                self.options = options

            async def send_commands(
                self, commands: list[str]
            ) -> list[tuple[str, str]]:
                # Implementation
                pass

            async def send_config(
                self, commands: list[str], *, commit: bool = False
            ) -> str:
                # Implementation
                pass

            async def is_alive(self) -> bool:
                # Implementation
                pass

        # Verify protocol conformance
        assert isinstance(MyDriver, DriverSpec)  # True if properly implemented

    Notes:
        - All methods must be async (coroutines)
        - Drivers should handle connection lifecycle within method calls
        - Error handling should raise appropriate NetsdkError subclasses
        - Drivers are responsible for cleaning up resources
        - Thread safety is not required as each invocation gets a new instance

    See Also:
        netsdk.drivers.netmiko: Complete reference implementation
        netsdk.drivers.scrapli: Alternative reference implementation
        netsdk.executor.handlers: Handler functions that invoke driver methods
    """

    options: DriverOptionsBase

    async def send_commands(self, commands: list[str]) -> list[tuple[str, str]]:
        """Execute show/display commands on the network device.

        Sends read-only commands to the device and returns the output for each
        command. This method is used for operational commands that query device
        state without making configuration changes.

        The method should handle connection establishment, command execution,
        and connection cleanup within a single invocation. Each call should be
        independent and not maintain persistent connections between calls.

        Args:
            commands (list[str]): List of commands to execute on the device.
                Commands should not include configuration mode commands.
                Example: ["show version", "show interfaces"]

        Returns:
            list[tuple[str, str]]: List of tuples where each tuple contains:
                - Element 0 (str): The command that was executed
                - Element 1 (str): The output/response from the device

        Raises:
            NetsdkError: Base exception for SDK-related errors
            ConnectionError: If unable to connect to the device
            AuthenticationError: If authentication fails
            TimeoutError: If command execution times out
            CommandError: If command execution fails on the device

        Example:
            commands = ["show version", "show ip interface brief"]
            results = await driver.send_commands(commands)

            for cmd, output in results:
                print(f"Command: {cmd}")
                print(f"Output: {output}")
                print("-" * 40)

        Notes:
            - Empty command list should return empty list, not raise error
            - Commands are executed in the order provided
            - Driver should handle privilege escalation if needed
            - Output should preserve original formatting from device
            - Timeout should be configurable via driver options
        """
        ...

    async def send_config(self, commands: list[str], *, commit: bool = False) -> str:
        """Send configuration commands to the network device.

        Sends configuration commands to modify device configuration. Depending
        on the device platform and the commit parameter, changes may be applied
        immediately or staged for later commit.

        The method should handle entering configuration mode, sending commands,
        optionally committing changes, and exiting configuration mode. Error
        handling should ensure the device is left in a consistent state.

        Args:
            commands (list[str]): List of configuration commands to send.
                Commands should be device CLI configuration commands.
                Example: ["interface Ethernet1/1", "description Uplink"]

            commit (bool, optional): Whether to commit configuration changes.
                - True: Commit/save the configuration (makes changes persistent)
                - False: Stage changes without committing (default)
                For platforms without explicit commit, this may trigger a save.

        Returns:
            str: Combined output from all configuration commands. The exact
                format depends on the underlying driver and device platform.
                May include command echoes, confirmation messages, or errors.

        Raises:
            NetsdkError: Base exception for SDK-related errors
            ConnectionError: If unable to connect to the device
            AuthenticationError: If authentication fails
            TimeoutError: If configuration times out
            ConfigError: If configuration commands fail or are invalid

        Example:
            config_commands = [
                "interface GigabitEthernet0/1",
                "description WAN Link",
                "ip address 10.0.0.1 255.255.255.0",
                "no shutdown",
            ]

            output = await driver.send_config(config_commands, commit=True)
            print(f"Configuration output: {output}")

        Notes:
            - Empty command list should return empty string
            - Commands are executed in the order provided
            - Driver should handle entering/exiting config mode
            - Commit behavior varies by platform (IOS vs Junos vs NX-OS)
            - Configuration errors should be detected and raised
            - Consider using transactions if supported by platform
        """
        ...

    async def is_alive(self) -> bool:
        """Check if the network device is reachable and responsive.

        Verifies that the device is accessible over the network and, depending
        on the driver implementation, may also verify authentication. This
        method is used for health checks and connectivity validation.

        The check should be lightweight and fast, as it may be called frequently
        for monitoring purposes. It should not make configuration changes or
        execute commands that could impact device performance.

        Returns:
            bool: True if device is reachable and responsive, False otherwise.
                - True: Device is accessible and ready for operations
                - False: Device is unreachable, authentication failed, or not responding

        Raises:
            NetsdkError: Only for unexpected errors during the check.
                Connection failures, timeouts, and auth errors should return
                False rather than raising exceptions, to allow graceful handling
                in bulk operations.

        Example:
            if await driver.is_alive():
                print("Device is reachable")
                results = await driver.send_commands(["show version"])
            else:
                print("Device is not reachable")

        Notes:
            - Should complete quickly (within configured timeout)
            - May or may not establish full authentication depending on driver
            - Return False for transient errors (timeouts, connection refused)
            - Should not leave persistent connections open
            - Suitable for use in monitoring and pre-flight checks
            - Implementation may vary: TCP connect, SSH handshake, or login attempt
        """
        ...
