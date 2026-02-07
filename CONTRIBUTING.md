# Contribuindo para DNS Changer Eye - macOS

Obrigado por considerar contribuir para o DNS Changer Eye! Este documento fornece diretrizes e instruções para contribuir ao projeto.

## Código de Conduta

Este projeto adere a um Código de Conduta. Ao participar, você concorda em manter um ambiente respeitoso e inclusivo.

---

## Como Contribuir

### Reportar Bugs

Antes de criar um relatório de bug, verifique a lista de problemas, pois você pode descobrir que o erro já foi relatado.

Ao relatar um bug, inclua:

- **Título descritivo**
- **Descrição exata do comportamento observado**
- **Comportamento esperado**
- **Passos para reproduzir o problema**
- **Exemplos específicos**
- **Versão do macOS**
- **Versão do Python**
- **Logs relevantes**

### Sugerir Melhorias

Sugestões de melhorias são bem-vindas! Ao criar uma sugestão de melhoria, inclua:

- **Título descritivo**
- **Descrição detalhada da melhoria sugerida**
- **Exemplos de como a melhoria funcionaria**
- **Por que essa melhoria seria útil**

### Pull Requests

- Siga o estilo de código existente
- Inclua testes apropriados
- Atualize a documentação conforme necessário
- Termine todos os arquivos com uma nova linha

---

## Guia de Estilo

### Python

- Siga [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use nomes descritivos para variáveis e funções
- Adicione docstrings para todas as funções públicas
- Mantenha linhas com menos de 100 caracteres

```python
def example_function(parameter1: str, parameter2: int) -> bool:
    """
    Descrição breve da função.
    
    Args:
        parameter1: Descrição do parâmetro 1
        parameter2: Descrição do parâmetro 2
        
    Returns:
        Descrição do retorno
    """
    pass
```

### Bash

- Use `#!/bin/bash` como shebang
- Adicione comentários para seções principais
- Use `set -e` para sair em caso de erro
- Cite variáveis: `"$variable"`

```bash
#!/bin/bash

# Descrição do script
set -e

# Função exemplo
example_function() {
    local variable="value"
    echo "Resultado: $variable"
}
```

### Markdown

- Use títulos apropriados
- Mantenha linhas com menos de 80 caracteres
- Use listas numeradas para procedimentos
- Use listas com bullets para itens

---

## Processo de Desenvolvimento

1. **Fork o repositório**
2. **Clone seu fork**: `git clone https://github.com/seu-usuario/dns-changer-macos.git`
3. **Crie uma branch**: `git checkout -b feature/sua-feature`
4. **Faça suas mudanças**
5. **Teste suas mudanças**
6. **Commit suas mudanças**: `git commit -m 'Adiciona sua feature'`
7. **Push para a branch**: `git push origin feature/sua-feature`
8. **Abra um Pull Request**

---

## Testes

Antes de submeter um Pull Request, teste suas mudanças:

```bash
# Teste manual
python3 dns_changer.py --help
python3 dns_changer.py --once
python3 dns_changer.py --get

# Teste de instalação
./install.sh

# Teste de desinstalação
bash ~/.dns_changer/uninstall.sh
```

---

## Documentação

- Mantenha o README.md atualizado
- Adicione exemplos de uso para novas features
- Documente mudanças em CHANGELOG.md
- Use comentários claros no código

---

## Versionamento

Este projeto segue [Semantic Versioning](https://semver.org/):

- **MAJOR**: Mudanças incompatíveis
- **MINOR**: Novas funcionalidades compatíveis
- **PATCH**: Correções de bugs

---

## Licença

Ao contribuir para este projeto, você concorda que suas contribuições serão licenciadas sob a GPL-3.0.

---

## Dúvidas?

Sinta-se livre para abrir uma issue com a tag `question`.

---

**Obrigado por contribuir! 🎉**
