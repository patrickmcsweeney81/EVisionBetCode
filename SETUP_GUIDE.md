# Project Setup - New Structure Guide

## Overview
Your project now has modern Python project configuration with centralized dependency management and automated quality checks.

## New Files Added

### 1. **pyproject.toml** - Project Configuration
- **What it does**: Single source of truth for project metadata, dependencies, and tool configs
- **Benefits**: 
  - Modern PEP 517/518 compliant standard
  - IDE-friendly (VS Code recognizes it)
  - Centralized configuration for black, isort, pytest, mypy, pylint
- **Key sections**:
  - `[project]`: Project metadata (name, version, description, authors)
  - `[project.dependencies]`: Core production dependencies
  - `[project.optional-dependencies]`: Feature-based dependency groups
  - `[tool.*]`: Configuration for linters, formatters, and test runners

### 2. **.pre-commit-config.yaml** - Automated Code Quality
- **What it does**: Runs checks automatically before each git commit
- **Benefits**:
  - Catches bugs early (before pushing to GitHub)
  - Enforces consistent formatting/linting across team
  - Detects secrets before accidental commit
  - Zero friction (runs transparently)
- **Checks included**:
  - Trailing whitespace removal
  - File fixes (end-of-file, line endings)
  - Secret detection
  - Code formatting (black, isort)
  - Linting (flake8, mypy)
  - YAML/Markdown validation

### 3. **.github/workflows/tests.yml** - CI/CD Pipeline
- **What it does**: Runs tests automatically on every push/PR
- **Benefits**:
  - Multi-version testing (Python 3.10, 3.11, 3.12)
  - Code coverage tracking (Codecov integration)
  - Catches failures before merge
  - No manual testing needed
- **Workflow includes**:
  - pytest with coverage
  - flake8 linting
  - mypy type checking
  - pylint analysis
  - Security scanning (bandit)

### 4. **Makefile** - Common Commands
- **What it does**: Shortcuts for repetitive tasks
- **Benefits**:
  - Cross-platform (Windows, Mac, Linux)
  - Self-documenting (`make help`)
  - Standardized across team
  - Chains complex tasks
- **Key commands**:
  - `make install` - Install production deps
  - `make dev-install` - Setup dev environment
  - `make run` - Start the bot
  - `make test` - Run tests with coverage
  - `make lint` - Check code quality
  - `make format` - Auto-format code
  - `make pre-commit` - Run pre-commit checks
  - `make clean` - Remove artifacts
  - `make check-all` - Run all checks before commit

### 5. **requirements/** Directory - Organized Dependencies
- **Structure**:
  ```
  requirements/
  ├── base.txt      (production: requests, python-dotenv, python-dateutil)
  ├── dev.txt       (development: black, isort, flake8, mypy, pytest, pre-commit)
  ├── test.txt      (testing: pytest, pytest-cov, pytest-timeout, pytest-mock)
  └── all.txt       (everything: dev + test + optional)
  ```
- **Benefits**:
  - Smaller production deployments (no test tools)
  - Clear dependencies by purpose
  - Faster CI/CD (only install what needed)
  - Security (fewer packages in prod)

## Getting Started

### 1. Install Development Environment
```bash
# Option A: Using Makefile (recommended)
make dev-install

# Option B: Using pip directly
pip install -e ".[dev]"
pip install pre-commit
pre-commit install
```

### 2. Install Pre-Commit Hooks
```bash
pre-commit install
```

Now pre-commit checks run automatically before each commit.

### 3. Run Tests Locally
```bash
# Using Makefile
make test

# Or directly
pytest --cov=core --cov-report=html
```

### 4. Format Code
```bash
# Using Makefile
make format

# Or directly
black . --line-length=100
isort . --profile=black --line-length=100
```

### 5. Lint Code
```bash
# Using Makefile
make lint

# Or directly
flake8 . --max-line-length=100
pylint core/ ev_arb_bot.py
```

### 6. Run the Bot
```bash
# Using Makefile
make run

# Or directly
python ev_arb_bot.py
```

## Dependency Installation Guide

### Production (Minimal)
```bash
pip install -r requirements/base.txt
# Or use pyproject.toml
pip install -e .
```

### Development (Full tools)
```bash
pip install -r requirements/dev.txt
# Or use pyproject.toml
pip install -e ".[dev]"
```

### Testing
```bash
pip install -r requirements/test.txt
```

### Everything
```bash
pip install -r requirements/all.txt
# Or
pip install -e ".[all]"
```

## GitHub Actions - What Happens on Push

1. **Tests Job**: Runs pytest on Python 3.10, 3.11, 3.12
   - Checks coverage
   - Uploads to Codecov
   
2. **Code Quality Job**: Formatting & linting checks
   - isort (import sorting)
   - black (formatting)
   - pylint (style analysis)
   - bandit (security issues)

3. **Docs Job**: Documentation validation
   - Verifies README.txt exists

Failed checks will block PR merge.

## Workflow Recommendations

### Before Committing (Local)
```bash
make format     # Auto-fix formatting
make lint       # Check style
make test       # Run tests
git add .
git commit      # Pre-commit hooks run here
git push
```

Or use the shortcut:
```bash
make check-all  # Runs format, lint, and test
```

### Before Merging PR (GitHub)
- GitHub Actions automatically runs all tests
- Check the PR status for test results
- Don't merge if tests fail

## Configuration Files Reference

### pyproject.toml sections:
- `[build-system]` - Build requirements
- `[project]` - Metadata
- `[project.dependencies]` - Core deps
- `[project.optional-dependencies]` - Feature groups
- `[tool.pytest.ini_options]` - pytest config
- `[tool.black]` - black formatter config
- `[tool.isort]` - isort sorter config
- `[tool.mypy]` - mypy type checker config

### .pre-commit-config.yaml hooks:
- pre-commit-hooks: File checks, trailing whitespace, YAML validation
- detect-secrets: Secret detection
- black: Code formatting
- isort: Import sorting
- flake8: Linting
- mypy: Type checking
- yamllint: YAML linting
- markdownlint: Markdown linting

## Troubleshooting

### Pre-commit not running
```bash
pre-commit install --install-hooks
pre-commit run --all-files
```

### Tests failing locally but passing on GitHub
- Check Python version: `python --version`
- Ensure dependencies installed: `pip install -e ".[dev]"`

### Can't run make commands (Windows)
- Install GNU Make: `choco install make` or use Git Bash
- Or use Makefile targets directly: `python -m pytest --cov=core`

### My code got reformatted by pre-commit
- This is expected! Pre-commit auto-fixes formatting
- Review changes and commit them
- Next commit will pass smoothly

## Next Steps

1. ✅ Review new configuration files
2. ✅ Run `make dev-install` to setup
3. ✅ Test with `make test`
4. ✅ Format code with `make format`
5. ✅ Commit and push changes
6. ✅ Monitor GitHub Actions on first PR
7. ✅ Iterate on any test failures

## Questions?

Refer to documentation in files:
- `pyproject.toml` - Tool configurations
- `.pre-commit-config.yaml` - Pre-commit hooks
- `.github/workflows/tests.yml` - CI/CD definition
- `Makefile` - Available commands
- `README.txt` - Project overview
