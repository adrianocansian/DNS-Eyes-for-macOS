#!/bin/bash

################################################################################
# DNS Changer Eye - macOS Sequoia Edition
# Uninstallation Script
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# FIX #10/#11: Paths now match exactly what install.sh creates
INSTALL_DIR="/usr/local/bin"
LOG_DIR="/var/log/dns_changer"
DAEMON_DIR="/Library/LaunchDaemons"
DAEMON_NAME="com.dns-changer.daemon"
DAEMON_PLIST="$DAEMON_DIR/$DAEMON_NAME.plist"
SCRIPT_PATH="$INSTALL_DIR/dns_changer.py"

################################################################################
# HELPER FUNCTIONS
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║     DNS Changer Eye - Uninstallation                       ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info()    { echo -e "${BLUE}ℹ $1${NC}"; }

confirm() {
    local prompt="$1"
    local response
    while true; do
        read -r -p "$(echo -e "${YELLOW}${prompt}${NC}") (y/n) " response
        case "$response" in
            [yY][eE][sS]|[yY]) return 0 ;;
            [nN][oO]|[nN])     return 1 ;;
            *) echo "Please answer 'y' or 'n'" ;;
        esac
    done
}

################################################################################
# STEP FUNCTIONS
################################################################################

check_sudo() {
    print_info "Checking administrator privileges..."
    if ! sudo -n true 2>/dev/null; then
        print_warning "Administrator password required. You may be prompted."
        sudo -v
    fi
    # Keep sudo token alive for the duration of the script
    (while true; do sudo -n true; sleep 50; done) &
    SUDO_KEEPALIVE_PID=$!
    trap 'kill "$SUDO_KEEPALIVE_PID" 2>/dev/null' EXIT
    print_success "Administrator privileges confirmed"
}

unload_daemon() {
    print_info "Unloading daemon..."

    # FIX #13: Use modern launchctl bootout API and with sudo (LaunchDaemon = system scope)
    if sudo launchctl list 2>/dev/null | grep -q "$DAEMON_NAME"; then
        sudo launchctl bootout system "$DAEMON_PLIST" 2>/dev/null || true
        sleep 2
        print_success "Daemon unloaded"
    else
        print_info "Daemon was not running"
    fi
}

remove_daemon_plist() {
    print_info "Removing LaunchDaemon plist..."

    if [ -f "$DAEMON_PLIST" ]; then
        # FIX #12: Requires sudo — /Library/LaunchDaemons/ is root-owned
        sudo rm -f "$DAEMON_PLIST"
        print_success "LaunchDaemon plist removed: $DAEMON_PLIST"
    else
        print_warning "LaunchDaemon plist not found at $DAEMON_PLIST"
    fi
}

remove_script() {
    print_info "Removing main script..."

    if [ -f "$SCRIPT_PATH" ]; then
        sudo rm -f "$SCRIPT_PATH"
        print_success "Script removed: $SCRIPT_PATH"
    else
        print_warning "Script not found at $SCRIPT_PATH"
    fi
}

remove_sudoers() {
    print_info "Checking for legacy sudoers configuration..."

    # This file was created by older versions of install.sh.
    # The current version uses a LaunchDaemon (root) and no longer needs sudoers.
    if [ -f "/etc/sudoers.d/dns_changer" ]; then
        sudo rm -f "/etc/sudoers.d/dns_changer"
        print_success "Legacy sudoers file removed"
    else
        print_info "No sudoers file found (expected for current version)"
    fi
}

reset_dns() {
    print_info "Resetting DNS to automatic DHCP..."

    # FIX #14: networksetup expects a *service name* (e.g. "Wi-Fi", "Ethernet"),
    # NOT a device name (e.g. "en0"). Use -listallnetworkservices to get the
    # correct name, skipping disabled services (prefixed with '*').
    local reset_ok=false

    while IFS= read -r service; do
        # Skip header line and disabled services
        [[ "$service" == "*"* ]] && continue
        [[ -z "$service" ]] && continue

        if sudo networksetup -setdnsservers "$service" Empty 2>/dev/null; then
            print_success "DNS reset to DHCP on: $service"
            reset_ok=true
        fi
    done < <(networksetup -listallnetworkservices 2>/dev/null | tail -n +2)

    if ! $reset_ok; then
        print_warning "Could not reset DNS automatically."
        echo "  Run manually for each interface:"
        echo "  sudo networksetup -setdnsservers \"Wi-Fi\" Empty"
        echo "  sudo networksetup -setdnsservers \"Ethernet\" Empty"
    fi
}

remove_log_directory() {
    print_info "Removing log directory..."

    # FIX #11: Remove the actual log directory (/var/log/dns_changer), not ~/.dns_changer
    if [ -d "$LOG_DIR" ]; then
        sudo rm -rf "$LOG_DIR"
        print_success "Log directory removed: $LOG_DIR"
    else
        print_warning "Log directory not found at $LOG_DIR"
    fi

    # Also clean up legacy user-level directory if it still exists from an old install
    LEGACY_DIR="$HOME/.dns_changer"
    if [ -d "$LEGACY_DIR" ]; then
        rm -rf "$LEGACY_DIR"
        print_success "Legacy config directory removed: $LEGACY_DIR"
    fi
}

print_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Uninstallation Completed Successfully!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "DNS Changer Eye has been completely removed from your system."
    echo ""
}

################################################################################
# MAIN
################################################################################

main() {
    print_header
    echo ""
    print_warning "You are about to uninstall DNS Changer Eye."
    echo ""

    if ! confirm "Do you want to continue with the uninstallation?"; then
        print_info "Uninstallation cancelled."
        exit 0
    fi

    echo ""

    check_sudo
    echo ""

    unload_daemon
    echo ""

    if confirm "Reset DNS to automatic DHCP on all active interfaces?"; then
        reset_dns
        echo ""
    fi

    remove_daemon_plist
    echo ""

    remove_script
    echo ""

    remove_sudoers
    echo ""

    remove_log_directory
    echo ""

    print_summary
}

main
