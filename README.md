# DNS Changer Eye - macOS Edition

A fully automated and comprehensive solution for continuous DNS server rotation on macOS.
Designed with a strong emphasis on privacy, security, and user convenience.

## Project Status

⚠️ This is an experimental research project.

The software is functional but under active development and should be
considered a testing and learning tool rather than a production-ready
solution.

Interfaces, behavior, and configuration details may change as the project evolves.

Feedback, audits, and contributions are highly welcome. **Use at your own risk!**

## Origin and Credits

This project is a native macOS adaptation of **DNS Changer Eye**, the original Linux implementation by [BullsEye0](https://github.com/BullsEye0/DNS_Changer_Eye). We extend our gratitude to BullsEye0 for the innovative concept and foundational work that inspired this macOS port.

The full article explaining the importance of DNS in ethical hacking can be found at [HackingPassion.com](https://hackingpassion.com/why-your-dns-settings-could-make-or-break-your-hacking-career/).

## 📋 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)
- [Security](#security)
- [FAQ](#faq)

---

## ✨ Features

### Main Features

- **Automatic DNS Rotation**: Switches between 25+ trusted DNS servers every 5 minutes (configurable, minimum 3 minutes).
- **Automatic Execution**: Starts automatically at system boot via LaunchDaemon (runs as root — no sudoers required).
- **Intelligent Detection**: Automatically detects the active network interface using a multi-strategy approach.
- **DNS Health Validation**: Tests each server before applying it, with a 30-minute healthy-server cache.
- **VPN Awareness**: Detects active VPN interfaces and pauses rotation automatically to avoid conflicts.
- **Secure Logging**: Records all changes and errors to `/var/log/dns_changer/` with restricted permissions (750/640).
- **PID Lock**: Prevents multiple instances from running simultaneously.
- **Simple Interface**: Intuitive command line with multiple options.
- **Reversible**: Easy uninstallation with automatic DNS reset on all active interfaces.

### Supported DNS Servers

The script includes a curated list of 25+ public and trusted DNS servers:

- **Cloudflare**: 1.1.1.1, 1.0.0.1
- **Quad9**: 9.9.9.9, 149.112.112.112
- **OpenDNS**: 208.67.222.222, 208.67.220.220
- **Google**: 8.8.8.8, 8.8.4.4
- **Verisign**: 64.6.64.6, 64.6.65.6
- And 20+ more servers

---

## 🔧 Requirements

### Operating System
- **macOS 12.0 or higher** (tested on Sequoia 15.0+)
- Administrator access

### Software
- **Python 3.6+** (pre-installed on macOS 12+)
- **Bash 3.2+** (default on macOS)

### Permissions
- `sudo` privileges (required during installation only)

---

## 📦 Installation

### Method 1: Automatic Installation (Recommended)

1. **Clone the repository**:
```bash
git clone https://github.com/adrianocansian/macOS-DNS-Eyes.git
cd macOS-DNS-Eyes
```

2. **Run the installer**:
```bash
chmod +x install.sh
sudo bash install.sh
```

3. **Follow the on-screen instructions**. The script will ask for your administrator password.

4. **Done!** The DNS Changer will start automatically at every system boot.

### Method 2: Manual Installation

If you prefer to install manually:

```bash
# 1. Copy the main script
sudo cp dns_changer.py /usr/local/bin/
sudo chmod 755 /usr/local/bin/dns_changer.py
sudo chown root:wheel /usr/local/bin/dns_changer.py

# 2. Create the log directory with secure permissions
sudo mkdir -p /var/log/dns_changer
sudo chown root:admin /var/log/dns_changer
sudo chmod 750 /var/log/dns_changer

# 3. Create the LaunchDaemon plist
sudo cp com.dns-changer.daemon.plist /Library/LaunchDaemons/
sudo chown root:wheel /Library/LaunchDaemons/com.dns-changer.daemon.plist
sudo chmod 644 /Library/LaunchDaemons/com.dns-changer.daemon.plist

# 4. Load the daemon
sudo launchctl bootstrap system /Library/LaunchDaemons/com.dns-changer.daemon.plist
```

> **Note:** No sudoers configuration is needed. The daemon runs as root via LaunchDaemon.

---

## 🚀 Usage

### Continuous Mode (Default)

Starts automatic DNS rotation:

```bash
sudo dns_changer.py
```

Press `Ctrl+C` to stop.

### Command-Line Options

```bash
# Rotate DNS once
sudo dns_changer.py --once

# Specify network interface
sudo dns_changer.py --interface Ethernet

# Change rotation interval (in seconds)
sudo dns_changer.py --interval 600

# Get current DNS configuration
sudo dns_changer.py --get

# Set specific DNS servers
sudo dns_changer.py --set 1.1.1.1 1.0.0.1

# Reset DNS to automatic (DHCP)
sudo dns_changer.py --reset

# Display help
dns_changer.py --help
```

### Practical Examples

```bash
# Rotate every 10 minutes
sudo dns_changer.py --interval 600

# Use only Ethernet
sudo dns_changer.py --interface Ethernet --interval 300

# Set Cloudflare DNS
sudo dns_changer.py --set 1.1.1.1 1.0.0.1

# Check current DNS
sudo dns_changer.py --get

# Reset to DHCP
sudo dns_changer.py --reset
```

---

## ⚙️ Configuration

### Change Rotation Interval

Edit the LaunchDaemon plist file:

```bash
sudo nano /Library/LaunchDaemons/com.dns-changer.daemon.plist
```

Look for:
```xml
<string>300</string>
```

Change `300` to the desired interval in seconds:
- `180` = 3 minutes (minimum enforced by the script)
- `300` = 5 minutes (default)
- `600` = 10 minutes
- `1800` = 30 minutes
- `3600` = 1 hour

**Minimum Interval:** The script enforces a minimum of 180 seconds (3 minutes). If you specify less, the script will automatically use 180 seconds and log a warning.

Then reload the daemon:
```bash
sudo launchctl bootout system /Library/LaunchDaemons/com.dns-changer.daemon.plist
sudo launchctl bootstrap system /Library/LaunchDaemons/com.dns-changer.daemon.plist
```

### Advanced Configuration (config.json)

For advanced customization, create a `config.json` file in one of these locations (in order of priority):

```
/etc/dns_changer/config.json
/usr/local/etc/dns_changer/config.json
~/.dns_changer/config.json
./config.json
```

Copy the example configuration and customize it:

```bash
cp config.example.json config.json
sudo nano config.json
```

The configuration file allows you to customize:

- **Rotation interval** — Change how often DNS servers rotate
- **DNS servers** — Select which servers to use
- **Logging** — Configure log retention and size limits

### Network Interface Detection

The DNS Changer automatically detects your active network interface using a multi-strategy approach:

**Detection Strategy:**
1. Lists all macOS network services respecting your interface priority
2. Identifies which services are currently active
3. Uses the highest-priority active interface
4. Falls back to default route detection if needed
5. Defaults to Wi-Fi if all else fails

**Multiple Active Interfaces:**

If you have multiple interfaces active (e.g., Wi-Fi + Ethernet), the script will:
- Log a warning showing all active interfaces
- Use the highest-priority interface according to your macOS settings
- Continue without interruption

**Specify a Different Interface:**

```bash
# List all available network services
networksetup -listallnetworkservices

# Run with a specific interface
sudo dns_changer.py --interface Ethernet
```

**VPN Considerations:**

When you connect to a VPN, DNS Changer behaves intelligently:

1. **Automatic Detection**: Detects when a VPN interface is active and UP
2. **DNS Overwrite Detection**: Monitors if the VPN overwrites DNS settings
3. **Intelligent Pausing**: Pauses rotation to avoid conflicts
4. **Automatic Resume**: Resumes when the overwrite is no longer detected

Log messages to watch:
```
WARNING: VPN detected with DNS overwrite. Pausing rotation to avoid conflicts.
WARNING: DNS was overwritten by an external process. Pausing rotation.
INFO: DNS is stable again. Resuming rotation.
```

Monitor VPN and overwrite detection:
```bash
tail -f /var/log/dns_changer/daemon.log | grep -iE "vpn|overwrite|pausing|resuming"
```

### Add Custom DNS Servers

Edit `dns_changer.py` and modify the `DNS_SERVERS` list:

```python
DNS_SERVERS = [
    ("1.1.1.1", "1.0.0.1"),       # Cloudflare
    ("your.dns.1", "your.dns.2"),  # Your custom server
    # ... more servers
]
```

---

## 📊 Monitoring

### Check Daemon Status

```bash
# Check if it's running
sudo launchctl list | grep dns-changer

# View logs in real-time
tail -f /var/log/dns_changer/daemon.log

# View error logs
tail -f /var/log/dns_changer/daemon_error.log

# View system logs
log show --predicate 'process == "dns_changer.py"' --last 1h
```

**Privacy Note:** Log files are stored at `/var/log/dns_changer/` with restricted permissions (directory: 750, files: 640). Only root and members of the `admin` group can read them.

### Check Current DNS

```bash
# Via script
sudo dns_changer.py --get

# Via networksetup (replace Wi-Fi with your interface name)
networksetup -getdnsservers Wi-Fi

# Via resolv.conf
cat /etc/resolv.conf
```

---

## 🔧 Troubleshooting

### Problem: "Permission Denied" when executing

**Solution**:
```bash
sudo chmod 755 /usr/local/bin/dns_changer.py
```

### Problem: Daemon does not start automatically

**Check**:
```bash
# Check if it's registered
sudo launchctl list | grep dns-changer

# Reload the daemon
sudo launchctl bootout system /Library/LaunchDaemons/com.dns-changer.daemon.plist
sudo launchctl bootstrap system /Library/LaunchDaemons/com.dns-changer.daemon.plist

# Check logs for errors
tail -50 /var/log/dns_changer/daemon_error.log
```

### Problem: DNS does not change

**Check**:
```bash
# 1. Verify current DNS
sudo dns_changer.py --get

# 2. Check daemon is running
sudo launchctl list | grep dns-changer

# 3. Check logs
tail -f /var/log/dns_changer/daemon.log
```

### Problem: VPN overrides DNS

DNS Changer automatically detects VPN overrides and pauses rotation. This is expected behavior. When your VPN disconnects and DNS stabilizes, rotation resumes automatically. You can monitor this in the logs:

```bash
tail -f /var/log/dns_changer/daemon.log | grep -iE "vpn|overwrite|pausing|resuming"
```

### Problem: "Another instance is already running"

```bash
# Check for running instances
ps aux | grep dns_changer

# If the process is not running but the lock file remains (orphaned lock):
sudo rm /var/run/dns_changer.pid
# or (if using fallback directory):
rm ~/.dns_changer/dns_changer.pid
```

### Problem: Log directory not accessible

```bash
# Verify permissions
ls -la /var/log/dns_changer/

# Expected:
# drwxr-x---  root  admin   (750)
# -rw-r-----  root  admin   (640)

# Fix permissions if needed
sudo chmod 750 /var/log/dns_changer
sudo chown root:admin /var/log/dns_changer
```

---

## 🗑️ Uninstallation

### Automatic Method

```bash
sudo bash /var/log/dns_changer/uninstall.sh
```

### Manual Method

```bash
# 1. Unload and remove the LaunchDaemon
sudo launchctl bootout system /Library/LaunchDaemons/com.dns-changer.daemon.plist
sudo rm /Library/LaunchDaemons/com.dns-changer.daemon.plist

# 2. Remove the main script
sudo rm /usr/local/bin/dns_changer.py

# 3. Reset DNS to DHCP on all active interfaces
networksetup -listallnetworkservices | grep -v '^\*' | tail -n +2 | while read svc; do
    sudo networksetup -setdnsservers "$svc" Empty
done

# 4. Remove the log directory
sudo rm -rf /var/log/dns_changer
```

---

## 🔒 Security

### Architecture Overview

DNS Changer Eye runs as a **system-level LaunchDaemon** (root), not as a user-level LaunchAgent. This means:

- No sudoers configuration is required or created during installation
- The daemon starts at system boot, before any user logs in
- All DNS changes are made directly by the daemon with root privileges

### Security Considerations

1. **Root Execution via LaunchDaemon**: The daemon runs as root through macOS's LaunchDaemon mechanism — the same way system services like `ntpd` and `syslogd` operate. No permanent root shell or `sudo` bypass is created.

2. **No Passwordless Sudoers**: Unlike older versions of this project, the current version does **not** configure `/etc/sudoers.d/dns_changer`. If you see this file on your system, it is a leftover from a previous installation and can be safely removed:
   ```bash
   sudo rm -f /etc/sudoers.d/dns_changer
   ```

3. **Secure Log Directory**: Logs are stored at `/var/log/dns_changer/` with restricted permissions:
   - Directory: `drwxr-x---` (750) — root:admin only
   - Log files: `-rw-r-----` (640) — root:admin only

4. **DNS Health Validation**: Before applying any DNS server, the script sends a real DNS query and validates the response (checks Transaction ID and QR bit). Servers that return invalid responses are excluded.

5. **PID Lock**: Only one instance of the daemon can run at a time. A lock file at `/var/run/dns_changer.pid` prevents concurrent execution.

6. **Open Source**: All source code is available for inspection and audit.

### Best Practices

- Keep the script updated by pulling from the repository periodically
- Periodically review the DNS server list in `dns_changer.py`
- Monitor logs regularly: `tail -f /var/log/dns_changer/daemon.log`
- Use on trusted networks
- Consider combining with a VPN for maximum privacy

---

## ❓ FAQ

### Q: Does this require sudoers configuration?
**A**: No. The current version runs as root via LaunchDaemon. No sudoers configuration is needed or created.

### Q: Is DNS Changer secure?
**A**: Yes. It uses only native macOS tools (`networksetup`), validates DNS servers before applying them, stores logs with restricted permissions, and requires no permanent privilege escalation beyond the LaunchDaemon mechanism.

### Q: What is the performance impact?
**A**: Minimal. The script uses approximately 5–10 MB of memory and only consumes CPU during rotations and health checks.

### Q: Can I use it with a VPN?
**A**: Yes. DNS Changer automatically detects VPN-related DNS overwrites and pauses rotation to avoid conflicts. It resumes automatically when the overwrite is no longer detected.

### Q: How do I know if it's working?
**A**: Run `sudo dns_changer.py --get` to see the current DNS, or check the logs: `tail -f /var/log/dns_changer/daemon.log`.

### Q: Can I change the rotation interval?
**A**: Yes, edit the interval value in `/Library/LaunchDaemons/com.dns-changer.daemon.plist` or use `--interval` on the command line. The minimum enforced interval is 180 seconds.

### Q: What happens if I uninstall?
**A**: The uninstall script stops the daemon, removes all installed files, and resets DNS to automatic DHCP on all active interfaces.

### Q: Does it work on corporate networks?
**A**: There may be restrictions. Corporate networks often enforce specific DNS servers via DHCP or firewall rules. Consult your network administrator.

### Q: Can I use multiple interfaces?
**A**: Yes, run separate instances with a different `--interface` argument, or configure multiple services in the plist.

### Q: What is the recommended rotation interval?
**A**: 5–10 minutes (300–600 seconds) is recommended for most use cases. Intervals below 3 minutes (180 seconds) are not permitted, as they can cause DNS resolution failures and broken connections.

### Q: Where are the log files?
**A**: All logs are stored at `/var/log/dns_changer/`. The main log is `daemon.log` and errors go to `daemon_error.log`. You need to be root or a member of the `admin` group to read them.

---

## 📝 License

This project is based on DNS Changer Eye (BullsEye0) and maintains compatibility with GPL-3.0.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📞 Support

If you encounter problems:

1. Check the [Troubleshooting](#troubleshooting) section
2. Check the logs: `tail -f /var/log/dns_changer/daemon.log`
3. Open an issue on GitHub

---

## 🎯 Roadmap

- [ ] Graphical User Interface (GUI)
- [ ] Support for custom DNS profiles
- [ ] Homebrew integration
- [ ] Apple Silicon (M1/M2/M3) explicit testing and documentation
- [ ] System notifications
- [ ] Usage statistics

---

## 📚 References

- [Apple LaunchDaemon Documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchDaemons.html)
- [networksetup Manual](https://ss64.com/osx/networksetup.html)
- [DNS Security Best Practices](https://www.cloudflare.com/learning/dns/dns-security/)
- [launchctl Man Page](https://ss64.com/osx/launchctl.html)

---

**Developed with ❤️ for macOS Sequoia**

Last updated: 2026
