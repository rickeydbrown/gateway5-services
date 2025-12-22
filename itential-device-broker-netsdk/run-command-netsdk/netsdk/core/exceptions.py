# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Exception classes for NetSDK.

This module defines the exception hierarchy for NetSDK, with NetsdkError as
the base exception. All SDK-specific errors inherit from NetsdkError, making
it easy to catch and handle SDK-related exceptions.

Classes:
    NetsdkError: Base exception for all SDK errors
    SerializationError: Raised for JSON serialization/deserialization failures
"""


class NetsdkError(Exception):
    """
    Base exception class for all Itential SDK errors.

    All SDK-specific exceptions inherit from this base class, making it easy
    to catch any SDK-related error.

    Args:
        message (str): Human-readable error message
    """

    def __init__(self, message: str) -> None:
        """
        Initialize the base SDK exception.

        Args:
            message (str): Human-readable error message
        """
        super().__init__(message)

    def __str__(self) -> str:
        """
        Return a string representation of the error.

        Returns:
            A formatted error message including details if available
        """
        return self.args[0]


class SerializationError(NetsdkError):
    """
    Exception raised for JSON serialization and deserialization errors.

    This exception is raised when JSON parsing (loads) or encoding (dumps)
    operations fail. Common scenarios include malformed JSON, invalid data
    types, or encoding errors.

    Args:
        message (str): Human-readable error message describing the failure
    """
