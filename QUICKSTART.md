# 🚀 Quick Start Guide - DNS Changer Eye macOS

Get started in less than 5 minutes!

---

## ⚡ Quick Installation

### Step 1: Download the Project
```bash
git clone https://github.com/adrianocansian/DNS-Eyes-for-macOS.git
cd DNS-Eyes-for-macOS
```

### Step 2: Run the Installer
```bash
chmod +x install.sh
./install.sh
```

You will be prompted to enter your administrator password. This is necessary to configure DNS permissions.

### Step 3: Done! ✅

The DNS Changer will start automatically. You can check if it's working:

```bash
dns_changer.py --get
```

---

## 🎮 Essential Commands

### Check Current DNS
```bash
dns_changer.py --get
```

### Rotate DNS Manually
```bash
dns_changer.py --once
```

### Stop the Daemon
```bash
launchctl unload ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

### Start the Daemon
```bash
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

### View Logs
```bash
tail -f ~/.dns_changer/daemon.log
```

### Uninstall
```bash
bash ~/.dns_changer/uninstall.sh
```

---

## ⚙️ Common Configurations

### Change Rotation Interval

**Every 10 minutes:**
```bash
dns_changer.py --interval 600
```

**Every 30 minutes:**
```bash
dns_changer.py --interval 1800
```

### Use a Specific Interface

**Ethernet:**
```bash
dns_changer.py --interface Ethernet
```

**Wi-Fi:**
```bash
dns_changer.py --interface Wi-Fi
```

### Set a Specific DNS

**Cloudflare:**
```bash
dns_changer.py --set 1.1.1.1 1.0.0.1
```

**Google:**
```bash
dns_changer.py --set 8.8.8.8 8.8.4.4
```

**Quad9:**
```bash
dns_changer.py --set 9.9.9.9 149.112.112.112
```

---

## 🔍 Status Check

### Is the Daemon Running?
```bash
launchctl list | grep dns-changer
```

If you see something like:
```
- 0 com.dns-changer.daemon
```

It means it's running! ✅

### Has the DNS Changed?
```bash
dns_changer.py --get
```

Run it multiple times (with a 5-minute interval) to see the DNS change.

---

## ❓ Quick Problems

### "Permission Denied"
```bash
chmod +x /usr/local/bin/dns_changer.py
```

### Daemon Doesn't Start
```bash
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

### Reset DNS
```bash
dns_changer.py --reset
```

---

## 📖 Next Steps

1. **Read the full README**: `README.md`
2. **Configure your preferred interval**: Edit the `.plist` file or use `--interval`
3. **Monitor the logs**: `tail -f ~/.dns_changer/daemon.log`
4. **Consider privacy**: Use with a VPN for maximum protection

---

## 💡 Tips

- ✅ Let it run in the background for maximum privacy
- ✅ Combine with a VPN for extra security
- ✅ Monitor logs periodically
- ✅ Update the script regularly

---

**Enjoy your privacy! 🔒**
