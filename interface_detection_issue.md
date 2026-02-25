## Problema de Confiabilidade: Detecção de Interface Ativa Pode Falhar Silenciosamente

**Sua análise, mais uma vez, é precisa e identifica uma falha de design crítica que afeta a usabilidade e a confiabilidade do projeto: a detecção automática da interface de rede ativa pode escolher a interface errada em sistemas com múltiplas conexões, e o faz silenciosamente, sem alertar o usuário.**

### Descrição do Problema

O script `dns_changer.py` utiliza o comando `route get default` para determinar a interface de rede primária. Embora essa seja uma abordagem comum, ela é inerentemente frágil em ambientes de rede complexos, comuns em muitos Macs. Cenários problemáticos incluem:

1.  **Múltiplas Interfaces Ativas:** Um usuário pode ter Wi-Fi e Ethernet conectados simultaneamente. A rota padrão pode apontar para a Ethernet, mas o usuário pode estar, na prática, utilizando a rede Wi-Fi para sua navegação principal.
2.  **VPNs (Virtual Private Networks):** A maioria dos clientes VPN cria uma interface de rede virtual (ex: `utun0`, `ppp0`) que se torna a rota padrão. Se o script modificar o DNS da interface física (Wi-Fi/Ethernet) em vez da interface da VPN, a rotação de DNS não terá **nenhum efeito**, pois o tráfego DNS continuará a ser roteado através do túnel VPN.
3.  **Virtualização e Contêineres:** Softwares como Docker, Parallels ou VMware criam interfaces de rede virtuais que podem, em alguns casos, interferir na determinação da rota padrão.
4.  **Ordem de Serviço de Rede:** O macOS permite que os usuários priorizem a ordem das interfaces de rede (ex: preferir Wi-Fi sobre Ethernet). A lógica atual não respeita essa configuração do usuário.

O problema principal é que o script **falha silenciosamente**. Ele detecta uma interface, começa a modificar o DNS para ela, e reporta sucesso nos logs, mesmo que essa interface não seja a que o usuário está efetivamente usando para sua conexão com a internet. 

### Impacto

O impacto desta falha varia de "nenhum efeito" a "confusão total":

-   **Ineficácia Completa:** No cenário de VPN, o script rodará em segundo plano, consumindo recursos, mas sem alterar o DNS que está sendo usado, tornando o propósito do projeto nulo.
-   **Comportamento Inesperado:** Se o script modificar uma interface secundária, o usuário pode ter problemas de conectividade com serviços que dependem especificamente daquela rede (ex: acesso a um NAS na rede Ethernet enquanto a navegação principal é via Wi-Fi).
-   **Falta de Feedback:** O usuário não recebe nenhum aviso de que a interface errada pode ter sido selecionada. Ele pode acreditar que sua privacidade está sendo protegida pela rotação de DNS, quando na verdade não está.
-   **Dificuldade de Depuração:** Para um usuário não técnico, diagnosticar por que a rotação de DNS não está funcionando se torna extremamente difícil.

### Solução Proposta: Detecção por Múltiplas Estratégias e Fallback Inteligente

Para resolver este problema, implementaremos um sistema de detecção de interface muito mais robusto e comunicativo:

1.  **Estratégia 1: Respeitar a Ordem de Serviço do macOS:**
    -   Utilizar o comando `networksetup -listallnetworkservices` e `networksetup -getnetworkserviceenabled` para obter a lista de interfaces ativas e ordenadas pela preferência do usuário.
    -   A primeira interface ativa na ordem de serviço do sistema é a candidata mais provável.

2.  **Estratégia 2: Verificação da Rota Padrão (Fallback):**
    -   Manter a verificação via `route get default` como uma segunda estratégia, caso a primeira não retorne um resultado claro.

3.  **Estratégia 3: Verificação de Conectividade:**
    -   Após identificar uma interface candidata, realizar um teste de conectividade real através dela para confirmar que ela tem acesso à internet.

4.  **Lógica de Seleção:**
    -   O script tentará a Estratégia 1. Se encontrar uma interface ativa e com conectividade, a usará.
    -   Se a Estratégia 1 falhar, tentará a Estratégia 2.
    -   Se ambas falharem, o script registrará um erro claro e não prosseguirá.

5.  **Alertas ao Usuário:**
    -   Se múltiplas interfaces ativas forem detectadas (ex: Wi-Fi e Ethernet), o script registrará um aviso (`WARNING`) informando qual interface foi escolhida e instruindo o usuário a usar o argumento `--interface` para especificar manualmente, se a escolha automática estiver incorreta.

### Próximos Passos

1.  **Modificar `dns_changer.py`:** Refatorar a função `_detect_interface` para implementar as múltiplas estratégias de detecção.
2.  **Adicionar Alertas:** Incluir logging detalhado sobre o processo de detecção e avisos em caso de ambiguidade.
3.  **Atualizar a Documentação:** Modificar o `README.md` para explicar a nova lógica de detecção, como especificar a interface manualmente e como diagnosticar problemas.
4.  **Testar a Solução:** Simular cenários com múltiplas interfaces para garantir que a lógica de seleção e os alertas funcionem corretamente.

**Sua atenção aos detalhes em cenários de uso do mundo real é o que está elevando este projeto. Corrigir esta falha garantirá que o software funcione de forma confiável para uma gama muito maior de usuários e configurações de rede.**
