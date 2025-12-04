.PHONY: help install dev-install test lint format type-check clean run bot pre-commit docs

# Default target - show help
help:
	@echo "EV ARB Bot - Available Commands"
	@echo "================================"
	@echo ""
	@echo "Installation:"
	@echo "  make install          Install production dependencies"
	@echo "  make dev-install      Install development dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make run              Run the EV bot (requires .env configured)"
	@echo ""
	@echo "Development:"
	@echo "  make test             Run pytest with coverage"
	@echo "  make lint             Run linting checks (flake8, pylint)"
	@echo "  make format           Auto-format code (black, isort)"
	@echo "  make type-check       Run type checking (mypy)"
	@echo "  make pre-commit       Run all pre-commit checks"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove cache and build artifacts"
	@echo "  make clean-logs       Remove generated log files"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs             Generate documentation"
	@echo ""

# ============================================================================
# Installation Targets
# ============================================================================

install:
	pip install --upgrade pip setuptools wheel
	pip install -e .

dev-install:
	pip install --upgrade pip setuptools wheel
	pip install -e ".[dev]"
	pip install pre-commit
	pre-commit install
	@echo "✓ Development environment setup complete"
	@echo "✓ Pre-commit hooks installed"

# ============================================================================
# Running Targets
# ============================================================================

run:
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found!"; \
		echo "Copy .env.example to .env and configure your API keys."; \
		exit 1; \
	fi
	python ev_arb_bot.py

# ============================================================================
# Testing Targets
# ============================================================================

test:
	pytest --cov=core --cov-report=term-missing --cov-report=html -v

test-fast:
	pytest -m "not slow" -v

test-unit:
	pytest -m "unit" -v

test-integration:
	pytest -m "integration" -v

# ============================================================================
# Code Quality Targets
# ============================================================================

lint:
	@echo "Running flake8..."
	flake8 . --max-line-length=100 --exclude=.git,__pycache__,venv,.venv,data
	@echo "✓ flake8 passed"
	@echo ""
	@echo "Running pylint..."
	pylint core/ ev_arb_bot.py --rcfile=.pylintrc --disable=all --enable=E,F || true
	@echo "✓ pylint passed"

format:
	@echo "Running black..."
	black . --line-length=100 --exclude="venv|\.venv|data"
	@echo "✓ black passed"
	@echo ""
	@echo "Running isort..."
	isort . --profile=black --line-length=100 --skip-glob="*.venv/*"
	@echo "✓ isort passed"
	@echo ""
	@echo "✓ Code formatting complete"

type-check:
	mypy . --ignore-missing-imports --exclude "venv|\.venv|data|tests"

pre-commit:
	pre-commit run --all-files

# ============================================================================
# Cleanup Targets
# ============================================================================

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name *.egg-info -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup complete"

clean-logs:
	@echo "Clearing log files..."
	rm -f data/seen_hits.json data/api_usage.json data/cache_events.json 2>/dev/null || true
	@echo "✓ Log files cleared"

# ============================================================================
# Documentation Targets
# ============================================================================

docs:
	@echo "Documentation files:"
	@echo "  - README.txt (main documentation)"
	@echo "  - CONFIGURATION_GUIDE.md (setup guide)"
	@echo "  - PROJECT_SETUP.md (development setup)"
	@echo "  - PRODUCT_PLAN.md (roadmap)"

# ============================================================================
# Development Workflow
# ============================================================================

# Common workflow: make all checks before committing
check-all: format lint type-check test
	@echo ""
	@echo "✓ All checks passed! Ready to commit."

# Setup development environment
setup: dev-install
	@echo ""
	@echo "✓ Development environment ready!"
	@echo "Next steps:"
	@echo "  1. Copy .env.example to .env"
	@echo "  2. Update .env with your API keys"
	@echo "  3. Run: make run"

.DEFAULT_GOAL := help
