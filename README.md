# DNS Changer Eye - macOS Sequoia Edition

Uma solução completa e automatizada para rotação contínua de servidores DNS no macOS Sequoia, com foco em privacidade, segurança e facilidade de uso.

## 📋 Índice

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Uso](#uso)
- [Configuração](#configuração)
- [Troubleshooting](#troubleshooting)
- [Desinstalação](#desinstalação)
- [Segurança](#segurança)
- [FAQ](#faq)

---

## ✨ Características

### Funcionalidades Principais

- **Rotação Automática de DNS**: Alterna entre 25+ servidores DNS confiáveis a cada 5 minutos (configurável)
- **Execução Automática**: Inicia automaticamente ao fazer login via LaunchDaemon
- **Detecção Inteligente**: Detecta automaticamente a interface de rede ativa
- **Logging Completo**: Registra todas as alterações e erros em arquivo de log
- **Interface Simples**: Linha de comando intuitiva com múltiplas opções
- **Segurança**: Configuração automática de sudoers para execução sem senha
- **Reversível**: Fácil desinstalação com reset automático de DNS

### Servidores DNS Suportados

O script inclui uma lista curada de 25+ servidores DNS públicos e confiáveis:

- **Cloudflare**: 1.1.1.1, 1.0.0.1
- **Quad9**: 9.9.9.9, 149.112.112.112
- **OpenDNS**: 208.67.222.222, 208.67.220.220
- **Google**: 8.8.8.8, 8.8.4.4
- **Verisign**: 64.6.64.6, 64.6.65.6
- E mais 15+ servidores

---

## 🔧 Requisitos

### Sistema Operacional
- **macOS 12.0 ou superior** (testado em Sequoia 15.0+)
- Acesso de administrador

### Software
- **Python 3.6+** (pré-instalado no macOS 12+)
- **Bash 3.2+** (padrão no macOS)

### Permissões
- Privilégios de `sudo` (será solicitado durante a instalação)

---

## 📦 Instalação

### Método 1: Instalação Automática (Recomendado)

1. **Clone ou baixe o repositório**:
```bash
git clone https://github.com/seu-usuario/dns-changer-macos.git
cd dns-changer-macos
```

2. **Execute o instalador**:
```bash
chmod +x install.sh
./install.sh
```

3. **Siga as instruções** na tela. O script solicitará sua senha de administrador.

4. **Pronto!** O DNS Changer iniciará automaticamente.

### Método 2: Instalação Manual

Se preferir instalar manualmente:

```bash
# 1. Copiar script principal
sudo cp dns_changer.py /usr/local/bin/
sudo chmod +x /usr/local/bin/dns_changer.py

# 2. Criar diretório de configuração
mkdir -p ~/.dns_changer

# 3. Configurar sudoers
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/networksetup" | sudo tee /etc/sudoers.d/dns_changer

# 4. Copiar LaunchAgent
cp com.dns-changer.daemon.plist ~/Library/LaunchAgents/
sed -i '' "s|__HOME__|$HOME|g" ~/Library/LaunchAgents/com.dns-changer.daemon.plist
sed -i '' "s|__USER__|$USER|g" ~/Library/LaunchAgents/com.dns-changer.daemon.plist

# 5. Carregar daemon
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

---

## 🚀 Uso

### Modo Contínuo (Padrão)

Inicia a rotação automática de DNS:

```bash
dns_changer.py
```

Pressione `Ctrl+C` para parar.

### Opções de Linha de Comando

```bash
# Rotacionar DNS uma única vez
dns_changer.py --once

# Especificar interface de rede
dns_changer.py --interface Ethernet

# Alterar intervalo de rotação (em segundos)
dns_changer.py --interval 600

# Obter configuração de DNS atual
dns_changer.py --get

# Definir DNS específicos
dns_changer.py --set 1.1.1.1 1.0.0.1

# Resetar DNS para DHCP automático
dns_changer.py --reset

# Exibir ajuda
dns_changer.py --help
```

### Exemplos Práticos

```bash
# Rotacionar a cada 10 minutos
dns_changer.py --interval 600

# Usar apenas Ethernet
dns_changer.py --interface Ethernet --interval 300

# Definir DNS do Cloudflare
dns_changer.py --set 1.1.1.1 1.0.0.1

# Verificar DNS atual
dns_changer.py --get

# Resetar para DHCP
dns_changer.py --reset
```

---

## ⚙️ Configuração

### Alterar Intervalo de Rotação

Edite o arquivo LaunchAgent:

```bash
nano ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

Procure por:
```xml
<string>300</string>
```

Altere `300` para o intervalo desejado em segundos:
- `300` = 5 minutos (padrão)
- `600` = 10 minutos
- `1800` = 30 minutos

Depois recarregue:
```bash
launchctl unload ~/Library/LaunchAgents/com.dns-changer.daemon.plist
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

### Especificar Interface de Rede

Se você tem múltiplas interfaces (Wi-Fi, Ethernet, VPN), pode especificar qual usar:

```bash
# Listar interfaces disponíveis
networksetup -listallnetworkservices

# Usar interface específica
dns_changer.py --interface Ethernet
```

### Adicionar Servidores DNS Customizados

Edite `dns_changer.py` e modifique a lista `DNS_SERVERS`:

```python
DNS_SERVERS = [
    ("1.1.1.1", "1.0.0.1"),      # Seu servidor 1
    ("seu.dns.1", "seu.dns.2"),  # Seu servidor 2
    # ... mais servidores
]
```

---

## 📊 Monitoramento

### Ver Status do Daemon

```bash
# Verificar se está rodando
launchctl list | grep dns-changer

# Ver logs em tempo real
tail -f ~/.dns_changer/daemon.log

# Ver logs de erro
tail -f ~/.dns_changer/daemon_error.log

# Ver todos os logs
log show --predicate 'process == "dns_changer.py"' --last 1h
```

### Verificar DNS Atual

```bash
# Via script
dns_changer.py --get

# Via networksetup
networksetup -getdnsservers Wi-Fi

# Via cat (método tradicional)
cat /etc/resolv.conf
```

---

## 🔧 Troubleshooting

### Problema: "Permissão Negada" ao Executar

**Solução**:
```bash
chmod +x /usr/local/bin/dns_changer.py
```

### Problema: Daemon Não Inicia Automaticamente

**Verificar**:
```bash
# Ver se está carregado
launchctl list | grep dns-changer

# Recarregar
launchctl unload ~/Library/LaunchAgents/com.dns-changer.daemon.plist
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

### Problema: "sudo: networksetup: command not found"

**Solução**: Reconfigurar sudoers:
```bash
echo "$USER ALL=(ALL) NOPASSWD: /usr/sbin/networksetup" | sudo tee /etc/sudoers.d/dns_changer
```

### Problema: DNS Não Muda

**Verificar**:
1. Interface correta: `dns_changer.py --get`
2. Privilégios: `sudo -l | grep networksetup`
3. Logs: `tail -f ~/.dns_changer/daemon.log`

### Problema: VPN Sobrescreve DNS

**Solução**: Alguns clientes VPN sobrescrevem DNS. Você pode:
- Desabilitar VPN temporariamente
- Usar DNS do VPN
- Reconfigurar após conectar VPN

---

## 🗑️ Desinstalação

### Método Automático

```bash
bash ~/.dns_changer/uninstall.sh
```

### Método Manual

```bash
# 1. Descarregar daemon
launchctl unload ~/Library/LaunchAgents/com.dns-changer.daemon.plist

# 2. Remover script
sudo rm /usr/local/bin/dns_changer.py

# 3. Remover sudoers
sudo rm /etc/sudoers.d/dns_changer

# 4. Remover arquivo de daemon
rm ~/Library/LaunchAgents/com.dns-changer.daemon.plist

# 5. Remover diretório de configuração
rm -rf ~/.dns_changer

# 6. Resetar DNS (opcional)
sudo networksetup -setdnsservers Wi-Fi Empty
```

---

## 🔒 Segurança

### Considerações de Segurança

1. **Privilégios de Root**: O script requer `sudo` para alterar DNS. Isso é necessário e seguro.

2. **Sudoers sem Senha**: A instalação configura `sudo` para executar `networksetup` sem senha. Isso é seguro porque:
   - Limitado apenas a `networksetup`
   - Requer que o usuário já esteja logado
   - O arquivo `/etc/sudoers.d/dns_changer` tem permissões restritas (440)

3. **Logs**: Os logs contêm informações de DNS alterados. Verifique permissões:
   ```bash
   ls -la ~/.dns_changer/
   ```

4. **LaunchDaemon**: Executa com privilégios do usuário (não root), aumentando segurança.

5. **Código Aberto**: Todo o código é transparente e pode ser auditado.

### Boas Práticas

- Mantenha o script atualizado
- Revise os servidores DNS periodicamente
- Monitore os logs regularmente
- Use em redes confiáveis
- Considere usar VPN + DNS Changer para máxima privacidade

---

## ❓ FAQ

### P: O DNS Changer é seguro?
**R**: Sim. O script usa apenas ferramentas nativas do macOS (`networksetup`) e não requer root permanente.

### P: Qual é o impacto de performance?
**R**: Mínimo. O script usa ~5-10MB de memória e consome CPU apenas durante rotações.

### P: Posso usar com VPN?
**R**: Sim, mas a VPN pode sobrescrever as configurações de DNS. Nesse caso, use o DNS da VPN.

### P: Como saber se está funcionando?
**R**: Execute `dns_changer.py --get` para ver o DNS atual, ou verifique os logs.

### P: Posso alterar o intervalo de rotação?
**R**: Sim, edite o arquivo `.plist` ou use `--interval` na linha de comando.

### P: O que acontece se desinstalar?
**R**: O script remove todos os arquivos e reseta o DNS para DHCP automático.

### P: Funciona em redes corporativas?
**R**: Pode haver restrições. Consulte seu administrador de rede.

### P: Posso usar múltiplas interfaces?
**R**: Sim, execute instâncias separadas com `--interface` diferente.

### P: Qual é o melhor intervalo de rotação?
**R**: 5-10 minutos (300-600 segundos) é recomendado. Intervalos muito curtos podem causar instabilidade.

---

## 📝 Licença

Este projeto é baseado em DNS Changer Eye (BullsEye0) e mantém compatibilidade com GPL-3.0.

---

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique os [Troubleshooting](#troubleshooting)
2. Consulte os logs: `tail -f ~/.dns_changer/daemon.log`
3. Abra uma issue no GitHub

---

## 🎯 Roadmap

- [ ] Interface gráfica (GUI)
- [ ] Suporte a perfis de DNS customizados
- [ ] Integração com Homebrew
- [ ] Suporte a M1/M2 (arm64)
- [ ] Notificações do sistema
- [ ] Estatísticas de uso

---

## 📚 Referências

- [Apple LaunchDaemon Documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchDaemons.html)
- [networksetup Manual](https://ss64.com/osx/networksetup.html)
- [DNS Security Best Practices](https://www.cloudflare.com/learning/dns/dns-security/)

---

**Desenvolvido com ❤️ para macOS Sequoia**

Última atualização: 2026
