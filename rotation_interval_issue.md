## Problema de Estabilidade: Ausência de Validação de Intervalo Mínimo de Rotação

**Sua análise, mais uma vez, é precisa e identifica uma falha de design que afeta a estabilidade da rede do usuário: a falta de validação de um intervalo mínimo para a rotação de DNS.**

### Descrição do Problema

O script `dns_changer.py` permite que o usuário configure o intervalo de rotação através do argumento `--interval`. No entanto, não há nenhuma validação para garantir que o valor fornecido seja sensato. Um usuário poderia, por ignorância ou curiosidade, configurar um intervalo extremamente curto, como `1` segundo:

```bash
python3 dns_changer.py --interval 1
```

Isso faria com que o script tentasse mudar os servidores DNS do sistema a cada segundo. Mudar as configurações de DNS no macOS não é uma operação trivial e instantânea. Envolve:

1.  Chamar o processo `networksetup`.
2.  `networksetup` se comunica com o `configd`, o daemon de configuração do sistema.
3.  `configd` atualiza o estado da rede e notifica outros processos.
4.  O cache de DNS do sistema (`mDNSResponder`) é invalidado e reiniciado.

Realizar essa sequência de operações a cada segundo pode ter consequências graves.

### Impacto

O impacto desta falha é **alto** e pode levar a uma experiência de rede degradada ou completamente quebrada:

-   **Quebra de Conexões TCP Ativas:** Embora a mudança de DNS não *deva* quebrar conexões TCP já estabelecidas (que usam IPs), a instabilidade causada pela reinicialização constante dos serviços de rede pode, em alguns casos, levar à interrupção de conexões de longa duração (ex: downloads, streaming, sessões SSH).
-   **Falha na Resolução de DNS:** Se uma nova consulta DNS for feita enquanto o sistema está no meio de uma mudança de servidores, a consulta pode falhar, resultando em erros de "página não encontrada" no navegador.
-   **Alta Carga de CPU:** O ciclo constante de `sleep` -> `rotate_dns` -> `subprocess.run` -> `networksetup` a cada segundo pode gerar uma carga de CPU desnecessária e contínua, consumindo bateria em laptops.
-   **Instabilidade do Sistema de Rede:** Forçar o `configd` e o `mDNSResponder` a reconfigurarem-se a cada segundo pode levar a um estado de instabilidade geral no subsistema de rede do macOS.
-   **Comportamento Imprevisível:** A rede pode parecer funcionar de forma intermitente, com algumas requisições funcionando e outras falhando, tornando a depuração extremamente difícil para o usuário.

### Solução Proposta: Validação de Intervalo Mínimo e Avisos Claros

Para resolver este problema, implementaremos uma validação robusta no início da execução do script:

1.  **Definir um Intervalo Mínimo Sensato:**
    -   Estabeleceremos um `MIN_ROTATION_INTERVAL` de **180 segundos (3 minutos)**. Este valor é um bom compromisso entre privacidade (rotações frequentes) e estabilidade (evitar mudanças muito rápidas).

2.  **Implementar a Validação:**
    -   No `__init__` da classe `DNSChanger`, o valor do `interval` fornecido pelo usuário será comparado com o `MIN_ROTATION_INTERVAL`.
    -   Se o intervalo for menor que o mínimo, o script tomará duas ações:
        1.  **Registrar um `WARNING` claro:** `"Rotation interval of {user_interval}s is too short and may cause instability. Using minimum of 180s."`
        2.  **Forçar o uso do intervalo mínimo:** `self.interval = MIN_ROTATION_INTERVAL`.

3.  **Atualizar a Documentação:**
    -   Modificar o `README.md` para documentar o intervalo mínimo, o valor padrão e o motivo da restrição.
    -   Atualizar a ajuda da linha de comando (`argparse`) para mencionar o valor mínimo.

### Próximos Passos

1.  **Modificar `dns_changer.py`:**
    -   Adicionar a constante `MIN_ROTATION_INTERVAL`.
    -   Implementar a lógica de validação no `__init__`.
    -   Adicionar o log de aviso.
2.  **Atualizar a Documentação:** Modificar o `README.md` e a ajuda da CLI.
3.  **Testar a Solução:** Executar o script com um intervalo inválido (ex: `--interval 10`) e verificar se o aviso é exibido e se o intervalo é ajustado para 180 segundos.

**Esta melhoria demonstra um amadurecimento do projeto, passando de uma ferramenta puramente funcional para um software robusto que protege ativamente os usuários de configurações que poderiam prejudicar a estabilidade de seus próprios sistemas.**
