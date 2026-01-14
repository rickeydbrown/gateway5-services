# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""NetSDK API package.

This package provides the public API interface for NetSDK, including
broker functions for inventory management and command execution.
"""

# Import broker immediately
from netsdk.api import broker

# Lazy load inventory to avoid circular imports
_inventory = None

def __getattr__(name):
    """Lazy import inventory module on first access."""
    global _inventory
    if name == "inventory":
        if _inventory is None:
            # Import using the full module path to avoid circular issues
            import sys
            import importlib.util
            from pathlib import Path

            # Get the inventory.py file path
            inventory_file = Path(__file__).parent / "inventory.py"

            # Load it as a module
            spec = importlib.util.spec_from_file_location("netsdk.api.inventory", inventory_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules['netsdk.api.inventory'] = module
            spec.loader.exec_module(module)
            _inventory = module
        return _inventory
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
