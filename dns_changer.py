#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS Changer Eye - macOS Sequoia Edition
Automatic DNS server rotation for privacy and security
Developed for macOS Sequoia (15.0+)

Author: macOS Adaptation
Based on: DNS Changer Eye (BullsEye0)
Date: 2026
"""

import os
import sys
import secrets
import time
import subprocess
import logging
import signal
import atexit
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_DIR = Path("/var/log/dns_changer")
LOG_FILE = LOG_DIR / "dns_changer.log"
PID_LOCK_FILE = Path("/var/run/dns_changer.pid")

# Create log directory if it doesn't exist
if not LOG_DIR.exists():
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # Fallback to user home directory if /var/log is not writable
        LOG_DIR = Path.home() / ".dns_changer"
        LOG_DIR.mkdir(exist_ok=True)
        PID_LOCK_FILE = LOG_DIR / "dns_changer.pid"
        LOG_FILE = LOG_DIR / "dns_changer.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DNS SERVERS
# ============================================================================

DNS_SERVERS = [
    # Cloudflare
    ("1.1.1.1", "1.0.0.1"),
    # Quad9
    ("9.9.9.9", "149.112.112.112"),
    # OpenDNS
    ("208.67.222.222", "208.67.220.220"),
    # Verisign
    ("64.6.64.6", "64.6.65.6"),
    # UncensoredDNS
    ("91.239.100.100", "89.233.43.71"),
    # CleanBrowsing
    ("185.228.168.9", "185.228.169.9"),
    # Yandex
    ("77.88.8.8", "77.88.8.1"),
    # AdGuard
    ("176.103.130.130", "176.103.130.131"),
    # DNS Advantage
    ("156.154.70.1", "156.154.71.1"),
    # Norton
    ("199.85.126.10", "199.85.127.10"),
    # GreenTeam
    ("81.218.119.11", "209.88.198.133"),
    # SafeDNS
    ("195.46.39.39", "195.46.39.40"),
    # SmartViper
    ("208.76.50.50", "208.76.51.51"),
    # Dyn
    ("216.146.35.35", "216.146.36.36"),
    # FreeDNS
    ("37.235.1.174", "37.235.1.177"),
    # Alternate DNS
    ("198.101.242.72", "23.253.163.53"),
    # puntCAT
    ("109.69.8.51", "8.8.8.8"),
    # Quad101
    ("101.101.101.101", "101.102.103.104"),
    # FDN
    ("80.67.169.12", "80.67.169.40"),
    # OpenNIC
    ("185.121.177.177", "185.121.177.53"),
    # AS250.net
    ("195.10.46.179", "212.82.225.7"),
    # Orange
    ("194.168.4.100", "194.168.8.100"),
    # SingNet
    ("203.122.222.6", "203.122.223.6"),
    # Level3
    ("209.244.0.3", "209.244.0.4"),
    # Google
    ("8.8.8.8", "8.8.4.4"),
]

# ============================================================================
# PID LOCK MANAGEMENT
# ============================================================================

def is_process_running(pid: int) -> bool:
    """
    Checks if a process with the given PID is still running.

    Args:
        pid: Process ID to check

    Returns:
        True if process is running, False otherwise
    """
    try:
        os.kill(pid, 0)  # Signal 0 doesn't kill, just checks if process exists
        return True
    except (ProcessLookupError, OSError):
        return False

def acquire_lock() -> bool:
    """
    Attempts to acquire the PID lock file.
    If another instance is running, returns False.
    If an orphaned lock exists, removes it and acquires the lock.

    Returns:
        True if lock was acquired, False if another instance is running
    """
    if PID_LOCK_FILE.exists():
        try:
            with open(PID_LOCK_FILE, 'r') as f:
                old_pid = int(f.read().strip())

            if is_process_running(old_pid):
                logger.error(f"Another instance is already running (PID: {old_pid})")
                return False
            else:
                logger.warning(f"Removing orphaned lock file (PID: {old_pid} not running)")
                PID_LOCK_FILE.unlink()
        except (ValueError, IOError) as e:
            logger.warning(f"Error reading lock file: {e}. Removing it.")
            try:
                PID_LOCK_FILE.unlink()
            except OSError:
                pass

    # Write current PID to lock file
    try:
        with open(PID_LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"Lock acquired (PID: {os.getpid()})")
        return True
    except IOError as e:
        logger.error(f"Failed to create lock file: {e}")
        return False

def release_lock():
    """
    Releases the PID lock file.
    This function is called automatically on exit.
    """
    try:
        if PID_LOCK_FILE.exists():
            # Only remove if it's our lock
            with open(PID_LOCK_FILE, 'r') as f:
                lock_pid = int(f.read().strip())
            if lock_pid == os.getpid():
                PID_LOCK_FILE.unlink()
                logger.info("Lock released")
    except (ValueError, IOError, OSError) as e:
        logger.warning(f"Error releasing lock: {e}")

# ============================================================================
# MAIN CLASS
# ============================================================================

class DNSChanger:
    """DNS rotation manager for macOS"""

    def __init__(self, interval: int = 300, interface: Optional[str] = None):
        """
        Initializes the DNS Changer

        Args:
            interval: Interval in seconds for DNS rotation (default: 300 = 5 min)
            interface: Specific network interface (Wi-Fi, Ethernet, etc.)
        """
        self.interval = interval
        self.interface = interface or self._detect_interface()
        self.running = False
        self.current_dns = None

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info(f"DNS Changer initialized for interface: {self.interface}")

    def _signal_handler(self, signum, frame):
        """Handler for shutdown signals"""
        logger.info("Received shutdown signal, shutting down...")
        self.running = False
        release_lock()
        sys.exit(0)

    def _detect_interface(self) -> str:
        """
        Automatically detects the active network interface

        Returns:
            Interface name (e.g., 'Wi-Fi', 'Ethernet')
        """
        try:
            result = subprocess.run(
                ["/sbin/route", "get", "default"],
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.split('\n'):
                if 'interface:' in line:
                    interface = line.split(':')[1].strip()
                    logger.info(f"Detected interface: {interface}")
                    return interface
        except Exception as e:
            logger.warning(f"Error detecting interface: {e}")

        logger.warning("Using default interface: Wi-Fi")
        return "Wi-Fi"

    def _validate_dns(self, dns1: str, dns2: str) -> bool:
        """
        Validates DNS IP addresses

        Args:
            dns1: First DNS server
            dns2: Second DNS server

        Returns:
            True if valid, False otherwise
        """
        import ipaddress

        try:
            ipaddress.ip_address(dns1)
            ipaddress.ip_address(dns2)
            return True
        except ValueError:
            logger.error(f"Invalid DNS: {dns1} or {dns2}")
            return False

    def _run_command(self, command: List[str]) -> Tuple[bool, str]:
        """
        Executes a command with root privileges

        Args:
            command: List with command and arguments

        Returns:
            Tuple (success, message)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def get_current_dns(self) -> Optional[Tuple[str, str]]:
        """
        Gets the current DNS configuration

        Returns:
            Tuple (dns1, dns2) or None if it fails to get it
        """
        success, output = self._run_command(
            ["networksetup", "-getdnsservers", self.interface]
        )

        if success and output:
            dns_list = output.strip().split('\n')
            if len(dns_list) >= 2:
                return (dns_list[0], dns_list[1])
            elif len(dns_list) == 1:
                return (dns_list[0], dns_list[0])

        return None

    def set_dns(self, dns1: str, dns2: str) -> bool:
        """
        Sets new DNS servers

        Args:
            dns1: First DNS server
            dns2: Second DNS server

        Returns:
            True if successful, False otherwise
        """
        if not self._validate_dns(dns1, dns2):
            return False

        success, output = self._run_command(
            ["sudo", "networksetup", "-setdnsservers", self.interface, dns1, dns2]
        )

        if success:
            self.current_dns = (dns1, dns2)
            logger.info(f"DNS changed to: {dns1}, {dns2}")
            return True
        else:
            logger.error(f"Error changing DNS: {output}")
            return False

    def rotate_dns(self) -> bool:
        """
        Rotates to a new random DNS server

        Returns:
            True if successful, False otherwise
        """
        dns1, dns2 = secrets.choice(DNS_SERVERS)

        # Avoid repeating the same DNS
        if self.current_dns == (dns1, dns2):
            return self.rotate_dns()

        return self.set_dns(dns1, dns2)

    def run(self):
        """Starts the DNS rotation loop"""
        self.running = True
        logger.info(f"Starting DNS rotation every {self.interval} seconds")

        try:
            # Initial rotation
            self.rotate_dns()

            # Main loop
            while self.running:
                time.sleep(self.interval)
                self.rotate_dns()

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.running = False
            logger.info("DNS Changer stopped")

    def run_once(self) -> bool:
        """Rotates DNS once"""
        logger.info("Running single DNS rotation")
        return self.rotate_dns()

    def reset_dns(self) -> bool:
        """
        Resets DNS to automatic (DHCP) configuration

        Returns:
            True if successful, False otherwise
        """
        success, output = self._run_command(
            ["sudo", "networksetup", "-setdnsservers", self.interface, "Empty"]
        )

        if success:
            logger.info("DNS reset to automatic DHCP")
            return True
        else:
            logger.error(f"Error resetting DNS: {output}")
            return False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_banner():
    """Displays the application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║          DNS Changer Eye - macOS Sequoia Edition          ║
    ║                                                           ║
    ║        Automatic Rotation of DNS Servers                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="DNS Changer Eye for macOS - Automatic DNS rotation"
    )
    parser.add_argument(
        "-i", "--interface",
        help="Network interface (e.g., Wi-Fi, Ethernet)",
        default=None
    )
    parser.add_argument(
        "-t", "--interval",
        type=int,
        default=300,
        help="Rotation interval in seconds (default: 300)"
    )
    parser.add_argument(
        "-o", "--once",
        action="store_true",
        help="Rotate DNS once"
    )
    parser.add_argument(
        "-r", "--reset",
        action="store_true",
        help="Reset DNS to automatic DHCP"
    )
    parser.add_argument(
        "-g", "--get",
        action="store_true",
        help="Display current DNS configuration"
    )
    parser.add_argument(
        "-s", "--set",
        nargs=2,
        metavar=("DNS1", "DNS2"),
        help="Set specific DNS servers (e.g., -s 1.1.1.1 1.0.0.1)"
    )

    args = parser.parse_args()

    print_banner()

    # Acquire lock to prevent multiple instances
    if not acquire_lock():
        print("Error: Another instance of DNS Changer is already running.")
        print("Please wait for it to finish or stop it manually.")
        return 1

    # Register cleanup function to be called on exit
    atexit.register(release_lock)

    changer = DNSChanger(interval=args.interval, interface=args.interface)

    if args.get:
        current = changer.get_current_dns()
        if current:
            print(f"Current DNS: {current[0]}, {current[1]}")
        else:
            print("Could not get DNS configuration")
        return 0

    if args.reset:
        if changer.reset_dns():
            print("DNS reset successfully")
            return 0
        else:
            print("Error resetting DNS")
            return 1

    if args.set:
        if changer.set_dns(args.set[0], args.set[1]):
            print(f"DNS set to: {args.set[0]}, {args.set[1]}")
            return 0
        else:
            print("Error setting DNS")
            return 1

    if args.once:
        if changer.run_once():
            print("DNS rotated successfully")
            return 0
        else:
            print("Error rotating DNS")
            return 1

    # Continuous mode (default)
    print(f"Starting continuous rotation (interval: {args.interval}s)")
    print("Press Ctrl+C to stop")
    changer.run()

    return 0

if __name__ == "__main__":
    sys.exit(main())
