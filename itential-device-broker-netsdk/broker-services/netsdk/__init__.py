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

# Import inventory module - with fallback to broker.inventory functions
# The inventory module may not be present in all deployments (e.g., when copied to /tmp)
# In that case, we use the inventory functions that broker.py re-exports
inventory = None
try:
    # Method 1: Try standard import
    from netsdk.api import inventory
except (ImportError, AttributeError):
    try:
        # Method 2: Direct module import
        import netsdk.api.inventory as inventory
    except ImportError:
        # Method 3: inventory.py not available - this is OK because broker.py
        # re-exports the inventory functions for backwards compatibility
        # Create a simple namespace object that proxies to broker
        import types
        inventory = types.SimpleNamespace()
        # The load_inventory function and others are available from broker
        inventory.load = broker.load
        inventory.load_inventory = broker.load_inventory
        inventory.load_from_file = broker.load_from_file
        inventory.load_from_stdin = broker.load_from_stdin
        inventory.loads = broker.loads

__all__ = (
    "__version__",
    "broker",
    "inventory",
    "logging",
)

__version__ = metadata.version
