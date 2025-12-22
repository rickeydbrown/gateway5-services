# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Response models for command execution results.

This module defines Pydantic models for representing the results of command
executions on network devices. The models provide validation and serialization
for command output data.

Classes:
    CommandResult: Represents the result of a single command execution
    RunCommandResponse: Container for multiple CommandResult objects
"""

from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import RootModel

__all__ = ("CommandResult", "PingResponse", "PingResult", "RunCommandResponse")


class CommandResult(BaseModel):
    """Represents the result of a single command execution.

    Attributes:
        command: The command that was executed
        output: The output returned from the command
    """

    name: str = Field(
        description="The network device host that commands were executed on"
    )

    command: str = Field(default=None, description="The command that was executed")

    output: Any = Field(
        default=None, description="The output returned from the command"
    )

    success: bool = Field(
        default=True, description="True if the commands where successfully run"
    )

    host: str = Field(default=None, description="Hostname or IP address of the host")

    start: str = Field(default=None, description="Start time")

    end: str = Field(default=None, description="End time")

    elapsed: str = Field(default=None, description="Elapsed time")

    error: str | None = Field(
        default=None, description="Error message if command failed"
    )

    error_type: str | None = Field(
        default=None, description="Type of error that occurred"
    )


class RunCommandResponse(RootModel[list[CommandResult]]):
    """Represents the response from running commands across multiple hosts.

    This is a list-like container of CommandResult objects that provides
    Pydantic validation and serialization.
    """

    root: list[CommandResult]


class PingResult(BaseModel):
    """Represents the result of checking if a network device is alive.

    Attributes:
        name: The network device host that was checked
        alive: Whether the device is reachable and responding
        success: Whether the check completed without errors
        host: Hostname or IP address of the host
        start: Start time of the check
        end: End time of the check
        elapsed: Elapsed time for the check
    """

    name: str = Field(description="The network device host that was checked")

    alive: bool = Field(
        default=False, description="Whether the device is reachable and responding"
    )

    success: bool = Field(
        default=True, description="True if the check completed without errors"
    )

    host: str = Field(default=None, description="Hostname or IP address of the host")

    start: str = Field(default=None, description="Start time")

    end: str = Field(default=None, description="End time")

    elapsed: str = Field(default=None, description="Elapsed time")

    error: str | None = Field(default=None, description="Error message if check failed")

    error_type: str | None = Field(
        default=None, description="Type of error that occurred"
    )


class PingResponse(RootModel[list[PingResult]]):
    """Represents the response from checking alive status across multiple hosts.

    This is a list-like container of PingResult objects that provides
    Pydantic validation and serialization.
    """

    root: list[PingResult]
