# DNS Changer Eye - macOS Edition

A fully automated and comprehensive solution for continuous DNS server rotation on macOS.
Designed with a strong emphasis on privacy, security, and user convenience.

## Project Status

⚠️ This is an experimental research project.

The software is functional but under active development and should be
considered a testing and learning tool rather than a production-ready
solution.

Interfaces, behavior and configuration details may change as the project evolves.

Feedback, audits and contributions are highly welcome. **Use at your own risk!** Feedback and audits are welcome.


## Origin and Credits

This project is conceptually inspired by  **DNS Changer Eye** by [BullsEye0](https://github.com/BullsEye0/DNS_Changer_Eye), (original Linux implementation by BullsEye0) and reimplemented
for native macOS integration. This repository adapts the concept for native macOS integration.

The full article explaining the importance of DNS in ethical hacking can be found at [HackingPassion.com](https://hackingpassion.com/why-your-dns-settings-could-make-or-break-your-hacking-career/).

## 📋 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)
- [Security](#security)
- [FAQ](#faq)

---

## ✨ Features

### Main Features

- **Automatic DNS Rotation**: Switches between 25+ trusted DNS servers every 5 minutes (configurable).
- **Automatic Execution**: Starts automatically on login via LaunchAgent.
- **Intelligent Detection**: Automatically detects the active network interface.
- **Complete Logging**: Records all changes and errors to a log file.
- **Simple Interface**: Intuitive command line with multiple options.
- **Security**: Automatic sudoers configuration for passwordless execution.
- **Reversible**: Easy uninstallation with automatic DNS reset.

### Supported DNS Servers

The script includes a curated list of 25+ public and trusted DNS servers:

- **Cloudflare**: 1.1.1.1, 1.0.0.1
- **Quad9**: 9.9.9.9, 149.112.112.112
- **OpenDNS**: 208.67.222.222, 208.67.220.220
- **Google**: 8.8.8.8, 8.8.4.4
- **Verisign**: 64.6.64.6, 64.6.65.6
- And 15+ more servers

---

## 🔧 Requirements

### Operating System
- **macOS 12.0 or higher** (tested on Sequoia 15.0+)
- Administrator access

### Software
- **Python 3.6+** (pre-installed on macOS 12+)
- **Bash 3.2+** (default on macOS)

### Permissions
- `sudo` privileges (will be requested during installation)

---

## 📦 Installation

### Method 1: Automatic Installation (Recommended)

1. **Clone or download the repository**:
```bash
git clone https://github.com/adrianocansian/macOS-DNS-Eyes.git
cd macOS-DNS-Eyes
```

2. **Verify file integrity** (IMPORTANT - Protects against supply chain attacks):
```bash
chmod +x verify.sh
bash verify.sh
```

This step is **critical for security**. It verifies that the files have not been modified or compromised. Only proceed if all files are verified successfully.

3. **Run the installer**:
```bash
chmod +x install.sh
sudo bash install.sh
```

4. **Follow the on-screen instructions**. The script will ask for your administrator password.

5. **Done!** The DNS Changer will start automatically.

### Method 2: Manual Installation

If you prefer to install manually:

```bash
# 1. Copy the main script
sudo cp dns_changer.py /usr/local/bin/
sudo chmod +x /usr/local/bin/dns_changer.py

# 2. Create the configuration directory
mkdir -p ~/.dns_changer

# 3. Configure sudoers
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/networksetup" | sudo tee /etc/sudoers.d/dns_changer

# 4. Copy the LaunchAgent
cp com.dns-changer.daemon.plist ~/Library/LaunchAgents/
sed -i '' "s|__HOME__|$HOME|g" ~/Library/LaunchAgents/com.dns-changer.daemon.plist
sed -i '' "s|__USER__|$USER|g" ~/Library/LaunchAgents/com.dns-changer.daemon.plist

# 5. Load the daemon
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

---

## 🚀 Usage

### Continuous Mode (Default)

Starts automatic DNS rotation:

```bash
dns_changer.py
```

Press `Ctrl+C` to stop.

### Command-Line Options

```bash
# Rotate DNS once
dns_changer.py --once

# Specify network interface
dns_changer.py --interface Ethernet

# Change rotation interval (in seconds)
dns_changer.py --interval 600

# Get current DNS configuration
dns_changer.py --get

# Set specific DNS servers
dns_changer.py --set 1.1.1.1 1.0.0.1

# Reset DNS to automatic (DHCP)
dns_changer.py --reset

# Display help
dns_changer.py --help
```

### Practical Examples

```bash
# Rotate every 10 minutes
dns_changer.py --interval 600

# Use only Ethernet
dns_changer.py --interface Ethernet --interval 300

# Set Cloudflare DNS
dns_changer.py --set 1.1.1.1 1.0.0.1

# Check current DNS
dns_changer.py --get

# Reset to DHCP
dns_changer.py --reset
```

---

## ⚙️ Configuration

### Change Rotation Interval

Edit the LaunchAgent file:

```bash
nano ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

Look for:
```xml
<string>300</string>
```

Change `300` to the desired interval in seconds:
- `300` = 5 minutes (default)
- `600` = 10 minutes
- `1800` = 30 minutes

Then reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.dns-changer.daemon.plist
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

### Network Interface Detection

The DNS Changer automatically detects your active network interface using a multi-strategy approach:

**Detection Strategy:**
1. Checks macOS network service preferences (respects your interface priority)
2. Identifies all active interfaces
3. Uses the highest-priority active interface
4. Falls back to default route detection if needed
5. Defaults to Wi-Fi if all else fails

**Multiple Active Interfaces:**

If you have multiple interfaces active (Wi-Fi + Ethernet), the script will:
- Log a warning showing which interfaces are active
- Use the highest-priority interface according to your macOS settings
- Continue without interruption

**Specify a Different Interface:**

If auto-detection chooses the wrong interface, specify it manually:

```bash
# List all available network services
networksetup -listallnetworkservices

# Run with a specific interface
dns_changer.py --interface Ethernet
```

**VPN Considerations:**

When you connect to a VPN, DNS Changer behaves intelligently:

1. **Automatic Detection:** Detects when a VPN is active
2. **DNS Overwrite Detection:** Monitors if VPN overwrites DNS settings
3. **Intelligent Pausing:** Pauses rotation to avoid conflicts
4. **Automatic Resume:** Resumes when VPN disconnects

**Log Messages:**

- `WARNING: VPN detected with DNS overwrite. Pausing rotation.`
- `INFO: Resuming DNS rotation.`
- `WARNING: DNS overwrite detected. Pausing rotation.`

**Troubleshooting:**

```bash
# Check VPN detection
tail -f /var/log/dns_changer/daemon.log | grep -i vpn

# Check DNS overwrite detection
tail -f /var/log/dns_changer/daemon.log | grep -i overwrite

# Check which interface was detected
tail -f /var/log/dns_changer/daemon.log | grep interface

# Check if VPN interface is active
ifconfig | grep -E "utun|ppp|tun|tap"
```

### Add Custom DNS Servers

Edit `dns_changer.py` and modify the `DNS_SERVERS` list:

```python
DNS_SERVERS = [
    ("1.1.1.1", "1.0.0.1"),      # Your server 1
    ("your.dns.1", "your.dns.2"),  # Your server 2
    # ... more servers
]
```

---

## 📊 Monitoring

### Check Daemon Status

```bash
# Check if it's running
launchctl list | grep dns-changer

# View logs in real-time
tail -f ~/.dns_changer/daemon.log

# View error logs
tail -f ~/.dns_changer/daemon_error.log

# View all logs
log show --predicate 'process == "dns_changer.py"' --last 1h
```

### Check Current DNS

```bash
# Via script
dns_changer.py --get

# Via networksetup
networksetup -getdnsservers Wi-Fi

# Via cat (traditional method)
cat /etc/resolv.conf
```

---

## 🔧 Troubleshooting

### Problem: "Permission Denied" when executing

**Solution**:
```bash
chmod +x /usr/local/bin/dns_changer.py
```

### Problem: Daemon does not start automatically

**Check**:
```bash
# Check if it's loaded
launchctl list | grep dns-changer

# Reload
launchctl unload ~/Library/LaunchAgents/com.dns-changer.daemon.plist
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

### Problem: "sudo: networksetup: command not found"

**Solution**: Reconfigure sudoers:
```bash
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/networksetup" | sudo tee /etc/sudoers.d/dns_changer
```

### Problem: DNS does not change

**Check**:
1. Correct interface: `dns_changer.py --get`
2. Privileges: `sudo -l | grep networksetup`
3. Logs: `tail -f ~/.dns_changer/daemon.log`

### Problem: VPN overrides DNS

**Solution**: Some VPN clients override DNS. You can:
- Temporarily disable the VPN
- Use the VPN's DNS
- Reconfigure after connecting to the VPN

---

## 🗑️ Uninstallation

### Automatic Method

```bash
bash ~/.dns_changer/uninstall.sh
```

### Manual Method

```bash
# 1. Unload the daemon
launchctl unload ~/Library/LaunchAgents/com.dns-changer.daemon.plist

# 2. Remove the script
sudo rm /usr/local/bin/dns_changer.py

# 3. Remove sudoers configuration
sudo rm /etc/sudoers.d/dns_changer

# 4. Remove the daemon file
rm ~/Library/LaunchAgents/com.dns-changer.daemon.plist

# 5. Remove the configuration directory
rm -rf ~/.dns_changer

# 6. Reset DNS (optional)
sudo networksetup -setdnsservers Wi-Fi Empty
```

---

## 🔒 Security

### Security Considerations

1. **File Integrity Verification (Supply Chain Protection)**: Before installation, always run the verify.sh script to ensure files have not been compromised. This protects against repository compromise, malicious forks, and man-in-the-middle attacks. Never skip this step!

2. **Root Privileges**: The script requires `sudo` to change DNS. This is necessary and secure.

3. **Passwordless Sudoers**: The installation configures `sudo` to run `networksetup` without a password. This is secure because:
   - It's limited only to `networksetup`
   - It requires the user to be already logged in
   - The `/etc/sudoers.d/dns_changer` file has restricted permissions (440)

4. **Logs**: The logs contain information about changed DNS. Check permissions:
   ```bash
   ls -la ~/.dns_changer/
   ```

5. **LaunchAgent** (user-level): Runs with user privileges (not root), increasing security.

6. **Open Source**: All code is transparent and can be audited.

### Supply Chain Security

This project implements multiple layers of protection against supply chain attacks:

- **SHA-256 Hash Verification**: Each release includes a SHA256SUMS file with cryptographic hashes of all critical files.
- **Automated Verification Script**: The verify.sh script automatically downloads and verifies file hashes from GitHub.
- **Transparent Code**: All source code is available for inspection and audit.
- **No External Dependencies**: The project uses only macOS native tools, reducing the attack surface.

### Best Practices

- Always verify file integrity before installation
- Keep the script updated
- Periodically review the DNS servers
- Regularly monitor the logs
- Use on trusted networks
- Consider using VPN + DNS Changer for maximum privacy

---

## ❓ FAQ

### Q: Is DNS Changer secure?
**A**: Yes. The script uses only native macOS tools (`networksetup`) and does not require permanent root.

### Q: What is the performance impact?
**A**: Minimal. The script uses ~5-10MB of memory and consumes CPU only during rotations.

### Q: Can I use it with a VPN?
**A**: Yes, but the VPN may override the DNS settings. In that case, use the VPN's DNS.

### Q: How do I know if it's working?
**A**: Run `dns_changer.py --get` to see the current DNS, or check the logs.

### Q: Can I change the rotation interval?
**A**: Yes, edit the `.plist` file or use `--interval` on the command line.

### Q: What happens if I uninstall?
**A**: The script removes all files and resets the DNS to automatic (DHCP).

### Q: Does it work on corporate networks?
**A**: There may be restrictions. Consult your network administrator.

### Q: Can I use multiple interfaces?
**A**: Yes, run separate instances with a different `--interface`.

### Q: What is the best rotation interval?
**A**: 5-10 minutes (300-600 seconds) is recommended. Very short intervals can cause instability.

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
2. Check the logs: `tail -f ~/.dns_changer/daemon.log`
3. Open an issue on GitHub

---

## 🎯 Roadmap

- [ ] Graphical User Interface (GUI)
- [ ] Support for custom DNS profiles
- [ ] Homebrew integration
- [ ] M1/M2 support (arm64)
- [ ] System notifications
- [ ] Usage statistics

---

## 📚 References

- [Apple LaunchDaemon Documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchDaemons.html)
- [networksetup Manual](https://ss64.com/osx/networksetup.html)
- [DNS Security Best Practices](https://www.cloudflare.com/learning/dns/dns-security/)

---

**Developed with ❤️ for macOS Sequoia**

Last updated: 2026
