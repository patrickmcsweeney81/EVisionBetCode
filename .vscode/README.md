# VS Code Workspace Configuration

This directory contains VS Code workspace configuration files for the EVisionBetCode project. These configurations are now committed to the repository to provide a consistent development experience for all contributors.

## Files Overview

### `settings.json`
**Purpose:** Project-wide settings for Python development, formatting, and linting.

**Key Features:**
- Python interpreter path pointing to `.venv/bin/python`
- Auto-formatting on save with Black (line length: 100)
- Auto-organize imports with isort
- Linting with Flake8 and Pylint
- Type checking with Pylance
- Pytest configuration for testing
- File exclusions for build artifacts and data files

### `launch.json`
**Purpose:** Debug configurations for common development tasks.

**Available Configurations:**
1. **Pipeline: Extract Odds** - Debug the odds extraction script
2. **Pipeline: Calculate EV** - Debug the EV calculation script
3. **Pipeline: Run Full (Extract + Calculate)** - Run the complete pipeline
4. **Backend API: Run Server** - Debug the FastAPI server with hot reload
5. **Tests: Run All** - Debug all tests
6. **Tests: Run Current File** - Debug the currently open test file
7. **Python: Current File** - Debug any Python file

**Usage:** Press `F5` or use the Run and Debug panel (Ctrl+Shift+D) to start debugging.

### `tasks.json`
**Purpose:** Pre-configured tasks for common development workflows.

**Available Tasks:**
- **Pipeline: Extract Odds** - Run odds extraction
- **Pipeline: Calculate EV** - Run EV calculation
- **Pipeline: Run Full (Extract + Calculate)** - Run complete pipeline (default build task)
- **Backend: Start API Server** - Start the FastAPI server with hot reload
- **Tests: Run All** - Run all tests
- **Tests: Run with Coverage** - Run tests with coverage report
- **Format: Black + isort** - Auto-format code
- **Lint: Flake8 + Pylint** - Run linters
- **Type Check: mypy** - Run type checking
- **Pre-commit: All Checks** - Run all pre-commit checks
- **Install: Dev Dependencies** - Install development dependencies

**Usage:** 
- Press `Ctrl+Shift+B` to run the default build task (full pipeline)
- Press `Ctrl+Shift+P` and type "Tasks: Run Task" to see all available tasks

### `extensions.json`
**Purpose:** Recommends essential VS Code extensions for this project.

**Essential Extensions:**
- Python - Core Python language support
- Pylance - Advanced IntelliSense and type checking
- Black Formatter - PEP 8 compliant code formatting
- isort - Import organization
- Flake8 - Code linting
- GitHub Copilot - AI pair programming
- Git Graph - Visual git history
- GitLens - Enhanced git integration

**Installation:**
When you open this workspace, VS Code will prompt you to install recommended extensions. You can also install them manually by searching in the Extensions panel (Ctrl+Shift+X).

## Quick Start

### First Time Setup

1. **Open the project in VS Code:**
   ```bash
   cd /path/to/EVisionBetCode
   code .
   ```

2. **Install recommended extensions:**
   - VS Code will prompt you to install recommended extensions
   - Click "Install All" or install them individually

3. **Select Python interpreter:**
   - Press `Ctrl+Shift+P`
   - Type "Python: Select Interpreter"
   - Choose `.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows)

4. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your ODDS_API_KEY
   ```

5. **Install dependencies:**
   - Press `Ctrl+Shift+P`
   - Type "Tasks: Run Task"
   - Select "Install: Dev Dependencies"
   - Or run: `make dev-install`

### Daily Development Workflow

1. **Run the pipeline:**
   - Press `Ctrl+Shift+B` (default build task)
   - Or use Tasks menu for individual steps

2. **Start the API server:**
   - Press `F5` and select "Backend API: Run Server"
   - Or use Tasks menu: "Backend: Start API Server"

3. **Run tests:**
   - Press `Ctrl+Shift+P` → "Tasks: Run Task" → "Tests: Run All"
   - Or use Test Explorer in the sidebar

4. **Debug code:**
   - Set breakpoints by clicking left of line numbers
   - Press `F5` to start debugging
   - Use debug configurations from the dropdown

### Code Quality Checks

**Before committing code:**
- Run: `Ctrl+Shift+P` → "Tasks: Run Task" → "Pre-commit: All Checks"
- Or in terminal: `make pre-commit`

This will run:
- Black formatting
- isort import organization
- Flake8 linting
- Pylint analysis
- mypy type checking
- pytest tests

## Customization

### Personal Settings
For personal preferences that shouldn't be shared, use your User Settings:
- Press `Ctrl+,` to open Settings
- Toggle to User settings (not Workspace)
- Add your personal configurations

### Workspace Settings
To modify workspace settings for all contributors:
1. Edit `.vscode/settings.json`
2. Commit and push changes
3. Document significant changes in this README

## Troubleshooting

### Python interpreter not found
**Problem:** VS Code can't find the Python interpreter.

**Solution:**
1. Ensure virtual environment is created: `python -m venv .venv`
2. Press `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose `.venv/bin/python`

### Linting not working
**Problem:** Flake8/Pylint not showing errors.

**Solution:**
1. Ensure dev dependencies are installed: `pip install -e ".[dev]"`
2. Reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"

### Formatting not working on save
**Problem:** Black doesn't format code when saving.

**Solution:**
1. Check that `editor.formatOnSave` is `true` in settings
2. Ensure Black Formatter extension is installed
3. Set Black Formatter as default: `"editor.defaultFormatter": "ms-python.black-formatter"`

### Tasks fail to run
**Problem:** Tasks return errors about missing commands.

**Solution:**
1. Ensure virtual environment is activated
2. Check that all dependencies are installed: `make dev-install`
3. Verify `.env` file exists with required variables

## Additional Resources

- [VSCODE_SETUP.md](../VSCODE_SETUP.md) - Detailed setup guide
- [README.md](../README.md) - Project documentation
- [Makefile](../Makefile) - Available make commands
- [pyproject.toml](../pyproject.toml) - Python project configuration

## Support

For issues or questions:
1. Check [VSCODE_SETUP.md](../VSCODE_SETUP.md) for detailed instructions
2. Review VS Code's Python documentation
3. Open an issue on GitHub

---

**Last Updated:** December 16, 2025
**VS Code Version:** 1.85+
**Python Version:** 3.10+
