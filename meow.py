#!/usr/bin/env python3
"""
meow.py — Directory Tree Visualizer 🐱
------------------------------------
Recursively prints the directory structure of a given root folder
in a tree-like format, excluding 'node_modules' directories.

Usage:
    python meow.py [path_to_directory]
If no path is provided, it defaults to the current directory.
"""

import os
import sys

def print_tree(root_dir, prefix=""):
    """Recursively prints the directory structure."""
    # Get all entries in the directory
    try:
        entries = sorted(os.listdir(root_dir))
    except PermissionError:
        print(prefix + "⚠️ [Permission Denied]")
        return

    # Exclude node_modules directories
    entries = [e for e in entries if e != "node_modules"]

    entries_count = len(entries)

    for i, entry in enumerate(entries):
        path = os.path.join(root_dir, entry)
        connector = "├── " if i < entries_count - 1 else "└── "
        print(prefix + connector + entry)

        # If the entry is a directory, recurse into it (excluding node_modules)
        if os.path.isdir(path):
            new_prefix = prefix + ("│   " if i < entries_count - 1 else "    ")
            print_tree(path, new_prefix)

def main():
    # Use provided path or default to current directory
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()

    if not os.path.exists(root_dir):
        print(f"Error: Path '{root_dir}' does not exist.")
        sys.exit(1)

    print(f"📁 Directory structure for: {os.path.abspath(root_dir)}\n")
    print_tree(root_dir)

if __name__ == "__main__":
    main()
