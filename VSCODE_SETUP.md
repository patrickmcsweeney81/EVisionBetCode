# VS Code Setup for Maximum Efficiency

This document explains how to configure VS Code for optimal development workflow with EVisionBet.

## Quick Setup

### 1. Create .vscode Directory (Local Only)
```bash
mkdir .vscode
```

### 2. Create Tasks Configuration

Create `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "🏀 NBA: Full Pipeline",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": ["run_nba_pipeline.py", "--extract"],
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            },
            "problemMatcher": []
        },
        {
            "label": "🏀 NBA: Filter Only",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": ["run_nba_pipeline.py"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            },
            "problemMatcher": []
        },
        {
            "label": "🧪 Run Tests",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": ["-m", "pytest", "test_pairing.py", "-v"],
            "group": {
                "kind": "test",
                "isDefault": true
            },
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            },
            "problemMatcher": []
        },
        {
            "label": "🚀 Start Backend API",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": ["-m", "uvicorn", "backend_api:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
            "isBackground": true,
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            },
            "problemMatcher": {
                "pattern": {
                    "regexp": "^.*$",
                    "file": 1,
                    "location": 2,
                    "message": 3
                },
                "background": {
                    "activeOnStart": true,
                    "beginsPattern": "^.*Uvicorn running.*$",
                    "endsPattern": "^.*Application startup complete.*$"
                }
            }
        },
        {
            "label": "🔍 Extract NBA Data",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": ["extract_nba_v3.py"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            },
            "problemMatcher": []
        },
        {
            "label": "📊 Calculate EV",
            "type": "shell",
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": ["calculate_nba_ev_full.py"],
            "group": "build",
            "presentation": {
                "reveal": "always",
                "panel": "dedicated"
            },
            "problemMatcher": []
        }
    ]
}
```

**Usage:**
- `Ctrl+Shift+B` (Cmd+Shift+B on Mac): Run default build task (Full Pipeline)
- `Ctrl+Shift+P` → "Tasks: Run Task" → Choose any task
- `Ctrl+Shift+P` → "Tasks: Run Test Task": Run tests

### 3. Create Settings Configuration

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.formatting.provider": "none",
    "editor.formatOnSave": true,
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.flake8Args": ["--max-line-length=100"],
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.rulers": [100],
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        }
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        "**/.mypy_cache": true,
        "**/*.pyc": true
    },
    "files.watcherExclude": {
        "**/data/**": true,
        "**/.venv/**": true
    }
}
```

### 4. Create Launch Configuration (Debugging)

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "🏀 Debug Pipeline",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/run_nba_pipeline.py",
            "args": ["--extract"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "🚀 Debug Backend API",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "backend_api:app",
                "--reload",
                "--host", "127.0.0.1",
                "--port", "8000"
            ],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "🧪 Debug Tests",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["test_pairing.py", "-v"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

## Hot Reload Development Workflow

### Terminal Setup (3 Terminals)

**Terminal 1: Backend API (Hot Reload)**
```bash
cd /home/runner/work/EVisionBetCode/EVisionBetCode
source .venv/bin/activate
uvicorn backend_api:app --reload --host 127.0.0.1 --port 8000
```
- Auto-restarts on any `.py` file change
- Visit http://localhost:8000/docs for API testing

**Terminal 2: Frontend (Hot Reload)**
```bash
cd ../EVisionBetSite/frontend
npm start
```
- Auto-reloads on React component changes
- Opens browser to http://localhost:3000

**Terminal 3: Ad-hoc Commands**
```bash
cd /home/runner/work/EVisionBetCode/EVisionBetCode
source .venv/bin/activate
# Use for pipeline runs, tests, etc.
```

## Keyboard Shortcuts Summary

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+B` | Run Full Pipeline (default build) |
| `Ctrl+Shift+T` | Run Tests (default test) |
| `F5` | Start Debugging (current file or launch config) |
| `Ctrl+Shift+P` → "Tasks: Run Task" | Show all available tasks |
| `Ctrl+Shift+P` → "Python: Select Interpreter" | Switch Python interpreter |

## Benefits

✅ **Automation**: Pre-commit hooks auto-format before commits  
✅ **Speed**: Hot reload eliminates manual restart cycles  
✅ **Convenience**: One-key task execution (Ctrl+Shift+B)  
✅ **Debugging**: Full breakpoint support for all scripts  
✅ **Consistency**: Team-wide formatting and linting rules

## Note

The `.vscode/` directory is in `.gitignore` for personal preferences. Share these configurations through documentation or via team setup scripts.
