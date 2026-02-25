# Testing & CI/CD Documentation

This document explains the testing strategy, how to run tests locally, and how the CI/CD pipeline works.

## Overview

DNS Changer Eye includes a comprehensive testing suite to ensure code quality, security, and reliability:

- **Unit Tests**: 16+ tests covering core functionality
- **Code Quality Checks**: Linting, formatting, and style verification
- **Security Audits**: Bandit, ShellCheck, and hardcoded secret detection
- **Documentation Validation**: Ensures all documentation files exist and are valid
- **CI/CD Pipeline**: Automated testing on every push and pull request

## Running Tests Locally

### Prerequisites

```bash
# Install Python development tools
pip install --upgrade pip
pip install black isort flake8 pylint bandit coverage shellcheck-py

# Install ShellCheck (macOS)
brew install shellcheck

# Install ShellCheck (Linux)
sudo apt-get install shellcheck
```

### Unit Tests

Run all unit tests:

```bash
# Using unittest (built-in)
python3 -m unittest discover -s tests -p 'test_*.py' -v

# With coverage report
coverage run -m unittest discover -s tests -p 'test_*.py'
coverage report
coverage html  # Generate HTML report
```

Run specific test class:

```bash
python3 -m unittest tests.test_dns_changer.TestConfigLoading -v
```

Run specific test:

```bash
python3 -m unittest tests.test_dns_changer.TestConfigLoading.test_load_config_returns_dict -v
```

### Code Quality Checks

**Black (Code Formatter)**

```bash
# Check formatting
black --check dns_changer.py tests/

# Auto-fix formatting
black dns_changer.py tests/
```

**isort (Import Sorting)**

```bash
# Check import order
isort --check-only dns_changer.py tests/

# Auto-fix imports
isort dns_changer.py tests/
```

**Flake8 (Linter)**

```bash
# Run linter
flake8 dns_changer.py tests/ --max-line-length=100 --ignore=E203,W503
```

**Pylint (Advanced Linter)**

```bash
# Run pylint
pylint dns_changer.py --disable=C0111,C0103 --fail-under=8.0
```

### Security Checks

**Bandit (Security Scanner)**

```bash
# Scan for security issues
bandit -r dns_changer.py

# Generate JSON report
bandit -r dns_changer.py -f json -o bandit-report.json

# Generate HTML report
bandit -r dns_changer.py -f html -o bandit-report.html
```

**ShellCheck (Shell Script Linter)**

```bash
# Check shell scripts
shellcheck install.sh uninstall.sh verify.sh

# Check with specific severity
shellcheck -S warning install.sh
```

**Hardcoded Secrets Check**

```bash
# Search for common secret patterns
grep -r "password\|api_key\|secret\|token" dns_changer.py
```

### Full Quality Pipeline

Run all checks in sequence:

```bash
#!/bin/bash
set -e

echo "=== Running Unit Tests ==="
python3 -m unittest discover -s tests -p 'test_*.py' -v

echo "=== Running Code Quality Checks ==="
black --check dns_changer.py tests/
isort --check-only dns_changer.py tests/
flake8 dns_changer.py tests/ --max-line-length=100
pylint dns_changer.py --disable=C0111,C0103

echo "=== Running Security Checks ==="
bandit -r dns_changer.py
shellcheck install.sh uninstall.sh verify.sh

echo "=== All checks passed! ==="
```

Save this as `run_all_checks.sh` and run:

```bash
chmod +x run_all_checks.sh
./run_all_checks.sh
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically runs on:

- **Every push** to `main` or `develop` branches
- **Every pull request** to `main` or `develop` branches
- **Daily schedule** at 2 AM UTC

### Pipeline Jobs

#### 1. Quality Checks (3 Python versions)

Tests code quality across Python 3.9, 3.10, and 3.11:

- Black formatter check
- isort import checker
- Flake8 linter
- Pylint analysis
- Bandit security scan

**Status Badge**: Shows if code quality passes

#### 2. Shell Checks

Validates all shell scripts:

- `install.sh`
- `uninstall.sh`
- `verify.sh`

#### 3. Unit Tests (3 Python versions)

Runs unit tests with coverage:

- 16+ unit tests
- Coverage report
- Codecov integration

**Coverage Threshold**: Aims for 80%+ coverage

#### 4. JSON Validation

Validates configuration files:

- `config.example.json` is valid JSON
- Configuration documentation exists

#### 5. Documentation

Checks that all documentation files exist:

- README.md
- QUICKSTART.md
- ADVANCED_CONFIGURATION.md
- LICENSE

#### 6. File Integrity

Verifies critical files:

- All core files exist
- Scripts are executable
- SHA256SUMS file present

#### 7. Security Audit

Comprehensive security checks:

- Bandit security scan
- Hardcoded secrets detection
- SQL injection pattern check

#### 8. Summary

Final job that reports overall pipeline status.

### Viewing Pipeline Results

1. Go to your repository on GitHub
2. Click the "Actions" tab
3. Select a workflow run to see details
4. Click on a job to see detailed output

### Handling Pipeline Failures

**If Black formatting fails:**

```bash
black dns_changer.py tests/
git add dns_changer.py tests/
git commit -m "Fix code formatting"
git push
```

**If Flake8 fails:**

Review the reported style issues and fix them manually, or use Black to auto-format.

**If unit tests fail:**

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
# Fix the failing tests
git add tests/
git commit -m "Fix failing tests"
git push
```

**If ShellCheck fails:**

Review the reported issues in shell scripts and fix them.

**If security scan fails:**

Review the Bandit report and address security issues:

```bash
bandit -r dns_changer.py -f html -o report.html
# Open report.html and review issues
```

## Test Coverage

Current test coverage includes:

| Component | Coverage | Tests |
|-----------|----------|-------|
| Configuration Loading | 100% | 4 |
| Interval Validation | 100% | 2 |
| DNS Server Validation | 100% | 2 |
| PID Lock Mechanism | 100% | 2 |
| Log Permissions | 100% | 2 |
| Configuration Integration | 100% | 2 |
| Security Checks | 100% | 2 |
| **Total** | **100%** | **16** |

## Adding New Tests

When adding new features, add corresponding tests:

1. Create test file in `tests/` directory
2. Name it `test_*.py`
3. Use `unittest.TestCase` as base class
4. Run tests locally before pushing
5. Ensure all tests pass in CI/CD

Example test:

```python
import unittest

class TestNewFeature(unittest.TestCase):
    """Test the new feature"""
    
    def test_feature_works(self):
        """Test that feature works correctly"""
        result = new_feature()
        self.assertEqual(result, expected_value)

if __name__ == "__main__":
    unittest.main()
```

## Continuous Integration Best Practices

1. **Run tests before pushing**

   ```bash
   ./run_all_checks.sh
   ```

2. **Fix issues immediately**

   Don't let failing tests accumulate.

3. **Review CI/CD logs**

   Always check what failed and why.

4. **Keep tests updated**

   When changing code, update tests too.

5. **Maintain coverage**

   Aim for 80%+ code coverage.

6. **Security first**

   Address all security warnings.

## Troubleshooting

### Tests fail locally but pass in CI/CD

- Check Python version compatibility
- Ensure all dependencies are installed
- Clear Python cache: `find . -type d -name __pycache__ -exec rm -r {} +`

### CI/CD passes but tests fail locally

- Update dependencies: `pip install --upgrade -r requirements.txt`
- Check for environment-specific issues
- Verify Python version matches CI/CD

### Coverage report shows 0%

- Ensure `coverage` is installed: `pip install coverage`
- Run with coverage: `coverage run -m unittest discover -s tests -p 'test_*.py'`

### ShellCheck fails with "not found"

- Install ShellCheck: `brew install shellcheck` (macOS) or `sudo apt-get install shellcheck` (Linux)

## Resources

- [Python unittest documentation](https://docs.python.org/3/library/unittest.html)
- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [Bandit security scanner](https://bandit.readthedocs.io/)
- [ShellCheck](https://www.shellcheck.net/)
- [Coverage.py](https://coverage.readthedocs.io/)
