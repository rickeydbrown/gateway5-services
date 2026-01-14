# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""NetSDK - Unified network device management library.

NetSDK provides a unified interface for connecting to and managing network devices
through multiple backend drivers (netmiko, scrapli). It abstracts the differences
between these libraries to provide consistent command execution and configuration
management across different network operating systems.

The library is async-first and designed for high concurrency, making it suitable
for managing large inventories of network devices in parallel.

Example:
    import asyncio
    import json
    from netsdk import broker
    from netsdk import inventory
    from netsdk import logging

    # Initialize logging (must be done explicitly)
    logging.initialize()
    logging.set_level(logging.INFO)

    inventory_data = {
        "inventory_nodes": [{
            "name": "router1",
            "attributes": {
                "host": "192.168.1.1",
                "user": "admin",
                "password": "admin",
                "driver": "netmiko",
                "platform": "cisco_ios"
            }
        }]
    }

    inv = inventory.load_inventory(json.dumps(inventory_data))
    result = asyncio.run(broker.run_command(inv, ["show version"]))
"""

from netsdk import metadata
from netsdk.api import broker
from netsdk.utils import logging

# Import inventory module directly - try multiple methods
inventory = None
try:
    # Method 1: Try standard import
    from netsdk.api import inventory
except (ImportError, AttributeError):
    try:
        # Method 2: Direct module import
        import netsdk.api.inventory as inventory
    except ImportError:
        try:
            # Method 3: Load from file path
            import sys
            import importlib.util
            from pathlib import Path

            inventory_file = Path(__file__).parent / "api" / "inventory.py"
            if inventory_file.exists():
                spec = importlib.util.spec_from_file_location("netsdk.api.inventory", inventory_file)
                inventory = importlib.util.module_from_spec(spec)
                sys.modules['netsdk.api.inventory'] = inventory
                spec.loader.exec_module(inventory)
            else:
                # Provide detailed diagnostic information
                api_dir = Path(__file__).parent / "api"
                api_contents = list(api_dir.iterdir()) if api_dir.exists() else ["API dir doesn't exist"]
                raise ImportError(
                    f"inventory.py not found at {inventory_file}\n"
                    f"API directory exists: {api_dir.exists()}\n"
                    f"API directory contents: {[f.name for f in api_contents if not f.name.startswith('__')]}"
                )
        except Exception as e:
            raise ImportError(f"Failed to import inventory module: {e}")

__all__ = (
    "__version__",
    "broker",
    "inventory",
    "logging",
)

__version__ = metadata.version
