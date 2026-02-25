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
import socket
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Set

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_DIR = Path("/var/log/dns_changer")
LOG_FILE = LOG_DIR / "dns_changer.log"
PID_LOCK_FILE = Path("/var/run/dns_changer.pid")

# ============================================================================
# DNS VALIDATION CONFIGURATION
# ============================================================================

DNS_HEALTH_CHECK_TIMEOUT = 2
DNS_HEALTH_CHECK_DOMAIN = "google.com"
HEALTHY_SERVERS_CACHE_TTL = 1800
MIN_HEALTHY_SERVERS = 3

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
# DNS HEALTH CHECK FUNCTIONS
# ============================================================================

class DNSHealthChecker:
    """Manages DNS server health checks and caching"""

    def __init__(self):
        """Initialize the health checker with empty cache"""
        self.healthy_servers: Set[Tuple[str, str]] = set()
        self.last_cache_update = None
        self.lock = False

    def is_dns_responsive(self, dns_ip: str, timeout: int = DNS_HEALTH_CHECK_TIMEOUT) -> bool:
        """
        Checks if a DNS server is responsive by performing a DNS query.

        Args:
            dns_ip: IP address of the DNS server to check
            timeout: Timeout in seconds for the DNS query

        Returns:
            True if DNS server is responsive, False otherwise
        """
        try:
            # Create a socket for DNS query
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)

            # Construct a simple DNS query for google.com (A record)
            # This is a minimal DNS query packet
            dns_query = b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
            dns_query += b'\x06google\x03com\x00\x00\x01\x00\x01'

            # Send query to DNS server
            sock.sendto(dns_query, (dns_ip, 53))

            # Try to receive response
            response, _ = sock.recvfrom(512)
            sock.close()

            # If we got a response, the server is responsive
            return len(response) > 0

        except (socket.timeout, socket.error, OSError) as e:
            logger.debug(f"DNS health check failed for {dns_ip}: {e}")
            return False

    def validate_dns_servers(self, dns_servers: List[Tuple[str, str]]) -> Set[Tuple[str, str]]:
        """
        Validates a list of DNS servers and returns only the healthy ones.

        Args:
            dns_servers: List of DNS server pairs to validate

        Returns:
            Set of healthy DNS server pairs
        """
        healthy = set()

        logger.info(f"Starting health check for {len(dns_servers)} DNS servers...")

        for dns1, dns2 in dns_servers:
            # Check if at least one server in the pair is responsive
            dns1_ok = self.is_dns_responsive(dns1)
            dns2_ok = self.is_dns_responsive(dns2)

            if dns1_ok or dns2_ok:
                healthy.add((dns1, dns2))
                status = "✓ HEALTHY" if (dns1_ok and dns2_ok) else "⚠ PARTIAL"
                logger.debug(f"{status}: {dns1}, {dns2}")
            else:
                logger.debug(f"✗ FAILED: {dns1}, {dns2}")

        logger.info(f"Health check complete: {len(healthy)}/{len(dns_servers)} servers are healthy")
        return healthy

    def get_healthy_servers(self, dns_servers: List[Tuple[str, str]], force_refresh: bool = False) -> Set[Tuple[str, str]]:
        """
        Gets the list of healthy DNS servers, using cache when available.

        Args:
            dns_servers: Full list of DNS servers
            force_refresh: Force re-validation even if cache is fresh

        Returns:
            Set of healthy DNS server pairs
        """
        now = datetime.now()

        # Check if cache needs update
        if force_refresh or self.last_cache_update is None or (now - self.last_cache_update).total_seconds() > HEALTHY_SERVERS_CACHE_TTL:
            logger.info("Updating DNS health check cache...")
            self.healthy_servers = self.validate_dns_servers(dns_servers)
            self.last_cache_update = now

        return self.healthy_servers

    def get_random_healthy_server(self, dns_servers: List[Tuple[str, str]]) -> Optional[Tuple[str, str]]:
        """
        Gets a random healthy DNS server, with fallback logic.

        Args:
            dns_servers: Full list of DNS servers

        Returns:
            A healthy DNS server pair, or None if no healthy servers available
        """
        healthy = self.get_healthy_servers(dns_servers)

        if not healthy:
            logger.warning("No healthy DNS servers in cache, forcing re-validation...")
            healthy = self.get_healthy_servers(dns_servers, force_refresh=True)

        if not healthy:
            logger.error("No healthy DNS servers found! Using fallback (Cloudflare)...")
            return ("1.1.1.1", "1.0.0.1")

        return secrets.choice(list(healthy))

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
        self.health_checker = DNSHealthChecker()

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

    def _get_network_service_order(self) -> List[str]:
        """Gets network service order from macOS preferences."""
        try:
            result = subprocess.run(
                ["/usr/sbin/networksetup", "-listallnetworkservices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            services = [line.strip() for line in result.stdout.strip().split('\n') 
                       if line.strip() and not line.startswith('*')]
            return services
        except Exception as e:
            logger.debug(f"Error getting network service order: {e}")
            return []

    def _is_interface_active(self, interface: str) -> bool:
        """Checks if a network interface is active."""
        try:
            result = subprocess.run(
                ["/usr/sbin/networksetup", "-getnetworkserviceenabled", interface],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "Enabled" in result.stdout
        except Exception as e:
            logger.debug(f"Error checking interface {interface}: {e}")
            return False

    def _detect_interface_by_route(self) -> Optional[str]:
        """Detects interface using default route (fallback method)."""
        try:
            result = subprocess.run(
                ["/sbin/route", "get", "default"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'interface:' in line:
                    return line.split(':')[1].strip()
        except Exception as e:
            logger.debug(f"Error detecting interface via route: {e}")
        return None

    def _detect_interface(self) -> str:
        """Detects active network interface using multiple strategies."""
        logger.info("Starting network interface detection...")
        
        services = self._get_network_service_order()
        active_services = [s for s in services if self._is_interface_active(s)]
        
        if active_services:
            if len(active_services) > 1:
                logger.warning(
                    f"Multiple active interfaces: {', '.join(active_services)}. "
                    f"Using '{active_services[0]}'. To use different: --interface <name>"
                )
            else:
                logger.info(f"Detected interface: {active_services[0]}")
            return active_services[0]
        
        route_interface = self._detect_interface_by_route()
        if route_interface:
            logger.info(f"Detected interface via route: {route_interface}")
            return route_interface
        
        logger.warning(
            "Could not auto-detect interface. Defaulting to Wi-Fi. "
            "Use --interface <name> if incorrect."
        )
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

    def _is_vpn_active(self) -> bool:
        """Checks if a VPN interface is currently active."""
        try:
            result = subprocess.run(
                ["ifconfig"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # VPN interfaces typically start with utun, ppp, tun, or tap
            vpn_patterns = ['utun', 'ppp', 'tun', 'tap']
            for line in result.stdout.split('\n'):
                for pattern in vpn_patterns:
                    if line.startswith(pattern):
                        logger.debug(f"VPN interface detected: {line.split(':')[0]}")
                        return True
            return False
        except Exception as e:
            logger.debug(f"Error checking VPN status: {e}")
            return False

    def _dns_was_overwritten(self) -> bool:
        """Checks if DNS settings were overwritten by another process."""
        if self.current_dns is None:
            return False
        
        current = self.get_current_dns()
        if current is None:
            return True
        
        # Check if current DNS differs from what we set
        if current != self.current_dns:
            logger.warning(
                f"DNS overwrite detected! Expected: {self.current_dns}, "
                f"Current: {current}"
            )
            return True
        
        return False

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
        Rotates to a new random healthy DNS server

        Returns:
            True if successful, False otherwise
        """
        dns_pair = self.health_checker.get_random_healthy_server(DNS_SERVERS)
        if dns_pair is None:
            logger.error("No DNS servers available")
            return False
        dns1, dns2 = dns_pair

        # Avoid repeating the same DNS
        if self.current_dns == (dns1, dns2):
            return self.rotate_dns()

        return self.set_dns(dns1, dns2)

    def run(self):
        """Starts the DNS rotation loop with VPN detection"""
        self.running = True
        logger.info(f"Starting DNS rotation every {self.interval} seconds")
        paused = False

        try:
            # Initial rotation
            self.rotate_dns()

            # Main loop
            while self.running:
                time.sleep(self.interval)
                
                # Check if DNS was overwritten
                if self._dns_was_overwritten():
                    if self._is_vpn_active():
                        if not paused:
                            logger.warning(
                                "VPN detected with DNS overwrite. "
                                "Pausing rotation to avoid conflicts."
                            )
                            paused = True
                    else:
                        if paused:
                            logger.info(
                                "DNS overwrite detected. "
                                "Pausing rotation."
                            )
                            paused = True
                else:
                    if paused:
                        logger.info("Resuming DNS rotation.")
                        paused = False
                
                # Only rotate if not paused
                if not paused:
                    self.rotate_dns()
                else:
                    logger.debug(
                        f"Rotation paused. Current DNS: {self.get_current_dns()}"
                    )

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
