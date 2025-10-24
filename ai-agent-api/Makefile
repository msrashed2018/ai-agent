.PHONY: help install dev test lint format clean migrate seed setup health
.PHONY: infra-start infra-stop infra-restart infra-logs infra-status infra-clean
.PHONY: api-start api-stop api-restart api-logs
.PHONY: start-all stop-all restart-all start stop restart status
.PHONY: task-list task-create task-execute task-status
.PHONY: execution-status execution-monitor session-monitor
.PHONY: login celery-inspect

# ============================================================================
# HELP
# ============================================================================

help: ## Show this help message
	@echo '$(BOLD)$(CYAN)AI Agent API - Development Commands$(NC)'
	@echo '=========================================='
	@echo ''
	@echo '$(BOLD)Quick Start:$(NC)'
	@echo '  make setup              # First-time setup'
	@echo '  make start-all          # Start everything (infra + API)'
	@echo '  make login              # Login as admin'
	@echo '  make task-list          # List tasks'
	@echo ''
	@echo '$(BOLD)Main Commands:$(NC)'
	@echo '  make start-all          # Start infrastructure + API'
	@echo '  make stop-all           # Stop everything'
	@echo '  make api-restart        # Restart API only'
	@echo '  make infra-restart      # Restart infrastructure only'
	@echo '  make status             # Show service status'
	@echo ''
	@echo '$(BOLD)All Available Commands:$(NC)'
	@awk 'BEGIN {FS = ":.*?## "; printf ""} /^[a-zA-Z_-]+:.*?## / {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

# ============================================================================
# INSTALLATION & SETUP
# ============================================================================

install: ## Install dependencies with Poetry
	poetry install --with dev,test

dev: install ## Install development dependencies
	poetry install --with dev,test
	pre-commit install || echo "pre-commit not configured"

setup: install docker-up migrate seed ## Complete first-time setup
	@mkdir -p data/agent-workdirs/active data/agent-workdirs/archives data/reports logs logs/monitoring
	@cp .env.example .env 2>/dev/null || echo ".env already exists"
	@echo "✅ Setup complete! Run 'make start' to begin."

# ============================================================================
# DOCKER INFRASTRUCTURE (Postgres, Redis, Celery)
# ============================================================================

infra-start: ## Start Docker infrastructure (Postgres + Redis + Celery)
	@echo "Starting Docker infrastructure..."
	docker compose -f docker-compose.dev.yml up -d
	@echo "✅ Infrastructure started (Postgres, Redis, Celery)"
	@echo "   Celery workers are installing dependencies on first start..."
	@echo "   Run 'make api-start' to start the API locally"

infra-stop: ## Stop Docker infrastructure
	@echo "Stopping Docker infrastructure..."
	docker compose -f docker-compose.dev.yml down
	@echo "✅ Infrastructure stopped"

infra-restart: infra-stop infra-start ## Restart Docker infrastructure

infra-logs: ## View Docker infrastructure logs
	docker compose -f docker-compose.dev.yml logs -f

infra-status: ## Show Docker container status
	@echo "$(BOLD)Docker Infrastructure Status:$(NC)"
	@docker compose -f docker-compose.dev.yml ps

infra-clean: ## Remove all containers and volumes (WARNING: deletes data)
	docker compose -f docker-compose.dev.yml down -v
	@echo "⚠️  All infrastructure data removed"

# ============================================================================
# API SERVICE (Runs locally for Claude Code CLI access)
# ============================================================================

api-start: ## Start API server locally (use 'make start-all' to start everything)
	@mkdir -p logs
	@echo "Starting API server locally..."
	@nohup poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 & echo $$! > .api.pid
	@sleep 2
	@echo "✅ API server started"
	@echo "   API: http://localhost:8000"
	@echo "   Docs: http://localhost:8000/docs"
	@echo "   Logs: make api-logs"

api-stop: ## Stop API server only
	@echo "Stopping API server..."
	@if [ -f .api.pid ]; then kill $$(cat .api.pid) 2>/dev/null || true; rm .api.pid; echo "✅ API stopped"; else echo "API not running"; fi

api-restart: api-stop api-start ## Restart API server only

api-logs: ## Tail API logs
	tail -f logs/api.log

# ============================================================================
# COMBINED COMMANDS (Infrastructure + API)
# ============================================================================

start-all: infra-start api-start ## Start everything (Infrastructure + API) - ONE COMMAND
	@echo ""
	@echo "$(GREEN)✅ Everything is running!$(NC)"
	@echo "   API: http://localhost:8000"
	@echo "   Docs: http://localhost:8000/docs"
	@echo ""
	@echo "$(CYAN)Next steps:$(NC)"
	@echo "   make login              # Login as admin"
	@echo "   make task-list          # List tasks"
	@echo "   make status             # Check all services"
	@echo "   make api-restart        # Restart API only"
	@echo "   make stop-all           # Stop everything"

stop-all: api-stop infra-stop ## Stop everything (API + Infrastructure)
	@echo "✅ All services stopped"

restart-all: stop-all start-all ## Restart everything

# Legacy aliases for backward compatibility
start: start-all ## Alias for start-all
stop: stop-all ## Alias for stop-all
restart: restart-all ## Alias for restart-all

status: ## Show status of all services (API + Infrastructure)
	@echo "$(BOLD)$(CYAN)Service Status:$(NC)"
	@echo ""
	@echo "$(BOLD)API Service (Local):$(NC)"
	@if [ -f .api.pid ] && ps -p $$(cat .api.pid) > /dev/null 2>&1; then \
		echo "  API Server:      $(GREEN)RUNNING$(NC) (PID: $$(cat .api.pid))"; \
		echo "  URL:             http://localhost:8000"; \
	else \
		echo "  API Server:      $(RED)STOPPED$(NC)"; \
	fi
	@echo ""
	@echo "$(BOLD)Infrastructure (Docker):$(NC)"
	@docker compose -f docker-compose.dev.yml ps --format "table {{.Service}}\t{{.Status}}" 2>/dev/null || echo "  Docker not running"
	@echo ""

health: ## Check API health
	@python3 scripts/aiagent.py health

# ============================================================================
# DATABASE
# ============================================================================

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration (interactive)
	@read -p "Migration name: " name; \
	alembic revision --autogenerate -m "$$name"

migrate-down: ## Rollback one migration
	alembic downgrade -1

seed: ## Seed database with test data
	poetry run python seed_db.py

db-reset: ## Reset database (WARNING: destroys all data)
	docker compose down postgres -v
	docker compose up -d postgres
	@sleep 5
	alembic upgrade head
	poetry run python seed_db.py

# ============================================================================
# DEVELOPMENT
# ============================================================================

test: ## Run all tests
	python run_tests.py

test-unit: ## Run unit tests only
	python run_tests.py --test tests/unit/

test-integration: ## Run integration tests only
	python run_tests.py --test tests/integration/

lint: ## Run linters
	poetry run ruff check app/ tests/
	@echo "✅ Linting completed"

format: ## Format code
	poetry run black app/ tests/
	poetry run ruff format app/ tests/
	@echo "✅ Code formatted"

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage

# ============================================================================
# AUTHENTICATION
# ============================================================================

login: ## Login as admin and save tokens
	@python3 scripts/auth_helper.py --user admin

login-user: ## Login as regular user
	@python3 scripts/auth_helper.py --user user

# ============================================================================
# CLI COMMANDS (Unified Python CLI)
# ============================================================================

task-list: ## List all tasks
	@python3 scripts/aiagent.py task list

task-create: ## Create a task (interactive)
	@read -p "Task name: " name; \
	read -p "Prompt template: " prompt; \
	read -p "Tags (comma-separated, optional): " tags; \
	python3 scripts/aiagent.py task create "$$prompt" --name "$$name" $${tags:+--tags $$tags} --report

task-execute: ## Execute a task (usage: make task-execute TASK_ID=<id>)
	@if [ -z "$(TASK_ID)" ]; then \
		echo "Usage: make task-execute TASK_ID=<task-id>"; \
		echo "Example: make task-execute TASK_ID=e65a456f-7841-4397-be65-e2c694ee2a80"; \
		exit 1; \
	fi
	@python3 scripts/aiagent.py task execute $(TASK_ID)

task-status: ## Get task status (usage: make task-status TASK_ID=<id>)
	@if [ -z "$(TASK_ID)" ]; then \
		echo "Usage: make task-status TASK_ID=<task-id>"; \
		exit 1; \
	fi
	@python3 scripts/aiagent.py task status $(TASK_ID)

execution-status: ## Get execution status (usage: make execution-status EXEC_ID=<id>)
	@if [ -z "$(EXEC_ID)" ]; then \
		echo "Usage: make execution-status EXEC_ID=<execution-id>"; \
		exit 1; \
	fi
	@python3 scripts/aiagent.py execution status $(EXEC_ID)

execution-monitor: ## Monitor execution with watch mode (usage: make execution-monitor EXEC_ID=<id>)
	@if [ -z "$(EXEC_ID)" ]; then \
		echo "Usage: make execution-monitor EXEC_ID=<execution-id>"; \
		exit 1; \
	fi
	@python3 scripts/aiagent.py execution monitor $(EXEC_ID) --watch

execution-logs: ## Show execution logs (usage: make execution-logs EXEC_ID=<id>)
	@if [ -z "$(EXEC_ID)" ]; then \
		echo "Usage: make execution-logs EXEC_ID=<execution-id>"; \
		exit 1; \
	fi
	@python3 scripts/aiagent.py execution logs $(EXEC_ID)

session-monitor: ## Monitor session (usage: make session-monitor SESSION_ID=<id>)
	@if [ -z "$(SESSION_ID)" ]; then \
		echo "Usage: make session-monitor SESSION_ID=<session-id>"; \
		exit 1; \
	fi
	@python3 scripts/aiagent.py session monitor $(SESSION_ID)

session-messages: ## List session messages (usage: make session-messages SESSION_ID=<id>)
	@if [ -z "$(SESSION_ID)" ]; then \
		echo "Usage: make session-messages SESSION_ID=<session-id>"; \
		exit 1; \
	fi
	@python3 scripts/aiagent.py session messages $(SESSION_ID)

# ============================================================================
# CELERY
# ============================================================================

celery-inspect: ## Inspect Celery worker status
	@docker compose exec celery-worker celery -A app.celery_app inspect active || echo "Worker not available"
	@echo ""
	@docker compose exec celery-worker celery -A app.celery_app inspect registered || echo "Worker not available"

celery-logs: ## View Celery worker logs
	docker compose logs -f celery-worker

# ============================================================================
# COLORS
# ============================================================================

BOLD := \033[1m
CYAN := \033[0;36m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m
