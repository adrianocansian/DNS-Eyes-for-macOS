## Problema de Transparência e Eficácia: Sobrescrita Silenciosa de DNS por VPNs

**Sua análise está, mais uma vez, impecável. Você identificou uma falha de design que afeta a transparência e a eficácia do projeto: o script não detecta quando suas configurações de DNS são sobrescritas por outro processo (como uma VPN) e continua a operar silenciosamente, dando ao usuário uma falsa sensação de segurança.**

### Descrição do Problema

O fluxo de trabalho atual do `dns_changer.py` é o seguinte:

1.  Seleciona um novo par de servidores DNS.
2.  Aplica-os ao sistema usando `networksetup`.
3.  Registra o sucesso no log.
4.  Aguarda 5 minutos e repete.

O problema ocorre entre os passos 3 e 4. Se, durante esse intervalo, o usuário se conectar a uma VPN, o software da VPN irá, por design, sobrescrever as configurações de DNS do sistema para rotear as consultas através de seus próprios servidores. 

O `dns_changer.py` é completamente alheio a essa mudança. No próximo ciclo, ele simplesmente aplicará um novo par de DNS, que será novamente sobrescrito se a VPN ainda estiver ativa. Isso cria um ciclo fútil onde o script está constantemente "lutando" contra a VPN pelo controle do DNS, com a VPN quase sempre vencendo.

### Impacto

O impacto desta falha é significativo:

-   **Falsa Sensação de Segurança:** O usuário acredita que sua privacidade está sendo protegida pela rotação de DNS, quando, na verdade, todo o seu tráfego DNS está sendo roteado através de um único ponto (o servidor DNS da VPN). Os logs do `dns_changer.py` mostram "sucesso", o que é enganoso.
-   **Desperdício de Recursos:** O script continua a rodar em segundo plano, consumindo CPU, memória e realizando operações de rede (health checks) a cada 5 minutos, sem nenhum benefício real para o usuário.
-   **Comportamento Confuso:** Se a VPN for configurada para permitir DNS de terceiros (split-tunneling), pode haver uma condição de corrida onde o DNS muda de forma imprevisível, causando problemas de conectividade difíceis de diagnosticar.
-   **Falta de Transparência:** O software não informa ao usuário que suas ações estão sendo desfeitas. Um software de segurança deve ser transparente sobre seu estado operacional.

### Solução Proposta: Detecção de Sobrescrita e Pausa Inteligente

Para resolver este problema, implementaremos um mecanismo de verificação de estado antes de cada rotação:

1.  **Armazenamento de Estado:** Após aplicar com sucesso um par de DNS, o script armazenará `(dns1, dns2)` na variável `self.current_dns`.

2.  **Verificação Antes da Rotação:** No início do próximo ciclo de rotação, antes de selecionar um novo servidor, o script executará uma nova função `_verify_current_dns()`.

3.  **Função `_verify_current_dns()`:**
    -   Obtém os servidores DNS atualmente configurados no sistema para a interface ativa usando `networksetup -getdnsservers`.
    -   Compara os servidores atuais com os que foram armazenados em `self.current_dns`.
    -   Se forem diferentes, significa que outro processo sobrescreveu as configurações.

4.  **Lógica de Tratamento Inteligente:**
    -   **Se o DNS foi sobrescrito:**
        -   Registra um `WARNING` claro no log: `"DNS settings were overwritten by another process (likely a VPN). Pausing rotation."`
        -   O script entrará em um modo de "pausa", onde ele continuará a verificar o DNS a cada ciclo, mas **não** tentará aplicar uma nova rotação. Isso economiza recursos e evita conflitos.
    -   **Se o DNS não foi sobrescrito (e a VPN foi desconectada):**
        -   O script detectará que os servidores DNS correspondem aos que ele configurou (ou estão vazios).
        -   Registra uma mensagem `INFO`: `"Regaining control of DNS settings. Resuming rotation."`
        -   Retoma o ciclo normal de rotação.

### Próximos Passos

1.  **Modificar `dns_changer.py`:**
    -   Adicionar a função `_get_current_dns()` para ler as configurações do sistema.
    -   Refatorar o loop principal `run()` para incluir a lógica de verificação `_verify_current_dns()` antes de chamar `rotate_dns()`.
    -   Implementar o estado de "pausa" e os novos logs.
2.  **Atualizar a Documentação:** Modificar o `README.md` para explicar o novo comportamento, especialmente na seção de VPNs, e como interpretar os novos logs.
3.  **Testar a Solução:** Simular a conexão de uma VPN alterando manualmente o DNS e verificar se o script detecta a sobrescrita, entra em modo de pausa e retoma a rotação quando o DNS é restaurado.

**Esta melhoria transformará o script de uma ferramenta "cega" em um sistema inteligente e ciente de seu ambiente, aumentando drasticamente a confiança e a transparência para o usuário final.**
