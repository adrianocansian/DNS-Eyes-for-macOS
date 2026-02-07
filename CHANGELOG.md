# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-02-06

### Added

- **Main Script** (`dns_changer.py`):
  - Automatic DNS rotation with 25+ public servers
  - Automatic network interface detection
  - IP address validation
  - Complete logging with a log file
  - Signal handling for graceful shutdown
  - Support for multiple command-line options

- **Installer** (`install.sh`):
  - Automated installation with requirements check
  - macOS version detection
  - Automatic sudoers configuration
  - LaunchAgent creation for automatic execution
  - Administrator privilege validation

- **Uninstaller** (`uninstall.sh`):
  - Complete removal of all files
  - Automatic DNS reset to DHCP
  - Confirmation of destructive actions
  - Configuration cleanup

- **LaunchDaemon** (`com.dns-changer.daemon.plist`):
  - Automatic execution on login
  - Automatic restart on failure
  - stdout and stderr logging
  - Environment configuration

- **Documentation**:
  - Complete README.md with detailed instructions
  - QUICKSTART.md for a quick start
  - CONTRIBUTING.md for contributions
  - CHANGELOG.md (this file)
  - Configuration examples

### Features

- ✅ Compatible with macOS 12.0+
- ✅ Supports Python 3.6+
- ✅ Uses native macOS tools (networksetup)
- ✅ No external dependencies
- ✅ Open source and auditable
- ✅ Complete logging
- ✅ Easy installation and uninstallation

### Security

- Automatic sudoers configuration
- Execution without permanent privileges
- Input validation
- Robust error handling

---

## [Planned]

### Next Versions

- [ ] Graphical User Interface (GUI)
- [ ] Support for custom DNS profiles
- [ ] Homebrew integration
- [ ] M1/M2 support (arm64) - already works
- [ ] System notifications
- [ ] Usage statistics
- [ ] Support for multiple simultaneous interfaces
- [ ] VPN integration
- [ ] Automated tests
- [ ] CI/CD pipeline

---

## Compatibility Notes

### Supported Versions

- macOS 12.0 (Monterey) ✅
- macOS 13.0 (Ventura) ✅
- macOS 14.0 (Sonoma) ✅
- macOS 15.0 (Sequoia) ✅

### Minimum Requirements

- Python 3.6+
- Bash 3.2+
- Administrator access

---

## Known Issues

### Version 1.0.0

1.  **VPN can override DNS**: Some VPN clients change DNS automatically
2.  **System Integrity Protection (SIP)**: May block certain operations
3.  **Multiple interfaces**: Requires separate instances for each interface

---

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution instructions.

---

## License

This project is licensed under the GPL-3.0 - see the [LICENSE](LICENSE) file for details.

---

## Authors

- **macOS Adaptation**: DNS Changer Eye Contributors
- **Original Project**: BullsEye0 (Jolanda de Koff)

---

## Acknowledgments

- BullsEye0 for the original DNS Changer Eye project
- The macOS community for feedback and suggestions
- All contributors

---

**Last updated**: 2026-02-06
