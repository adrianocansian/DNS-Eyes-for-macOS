# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-02-06

### Adicionado

- **Script Principal** (`dns_changer.py`):
  - Rotação automática de DNS com 25+ servidores públicos
  - Detecção automática de interface de rede
  - Validação de endereços IP
  - Logging completo com arquivo de log
  - Tratamento de sinais para encerramento gracioso
  - Suporte a múltiplas opções de linha de comando

- **Instalador** (`install.sh`):
  - Instalação automatizada com verificação de requisitos
  - Detecção de versão do macOS
  - Configuração automática de sudoers
  - Criação de LaunchAgent para execução automática
  - Validação de privilégios de administrador

- **Desinstalador** (`uninstall.sh`):
  - Remoção completa de todos os arquivos
  - Reset automático de DNS para DHCP
  - Confirmação de ações destrutivas
  - Limpeza de configurações

- **LaunchDaemon** (`com.dns-changer.daemon.plist`):
  - Execução automática ao fazer login
  - Reinicialização automática em caso de falha
  - Logging de stdout e stderr
  - Configuração de ambiente

- **Documentação**:
  - README.md completo com instruções detalhadas
  - QUICKSTART.md para início rápido
  - CONTRIBUTING.md para contribuições
  - CHANGELOG.md (este arquivo)
  - Exemplos de configuração

### Características

- ✅ Compatível com macOS 12.0+
- ✅ Suporta Python 3.6+
- ✅ Usa ferramentas nativas do macOS (networksetup)
- ✅ Sem dependências externas
- ✅ Código aberto e auditável
- ✅ Logging completo
- ✅ Fácil instalação e desinstalação

### Segurança

- Configuração automática de sudoers
- Execução sem privilégios permanentes
- Validação de entrada
- Tratamento de erros robusto

---

## [Planejado]

### Próximas Versões

- [ ] Interface gráfica (GUI)
- [ ] Suporte a perfis de DNS customizados
- [ ] Integração com Homebrew
- [ ] Suporte a M1/M2 (arm64) - já funciona
- [ ] Notificações do sistema
- [ ] Estatísticas de uso
- [ ] Suporte a múltiplas interfaces simultâneas
- [ ] Integração com VPN
- [ ] Testes automatizados
- [ ] CI/CD pipeline

---

## Notas de Compatibilidade

### Versões Suportadas

- macOS 12.0 (Monterey) ✅
- macOS 13.0 (Ventura) ✅
- macOS 14.0 (Sonoma) ✅
- macOS 15.0 (Sequoia) ✅

### Requisitos Mínimos

- Python 3.6+
- Bash 3.2+
- Acesso de administrador

---

## Problemas Conhecidos

### Versão 1.0.0

1. **VPN pode sobrescrever DNS**: Alguns clientes VPN alteram DNS automaticamente
2. **System Integrity Protection (SIP)**: Pode bloquear certas operações
3. **Múltiplas interfaces**: Requer instâncias separadas para cada interface

---

## Como Contribuir

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para instruções de contribuição.

---

## Licença

Este projeto é licenciado sob a GPL-3.0 - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## Autores

- **Adaptação para macOS**: DNS Changer Eye Contributors
- **Projeto Original**: BullsEye0 (Jolanda de Koff)

---

## Agradecimentos

- BullsEye0 pelo projeto original DNS Changer Eye
- Comunidade macOS por feedback e sugestões
- Todos os contribuidores

---

**Última atualização**: 2026-02-06
