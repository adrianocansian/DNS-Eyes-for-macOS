#!/bin/bash

################################################################################
# DNS Changer Eye - macOS Sequoia Edition
# Script de Instalação Automatizado
# 
# Este script instala e configura o DNS Changer para execução automática
# Requer macOS 12.0 ou superior
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
    print_info "Verificando requisitos..."
    
    # Verificar macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "Este script requer macOS"
        exit 1
    fi
    
    # Verificar versão do macOS
    MACOS_VERSION=$(sw_vers -productVersion | cut -d. -f1)
    if [ "$MACOS_VERSION" -lt 12 ]; then
        print_error "macOS 12.0 ou superior é necessário (você tem: $MACOS_VERSION)"
        exit 1
    fi
    print_success "macOS $MACOS_VERSION detectado"
    
    # Verificar Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 não encontrado"
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python $PYTHON_VERSION encontrado"
    
    # Verificar networksetup
    if ! command -v networksetup &> /dev/null; then
        print_error "networksetup não encontrado"
        exit 1
    fi
    print_success "networksetup disponível"
}

check_sudo() {
    print_info "Verificando privilégios de administrador..."
    
    if ! sudo -n true 2>/dev/null; then
        print_warning "Você será solicitado a inserir sua senha para privilégios de administrador"
        sudo -v
    fi
    print_success "Privilégios de administrador confirmados"
}

create_directories() {
    print_info "Criando diretórios..."
    
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DAEMON_DIR"
    
    print_success "Diretórios criados"
}

copy_script() {
    print_info "Instalando script principal..."
    
    if [ ! -f "$SCRIPT_NAME" ]; then
        print_error "Arquivo $SCRIPT_NAME não encontrado no diretório atual"
        exit 1
    fi
    
    sudo cp "$SCRIPT_NAME" "$SCRIPT_PATH"
    sudo chmod +x "$SCRIPT_PATH"
    
    print_success "Script instalado em $SCRIPT_PATH"
}

create_daemon_plist() {
    print_info "Criando LaunchAgent daemon..."
    
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
    
    # Substituir placeholders
    sed -i '' "s|__HOME__|$HOME|g" "$DAEMON_PLIST"
    sed -i '' "s|__USER__|$USER|g" "$DAEMON_PLIST"
    
    chmod 644 "$DAEMON_PLIST"
    
    print_success "LaunchAgent criado em $DAEMON_PLIST"
}

setup_sudoers() {
    print_info "Configurando sudoers para execução sem senha..."
    
    # Criar arquivo temporário
    TEMP_SUDOERS=$(mktemp)
    
    # Adicionar entrada para networksetup
    echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/networksetup" >> "$TEMP_SUDOERS"
    
    # Verificar sintaxe
    if ! sudo visudo -c -f "$TEMP_SUDOERS" 2>/dev/null; then
        print_error "Erro na configuração do sudoers"
        rm "$TEMP_SUDOERS"
        return 1
    fi
    
    # Aplicar configuração
    sudo bash -c "cat $TEMP_SUDOERS >> /etc/sudoers.d/dns_changer"
    sudo chmod 440 /etc/sudoers.d/dns_changer
    
    rm "$TEMP_SUDOERS"
    
    print_success "Sudoers configurado"
}

load_daemon() {
    print_info "Carregando daemon..."
    
    # Descarregar se já estiver carregado
    launchctl unload "$DAEMON_PLIST" 2>/dev/null || true
    
    # Carregar daemon
    launchctl load "$DAEMON_PLIST"
    
    sleep 2
    
    # Verificar se está rodando
    if launchctl list | grep -q "$DAEMON_NAME"; then
        print_success "Daemon carregado e rodando"
    else
        print_warning "Daemon carregado mas pode não estar rodando ainda"
    fi
}

create_uninstall_script() {
    print_info "Criando script de desinstalação..."
    
    cat > "$CONFIG_DIR/uninstall.sh" << 'EOF'
#!/bin/bash

echo "Desinstalando DNS Changer..."

# Descarregar daemon
launchctl unload "$HOME/Library/LaunchAgents/com.dns-changer.daemon.plist" 2>/dev/null || true

# Remover arquivos
sudo rm -f /usr/local/bin/dns_changer.py
sudo rm -f /etc/sudoers.d/dns_changer
rm -rf "$HOME/.dns_changer"
rm -f "$HOME/Library/LaunchAgents/com.dns-changer.daemon.plist"

echo "DNS Changer desinstalado com sucesso"
EOF
    
    chmod +x "$CONFIG_DIR/uninstall.sh"
    
    print_success "Script de desinstalação criado em $CONFIG_DIR/uninstall.sh"
}

print_summary() {
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Instalação Concluída com Sucesso!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Informações da Instalação:"
    echo "  Script Principal: $SCRIPT_PATH"
    echo "  Diretório Config: $CONFIG_DIR"
    echo "  LaunchAgent: $DAEMON_PLIST"
    echo ""
    echo "Comandos Úteis:"
    echo "  • Ver status: launchctl list | grep dns-changer"
    echo "  • Ver logs: tail -f $CONFIG_DIR/daemon.log"
    echo "  • Parar daemon: launchctl unload $DAEMON_PLIST"
    echo "  • Iniciar daemon: launchctl load $DAEMON_PLIST"
    echo "  • Desinstalar: bash $CONFIG_DIR/uninstall.sh"
    echo ""
    echo "O DNS Changer iniciará automaticamente na próxima vez que você fizer login"
    echo ""
}

################################################################################
# EXECUÇÃO PRINCIPAL
################################################################################

main() {
    print_header
    
    echo ""
    print_info "Iniciando instalação do DNS Changer para macOS..."
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

# Executar
main
