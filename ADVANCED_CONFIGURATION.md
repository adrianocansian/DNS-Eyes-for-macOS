# Advanced Configuration Guide

This guide explains how to customize DNS Changer Eye for advanced use cases using the `config.json` file.

## Quick Start

1. Copy the example configuration:
   ```bash
   cp config.example.json config.json
   ```

2. Edit the configuration:
   ```bash
   nano config.json
   ```

3. The script will automatically load the configuration on the next run.

## Configuration File Locations

The script searches for `config.json` in the following locations (in order):

1. `/etc/dns_changer/config.json` - System-wide configuration
2. `/usr/local/etc/dns_changer/config.json` - Local system configuration
3. `~/.dns_changer/config.json` - User-specific configuration
4. `./config.json` - Configuration in the script directory

The first file found will be used. If no configuration file exists, the script uses built-in defaults.

## Configuration Sections

### General Settings

Control basic operation parameters:

```json
{
  "dns_changer": {
    "general": {
      "enabled": true,
      "interval": 300,
      "interface": "auto",
      "log_level": "INFO"
    }
  }
}
```

**Options:**

- **`enabled`** (boolean): Enable or disable the script. Set to `false` to pause DNS rotation without uninstalling.
- **`interval`** (integer): Rotation interval in seconds. Minimum: 180 (3 minutes), Maximum: 86400 (24 hours). Default: 300 (5 minutes).
- **`interface`** (string): Network interface to modify. Use `auto` for automatic detection, or specify `Wi-Fi`, `Ethernet`, `VPN`, etc.
- **`log_level`** (string): Logging verbosity. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`. Default: `INFO`.

### DNS Servers

Customize which DNS servers are used for rotation:

```json
{
  "dns_changer": {
    "dns_servers": {
      "cloudflare": ["1.1.1.1", "1.0.0.1"],
      "quad9": ["9.9.9.9", "149.112.112.112"],
      "custom": ["203.0.113.1", "203.0.113.2"]
    }
  }
}
```

**Notes:**

- Each entry must have exactly two IP addresses (primary and secondary).
- You can add custom DNS servers by adding new entries.
- Remove entries by deleting them from the configuration.
- The script will randomly select from the configured servers.

### Security Settings

Control security-related behavior:

```json
{
  "dns_changer": {
    "security": {
      "require_sudo": true,
      "log_dns_changes": true,
      "validate_dns": true
    }
  }
}
```

**Options:**

- **`require_sudo`** (boolean): Require `sudo` to run the script. Default: `true`.
- **`log_dns_changes`** (boolean): Log all DNS changes to the log file. Default: `true`.
- **`validate_dns`** (boolean): Validate that DNS servers are responding before applying. Default: `true`.

### Daemon Settings

Configure LaunchDaemon behavior:

```json
{
  "dns_changer": {
    "daemon": {
      "enabled": true,
      "label": "com.dns-changer.daemon",
      "run_at_load": true,
      "keep_alive": true,
      "throttle_interval": 10
    }
  }
}
```

**Options:**

- **`enabled`** (boolean): Enable or disable the LaunchDaemon. Default: `true`.
- **`label`** (string): Unique identifier for the LaunchDaemon. Default: `com.dns-changer.daemon`.
- **`run_at_load`** (boolean): Start the script when the daemon is loaded. Default: `true`.
- **`keep_alive`** (boolean): Automatically restart the script if it crashes. Default: `true`.
- **`throttle_interval`** (integer): Minimum seconds between consecutive runs. Default: `10`.

### Logging Settings

Configure logging behavior:

```json
{
  "dns_changer": {
    "logging": {
      "enabled": true,
      "log_dir": "/var/log/dns_changer",
      "max_log_size": "1MB",
      "retention_days": 30
    }
  }
}
```

**Options:**

- **`enabled`** (boolean): Enable or disable logging. Default: `true`.
- **`log_dir`** (string): Directory where logs are stored. Default: `/var/log/dns_changer`.
- **`max_log_size`** (string): Maximum size of a single log file before rotation. Default: `1MB`.
- **`retention_days`** (integer): Number of days to retain log files. Default: `30`.

## Example Configurations

### Minimal Configuration

For users who want to use mostly defaults with just a few customizations:

```json
{
  "dns_changer": {
    "general": {
      "interval": 600
    }
  }
}
```

This configuration only changes the rotation interval to 10 minutes, using defaults for everything else.

### Privacy-Focused Configuration

For maximum privacy with only privacy-respecting DNS servers:

```json
{
  "dns_changer": {
    "general": {
      "interval": 300,
      "log_level": "WARNING"
    },
    "dns_servers": {
      "cloudflare": ["1.1.1.1", "1.0.0.1"],
      "quad9": ["9.9.9.9", "149.112.112.112"],
      "uncensored_dns": ["91.239.100.100", "89.233.43.71"]
    },
    "security": {
      "validate_dns": true,
      "log_dns_changes": true
    }
  }
}
```

### Enterprise Configuration

For enterprise deployments with strict logging and security requirements:

```json
{
  "dns_changer": {
    "general": {
      "interval": 1800,
      "log_level": "INFO"
    },
    "security": {
      "require_sudo": true,
      "log_dns_changes": true,
      "validate_dns": true
    },
    "logging": {
      "enabled": true,
      "log_dir": "/var/log/dns_changer",
      "max_log_size": "10MB",
      "retention_days": 90
    }
  }
}
```

### Development Configuration

For development and debugging:

```json
{
  "dns_changer": {
    "general": {
      "interval": 60,
      "log_level": "DEBUG"
    },
    "security": {
      "validate_dns": false
    }
  }
}
```

## Troubleshooting Configuration

### Configuration Not Being Loaded

1. Verify the file exists in one of the search paths:
   ```bash
   ls -la /etc/dns_changer/config.json
   ls -la ~/.dns_changer/config.json
   ls -la ./config.json
   ```

2. Check for JSON syntax errors:
   ```bash
   python3 -m json.tool config.json
   ```

3. Check the logs for configuration loading messages:
   ```bash
   tail -f /var/log/dns_changer/daemon.log | grep -i config
   ```

### Invalid Configuration Values

If you specify invalid values, the script will:

1. Log a warning message
2. Use the default value for that setting
3. Continue running normally

Check the logs to see which values were rejected:

```bash
grep "WARNING\|ERROR" /var/log/dns_changer/daemon.log
```

### Permissions Issues

If the script cannot read the configuration file:

```bash
# Check file permissions
ls -la config.json

# Ensure the file is readable
chmod 644 config.json
```

## Best Practices

1. **Start with defaults**: Begin with the example configuration and only change what you need.
2. **Validate JSON**: Always validate your JSON before deploying:
   ```bash
   python3 -m json.tool config.json > /dev/null && echo "Valid JSON"
   ```
3. **Test changes**: After modifying the configuration, restart the daemon to apply changes:
   ```bash
   launchctl unload /Library/LaunchDaemons/com.dns-changer.daemon.plist
   launchctl load /Library/LaunchDaemons/com.dns-changer.daemon.plist
   ```
4. **Monitor logs**: Keep an eye on the logs after configuration changes:
   ```bash
   tail -f /var/log/dns_changer/daemon.log
   ```
5. **Backup configuration**: Keep a backup of your working configuration:
   ```bash
   cp config.json config.json.backup
   ```

## Configuration Priority

When multiple configuration sources exist, they are applied in this order:

1. Built-in defaults (lowest priority)
2. System-wide configuration (`/etc/dns_changer/config.json`)
3. Local configuration (`/usr/local/etc/dns_changer/config.json`)
4. User configuration (`~/.dns_changer/config.json`)
5. Script directory configuration (`./config.json`) (highest priority)

The first configuration file found is used. Subsequent files are ignored.
