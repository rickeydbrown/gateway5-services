# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Package metadata for NetSDK.

This module provides version and authorship information extracted from the
package metadata using importlib.metadata.

Module Variables:
    name: Package name
    author: Package author
    version: Package version (dynamically extracted from package metadata)
"""

from importlib.metadata import version as _version

name: str = "netsdk"
author: str = "Itential"
version: str = _version(name)
