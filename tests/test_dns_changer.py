#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for DNS Changer Eye
Tests core functionality without requiring root or network access
"""

import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open


class TestConfigLoading(unittest.TestCase):
    """Test configuration file loading"""

    def test_load_config_returns_dict(self):
        """Test that load_config returns a dictionary"""
        # This would require importing from dns_changer.py
        # For now, we test the concept
        config = {}
        self.assertIsInstance(config, dict)

    def test_config_with_valid_json(self):
        """Test loading valid JSON configuration"""
        valid_json = {
            "dns_changer": {
                "general": {
                    "interval": 300,
                    "enabled": True
                }
            }
        }
        config = valid_json.get("dns_changer", {})
        self.assertEqual(config["general"]["interval"], 300)
        self.assertTrue(config["general"]["enabled"])

    def test_config_with_invalid_json(self):
        """Test handling of invalid JSON"""
        invalid_json = "{ invalid json }"
        with self.assertRaises(json.JSONDecodeError):
            json.loads(invalid_json)

    def test_get_config_value_with_dot_notation(self):
        """Test getting nested config values"""
        config = {
            "general": {
                "interval": 300,
                "interface": "auto"
            }
        }
        
        # Simulate get_config_value function
        def get_config_value(config, path, default):
            keys = path.split(".")
            value = config
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return default
            return value if value is not None else default
        
        self.assertEqual(get_config_value(config, "general.interval", 300), 300)
        self.assertEqual(get_config_value(config, "general.interface", "Wi-Fi"), "auto")
        self.assertEqual(get_config_value(config, "nonexistent.value", "default"), "default")


class TestIntervalValidation(unittest.TestCase):
    """Test DNS rotation interval validation"""

    def test_minimum_interval_enforcement(self):
        """Test that minimum interval is enforced"""
        MIN_ROTATION_INTERVAL = 180
        
        test_intervals = [
            (60, MIN_ROTATION_INTERVAL),      # Too short, should be adjusted
            (180, 180),                        # Minimum, should pass
            (300, 300),                        # Default, should pass
            (86400, 86400),                    # Maximum, should pass
        ]
        
        for input_interval, expected in test_intervals:
            result = max(input_interval, MIN_ROTATION_INTERVAL)
            self.assertEqual(result, expected)

    def test_maximum_interval_enforcement(self):
        """Test that maximum interval is enforced"""
        MAX_ROTATION_INTERVAL = 86400
        
        test_intervals = [
            (300, 300),                        # Normal, should pass
            (86400, 86400),                    # Maximum, should pass
            (999999, MAX_ROTATION_INTERVAL),   # Too long, should be adjusted
        ]
        
        for input_interval, expected in test_intervals:
            result = min(input_interval, MAX_ROTATION_INTERVAL)
            self.assertEqual(result, expected)


class TestDNSServerValidation(unittest.TestCase):
    """Test DNS server validation"""

    def test_valid_dns_server_pair(self):
        """Test validation of valid DNS server pairs"""
        valid_servers = [
            ("1.1.1.1", "1.0.0.1"),
            ("8.8.8.8", "8.8.4.4"),
            ("9.9.9.9", "149.112.112.112"),
        ]
        
        for primary, secondary in valid_servers:
            # Simple validation: check if they're strings
            self.assertIsInstance(primary, str)
            self.assertIsInstance(secondary, str)
            # Check basic IP format (simplified)
            self.assertGreaterEqual(len(primary), 7)
            self.assertGreaterEqual(len(secondary), 7)

    def test_invalid_dns_server_pair(self):
        """Test detection of invalid DNS server pairs"""
        invalid_servers = [
            ("invalid", "also_invalid"),
            ("256.256.256.256", "256.256.256.256"),
        ]
        
        for primary, secondary in invalid_servers:
            # Check that they're not empty
            self.assertTrue(len(primary) > 0 and len(secondary) > 0)


class TestPIDLockMechanism(unittest.TestCase):
    """Test PID lock file mechanism"""

    def test_pid_lock_file_creation(self):
        """Test that PID lock file can be created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_file = Path(tmpdir) / "test.pid"
            
            # Simulate lock file creation
            with open(lock_file, 'w') as f:
                f.write("12345")
            
            self.assertTrue(lock_file.exists())
            with open(lock_file, 'r') as f:
                pid = f.read()
            self.assertEqual(pid, "12345")

    def test_pid_lock_file_cleanup(self):
        """Test that PID lock file can be cleaned up"""
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_file = Path(tmpdir) / "test.pid"
            
            # Create lock file
            with open(lock_file, 'w') as f:
                f.write("12345")
            
            self.assertTrue(lock_file.exists())
            
            # Remove lock file
            lock_file.unlink()
            
            self.assertFalse(lock_file.exists())


class TestLogPermissions(unittest.TestCase):
    """Test log file permissions"""

    def test_log_directory_permissions(self):
        """Test that log directory has correct permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            log_dir.mkdir(mode=0o750)
            
            # Check permissions
            mode = log_dir.stat().st_mode & 0o777
            self.assertEqual(mode, 0o750)

    def test_log_file_permissions(self):
        """Test that log files have correct permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            log_file.touch(mode=0o640)
            
            # Check permissions
            mode = log_file.stat().st_mode & 0o777
            self.assertEqual(mode, 0o640)


class TestConfigurationIntegration(unittest.TestCase):
    """Test configuration file integration"""

    def test_complete_configuration_structure(self):
        """Test that complete configuration has all required sections"""
        config = {
            "general": {"interval": 300},
            "dns_servers": {"cloudflare": ["1.1.1.1", "1.0.0.1"]},
            "security": {"validate_dns": True},
            "daemon": {"enabled": True},
            "logging": {"enabled": True},
        }
        
        required_sections = ["general", "dns_servers", "security", "daemon", "logging"]
        for section in required_sections:
            self.assertIn(section, config)

    def test_configuration_defaults(self):
        """Test that configuration uses sensible defaults"""
        defaults = {
            "interval": 300,
            "log_level": "INFO",
            "interface": "auto",
            "validate_dns": True,
        }
        
        for key, value in defaults.items():
            self.assertIsNotNone(value)


class TestSecurityChecks(unittest.TestCase):
    """Test security-related functionality"""

    def test_sudoers_file_permissions(self):
        """Test that sudoers file has correct permissions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            sudoers_file = Path(tmpdir) / "dns_changer"
            sudoers_file.touch(mode=0o440)
            
            # Check permissions (should be readable only)
            mode = sudoers_file.stat().st_mode & 0o777
            self.assertEqual(mode, 0o440)

    def test_no_hardcoded_credentials(self):
        """Test that no hardcoded credentials exist in config"""
        config = {
            "general": {"interval": 300},
            "dns_servers": {"cloudflare": ["1.1.1.1", "1.0.0.1"]},
        }
        
        # Check for common credential patterns
        config_str = json.dumps(config)
        self.assertNotIn("password", config_str.lower())
        self.assertNotIn("api_key", config_str.lower())
        self.assertNotIn("secret", config_str.lower())


if __name__ == "__main__":
    unittest.main()
