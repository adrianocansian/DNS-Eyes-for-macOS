#!/usr/bin/env python3

"""
DNS Changer Eye - macOS Sequoia Edition
Secure plist Configuration Script

This script safely modifies the LaunchAgent plist file by using the plistlib
module, which properly handles XML escaping and ensures the plist structure
remains valid even with special characters in usernames or paths.

Usage:
    python3 configure_plist.py <plist_file> <home_dir> <username>

Arguments:
    plist_file: Path to the plist file to configure
    home_dir:   The home directory path (typically $HOME)
    username:   The username (typically $USER)
"""

import sys
import plistlib
from pathlib import Path


def validate_arguments(args):
    """
    Validate command-line arguments.

    Args:
        args: List of command-line arguments

    Returns:
        Tuple of (plist_file, home_dir, username)

    Raises:
        SystemExit: If arguments are invalid
    """
    if len(args) != 4:
        print("Usage: python3 configure_plist.py <plist_file> <home_dir> <username>")
        sys.exit(1)

    plist_file = Path(args[1])
    home_dir = args[2]
    username = args[3]

    # Validate plist file exists
    if not plist_file.exists():
        print(f"Error: plist file not found: {plist_file}")
        sys.exit(1)

    # Validate home directory is not empty
    if not home_dir or not home_dir.startswith("/"):
        print(f"Error: Invalid home directory: {home_dir}")
        sys.exit(1)

    # Validate username is not empty
    if not username:
        print("Error: Username cannot be empty")
        sys.exit(1)

    return plist_file, home_dir, username


def configure_plist(plist_file, home_dir, username):
    """
    Safely configure the plist file with home directory and username.

    This function uses plistlib to read and modify the plist, ensuring that
    all values are properly escaped and the XML structure remains valid.

    Args:
        plist_file: Path to the plist file
        home_dir:   The home directory path
        username:   The username

    Raises:
        Exception: If plist reading/writing fails
    """
    try:
        # Read the plist file
        with open(plist_file, "rb") as f:
            plist_data = plistlib.load(f)

        # Modify the plist with the new values
        # All values are automatically XML-escaped by plistlib
        plist_data["StandardOutPath"] = f"{home_dir}/.dns_changer/daemon.log"
        plist_data["StandardErrorPath"] = f"{home_dir}/.dns_changer/daemon_error.log"
        plist_data["UserName"] = username

        # Write the modified plist back to the file
        with open(plist_file, "wb") as f:
            plistlib.dump(plist_data, f)

        print(f"✓ Successfully configured plist: {plist_file}")
        print(f"  - StandardOutPath: {plist_data['StandardOutPath']}")
        print(f"  - StandardErrorPath: {plist_data['StandardErrorPath']}")
        print(f"  - UserName: {plist_data['UserName']}")

    except plistlib.InvalidFileException as e:
        print(f"Error: Invalid plist file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to configure plist: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    plist_file, home_dir, username = validate_arguments(sys.argv)
    configure_plist(plist_file, home_dir, username)


if __name__ == "__main__":
    main()
