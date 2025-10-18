.PHONY: help install dev test lint format clean

help:
	@echo "Available commands:"
	@echo "  make install    Install dependencies"
	@echo "  make dev        Install with dev dependencies"
	@echo "  make test       Run tests"
	@echo "  make lint       Run linters"
	@echo "  make format     Format code"
	@echo "  make clean      Clean build artifacts"

install:
	poetry install --no-dev

dev:
	poetry install

test:
	poetry run pytest tests/ -v

test-cov:
	poetry run pytest tests/ --cov=ai_agent_cli --cov-report=html --cov-report=term

lint:
	poetry run ruff check ai_agent_cli/
	poetry run mypy ai_agent_cli/

format:
	poetry run black ai_agent_cli/ tests/
	poetry run ruff check --fix ai_agent_cli/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
