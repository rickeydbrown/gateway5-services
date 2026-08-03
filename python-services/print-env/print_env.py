#!/usr/bin/env python3
"""
Print Env Service
Prints the Python version, interpreter executable path, and (if running
inside a virtual environment) the venv's executable path.

Usage:
    ./print_env.py
"""

import sys


def main():
    print(f"Python version: {sys.version}")
    print(f"Executable path: {sys.executable}")

    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        print(f"Venv executable path: {sys.executable}")
    else:
        print("Not running inside a virtual environment")


if __name__ == "__main__":
    main()
