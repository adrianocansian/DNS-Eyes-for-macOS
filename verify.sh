#!/bin/bash

################################################################################
# DNS Changer Eye - macOS Sequoia Edition
# File Integrity Verification Script
#
# This script verifies the integrity of critical files before installation.
# It downloads the SHA-256 hashes from the GitHub repository and compares them
# with the local files to protect against supply chain attacks.
#
# Usage: bash verify.sh
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# GitHub repository information
GITHUB_REPO="adrianocansian/macOS-DNS-Eyes"
GITHUB_BRANCH="main"
GITHUB_RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/${GITHUB_BRANCH}"

# Files to verify
FILES_TO_VERIFY=(
    "dns_changer.py"
    "install.sh"
    "uninstall.sh"
    "com.dns-changer.daemon.plist"
)

################################################################################
# FUNCTIONS
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║     DNS Changer Eye - File Integrity Verification          ║"
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

    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed"
        echo "Install it with: brew install curl"
        exit 1
    fi
    print_success "curl is available"

    # Check if shasum is available
    if ! command -v shasum &> /dev/null; then
        print_error "shasum is not available"
        exit 1
    fi
    print_success "shasum is available"
}

download_hashes() {
    print_info "Downloading SHA-256 hashes from GitHub..."

    TEMP_HASHES=$(mktemp)

    if ! curl -s "${GITHUB_RAW_URL}/SHA256SUMS" -o "$TEMP_HASHES"; then
        print_error "Failed to download SHA256SUMS from GitHub"
        rm "$TEMP_HASHES"
        exit 1
    fi

    if [ ! -s "$TEMP_HASHES" ]; then
        print_error "Downloaded SHA256SUMS is empty"
        rm "$TEMP_HASHES"
        exit 1
    fi

    print_success "SHA-256 hashes downloaded successfully"
    echo "$TEMP_HASHES"
}

verify_files() {
    local hashes_file="$1"
    local all_verified=true

    print_info "Verifying file integrity..."
    echo ""

    while IFS= read -r line; do
        if [ -z "$line" ]; then
            continue
        fi

        local expected_hash=$(echo "$line" | awk '{print $1}')
        local filename=$(echo "$line" | awk '{print $2}')

        if [ ! -f "$filename" ]; then
            print_warning "File not found: $filename (skipped)"
            continue
        fi

        local actual_hash=$(shasum -a 256 "$filename" | awk '{print $1}')

        if [ "$expected_hash" = "$actual_hash" ]; then
            print_success "Verified: $filename"
        else
            print_error "VERIFICATION FAILED: $filename"
            echo "  Expected: $expected_hash"
            echo "  Got:      $actual_hash"
            all_verified=false
        fi
    done < "$hashes_file"

    echo ""
    return $([ "$all_verified" = true ] && echo 0 || echo 1)
}

print_summary() {
    local status="$1"

    echo ""
    if [ "$status" -eq 0 ]; then
        echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✓ All files verified successfully!${NC}"
        echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "You can now safely proceed with installation:"
        echo "  sudo bash install.sh"
        echo ""
    else
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}✗ Verification failed!${NC}"
        echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "DO NOT proceed with installation!"
        echo "Possible causes:"
        echo "  1. Files have been modified (supply chain attack?)"
        echo "  2. You are using an outdated version of the files"
        echo "  3. Network error during hash download"
        echo ""
        echo "Please:"
        echo "  1. Re-clone the repository: git clone https://github.com/adrianocansian/macOS-DNS-Eyes.git"
        echo "  2. Run this verification script again"
        echo ""
    fi
}

################################################################################
# MAIN EXECUTION
################################################################################

main() {
    print_header
    echo ""

    check_requirements
    echo ""

    HASHES_FILE=$(download_hashes)
    echo ""

    if verify_files "$HASHES_FILE"; then
        print_summary 0
        rm "$HASHES_FILE"
        exit 0
    else
        print_summary 1
        rm "$HASHES_FILE"
        exit 1
    fi
}

# Execute
main
