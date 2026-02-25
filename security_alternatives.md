## Análise de Alternativas de Segurança para Execução em Segundo Plano

### 1. `LaunchAgent` + `sudoers` (Abordagem Atual - Insegura)

-   **Descrição:** Um `LaunchAgent` é executado com os privilégios do usuário logado. Para realizar tarefas administrativas, ele precisa de uma regra `NOPASSWD` no `sudoers`.
-   **Vantagens:**
    -   Fácil de implementar.
-   **Desvantagens:**
    -   **Inseguro:** Cria um vetor de escalada de privilégio assistida.
    -   **Não-padrão:** Não é a abordagem recomendada para serviços de sistema.

### 2. `LaunchDaemon` (Padrão Ouro do macOS)

-   **Descrição:** Um `LaunchDaemon` é um serviço de nível de sistema que roda como `root` por padrão. Ele é instalado em `/Library/LaunchDaemons` e gerenciado pelo `launchd`.
-   **Vantagens:**
    -   **Seguro:** Elimina a necessidade de `sudo` e `sudoers`, fechando o vetor de ataque.
    -   **Padrão de Mercado:** A abordagem correta e profissional para serviços de sistema no macOS.
    -   **Robusto:** O `launchd` garante que o serviço seja executado de forma confiável.
-   **Desvantagens:**
    -   Requer um pouco mais de cuidado na instalação (propriedade do arquivo, permissões).

### 3. Script com Autenticação (Abordagem Interativa)

-   **Descrição:** O script pode ser modificado para solicitar a senha do usuário sempre que precisar de privilégios elevados. Isso pode ser feito usando `osascript` para exibir uma caixa de diálogo de autenticação nativa do macOS.
-   **Vantagens:**
    -   **Seguro:** A senha é solicitada a cada execução, garantindo a intenção do usuário.
-   **Desvantagens:**
    -   **Não-automático:** Não é adequado para execução em segundo plano a cada 5 minutos.
    -   **Inconveniente:** A solicitação constante de senha tornaria o software inutilizável para o seu propósito principal.

### Decisão

A migração para um **`LaunchDaemon`** é a única solução que atende aos requisitos de segurança e automação do projeto. É a abordagem mais segura, profissional e alinhada com as melhores práticas de mercado para o ecossistema macOS.
