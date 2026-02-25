#!/bin/bash

################################################################################
# DNS Changer Eye - macOS Sequoia Edition
# Automated Installation Script
#
# This script installs and configures the DNS Changer for automatic execution
# Requires macOS 12.0 or higher
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Settings
INSTALL_DIR="/usr/local/bin"
LOG_DIR="/var/log/dns_changer"
# FIX #3/#7: LaunchDaemon requires root — never write here without sudo
DAEMON_DIR="/Library/LaunchDaemons"
DAEMON_NAME="com.dns-changer.daemon"
DAEMON_PLIST="$DAEMON_DIR/$DAEMON_NAME.plist"
SCRIPT_NAME="dns_changer.py"
SCRIPT_PATH="$INSTALL_DIR/$SCRIPT_NAME"

################################################################################
# HELPER FUNCTIONS
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║     DNS Changer Eye - macOS Sequoia Installation           ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info()    { echo -e "${BLUE}ℹ $1${NC}"; }

################################################################################
# STEP FUNCTIONS
################################################################################

check_requirements() {
    print_info "Checking requirements..."

    # Check macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script requires macOS"
        exit 1
    fi

    # Check macOS version (must be 12+)
    MACOS_VERSION=$(sw_vers -productVersion | cut -d. -f1)
    if [ "$MACOS_VERSION" -lt 12 ]; then
        print_error "macOS 12.0 or higher is required (detected: $MACOS_VERSION)"
        exit 1
    fi
    print_success "macOS $MACOS_VERSION detected"

    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Install it via Homebrew: brew install python3"
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"

    # Check networksetup
    if ! command -v networksetup &> /dev/null; then
        print_error "networksetup not found. This tool is required and ships with macOS."
        exit 1
    fi
    print_success "networksetup available"

    # FIX #8: Verify dns_changer.py exists and has the expected shebang
    if [ ! -f "$SCRIPT_NAME" ]; then
        print_error "File '$SCRIPT_NAME' not found in the current directory"
        exit 1
    fi
    if ! head -1 "$SCRIPT_NAME" | grep -q "python3"; then
        print_error "'$SCRIPT_NAME' does not appear to be a valid Python 3 script (missing shebang)"
        exit 1
    fi
    print_success "$SCRIPT_NAME integrity check passed"
}

check_sudo() {
    print_info "Checking administrator privileges..."

    if ! sudo -n true 2>/dev/null; then
        print_warning "Administrator password required. You may be prompted."
        sudo -v
    fi

    # FIX #6: Keep sudo token alive in the background for the duration of the script
    # This prevents mid-install password prompts on slow systems
    (while true; do sudo -n true; sleep 50; done) &
    SUDO_KEEPALIVE_PID=$!
    # Ensure the background job is killed when the script exits
    trap 'kill "$SUDO_KEEPALIVE_PID" 2>/dev/null' EXIT

    print_success "Administrator privileges confirmed"
}

# FIX #1: Create log directory BEFORE the plist that references it
create_log_directory() {
    print_info "Creating log directory with secure permissions..."

    sudo mkdir -p "$LOG_DIR"
    sudo chown root:admin "$LOG_DIR"
    # 750: root can rwx, admin group can r-x, others have no access
    sudo chmod 750 "$LOG_DIR"

    # FIX #2: Removed incorrect "sudo chmod u+s" (setuid on directories is a no-op on macOS)
    # If you want new files to inherit the group, use g+s instead:
    # sudo chmod g+s "$LOG_DIR"
    # We omit this here as dns_changer.py manages its own file permissions explicitly.

    print_success "Log directory created at $LOG_DIR (permissions: 750)"
}

copy_script() {
    print_info "Installing main script..."

    sudo cp "$SCRIPT_NAME" "$SCRIPT_PATH"
    sudo chmod 755 "$SCRIPT_PATH"
    sudo chown root:wheel "$SCRIPT_PATH"

    print_success "Script installed at $SCRIPT_PATH"
}

create_daemon_plist() {
    print_info "Creating LaunchDaemon (runs as root — no sudoers needed)..."

    # FIX #3/#7: Write to a temp file first, then move with sudo into the protected directory.
    # Direct "cat > /Library/LaunchDaemons/..." would fail without root.
    TMP_PLIST=$(mktemp /tmp/dns-changer-plist.XXXXXX)

    cat > "$TMP_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dns-changer.daemon</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/dns_changer.py</string>
        <string>--interval</string>
        <string>300</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/var/log/dns_changer/daemon.log</string>

    <key>StandardErrorPath</key>
    <string>/var/log/dns_changer/daemon_error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

    sudo mv "$TMP_PLIST" "$DAEMON_PLIST"
    sudo chown root:wheel "$DAEMON_PLIST"
    sudo chmod 644 "$DAEMON_PLIST"

    print_success "LaunchDaemon plist created at $DAEMON_PLIST"
}

load_daemon() {
    print_info "Loading daemon..."

    # FIX #5: Use modern launchctl bootstrap/bootout API (macOS 11+)
    # "launchctl load" is deprecated since macOS Big Sur
    if sudo launchctl list | grep -q "$DAEMON_NAME"; then
        print_info "Daemon already loaded — reloading..."
        sudo launchctl bootout system "$DAEMON_PLIST" 2>/dev/null || true
        sleep 1
    fi

    sudo launchctl bootstrap system "$DAEMON_PLIST"
    sleep 2

    if sudo launchctl list | grep -q "$DAEMON_NAME"; then
        print_success "Daemon loaded and running"
    else
        print_warning "Daemon registered but may not have started yet. Check logs:"
        print_warning "  tail -f $LOG_DIR/daemon.log"
    fi
}

# FIX #4: Uninstall script now references correct paths matching this installer
create_uninstall_script() {
    print_info "Creating uninstall script..."

    sudo tee "$LOG_DIR/uninstall.sh" > /dev/null << EOF
#!/bin/bash
# DNS Changer Eye - Uninstall Script
# Auto-generated by install.sh on $(date)

set -e

DAEMON_PLIST="/Library/LaunchDaemons/com.dns-changer.daemon.plist"
SCRIPT_PATH="/usr/local/bin/dns_changer.py"
LOG_DIR="/var/log/dns_changer"

echo "Uninstalling DNS Changer Eye..."

# Unload daemon using modern API
if sudo launchctl list | grep -q "com.dns-changer.daemon"; then
    sudo launchctl bootout system "\$DAEMON_PLIST" 2>/dev/null || true
    echo "✓ Daemon unloaded"
else
    echo "⚠ Daemon was not running"
fi

# Remove plist
sudo rm -f "\$DAEMON_PLIST"
echo "✓ LaunchDaemon plist removed"

# Remove main script
sudo rm -f "\$SCRIPT_PATH"
echo "✓ Main script removed"

# Reset DNS to DHCP on detected interface (using service name, not device name)
IFACE=\$(networksetup -listallnetworkservices 2>/dev/null | grep -v '^\*' | head -1)
if [ -n "\$IFACE" ]; then
    sudo networksetup -setdnsservers "\$IFACE" Empty 2>/dev/null && echo "✓ DNS reset to DHCP on \$IFACE"
fi

# Remove log directory
sudo rm -rf "\$LOG_DIR"
echo "✓ Log directory removed"

echo ""
echo "DNS Changer Eye has been completely uninstalled."
EOF

    sudo chmod 755 "$LOG_DIR/uninstall.sh"
    sudo chown root:admin "$LOG_DIR/uninstall.sh"

    print_success "Uninstall script created at $LOG_DIR/uninstall.sh"
}

print_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Installation Completed Successfully!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Installation details:"
    echo "  Main script  : $SCRIPT_PATH"
    echo "  Log directory: $LOG_DIR"
    echo "  LaunchDaemon : $DAEMON_PLIST"
    echo ""
    echo "Useful commands:"
    echo "  • Check status : sudo launchctl list | grep dns-changer"
    echo "  • View logs    : tail -f $LOG_DIR/daemon.log"
    echo "  • Stop daemon  : sudo launchctl bootout system $DAEMON_PLIST"
    echo "  • Start daemon : sudo launchctl bootstrap system $DAEMON_PLIST"
    echo "  • Uninstall    : sudo bash $LOG_DIR/uninstall.sh"
    echo ""
    echo "DNS Changer will start automatically at every system boot."
    echo "No sudoers configuration needed — it runs as root via LaunchDaemon."
    echo ""
}

################################################################################
# MAIN
################################################################################

main() {
    print_header
    echo ""
    print_info "Starting DNS Changer for macOS installation..."
    echo ""

    check_requirements
    echo ""

    check_sudo
    echo ""

    # FIX #1: Log directory must exist before the plist that references it
    create_log_directory
    echo ""

    copy_script
    echo ""

    create_daemon_plist
    echo ""

    load_daemon
    echo ""

    create_uninstall_script
    echo ""

    print_summary
}

main
