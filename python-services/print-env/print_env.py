#!/usr/bin/env python3
"""
Print Env Service
Prints the Python version, interpreter executable path, (if running
inside a virtual environment) the venv's executable path, and the
install locations of the netmiko and pyaml packages.

Usage:
    ./print_env.py
"""

import sys

import netmiko
import pyaml


def main():
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)

    rows = [
        ("Python version", sys.version.split()[0]),
        ("Executable path", sys.executable),
        ("Venv executable path", sys.executable if in_venv else "n/a (not in a venv)"),
        ("Netmiko package path", netmiko.__file__),
        ("Pyaml package path", pyaml.__file__),
    ]

    width = max(len(label) for label, _ in rows)

    print("Environment Info")
    print("=" * (width + 2))
    for label, value in rows:
        print(f"{label.ljust(width)} : {value}")


if __name__ == "__main__":
    main()
