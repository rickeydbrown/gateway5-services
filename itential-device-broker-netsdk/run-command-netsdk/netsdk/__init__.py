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
    from netsdk import broker
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

    inventory = broker.load_inventory(inventory_data["inventory_nodes"])
    result = asyncio.run(broker.run_command(inventory, ["show version"]))
"""

from netsdk import metadata
from netsdk.executor import broker
from netsdk.utils import logging

__all__ = (
    "__version__",
    "broker",
    "logging",
)

__version__ = metadata.version
