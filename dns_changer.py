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
import ipaddress  # FIX #9: moved from inside method to top-level import
import secrets
import time
import subprocess
import logging
import logging.handlers
import signal
import atexit
import socket
import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Set, Dict, Any

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_DIR = Path("/var/log/dns_changer")
LOG_FILE = LOG_DIR / "dns_changer.log"
PID_LOCK_FILE = Path("/var/run/dns_changer.pid")

# FIX #3: Centralize fallback so both LOG_DIR and PID_LOCK_FILE are updated together.
# This prevents the lock file remaining at /var/run/ after the log dir falls back to ~/
_fallback_dir = Path.home() / ".dns_changer"

def _setup_log_dir() -> Path:
    """
    Attempts to create /var/log/dns_changer.
    Falls back to ~/.dns_changer if /var/log is not writable.
    Returns the directory that was successfully created/confirmed.
    """
    global LOG_FILE, PID_LOCK_FILE

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True, mode=0o750)
        os.chmod(LOG_DIR, 0o750)
        return LOG_DIR
    except PermissionError:
        _fallback_dir.mkdir(exist_ok=True, mode=0o700)
        os.chmod(_fallback_dir, 0o700)
        # FIX #3: Update BOTH paths atomically when falling back
        LOG_FILE = _fallback_dir / "dns_changer.log"
        PID_LOCK_FILE = _fallback_dir / "dns_changer.pid"
        return _fallback_dir

_active_log_dir = _setup_log_dir()

# Configure logger with RotatingFileHandler for secure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

try:
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    os.chmod(LOG_FILE, 0o640)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except PermissionError:
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    os.chmod(LOG_FILE, 0o600)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ============================================================================
# DNS VALIDATION CONFIGURATION
# ============================================================================

DNS_HEALTH_CHECK_TIMEOUT = 2
DNS_HEALTH_CHECK_DOMAIN = "google.com"
HEALTHY_SERVERS_CACHE_TTL = 1800
MIN_HEALTHY_SERVERS = 3
MIN_ROTATION_INTERVAL = 180   # 3 minutes minimum to avoid network instability
MAX_ROTATION_INTERVAL = 86400 # 24 hours maximum

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
# CONFIGURATION LOADING
# ============================================================================

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json if it exists.
    Falls back to defaults if not found.
    """
    config_paths = [
        Path("/etc/dns_changer/config.json"),
        Path("/usr/local/etc/dns_changer/config.json"),
        Path.home() / ".dns_changer" / "config.json",
        Path(__file__).parent / "config.json",
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded configuration from {config_path}")
                    return config.get("dns_changer", {})
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")

    logger.info("No configuration file found. Using defaults.")
    return {}

def get_config_value(config: Dict[str, Any], path: str, default: Any) -> Any:
    """
    Get a value from config dictionary using dot notation.
    Example: get_config_value(config, "general.interval", 300)
    """
    keys = path.split(".")
    value = config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    return value if value is not None else default

# Load configuration at startup
CONFIG = load_config()

# ============================================================================
# DNS HEALTH CHECK FUNCTIONS
# ============================================================================

class DNSHealthChecker:
    """Manages DNS server health checks and caching."""

    # FIX #4: Proper DNS query packet constants
    # Transaction ID: 0xABCD (arbitrary, just needs to be 2 bytes)
    # Flags: 0x0100 (standard query, recursion desired)
    # Questions: 1, Answer/Authority/Additional RRs: 0
    _DNS_QUERY_HEADER = b'\xab\xcd\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
    # Encoded "google.com" + QTYPE A (1) + QCLASS IN (1)
    _DNS_QUERY_BODY = b'\x06google\x03com\x00\x00\x01\x00\x01'
    _DNS_QUERY = _DNS_QUERY_HEADER + _DNS_QUERY_BODY
    # Minimum valid DNS response size (header only = 12 bytes)
    _MIN_RESPONSE_SIZE = 12

    def __init__(self):
        self.healthy_servers: Set[Tuple[str, str]] = set()
        self.last_cache_update = None

    def is_dns_responsive(self, dns_ip: str, timeout: int = DNS_HEALTH_CHECK_TIMEOUT) -> bool:
        """
        Checks if a DNS server is responsive by sending a real DNS query
        and validating that the response is a well-formed DNS reply.

        Args:
            dns_ip: IP address of the DNS server to check
            timeout: Timeout in seconds

        Returns:
            True if DNS server returns a valid response, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.sendto(self._DNS_QUERY, (dns_ip, 53))
            response, _ = sock.recvfrom(512)
            sock.close()

            # FIX #4: Validate response properly:
            # - Must be at least 12 bytes (DNS header size)
            # - First 2 bytes must match our Transaction ID (0xABCD)
            # - Bit QR (bit 15 of flags word) must be 1 (it's a response)
            if len(response) < self._MIN_RESPONSE_SIZE:
                return False
            if response[0:2] != b'\xab\xcd':
                return False
            # QR bit is the highest bit of byte index 2
            if not (response[2] & 0x80):
                return False
            return True

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
            dns1_ok = self.is_dns_responsive(dns1)
            dns2_ok = self.is_dns_responsive(dns2)

            if dns1_ok or dns2_ok:
                healthy.add((dns1, dns2))
                status = "✓ HEALTHY" if (dns1_ok and dns2_ok) else "⚠ PARTIAL"
                logger.debug(f"{status}: {dns1}, {dns2}")
            else:
                logger.debug(f"✗ FAILED: {dns1}, {dns2}")

        logger.info(f"Health check complete: {len(healthy)}/{len(dns_servers)} servers healthy")
        return healthy

    def get_healthy_servers(
        self,
        dns_servers: List[Tuple[str, str]],
        force_refresh: bool = False
    ) -> Set[Tuple[str, str]]:
        """
        Gets the list of healthy DNS servers, using cache when available.
        """
        now = datetime.now()
        cache_expired = (
            self.last_cache_update is None
            or (now - self.last_cache_update).total_seconds() > HEALTHY_SERVERS_CACHE_TTL
        )

        if force_refresh or cache_expired:
            logger.info("Updating DNS health check cache...")
            self.healthy_servers = self.validate_dns_servers(dns_servers)
            self.last_cache_update = now

        return self.healthy_servers

    def get_random_healthy_server(
        self,
        dns_servers: List[Tuple[str, str]],
        exclude: Optional[Tuple[str, str]] = None,
        max_retries: int = 5
    ) -> Optional[Tuple[str, str]]:
        """
        Gets a random healthy DNS server, excluding the current one if possible.

        FIX #1: Replaced unlimited recursion with an iterative loop bounded
        by max_retries to prevent RecursionError when the healthy pool is small.

        Args:
            dns_servers: Full list of DNS servers
            exclude: Server pair to avoid (current DNS)
            max_retries: Maximum attempts to find a different server

        Returns:
            A healthy DNS server pair different from `exclude`, or the best
            available fallback. Returns None only if no servers exist at all.
        """
        healthy = self.get_healthy_servers(dns_servers)

        if not healthy:
            logger.warning("No healthy DNS servers in cache, forcing re-validation...")
            healthy = self.get_healthy_servers(dns_servers, force_refresh=True)

        if not healthy:
            logger.error("No healthy DNS servers found! Using Cloudflare as fallback.")
            fallback = ("1.1.1.1", "1.0.0.1")
            return None if exclude == fallback else fallback

        # If only one server available (same as current), accept it rather than looping
        candidates = list(healthy - {exclude}) if exclude else list(healthy)
        if not candidates:
            logger.warning(
                "Only the current DNS server is healthy. "
                "Cannot rotate to a different server this cycle."
            )
            return None  # Signal to caller: skip this rotation cycle

        # Pick randomly from candidates (already excludes current)
        for _ in range(max_retries):
            chosen = secrets.choice(candidates)
            if chosen != exclude:
                return chosen

        # Fallback: return any candidate
        return candidates[0]

# ============================================================================
# PID LOCK MANAGEMENT
# ============================================================================

def is_process_running(pid: int) -> bool:
    """
    Checks if a process with the given PID is still running.
    """
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OSError):
        return False

def acquire_lock() -> bool:
    """
    Attempts to acquire the PID lock file.
    Returns False if another instance is already running.
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

    try:
        with open(PID_LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"Lock acquired (PID: {os.getpid()}) at {PID_LOCK_FILE}")
        return True
    except IOError as e:
        logger.error(f"Failed to create lock file: {e}")
        return False

def release_lock():
    """
    Releases the PID lock file. Called automatically on exit.
    """
    try:
        if PID_LOCK_FILE.exists():
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
    """DNS rotation manager for macOS."""

    def __init__(self, interval: int = 300, interface: Optional[str] = None):
        """
        Initializes the DNS Changer.

        Args:
            interval: Interval in seconds for DNS rotation (default: 300)
            interface: Specific network interface name (e.g. 'Wi-Fi', 'Ethernet')
        """
        # Apply interval from config file if not overridden by CLI
        config_interval = get_config_value(CONFIG, "general.interval", None)
        effective_interval = interval if interval != 300 else (config_interval or interval)

        if effective_interval < MIN_ROTATION_INTERVAL:
            logger.warning(
                f"Interval {effective_interval}s is too short. "
                f"Using minimum {MIN_ROTATION_INTERVAL}s."
            )
            self.interval = MIN_ROTATION_INTERVAL
        elif effective_interval > MAX_ROTATION_INTERVAL:
            logger.warning(
                f"Interval {effective_interval}s exceeds maximum. "
                f"Using maximum {MAX_ROTATION_INTERVAL}s."
            )
            self.interval = MAX_ROTATION_INTERVAL
        else:
            self.interval = effective_interval
            logger.info(f"Rotation interval set to {self.interval}s")

        self.interface = interface or self._detect_interface()
        self.running = False
        self.current_dns: Optional[Tuple[str, str]] = None
        self.health_checker = DNSHealthChecker()

        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info(f"DNS Changer initialized for interface: {self.interface}")

    def _signal_handler(self, signum, frame):
        """Handler for shutdown signals."""
        logger.info("Received shutdown signal, shutting down gracefully...")
        self.running = False
        release_lock()
        sys.exit(0)

    def _get_network_service_order(self) -> List[str]:
        """Gets network service order from macOS preferences."""
        try:
            result = subprocess.run(
                ["/usr/sbin/networksetup", "-listallnetworkservices"],
                capture_output=True, text=True, timeout=5
            )
            return [
                line.strip()
                for line in result.stdout.strip().split('\n')
                if line.strip() and not line.startswith('*')
            ]
        except Exception as e:
            logger.debug(f"Error getting network service order: {e}")
            return []

    def _is_interface_active(self, interface: str) -> bool:
        """Checks if a network interface is enabled."""
        try:
            result = subprocess.run(
                ["/usr/sbin/networksetup", "-getnetworkserviceenabled", interface],
                capture_output=True, text=True, timeout=5
            )
            return "Enabled" in result.stdout
        except Exception as e:
            logger.debug(f"Error checking interface {interface}: {e}")
            return False

    def _detect_interface_by_route(self) -> Optional[str]:
        """Detects interface via default route (fallback method)."""
        try:
            result = subprocess.run(
                ["/sbin/route", "get", "default"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.split('\n'):
                if 'interface:' in line:
                    return line.split(':')[1].strip()
        except Exception as e:
            logger.debug(f"Error detecting interface via route: {e}")
        return None

    def _detect_interface(self) -> str:
        """
        Detects active network interface using multiple strategies:
        1. List enabled network services (preferred)
        2. Default route interface (fallback)
        3. 'Wi-Fi' hardcoded (last resort)
        """
        logger.info("Starting network interface detection...")

        services = self._get_network_service_order()
        active_services = [s for s in services if self._is_interface_active(s)]

        if active_services:
            if len(active_services) > 1:
                logger.warning(
                    f"Multiple active interfaces detected: {', '.join(active_services)}. "
                    f"Using '{active_services[0]}'. Override with --interface <name> if needed."
                )
            else:
                logger.info(f"Detected active interface: {active_services[0]}")
            return active_services[0]

        route_iface = self._detect_interface_by_route()
        if route_iface:
            logger.info(f"Detected interface via default route: {route_iface}")
            return route_iface

        logger.warning(
            "Could not auto-detect network interface. Defaulting to 'Wi-Fi'. "
            "Use --interface <name> to override."
        )
        return "Wi-Fi"

    def _validate_dns(self, dns1: str, dns2: str) -> bool:
        """
        Validates DNS IP addresses using the ipaddress module.

        FIX #9: ipaddress is now imported at the top of the file.
        """
        try:
            ipaddress.ip_address(dns1)
            ipaddress.ip_address(dns2)
            return True
        except ValueError:
            logger.error(f"Invalid DNS address: '{dns1}' or '{dns2}'")
            return False

    def _run_command(self, command: List[str]) -> Tuple[bool, str]:
        """
        Executes a system command and returns (success, output).
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
        """
        Checks if a VPN interface is currently active.

        FIX #6: Added 'ipsec' and 'wireguard' to the pattern list, and
        specifically checks for 'flags=...UP' to confirm the interface
        is actually UP, reducing false positives from inactive utun interfaces
        created by iCloud, Bluetooth, or developer tools.
        """
        try:
            result = subprocess.run(
                ["ifconfig"],
                capture_output=True, text=True, timeout=5
            )
            # VPN interfaces typically start with utun, ppp, tun, tap, ipsec, wg
            vpn_prefixes = ('utun', 'ppp', 'tun', 'tap', 'ipsec', 'wg')
            lines = result.stdout.split('\n')
            current_iface = None
            for line in lines:
                # Interface header lines start with a non-space character
                if line and not line[0].isspace():
                    current_iface = line.split(':')[0]
                # Check if this interface header is a VPN and is UP
                if (current_iface and
                        any(current_iface.startswith(p) for p in vpn_prefixes) and
                        'flags=' in line and 'UP' in line):
                    logger.debug(f"Active VPN interface detected: {current_iface}")
                    return True
            return False
        except Exception as e:
            logger.debug(f"Error checking VPN status: {e}")
            return False

    def _dns_was_overwritten(self) -> bool:
        """
        Checks if DNS settings were changed by an external process.

        FIX #2: get_current_dns() now uses 'sudo networksetup' consistently,
        preventing false overwrite detection caused by permission failures
        returning None.
        """
        if self.current_dns is None:
            return False

        current = self.get_current_dns()
        if current is None:
            # Command failed for reasons other than permissions — treat conservatively
            logger.warning("Could not read current DNS; skipping overwrite check.")
            return False

        if current != self.current_dns:
            logger.warning(
                f"DNS overwrite detected! Expected: {self.current_dns}, "
                f"Current: {current}"
            )
            return True

        return False

    def get_current_dns(self) -> Optional[Tuple[str, str]]:
        """
        Gets the current DNS configuration via networksetup.

        FIX #2: Uses 'sudo networksetup' (same as set_dns) so both
        read and write operations have the same privilege level,
        preventing spurious None returns that trigger false overwrite detection.
        """
        success, output = self._run_command(
            ["sudo", "networksetup", "-getdnsservers", self.interface]
        )

        if success and output:
            dns_list = output.strip().split('\n')
            # Filter out non-IP lines (e.g. "There aren't any DNS Servers set...")
            ip_lines = []
            for line in dns_list:
                line = line.strip()
                try:
                    ipaddress.ip_address(line)
                    ip_lines.append(line)
                except ValueError:
                    pass
            if len(ip_lines) >= 2:
                return (ip_lines[0], ip_lines[1])
            elif len(ip_lines) == 1:
                return (ip_lines[0], ip_lines[0])

        return None

    def set_dns(self, dns1: str, dns2: str) -> bool:
        """
        Sets new DNS servers on the active interface.
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
        Rotates to a new random healthy DNS server.

        FIX #1: Replaced unbounded recursion with iterative selection via
        get_random_healthy_server(exclude=self.current_dns). If no alternative
        is available, logs a warning and skips this cycle gracefully.
        """
        dns_pair = self.health_checker.get_random_healthy_server(
            DNS_SERVERS, exclude=self.current_dns
        )

        if dns_pair is None:
            logger.warning("No alternative DNS available this cycle. Keeping current DNS.")
            return False

        dns1, dns2 = dns_pair
        return self.set_dns(dns1, dns2)

    def run(self):
        """
        Starts the continuous DNS rotation loop with VPN detection.

        FIX #5: Corrected the pause/resume logic so that:
        - DNS overwrite WITHOUT VPN → correctly sets paused=True on first detection
        - DNS overwrite WITH VPN    → pauses rotation with appropriate message
        - No overwrite after pause  → resumes rotation
        """
        self.running = True
        logger.info(f"Starting DNS rotation every {self.interval} seconds")
        paused = False

        try:
            # Perform initial rotation immediately on startup
            self.rotate_dns()

            while self.running:
                time.sleep(self.interval)

                overwritten = self._dns_was_overwritten()

                if overwritten:
                    if not paused:
                        # FIX #5: Enter pause state on FIRST detection, log correctly
                        if self._is_vpn_active():
                            logger.warning(
                                "VPN detected with DNS overwrite. "
                                "Pausing rotation to avoid conflicts."
                            )
                        else:
                            logger.warning(
                                "DNS was overwritten by an external process. "
                                "Pausing rotation."
                            )
                        paused = True
                else:
                    if paused:
                        logger.info("DNS is stable again. Resuming rotation.")
                        paused = False

                if not paused:
                    self.rotate_dns()
                else:
                    logger.debug(f"Rotation paused. Current DNS: {self.get_current_dns()}")

        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("DNS Changer stopped.")

    def run_once(self) -> bool:
        """Rotates DNS a single time."""
        logger.info("Running single DNS rotation.")
        return self.rotate_dns()

    def reset_dns(self) -> bool:
        """Resets DNS to automatic DHCP configuration."""
        success, output = self._run_command(
            ["sudo", "networksetup", "-setdnsservers", self.interface, "Empty"]
        )

        if success:
            self.current_dns = None
            logger.info("DNS reset to automatic DHCP.")
            return True
        else:
            logger.error(f"Error resetting DNS: {output}")
            return False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_banner():
    """Displays the application banner."""
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
    """Main entry point."""
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
        help=f"Rotation interval in seconds (min: {MIN_ROTATION_INTERVAL}, "
             f"max: {MAX_ROTATION_INTERVAL}, default: 300)"
    )
    parser.add_argument(
        "-o", "--once",
        action="store_true",
        help="Rotate DNS once and exit"
    )
    parser.add_argument(
        "-r", "--reset",
        action="store_true",
        help="Reset DNS to automatic DHCP and exit"
    )
    parser.add_argument(
        "-g", "--get",
        action="store_true",
        help="Display current DNS configuration and exit"
    )
    parser.add_argument(
        "-s", "--set",
        nargs=2,
        metavar=("DNS1", "DNS2"),
        help="Set specific DNS servers and exit (e.g., -s 1.1.1.1 1.0.0.1)"
    )

    args = parser.parse_args()
    print_banner()

    if not acquire_lock():
        print("Error: Another instance of DNS Changer is already running.")
        print("Stop it first or wait for it to finish.")
        return 1

    atexit.register(release_lock)

    changer = DNSChanger(interval=args.interval, interface=args.interface)

    if args.get:
        current = changer.get_current_dns()
        if current:
            print(f"Current DNS: {current[0]}, {current[1]}")
        else:
            print("Could not retrieve DNS configuration.")
        return 0

    if args.reset:
        return 0 if changer.reset_dns() else 1

    if args.set:
        return 0 if changer.set_dns(args.set[0], args.set[1]) else 1

    if args.once:
        return 0 if changer.run_once() else 1

    # Continuous mode (default)
    print(f"Starting continuous rotation every {changer.interval}s. Press Ctrl+C to stop.")
    changer.run()
    return 0

if __name__ == "__main__":
    sys.exit(main())
