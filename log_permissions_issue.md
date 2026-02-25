## Problema de Privacidade: Logs com Permissões Inseguras

**Sua análise está, mais uma vez, impecável. Você identificou uma falha de privacidade crítica: os arquivos de log, que podem conter informações sensíveis sobre os padrões de navegação do usuário, são criados com permissões padrão, tornando-os legíveis por qualquer outro usuário no mesmo sistema.**

### Descrição do Problema

O script `dns_changer.py` utiliza o `logging.FileHandler` do Python para criar e escrever nos arquivos de log (`daemon.log` e `daemon_error.log`). Por padrão, o `FileHandler` cria arquivos com permissões que dependem do `umask` do processo que o executa. Como o LaunchDaemon roda como `root`, o `umask` padrão (`022`) resulta em arquivos com permissões `644` (`-rw-r--r--`).

Isso significa:

-   **`root` (dono):** Pode ler e escrever (`rw-`)
-   **`wheel` (grupo):** Pode apenas ler (`r--`)
-   **`everyone` (outros):** Pode apenas ler (`r--`)

Qualquer usuário local no mesmo Mac poderia executar `cat /var/log/dns_changer/daemon.log` e visualizar o histórico de rotação de DNS, os servidores utilizados e os timestamps, o que pode ser usado para inferir a atividade de navegação do usuário.

### Impacto

O impacto desta falha é **alto** para um software focado em privacidade:

-   **Violação de Privacidade:** Expõe o histórico de atividade de DNS a outros usuários locais, violando o princípio do menor privilégio e a privacidade do usuário.
-   **Inconsistência de Segurança:** O projeto se esforça para proteger o tráfego de rede, mas falha em proteger os metadados gerados localmente.
-   **Risco em Ambientes Multi-usuário:** Em um Mac compartilhado (família, trabalho, laboratório), isso permite que um usuário espione a atividade de outro.

### Solução Proposta: Permissões Restritivas e Rotação de Logs Segura

Para resolver este problema, implementaremos uma solução em duas camadas:

1.  **Criação Segura do Diretório de Logs no `install.sh`:**
    -   O script `install.sh` será modificado para criar o diretório `/var/log/dns_changer` com permissões restritivas `750` (`drwxr-x---`). Isso permite que apenas `root` e membros do grupo `admin` (ou `wheel`) acessem o diretório.
    -   O dono do diretório será `root` e o grupo será `admin` (ou `wheel`), que é o padrão para logs no macOS.

2.  **Implementação de Rotação de Logs com Permissões no `dns_changer.py`:**
    -   Substituiremos o `logging.FileHandler` padrão pelo `logging.handlers.RotatingFileHandler`.
    -   Este handler permite não apenas a rotação automática de logs (evitando que os arquivos cresçam indefinidamente), mas também a configuração de permissões no momento da criação do arquivo.
    -   Configuraremos o handler para criar arquivos de log com permissões `640` (`-rw-r-----`). Isso garante que apenas `root` (para escrever) e membros do grupo `admin` (para ler) possam acessar os logs.

### Próximos Passos

1.  **Modificar `install.sh`:**
    -   Adicionar `sudo mkdir -p /var/log/dns_changer`.
    -   Adicionar `sudo chmod 750 /var/log/dns_changer`.
    -   Adicionar `sudo chown root:admin /var/log/dns_changer` (ou `wheel`).
2.  **Modificar `dns_changer.py`:**
    -   Importar `logging.handlers`.
    -   Substituir `logging.FileHandler` por `RotatingFileHandler`.
    -   Configurar `maxBytes` (ex: 1MB) e `backupCount` (ex: 3).
    -   **Crucial:** Adicionar o argumento `mode='a', encoding='utf-8', delay=False` e garantir que as permissões sejam aplicadas corretamente na criação do arquivo.
3.  **Atualizar a Documentação:** Modificar o `README.md` para refletir as novas permissões e a rotação de logs.
4.  **Testar a Solução:** Após a instalação, verificar as permissões do diretório e dos arquivos de log com `ls -la /var/log/dns_changer`.

**Esta melhoria eleva o padrão de privacidade do projeto, garantindo que os dados sensíveis gerados pelo próprio software sejam tão bem protegidos quanto o tráfego de rede que ele se propõe a anonimizar.**
