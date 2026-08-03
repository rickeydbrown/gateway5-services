#!/usr/bin/env python3
"""
Print Env Service
Prints the Python version, interpreter executable path, (if running
inside a virtual environment) the venv's executable path, and the
location of the installed netmiko package.

Usage:
    ./print_env.py
"""

import sys

import netmiko


def main():
    print(f"Python version: {sys.version}")
    print(f"Executable path: {sys.executable}")

    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        print(f"Venv executable path: {sys.executable}")
    else:
        print("Not running inside a virtual environment")

    print(f"Netmiko package path: {netmiko.__file__}")


if __name__ == "__main__":
    main()
