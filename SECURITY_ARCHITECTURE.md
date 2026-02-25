## Security Architecture: LaunchDaemon vs LaunchAgent+sudoers

### Executive Summary

The DNS Changer Eye project has been refactored to use a **LaunchDaemon** architecture instead of the previous **LaunchAgent + sudoers** approach. This change significantly improves security by eliminating a critical privilege escalation vector.

### Previous Architecture (Vulnerable)

**Components:**
- `LaunchAgent` running with user privileges
- `sudoers` rule allowing passwordless execution of `networksetup`
- User account compromise leads to system-wide DNS hijacking

**Security Issues:**
1. **Privilege Escalation Vector:** An attacker with user-level access could execute `sudo /usr/sbin/networksetup` without authentication
2. **Persistent Backdoor:** DNS hijacking affects all network traffic indefinitely
3. **Non-Standard:** Not aligned with macOS security best practices

### New Architecture (Secure)

**Components:**
- `LaunchDaemon` running as root (no sudoers needed)
- Direct execution of `networksetup` with root privileges
- Logs stored in `/var/log/dns_changer/` with proper permissions

**Security Improvements:**
1. **Eliminated Privilege Escalation:** No `sudoers` rule means no passwordless sudo
2. **Proper Isolation:** Root-level operations are contained within the daemon
3. **Standard Approach:** Aligns with macOS system service architecture
4. **Cleaner Permissions:** Log directory owned by `root:wheel` with 755 permissions

### Comparison Table

| Aspect | LaunchAgent + sudoers | LaunchDaemon |
|--------|----------------------|--------------|
| **Execution Context** | User privileges | Root privileges |
| **Privilege Escalation** | Via sudoers rule | Not applicable |
| **Authentication Required** | No (NOPASSWD) | Not applicable |
| **Attack Surface** | sudoers file + user account | Only system boot |
| **Standard Practice** | No | Yes (industry standard) |
| **Log Location** | User home directory | `/var/log/dns_changer/` |
| **Security Risk** | High | Low |

### Installation Changes

**Before:**
```bash
# Install script
sudo cp dns_changer.py /usr/local/bin/
mkdir -p ~/.dns_changer
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/networksetup" | sudo tee /etc/sudoers.d/dns_changer
cp com.dns-changer.daemon.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

**After:**
```bash
# Install script
sudo cp dns_changer.py /usr/local/bin/
sudo mkdir -p /var/log/dns_changer
sudo chown root:wheel /var/log/dns_changer
sudo cp com.dns-changer.daemon.plist /Library/LaunchDaemons/
sudo chown root:wheel /Library/LaunchDaemons/com.dns-changer.daemon.plist
sudo launchctl load /Library/LaunchDaemons/com.dns-changer.daemon.plist
```

### Security Implications

**User Account Compromise Scenario:**

**Before (Vulnerable):**
1. Attacker gains access to user account
2. Attacker runs: `sudo /usr/sbin/networksetup -setdnsservers Wi-Fi 192.168.1.1`
3. System-wide DNS hijacking occurs
4. Attacker can intercept all network traffic

**After (Secure):**
1. Attacker gains access to user account
2. Attacker cannot execute `networksetup` without root password
3. Attacker cannot modify DNS settings
4. System remains secure

### Uninstallation

**Before:**
```bash
launchctl unload ~/Library/LaunchAgents/com.dns-changer.daemon.plist
sudo rm -f /usr/local/bin/dns_changer.py
sudo rm -f /etc/sudoers.d/dns_changer
rm -rf ~/.dns_changer
```

**After:**
```bash
sudo launchctl unload /Library/LaunchDaemons/com.dns-changer.daemon.plist
sudo rm -f /usr/local/bin/dns_changer.py
sudo rm -rf /var/log/dns_changer
sudo rm -f /Library/LaunchDaemons/com.dns-changer.daemon.plist
```

### Conclusion

The migration to LaunchDaemon represents a significant security improvement. It eliminates a critical privilege escalation vector while maintaining full functionality and aligning with macOS security best practices.
