## Documentação do Arquivo de Configuração

O arquivo `config.example.json` fornece um exemplo de como customizar o comportamento do DNS Changer Eye. Para utilizá-lo, crie um arquivo chamado `config.json` no mesmo diretório do script `dns_changer.py` e modifique as opções desejadas.

### Estrutura do Arquivo

O arquivo de configuração é dividido em seções:

-   **`general`**: Configurações gerais de operação.
-   **`dns_servers`**: Lista de servidores DNS a serem utilizados.
-   **`security`**: Opções de segurança.
-   **`daemon`**: Configurações do LaunchDaemon.
-   **`logging`**: Opções de log.
-   **`notifications`**: Configurações de notificação (ainda não implementado).

### Opções de Configuração

#### `general`

| Chave | Tipo | Descrição | Padrão |
|---|---|---|---|
| `enabled` | booleano | Habilita ou desabilita o script. | `true` |
| `interval` | inteiro | Intervalo de rotação em segundos. | `300` |
| `interface` | string | Interface de rede a ser utilizada. `auto` para detecção automática. | `auto` |
| `log_level` | string | Nível de log (`INFO`, `DEBUG`, `WARNING`, `ERROR`). | `INFO` |

#### `dns_servers`

Esta seção contém uma lista de servidores DNS. Você pode adicionar, remover ou modificar os servidores existentes. Cada entrada deve ser um par de IPs (primário e secundário).

#### `security`

| Chave | Tipo | Descrição | Padrão |
|---|---|---|---|
| `require_sudo` | booleano | Requer `sudo` para executar o script. | `true` |
| `sudoers_file` | string | Caminho para o arquivo `sudoers`. | `/etc/sudoers.d/dns_changer` |
| `log_dns_changes` | booleano | Registra as alterações de DNS no log. | `true` |
| `validate_dns` | booleano | Valida se o servidor DNS está respondendo antes de aplicar. | `true` |

#### `daemon`

| Chave | Tipo | Descrição | Padrão |
|---|---|---|---|
| `enabled` | booleano | Habilita ou desabilita o LaunchDaemon. | `true` |
| `label` | string | Rótulo do LaunchDaemon. | `com.dns-changer.daemon` |
| `plist_path` | string | Caminho para o arquivo `.plist`. | `~/Library/LaunchAgents/com.dns-changer.daemon.plist` |
| `run_at_load` | booleano | Executa o script quando o daemon é carregado. | `true` |
| `keep_alive` | booleano | Mantém o script em execução. | `true` |
| `throttle_interval` | inteiro | Intervalo de aceleração para evitar execuções repetidas. | `10` |

#### `logging`

| Chave | Tipo | Descrição | Padrão |
|---|---|---|---|
| `enabled` | booleano | Habilita ou desabilita o log. | `true` |
| `log_dir` | string | Diretório de log. | `~/.dns_changer` |
| `log_file` | string | Arquivo de log principal. | `~/.dns_changer/daemon.log` |
| `error_log` | string | Arquivo de log de erros. | `~/.dns_changer/daemon_error.log` |
| `max_log_size` | string | Tamanho máximo do arquivo de log (ex: `10MB`). | `10MB` |
| `retention_days` | inteiro | Dias para reter os arquivos de log. | `30` |

#### `notifications`

Esta seção ainda não está implementada.
