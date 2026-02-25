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
    echo "║     DNS Changer Eye - Uninstallation                       ║"
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

confirm() {
    local prompt="$1"
    local response
    
    while true; do
        read -r -p "$(echo -e "${YELLOW}${prompt}${NC}") (y/n) " response
        case "$response" in
            [yY][eE][sS]|[yY])
                return 0
                ;;
            [nN][oO]|[nN])
                return 1
                ;;
            *)
                echo "Please answer 'y' or 'n'"
                ;;
        esac
    done
}

unload_daemon() {
    print_info "Unloading daemon..."
    
    if [ -f "$DAEMON_PLIST" ]; then
        if launchctl list | grep -q "$DAEMON_NAME"; then
            launchctl unload "$DAEMON_PLIST" 2>/dev/null || true
            sleep 2
            print_success "Daemon unloaded"
        else
            print_info "Daemon was not loaded"
        fi
    else
        print_warning "Daemon file not found"
    fi
}

remove_script() {
    print_info "Removing main script..."
    
    if [ -f "$SCRIPT_PATH" ]; then
        sudo rm -f "$SCRIPT_PATH"
        print_success "Script removed"
    else
        print_warning "Script not found at $SCRIPT_PATH"
    fi
}

remove_sudoers() {
    print_info "Removing sudoers configuration..."
    
    if [ -f "/etc/sudoers.d/dns_changer" ]; then
        sudo rm -f "/etc/sudoers.d/dns_changer"
        print_success "Sudoers file removed"
    else
        print_warning "Sudoers file not found"
    fi
}

remove_daemon_plist() {
    print_info "Removing daemon file..."
    
    if [ -f "$DAEMON_PLIST" ]; then
        rm -f "$DAEMON_PLIST"
        print_success "Daemon file removed"
    else
        print_warning "Daemon file not found"
    fi
}

remove_config_dir() {
    print_info "Removing configuration directory..."
    
    if [ -d "$CONFIG_DIR" ]; then
        rm -rf "$CONFIG_DIR"
        print_success "Configuration directory removed"
    else
        print_warning "Configuration directory not found"
    fi
}

reset_dns() {
    print_info "Resetting DNS to automatic DHCP..."
    
    # Detect active interface
    INTERFACE=$(route get default 2>/dev/null | grep 'interface:' | awk '{print $2}' || echo "Wi-Fi")
    
    if sudo networksetup -setdnsservers "$INTERFACE" Empty 2>/dev/null; then
        print_success "DNS reset to automatic DHCP"
    else
        print_warning "Could not reset DNS automatically"
        echo "Run manually: sudo networksetup -setdnsservers $INTERFACE Empty"
    fi
}

print_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Uninstallation Completed Successfully!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "DNS Changer has been completely removed from your system."
    echo ""
}

################################################################################
# MAIN EXECUTION
################################################################################

main() {
    print_header
    
    echo ""
    print_warning "You are about to uninstall DNS Changer"
    echo ""
    
    if ! confirm "Do you want to continue with the uninstallation?"; then
        print_info "Uninstallation cancelled"
        exit 0
    fi
    
    echo ""
    
    unload_daemon
    echo ""
    
    if confirm "Do you want to reset DNS to automatic DHCP?"; then
        reset_dns
        echo ""
    fi
    
    remove_script
    echo ""
    
    remove_sudoers
    echo ""
    
    remove_daemon_plist
    echo ""
    
    remove_config_dir
    echo ""
    
    print_summary
}

# Execute
main
