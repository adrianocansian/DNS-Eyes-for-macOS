# 🚀 Guia de Início Rápido - DNS Changer Eye macOS

Comece em menos de 5 minutos!

---

## ⚡ Instalação Rápida

### Passo 1: Baixe o Projeto
```bash
git clone https://github.com/seu-usuario/dns-changer-macos.git
cd dns-changer-macos
```

### Passo 2: Execute o Instalador
```bash
chmod +x install.sh
./install.sh
```

Você será solicitado a inserir sua senha de administrador. Isso é necessário para configurar as permissões de DNS.

### Passo 3: Pronto! ✅

O DNS Changer iniciará automaticamente. Você pode verificar se está funcionando:

```bash
dns_changer.py --get
```

---

## 🎮 Comandos Essenciais

### Ver DNS Atual
```bash
dns_changer.py --get
```

### Rotacionar DNS Manualmente
```bash
dns_changer.py --once
```

### Parar o Daemon
```bash
launchctl unload ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

### Iniciar o Daemon
```bash
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

### Ver Logs
```bash
tail -f ~/.dns_changer/daemon.log
```

### Desinstalar
```bash
bash ~/.dns_changer/uninstall.sh
```

---

## ⚙️ Configurações Comuns

### Alterar Intervalo de Rotação

**Cada 10 minutos:**
```bash
dns_changer.py --interval 600
```

**Cada 30 minutos:**
```bash
dns_changer.py --interval 1800
```

### Usar Interface Específica

**Ethernet:**
```bash
dns_changer.py --interface Ethernet
```

**Wi-Fi:**
```bash
dns_changer.py --interface Wi-Fi
```

### Definir DNS Específico

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

## 🔍 Verificação de Status

### Daemon Rodando?
```bash
launchctl list | grep dns-changer
```

Se aparecer algo como:
```
- 0 com.dns-changer.daemon
```

Significa que está rodando! ✅

### DNS Mudou?
```bash
dns_changer.py --get
```

Execute várias vezes (com intervalo de 5 minutos) para ver o DNS mudar.

---

## ❓ Problemas Rápidos

### "Permissão Negada"
```bash
chmod +x /usr/local/bin/dns_changer.py
```

### Daemon Não Inicia
```bash
launchctl load ~/Library/LaunchAgents/com.dns-changer.daemon.plist
```

### Resetar DNS
```bash
dns_changer.py --reset
```

---

## 📖 Próximos Passos

1. **Leia o README completo**: `README.md`
2. **Configure seu intervalo preferido**: Edite o `.plist` ou use `--interval`
3. **Monitore os logs**: `tail -f ~/.dns_changer/daemon.log`
4. **Considere privacidade**: Use com VPN para máxima proteção

---

## 💡 Dicas

- ✅ Deixe rodando em background para máxima privacidade
- ✅ Combine com VPN para segurança extra
- ✅ Monitore logs periodicamente
- ✅ Atualize o script regularmente

---

**Aproveite a privacidade! 🔒**
