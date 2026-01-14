# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""NetSDK API package.

This package provides the public API interface for NetSDK, including
broker functions for inventory management and command execution.
"""

from netsdk.api import broker

# Note: inventory module is imported by netsdk/__init__.py directly
# to avoid circular import issues. This is a workaround for portable
# distributions where the package is not installed via pip.

__all__ = ("broker",)
