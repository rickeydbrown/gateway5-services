# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Driver interface definitions and base classes for NetSDK.

This module defines the core interfaces and base classes that all NetSDK
drivers must implement or extend. It provides:

1. MapFrom: Metadata for mapping Host fields to driver option fields
2. DriverOptionsBase: Base class for driver-specific connection options
3. DriverSpec: Protocol defining the interface all drivers must implement

The driver system allows NetSDK to support multiple backend libraries
(like netmiko and scrapli) through a consistent interface.

Classes:
    DriverOptionsBase: Base Pydantic model for driver options
    DriverSpec: Protocol defining required driver methods

Named Tuples:
    MapFrom: Metadata for field mapping from Host to driver options
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

MapFrom is used as Pydantic field metadata to specify which Host field
should be mapped to a driver option field when no explicit value is provided.

Args:
    name: The name of the field in the Host model to map from

Example:
    username: Annotated[
        str,
        Field(default=None, description="Username"),
        MapFrom("user"),  # Maps from host.user if username not set
    ]
"""


class DriverOptionsBase(BaseModel):
    """Base class for driver-specific connection options.

    All driver option classes must inherit from this base class, which provides
    common configuration for validation and immutability.

    The model is frozen (immutable) and forbids extra fields to ensure
    strict validation of driver options.

    Configuration:
        extra: "forbid" - Reject any fields not explicitly defined
        frozen: True - Make instances immutable after creation
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


@runtime_checkable
class DriverSpec(Protocol):
    """Protocol defining the interface for network device drivers.

    All driver implementations must provide these methods to be compatible
    with the NetSDK broker system.

    This protocol is runtime checkable, allowing isinstance() checks to verify
    that dynamically loaded drivers conform to the expected interface.
    """

    options: DriverOptionsBase

    async def send_commands(self, commands: list[str]) -> list[tuple[str, str]]:
        """Run commands on the device."""
        ...

    async def send_config(self, commands: list[str]) -> str:
        """Send configuration commands to the device."""
        ...

    async def is_alive(self) -> bool:
        """Check if the device is reachable and optionally authenticated."""
        ...
