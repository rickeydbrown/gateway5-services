# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""NetSDK API package.

This package provides the public API interface for NetSDK, including
broker functions for command execution and inventory functions for
inventory management.
"""

# Use lazy imports to avoid circular import issues
# Import submodules by their actual module name, not from parent
import importlib

def __getattr__(name):
    """Lazy import API modules to avoid circular imports."""
    if name in ("broker", "inventory"):
        # Import the module directly without going through netsdk.api
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = (
    "broker",
    "inventory",
)
