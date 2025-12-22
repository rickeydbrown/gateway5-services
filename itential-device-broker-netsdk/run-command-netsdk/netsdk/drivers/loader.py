# Copyright 2025 Itential Inc. All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Dynamic module and class loader with entry point and filesystem support.

This module provides the Loader class which dynamically loads Python classes
from either entry points (for installed packages) or from the filesystem
(for local development). It includes caching to improve performance.

The loader is used to dynamically load network device drivers and their
option classes at runtime, enabling a plugin-based architecture.

Classes:
    Loader: Dynamic class loader with entry point and filesystem support

Module Variables:
    driver_loader: Pre-configured loader for network device drivers
    options_loader: Pre-configured loader for driver option classes
"""

import importlib.util
import os
import pathlib
import sys

from importlib.metadata import entry_points
from pathlib import Path

from netsdk.utils import logging

__all__ = ("Loader", "driver_loader", "options_loader")


class Loader:
    """Loader class for dynamically loading classes using entry points or files.

    The Loader supports two mechanisms for discovering and loading drivers:
    1. Entry points: Checks for 'netsdk.driver.{name}' entry points first
    2. Filesystem: Falls back to loading from files in the base_path directory

    This allows drivers to be:
    - Distributed as separate packages and registered via entry points
    - Bundled as files in the drivers directory

    Files starting with underscore (_) are automatically ignored.

    Example:
        loader = Loader("/path/to/drivers", "Driver")

        # Tries entry point 'netsdk.driver.netmiko' first,
        # then falls back to /path/to/drivers/netmiko.py
        driver_class = loader.load("netmiko")
        driver_instance = loader.load_instance("netmiko")
    """

    def __init__(self, base_path: str, class_name: str = "Driver") -> None:
        """Initialize the Loader with a base path and class name.

        Args:
            base_path: The base directory path where modules are located
            class_name: The name of the class to load from each module
                (default: "Driver")

        Raises:
            FileNotFoundError: If the base_path does not exist
        """
        self.base_path = Path(base_path)
        self.class_name = class_name
        self._cache: dict[str, type] = {}

        if not self.base_path.exists():
            logging.error(f"base path not found: {base_path}")
            raise FileNotFoundError(f"base path not found: {base_path}")

        if not self.base_path.is_dir():
            logging.error(f"base path is not a directory: {base_path}")
            raise NotADirectoryError(f"base path is not a directory: {base_path}")

        logging.debug(
            f"initialized loader with base_path={base_path}, class_name={class_name}"
        )

    def load(self, name: str) -> type:
        """Load a driver class by name.

        Attempts to load the driver from entry points first, then falls back
        to filesystem-based loading if the entry point is not found.

        Args:
            name: The name of the driver to load (e.g., 'netmiko', 'scrapli')

        Returns:
            The loaded driver class

        Raises:
            FileNotFoundError: If the driver file cannot be found
            ImportError: If the driver module cannot be imported
            AttributeError: If the driver class is not found in the module
            TypeError: If the loaded class doesn't meet driver requirements

        Examples:
            >>> loader = Loader("/path/to/drivers", "Driver")
            >>> netmiko_driver = loader.load("netmiko")
        """
        # Check if the module is already loaded in cache
        if name in self._cache:
            logging.debug(f"returning cached {self.class_name} for: {name}")
            return self._cache[name]

        try:
            loaded_class = self._load_from_entry_point(name)
            if loaded_class is not None:
                logging.debug(
                    f"loaded {self.class_name} from entry point: netsdk-driver/{name}"
                )
                self._validate_driver_class(loaded_class, name)
                self._cache[name] = loaded_class
                return loaded_class

        except Exception as exc:
            logging.debug(f"entry point not found for {name}, trying filesystem: {exc}")

        # Fall back to loading from filesystem
        logging.debug(f"falling back to filesystem loading for: {name}")
        loaded_class = self._load_from_file(name)
        self._validate_driver_class(loaded_class, name)
        self._cache[name] = loaded_class
        return loaded_class

    def _validate_driver_class(self, driver_class: type, name: str) -> None:
        """Validate that a driver class meets the required interface.

        Args:
            driver_class: The driver class to validate
            name: The name of the driver (for error messages)

        Raises:
            TypeError: If the driver class doesn't meet requirements
        """
        # Only validate actual Driver classes, not DriverOptions
        if self.class_name != "Driver":
            return

        # Check it's actually a class
        if not isinstance(driver_class, type):
            msg = (
                f"driver '{name}' is not a class: got {type(driver_class).__name__}. "
                "Drivers must be classes that can be instantiated."
            )
            raise TypeError(msg)

        # Check for required methods
        required_methods = {"send_commands", "send_config", "is_alive"}
        missing = [
            method_name
            for method_name in required_methods
            if not hasattr(driver_class, method_name)
        ]

        if missing:
            msg = (
                f"driver '{name}' missing required methods: {', '.join(missing)}. "
                "All drivers must implement the DriverSpec protocol with "
                "send_commands(), send_config(), and is_alive() methods."
            )
            raise TypeError(msg)

        logging.debug(f"validated driver '{name}' conforms to DriverSpec interface")

    def _load_from_entry_point(self, name: str) -> type | None:
        """Load a driver class from entry points.

        Searches the 'netsdk.driver' entry point group for a driver
        matching the given name and loads its class.

        Args:
            name: The name of the driver entry point to load

        Returns:
            The loaded driver class, or None if not found

        Raises:
            AttributeError: If the class is not found in the entry point module
        """
        eps = entry_points()
        driver_eps = eps.select(group="netsdk.driver")

        # Find the entry point matching the driver name
        for ep in driver_eps:
            if ep.name == name:
                logging.debug(f"found entry point: {ep.name} -> {ep.value}")
                module = ep.load()

                # Try to get the class from the module
                try:
                    return getattr(module, self.class_name)

                except AttributeError:
                    # If the entry point itself is the class, return it directly
                    if hasattr(module, "__mro__"):  # It's a class
                        return module
                    raise AttributeError(
                        f"{self.class_name} class not found in entry point '{ep.name}'"
                    ) from None

        return None

    def _load_from_file(self, name: str) -> type:
        """Load a driver class from a filesystem module.

        Loads a Python module from the filesystem using the given name
        and extracts the driver class from it.

        Args:
            name: The name of the module file (without .py extension)

        Returns:
            The loaded driver class

        Raises:
            FileNotFoundError: If the module file does not exist
            ImportError: If the module cannot be imported
            AttributeError: If the class is not found in the module
        """
        filename = f"{name}.py"
        file_path = self.base_path / filename

        if not file_path.exists():
            logging.error(f"file not found: {file_path}")
            raise FileNotFoundError(f"file not found: {file_path}")

        # Add the parent of netsdk to sys.path for absolute imports
        netsdk_parent = file_path.parent.parent.parent
        if str(netsdk_parent) not in sys.path:
            sys.path.insert(0, str(netsdk_parent))

        # Construct the full module path relative to the sys.path entry
        # e.g., "netsdk.drivers.netmiko" instead of just "netmiko"
        relative_path = file_path.relative_to(netsdk_parent)
        module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")

        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"failed to create module spec for {file_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logging.debug(f"loaded module from file: {file_path}")

        except Exception as exc:
            logging.exception(exc)
            raise ImportError(f"failed to import module from '{file_path}'") from exc

        try:
            result = getattr(module, self.class_name)

        except AttributeError as exc:
            logging.exception(exc)
            raise AttributeError(
                f"{self.class_name} class not found in '{file_path}'"
            ) from exc

        else:
            logging.debug(f"loaded {self.class_name} class from {file_path}")
            return result


driver_loader = Loader(pathlib.Path(__file__).parent, "Driver")
options_loader = Loader(pathlib.Path(__file__).parent, "DriverOptions")
