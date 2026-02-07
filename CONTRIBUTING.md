# Contributing to DNS Changer Eye - macOS

Thank you for considering contributing to DNS Changer Eye! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you agree to maintain a respectful and inclusive environment.

---

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check the issue list as you may find that the bug has already been reported.

When reporting a bug, please include:

- **A descriptive title**
- **An exact description of the observed behavior**
- **The expected behavior**
- **Steps to reproduce the problem**
- **Specific examples**
- **macOS version**
- **Python version**
- **Relevant logs**

### Suggesting Enhancements

Enhancement suggestions are welcome! When creating an enhancement suggestion, please include:

- **A descriptive title**
- **A detailed description of the suggested enhancement**
- **Examples of how the enhancement would work**
- **Why this enhancement would be useful**

### Pull Requests

- Follow the existing code style
- Include appropriate tests
- Update the documentation as needed
- End all files with a new line

---

## Style Guide

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use descriptive names for variables and functions
- Add docstrings for all public functions
- Keep lines under 100 characters

```python
def example_function(parameter1: str, parameter2: int) -> bool:
    """
    Brief description of the function.
    
    Args:
        parameter1: Description of parameter 1
        parameter2: Description of parameter 2
        
    Returns:
        Description of the return value
    """
    pass
```

### Bash

- Use `#!/bin/bash` as the shebang
- Add comments for main sections
- Use `set -e` to exit on error
- Quote variables: `"$variable"`

```bash
#!/bin/bash

# Description of the script
set -e

# Example function
example_function() {
    local variable="value"
    echo "Result: $variable"
}
```

### Markdown

- Use appropriate titles
- Keep lines under 80 characters
- Use numbered lists for procedures
- Use bullet points for items

---

## Development Process

1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/your-username/dns-changer-macos.git`
3. **Create a branch**: `git checkout -b feature/your-feature`
4. **Make your changes**
5. **Test your changes**
6. **Commit your changes**: `git commit -m 'Add your feature'`
7. **Push to the branch**: `git push origin feature/your-feature`
8. **Open a Pull Request**

---

## Testing

Before submitting a Pull Request, test your changes:

```bash
# Manual test
python3 dns_changer.py --help
python3 dns_changer.py --once
python3 dns_changer.py --get

# Installation test
./install.sh

# Uninstallation test
bash ~/.dns_changer/uninstall.sh
```

---

## Documentation

- Keep README.md updated
- Add usage examples for new features
- Document changes in CHANGELOG.md
- Use clear comments in the code

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible changes
- **MINOR**: New compatible features
- **PATCH**: Bug fixes

---

## License

By contributing to this project, you agree that your contributions will be licensed under the GPL-3.0.

---

## Questions?

Feel free to open an issue with the `question` tag.

---

**Thank you for contributing! 🎉**
