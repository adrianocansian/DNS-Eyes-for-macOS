#!/bin/bash

################################################################################
# DNS Changer Eye - macOS Sequoia Edition
# Script de Desinstalação
################################################################################

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="$HOME/.dns_changer"
DAEMON_DIR="$HOME/Library/LaunchAgents"
DAEMON_NAME="com.dns-changer.daemon"
DAEMON_PLIST="$DAEMON_DIR/$DAEMON_NAME.plist"
SCRIPT_NAME="dns_changer.py"
SCRIPT_PATH="$INSTALL_DIR/$SCRIPT_NAME"

################################################################################
# FUNÇÕES
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║     DNS Changer Eye - Desinstalação                        ║"
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
        read -p "$(echo -e ${YELLOW}$prompt${NC}) (s/n) " response
        case "$response" in
            [sS][iI]|[sS])
                return 0
                ;;
            [nN][aA][oO]|[nN])
                return 1
                ;;
            *)
                echo "Por favor, responda 's' ou 'n'"
                ;;
        esac
    done
}

unload_daemon() {
    print_info "Descarregando daemon..."
    
    if [ -f "$DAEMON_PLIST" ]; then
        if launchctl list | grep -q "$DAEMON_NAME"; then
            launchctl unload "$DAEMON_PLIST" 2>/dev/null || true
            sleep 2
            print_success "Daemon descarregado"
        else
            print_info "Daemon não estava carregado"
        fi
    else
        print_warning "Arquivo de daemon não encontrado"
    fi
}

remove_script() {
    print_info "Removendo script principal..."
    
    if [ -f "$SCRIPT_PATH" ]; then
        sudo rm -f "$SCRIPT_PATH"
        print_success "Script removido"
    else
        print_warning "Script não encontrado em $SCRIPT_PATH"
    fi
}

remove_sudoers() {
    print_info "Removendo configuração do sudoers..."
    
    if [ -f "/etc/sudoers.d/dns_changer" ]; then
        sudo rm -f "/etc/sudoers.d/dns_changer"
        print_success "Sudoers removido"
    else
        print_warning "Arquivo sudoers não encontrado"
    fi
}

remove_daemon_plist() {
    print_info "Removendo arquivo de daemon..."
    
    if [ -f "$DAEMON_PLIST" ]; then
        rm -f "$DAEMON_PLIST"
        print_success "Arquivo de daemon removido"
    else
        print_warning "Arquivo de daemon não encontrado"
    fi
}

remove_config_dir() {
    print_info "Removendo diretório de configuração..."
    
    if [ -d "$CONFIG_DIR" ]; then
        rm -rf "$CONFIG_DIR"
        print_success "Diretório de configuração removido"
    else
        print_warning "Diretório de configuração não encontrado"
    fi
}

reset_dns() {
    print_info "Resetando DNS para DHCP automático..."
    
    # Detectar interface ativa
    INTERFACE=$(route get default 2>/dev/null | grep 'interface:' | awk '{print $2}' || echo "Wi-Fi")
    
    if sudo networksetup -setdnsservers "$INTERFACE" Empty 2>/dev/null; then
        print_success "DNS resetado para DHCP automático"
    else
        print_warning "Não foi possível resetar DNS automaticamente"
        echo "Execute manualmente: sudo networksetup -setdnsservers $INTERFACE Empty"
    fi
}

print_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Desinstalação Concluída com Sucesso!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "O DNS Changer foi completamente removido do seu sistema."
    echo ""
}

################################################################################
# EXECUÇÃO PRINCIPAL
################################################################################

main() {
    print_header
    
    echo ""
    print_warning "Você está prestes a desinstalar o DNS Changer"
    echo ""
    
    if ! confirm "Deseja continuar com a desinstalação?"; then
        print_info "Desinstalação cancelada"
        exit 0
    fi
    
    echo ""
    
    unload_daemon
    echo ""
    
    if confirm "Deseja resetar o DNS para DHCP automático?"; then
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

# Executar
main
