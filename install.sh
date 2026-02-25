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
CONFIG_DIR="$HOME/.dns_changer"
DAEMON_DIR="$HOME/Library/LaunchAgents"
DAEMON_NAME="com.dns-changer.daemon"
DAEMON_PLIST="$DAEMON_DIR/$DAEMON_NAME.plist"
SCRIPT_NAME="dns_changer.py"
SCRIPT_PATH="$INSTALL_DIR/$SCRIPT_NAME"

################################################################################
# FUNCTIONS
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

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_requirements() {
    print_info "Checking requirements..."

    # Check macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "This script requires macOS"
        exit 1
    fi

    # Check macOS version
    MACOS_VERSION=$(sw_vers -productVersion | cut -d. -f1)
    if [ "$MACOS_VERSION" -lt 12 ]; then
        print_error "macOS 12.0 or higher is required (you have: $MACOS_VERSION)"
        exit 1
    fi
    print_success "macOS $MACOS_VERSION detected"

    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"

    # Check networksetup
    if ! command -v networksetup &> /dev/null; then
        print_error "networksetup not found"
        exit 1
    fi
    print_success "networksetup available"
}

check_sudo() {
    print_info "Checking administrator privileges..."

    if ! sudo -n true 2>/dev/null; then
        print_warning "You will be prompted to enter your password for administrator privileges"
        sudo -v
    fi
    print_success "Administrator privileges confirmed"
}

create_directories() {
    print_info "Creating directories..."

    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DAEMON_DIR"

    print_success "Directories created"
}

copy_script() {
    print_info "Installing main script..."

    if [ ! -f "$SCRIPT_NAME" ]; then
        print_error "File $SCRIPT_NAME not found in the current directory"
        exit 1
    fi

    sudo cp "$SCRIPT_NAME" "$SCRIPT_PATH"
    sudo chmod +x "$SCRIPT_PATH"

    print_success "Script installed at $SCRIPT_PATH"
}

create_daemon_plist() {
    print_info "Creating LaunchAgent daemon..."

    cat > "$DAEMON_PLIST" << 'EOF'
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
    <string>__HOME__/.dns_changer/daemon.log</string>

    <key>StandardErrorPath</key>
    <string>__HOME__/.dns_changer/daemon_error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>UserName</key>
    <string>__USER__</string>
</dict>
</plist>
EOF

    # Replace placeholders
    sed -i \'\' "s|__HOME__|$HOME|g" "$DAEMON_PLIST"
    sed -i \'\' "s|__USER__|$USER|g" "$DAEMON_PLIST"

    chmod 644 "$DAEMON_PLIST"

    print_success "LaunchAgent created at $DAEMON_PLIST"
}

setup_sudoers() {
    print_info "Configuring sudoers for passwordless execution..."

    # Create temporary file
    TEMP_SUDOERS=$(mktemp)

    # Add entry for networksetup
    echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/networksetup" >> "$TEMP_SUDOERS"

    # Check syntax
    if ! sudo visudo -c -f "$TEMP_SUDOERS" 2>/dev/null; then
        print_error "Error in sudoers configuration"
        rm "$TEMP_SUDOERS"
        return 1
    fi

    # Apply configuration
    sudo bash -c "cat $TEMP_SUDOERS >> /etc/sudoers.d/dns_changer"
    sudo chmod 440 /etc/sudoers.d/dns_changer

    rm "$TEMP_SUDOERS"

    print_success "Sudoers configured"
}

load_daemon() {
    print_info "Loading daemon..."

    # Unload if already loaded
    launchctl unload "$DAEMON_PLIST" 2>/dev/null || true

    # Load daemon
    launchctl load "$DAEMON_PLIST"

    sleep 2

    # Check if it\'s running
    if launchctl list | grep -q "$DAEMON_NAME"; then
        print_success "Daemon loaded and running"
    else
        print_warning "Daemon loaded but may not be running yet"
    fi
}

create_uninstall_script() {
    print_info "Creating uninstall script..."

    cat > "$CONFIG_DIR/uninstall.sh" << 'EOF'
#!/bin/bash

echo "Uninstalling DNS Changer..."

# Unload daemon
launchctl unload "$HOME/Library/LaunchAgents/com.dns-changer.daemon.plist" 2>/dev/null || true

# Remove files
sudo rm -f /usr/local/bin/dns_changer.py
sudo rm -f /etc/sudoers.d/dns_changer
rm -rf "$HOME/.dns_changer"
rm -f "$HOME/Library/LaunchAgents/com.dns-changer.daemon.plist"

echo "DNS Changer uninstalled successfully"
EOF

    chmod +x "$CONFIG_DIR/uninstall.sh"

    print_success "Uninstall script created at $CONFIG_DIR/uninstall.sh"
}

print_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Installation Completed Successfully!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Installation Information:"
    echo "  Main Script: $SCRIPT_PATH"
    echo "  Config Directory: $CONFIG_DIR"
    echo "  LaunchAgent: $DAEMON_PLIST"
    echo ""
    echo "Useful Commands:"
    echo "  • Check status: launchctl list | grep dns-changer"
    echo "  • View logs: tail -f $CONFIG_DIR/daemon.log"
    echo "  • Stop daemon: launchctl unload $DAEMON_PLIST"
    echo "  • Start daemon: launchctl load $DAEMON_PLIST"
    echo "  • Uninstall: bash $CONFIG_DIR/uninstall.sh"
    echo ""
    echo "The DNS Changer will start automatically the next time you log in"
    echo ""
}

################################################################################
# MAIN EXECUTION
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

    create_directories
    echo ""

    copy_script
    echo ""

    create_daemon_plist
    echo ""

    setup_sudoers
    echo ""

    load_daemon
    echo ""

    create_uninstall_script
    echo ""

    print_summary
}

# Execute
main
