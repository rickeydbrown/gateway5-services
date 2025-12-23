# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Core domain models for network devices.

This module defines the Host and Inventory models using Pydantic. Host represents
a network device with all its connection parameters and driver options. Inventory
is a collection of Host objects with validation and sequence-like interface.

Classes:
    Host: Immutable model representing a network device with connection parameters
    Inventory: Collection of Host objects with validation and iteration support
"""

from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from netsdk.executor import loader

__all__ = ("Host", "Inventory")


class Host(BaseModel):
    """Immutable model representing a network device with connection parameters.

    Host encapsulates all information needed to connect to and interact with a network
    device, including connection details, authentication credentials, and driver-specific
    configuration options. Host instances are immutable and validated using Pydantic.

    The model supports multiple drivers (netmiko, scrapli) and provides flexible field
    mapping through aliases to work with various inventory formats. Common Host fields
    are automatically mapped to driver-specific options when establishing connections.

    Attributes:
        name: Unique identifier for the host within the inventory
        host: Hostname or IP address of the target device
        port: Optional TCP port number (defaults to driver-specific port)
        driver: Driver library to use (default: "netmiko")
        platform: Network OS platform identifier (e.g., "cisco_ios", "juniper_junos")
        user: Authentication username
        password: Authentication password
        become: Whether to enter privileged/enable mode after connecting
        become_password: Password for privilege escalation (enable mode)
        driver_options: Driver-specific configuration options

    Examples:
        Basic host with minimal configuration:
            >>> host = Host(
            ...     name="router1",
            ...     host="192.168.1.1",
            ...     user="admin",
            ...     password="secret"
            ... )

        Host with platform and privilege escalation:
            >>> host = Host(
            ...     name="switch1",
            ...     host="10.0.0.1",
            ...     platform="cisco_ios",
            ...     user="admin",
            ...     password="secret",
            ...     become=True,
            ...     become_password="enable_secret"
            ... )

        Host with driver-specific options:
            >>> from netsdk.drivers.netmiko import DriverOptions
            >>> options = DriverOptions(fast_cli=True, timeout=60)
            >>> host = Host(
            ...     name="router2",
            ...     host="192.168.1.2",
            ...     driver="netmiko",
            ...     platform="arista_eos",
            ...     driver_options=options
            ... )

    Note:
        All Host instances are immutable (frozen=True) to ensure thread-safety
        and prevent accidental modification during parallel operations.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True, frozen=True)

    name: str = Field(
        description=(
            "Unique identifier for this host within the inventory. This name is used to "
            "reference the host throughout the SDK and should be descriptive and meaningful "
            "for your network topology. It must be unique across all hosts in the inventory. "
            "Examples: 'dc1-spine1', 'lab-router-01', 'prod-switch-core'. This field is "
            "required and has no default value."
        ),
    )

    host: str = Field(
        description=(
            "Hostname or IP address of the target network device. This is the primary "
            "connection parameter used to establish connectivity to the device. Supports both "
            "IPv4 addresses (e.g., '192.168.1.1', '10.0.0.1') and hostnames that can be "
            "resolved via DNS (e.g., 'router1.example.com', 'switch.local'). IPv6 addresses "
            "are also supported when using compatible drivers and transports. This field is "
            "required for establishing a connection and has no default value. In inventory "
            "data structures, this field can also be specified using the alias 'itential_host'."
        ),
        alias="itential_host",
    )

    port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
        description=(
            "TCP port number to connect to on the target device. When not specified, the "
            "driver will use the default port for the selected connection protocol (typically "
            "SSH: 22, Telnet: 23). Override this when connecting to devices with non-standard "
            "port configurations, when using port forwarding, or when devices are behind "
            "NAT/firewall with port translation. Must be a valid port number between 1 and "
            "65535. Common use cases include SSH on non-standard ports (e.g., 2222, 8022) or "
            "connecting through jump hosts with port forwarding. In inventory data structures, "
            "this field can also be specified using the alias 'itential_port'."
        ),
        alias="itential_port",
    )

    driver: str = Field(
        default="netmiko",
        alias="itential_driver",
        description=(
            "Driver library to use for connecting to and communicating with the network device. "
            "The driver determines which underlying library and connection method will be used "
            "to establish connectivity and execute commands. Available drivers are discovered "
            "dynamically from installed packages and registered entry points. Built-in drivers "
            "include 'netmiko' (multi-vendor SSH library with broad device support) and 'scrapli' "
            "(modern async-capable SSH library with performance optimizations). The default value "
            "is 'netmiko' for maximum compatibility. Each driver may support different features, "
            "platforms, and performance characteristics. In inventory data structures, this field "
            "can also be specified using the alias 'itential_driver'."
        ),
    )

    platform: str | None = Field(
        default=None,
        alias="itential_platform",
        description=(
            "Network operating system platform identifier for the target device. This value "
            "is mapped to driver-specific platform names (e.g., 'device_type' for Netmiko, "
            "'platform' for Scrapli) and determines which command patterns, prompts, and "
            "behaviors the driver will use. Common examples include 'cisco_ios', 'cisco_nxos', "
            "'arista_eos', 'juniper_junos', 'hp_procurve'. The exact platform identifiers "
            "supported depend on the chosen driver library. Refer to the specific driver "
            "documentation for a complete list of supported platforms. This field is typically "
            "required unless the driver can auto-detect the platform. In inventory data "
            "structures, this field can also be specified using the alias 'itential_platform'."
        ),
    )

    user: str | None = Field(
        default=None,
        alias="itential_user",
        description=(
            "Username for authenticating to the network device. This is the login account "
            "used to establish the initial connection to the device. For devices requiring "
            "privilege escalation (enable mode), this is typically the regular user account "
            "before escalation. This field is mapped to driver-specific username fields "
            "(e.g., 'username' for Netmiko, 'auth_username' for Scrapli). Required unless "
            "using alternative authentication methods such as SSH key-based authentication "
            "without a username, or connecting to devices that don't require authentication "
            "(uncommon). In inventory data structures, this field can also be specified using "
            "the alias 'itential_user'."
        ),
    )

    password: str | None = Field(
        default=None,
        alias="itential_password",
        description=(
            "Password for authenticating to the network device. Used in conjunction with "
            "'user' for password-based authentication. This is the password for the initial "
            "login to the device, not the enable/privilege escalation password (use "
            "'become_password' for that). This field is mapped to driver-specific password "
            "fields (e.g., 'password' for Netmiko, 'auth_password' for Scrapli). Required "
            "if not using SSH key-based authentication or other alternative authentication "
            "methods. Note: For production environments, consider using SSH key authentication "
            "instead of password authentication for improved security, or store passwords in "
            "secure credential management systems. In inventory data structures, this field "
            "can also be specified using the alias 'itential_password'."
        ),
    )

    become: bool = Field(
        default=False,
        alias="itential_become",
        description=(
            "Whether to automatically enter privileged/enable mode after connecting to the "
            "device. When set to True, the driver will execute the platform-specific privilege "
            "escalation command (e.g., 'enable' on Cisco IOS, Arista EOS) immediately after "
            "authentication. This is commonly required for configuration changes, accessing "
            "privileged show commands, or performing administrative tasks on devices that use "
            "privilege levels (Cisco IOS, Arista EOS, and similar network operating systems). "
            "When enabled, you must also set 'become_password' if the device requires an enable "
            "password. The default value is False, meaning the connection will remain at user "
            "execution (non-privileged) level. In inventory data structures, this field can "
            "also be specified using the alias 'itential_become'."
        ),
    )

    become_password: str | None = Field(
        default=None,
        alias="itential_become_password",
        description=(
            "Enable password for privilege escalation (privileged/enable mode). This is the "
            "password used when entering enable mode on devices that support privilege levels. "
            "On Cisco IOS and similar devices, this is the password prompted for by the 'enable' "
            "command. This field is mapped to driver-specific fields (e.g., 'secret' for Netmiko, "
            "'auth_secondary' for Scrapli). Only required when 'become' is set to True and the "
            "device requires an enable password. Some devices may not require a separate enable "
            "password, in which case this can be left as None even when 'become' is True. Note: "
            "This is different from the login password ('password') and is specifically for "
            "privilege escalation. In inventory data structures, this field can also be specified "
            "using the alias 'itential_become_password'."
        ),
    )

    driver_options: Any | None = Field(
        default=None,
        alias="itential_driver_options",
        description=(
            "Driver-specific configuration options for fine-tuning connection behavior and "
            "performance. This field accepts a DriverOptions instance specific to the chosen "
            "driver (e.g., netmiko.DriverOptions, scrapli.DriverOptions). Driver options allow "
            "you to configure advanced settings such as timeout values, connection parameters, "
            "performance optimizations, and library-specific features that are not part of the "
            "common Host interface. When Host fields (like 'user', 'password', 'host') are mapped "
            "to driver options via MapFrom metadata, the Host field values are used as defaults "
            "unless explicitly overridden in driver_options. Each driver has its own set of "
            "available options - refer to the driver-specific documentation for complete details. "
            "Common driver options include fast_cli mode, global delay factors, timeout settings, "
            "and transport-specific configurations. In inventory data structures, this field can "
            "also be specified using the alias 'itential_driver_options'."
        ),
    )

    def __str__(self) -> str:
        """Return human-readable string representation of the host.

        Returns:
            Formatted string showing host name, address, and driver
        """
        return f"Host(name={self.name}, host={self.host}, driver={self.driver})"

    def __repr__(self) -> str:
        """Return detailed string representation for debugging.

        Returns:
            String with quoted values suitable for repr() output
        """
        return f"Host(name={self.name!r}, host={self.host!r}, driver={self.driver!r})"


class Inventory(Sequence):
    """Collection of Host objects with validation and sequence-like interface.

    Inventory represents a collection of network devices (Host objects) with support
    for iteration, indexing, and validation. It implements the Sequence protocol,
    allowing it to be used like a list with standard Python sequence operations.

    The Inventory class handles parsing of inventory data structures (typically loaded
    from JSON or YAML files) and converts them into validated Host objects. It supports
    driver-specific options parsing and provides pre-flight validation to catch
    configuration errors before attempting device connections.

    Attributes:
        elements: Internal list of Host objects in the inventory

    Examples:
        Create inventory from dictionary structure:
            >>> inventory_data = [{
            ...     "name": "router1",
            ...     "attributes": {
            ...         "itential_host": "192.168.1.1",
            ...         "itential_user": "admin",
            ...         "itential_password": "secret",
            ...         "itential_platform": "cisco_ios"
            ...     }
            ... }]
            >>> inventory = Inventory(inventory_data)

        Access hosts using sequence operations:
            >>> first_host = inventory[0]
            >>> for host in inventory:
            ...     print(host.name)
            >>> if "router1" in inventory:
            ...     print("Host found")

        Non-strict mode for partial validation:
            >>> inventory = Inventory(data, strict=False)
            >>> errors = inventory.validate()
            >>> if errors:
            ...     print(f"Found {len(errors)} validation errors")

    Note:
        When strict=True (default), the constructor raises ValueError if any hosts
        fail validation. Use strict=False to defer validation and inspect errors
        using the validate() method.
    """

    def __init__(
        self, items: list[dict[str, Any]] | None = None, *, strict: bool = True
    ) -> None:
        """Initialize inventory with host definitions and optional validation.

        Parses inventory node dictionaries into Host objects with driver-specific
        options. Each node should contain a 'name' and 'attributes' dictionary with
        host connection parameters. The 'attributes' dictionary uses 'itential_*'
        field names that are mapped to Host model fields via aliases.

        Args:
            items: List of inventory node dictionaries. Each node should have
                'name' (str) and 'attributes' (dict) keys. The attributes dict
                contains host parameters using 'itential_*' naming convention.
                Example: [{"name": "router1", "attributes": {"itential_host": "192.168.1.1"}}]
            strict: If True, validates all hosts during initialization and raises
                ValueError if any validation errors occur. If False, defers validation
                and allows inspection of errors via validate() method. Default: True.

        Raises:
            ValueError: If strict=True and any hosts fail validation. Error message
                includes all validation errors encountered.

        Examples:
            Strict validation (raises on error):
                >>> inventory = Inventory(data)  # Raises ValueError if invalid

            Deferred validation:
                >>> inventory = Inventory(data, strict=False)
                >>> errors = inventory.validate()
                >>> if errors:
                ...     print("Validation failed:", errors)
        """
        self.elements: list[Host] = []

        for node in items or []:
            # Extract name and attributes
            name = node.get("name")
            attributes = node.get("attributes", {})

            driver = attributes.get("itential_driver", "netmiko")

            kwargs = {"name": name}

            for field, info in Host.model_fields.items():
                key = getattr(info, "alias", field)
                if key in attributes:
                    kwargs[key] = attributes[key]

            driver_options = attributes.get("itential_driver_options", {})
            options_kwargs = {}
            if driver in driver_options:
                options_kwargs = dict(driver_options[driver])

            options = loader.options_loader.load(driver)
            kwargs["itential_driver_options"] = options(**options_kwargs)

            self.elements.append(Host(**kwargs))

        # Validate inventory if strict mode is enabled
        if strict:
            errors = self.validate()
            if errors:
                error_msg = "\n  ".join(errors)
                msg = (
                    f"Inventory validation failed with {len(errors)} error(s):"
                    f"\n  {error_msg}"
                )
                raise ValueError(msg)

    def __len__(self) -> int:
        """Return the number of hosts in the inventory.

        Returns:
            Count of Host objects in the inventory
        """
        return len(self.elements)

    def __iter__(self) -> Iterator[Host]:
        """Return iterator over hosts in the inventory.

        Returns:
            Iterator yielding Host objects in order
        """
        return iter(self.elements)

    def __contains__(self, item: Host | str) -> bool:
        """Check if a host exists in the inventory by object or name.

        Supports both Host object comparison and string-based name lookup
        for flexible membership testing.

        Args:
            item: Either a Host object for identity comparison or a string
                for name-based lookup

        Returns:
            True if the host exists in the inventory, False otherwise

        Examples:
            >>> host in inventory  # Check by Host object
            >>> "router1" in inventory  # Check by name string
        """
        if isinstance(item, Host):
            return item in self.elements
        if isinstance(item, str):
            return any(host.name == item for host in self.elements)
        return False

    def __getitem__(self, index: int | slice) -> Host | list[Host]:
        """Get host(s) by index or slice.

        Implements sequence protocol for indexed access and slicing operations.
        Supports negative indices and standard Python slice notation.

        Args:
            index: Integer index for single host access or slice object for
                multiple hosts. Supports negative indices (e.g., -1 for last host)

        Returns:
            Single Host object if index is int, list of Host objects if slice

        Raises:
            IndexError: If index is out of range

        Examples:
            >>> first = inventory[0]  # First host
            >>> last = inventory[-1]  # Last host
            >>> subset = inventory[1:3]  # Hosts at index 1 and 2
            >>> reversed_subset = inventory[::-1]  # All hosts in reverse
        """
        if isinstance(index, slice):
            return self.elements[index]
        return self.elements[index]

    def __str__(self) -> str:
        """Return human-readable string representation of the inventory.

        Returns:
            String showing inventory size
        """
        return f"Inventory({len(self)} hosts)"

    def __repr__(self) -> str:
        """Return detailed string representation showing all host names.

        Returns:
            String with list of host names for debugging
        """
        host_names = [host.name for host in self.elements]
        return f"Inventory(hosts={host_names})"

    def validate(self) -> list[str]:
        """Validate all hosts in the inventory for configuration correctness.

        Performs comprehensive pre-flight validation to catch configuration errors
        before attempting device connections. This validation includes:

        - Driver availability: Ensures specified drivers can be loaded
        - Driver options: Validates driver-specific option classes exist
        - Option instantiation: Verifies driver options can be constructed
        - Field mapping: Checks Host fields map correctly to driver options

        Validation is non-blocking - all hosts are checked and all errors are
        collected before returning, allowing you to see all issues at once.

        Returns:
            List of validation error messages, one per error found. Empty list
            indicates all hosts are valid and ready for use. Each error message
            includes the host name and specific issue encountered.

        Examples:
            Check for errors and handle appropriately:
                >>> errors = inventory.validate()
                >>> if errors:
                ...     print(f"Found {len(errors)} validation errors:")
                ...     for error in errors:
                ...         print(f"  - {error}")
                ... else:
                ...     print("All hosts validated successfully")

            Validate before executing commands:
                >>> errors = inventory.validate()
                >>> if not errors:
                ...     results = await broker.run_command(inventory, ["show version"])

        Note:
            This method is automatically called during __init__ when strict=True.
            Use this method manually when initializing with strict=False to
            inspect validation errors without raising exceptions.
        """
        errors = []

        for host in self.elements:
            # Check driver is loadable
            try:
                # Driver validation happens in loader.load() now
                loader.driver_loader.load(host.driver)
            except (FileNotFoundError, ImportError, TypeError) as exc:
                errors.append(
                    f"host '{host.name}': invalid driver '{host.driver}': {exc}"
                )
                continue

            # Check driver options class is loadable
            try:
                options_class = loader.options_loader.load(host.driver)
            except (FileNotFoundError, ImportError, AttributeError) as exc:
                msg = (
                    f"host '{host.name}': "
                    f"invalid driver options for '{host.driver}': {exc}"
                )
                errors.append(msg)
                continue

            # Validate we can build driver options (may catch type errors)
            try:
                options_kwargs = {}
                if host.driver_options:
                    for field_name in options_class.model_fields:
                        if hasattr(host.driver_options, field_name):
                            value = getattr(host.driver_options, field_name)
                            if value is not None:
                                options_kwargs[field_name] = value

                # Try to instantiate options to validate
                options_class(**options_kwargs)
            except Exception as exc:
                errors.append(f"host '{host.name}': invalid driver options: {exc}")

        return errors
