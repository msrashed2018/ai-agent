.PHONY: help install dev test test-full test-unit test-integration test-e2e test-cov test-watch test-sessions test-permissions test-tasks test-api lint format clean docker-build docker-up docker-down migrate seed-db deps-check quality ci setup

help: ## Show this help message
	@echo 'AI-Agent-API-Service Development Commands'
	@echo '========================================'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies with Poetry
	poetry install --with dev,test

dev: ## Install development dependencies and setup
	poetry install --with dev,test
	pre-commit install || echo "pre-commit not configured"

deps-check: ## Check if test dependencies are installed
	python run_tests.py --check-deps

test: ## Run comprehensive test suite with coverage
	python run_tests.py

test-full: ## Run full test suite (alias for test)
	python run_tests.py

test-unit: ## Run unit tests only
	python run_tests.py --test tests/unit/

test-integration: ## Run integration tests only  
	python run_tests.py --test tests/integration/

test-e2e: ## Run end-to-end tests only
	python run_tests.py --test tests/e2e/

test-cov: ## Run tests with coverage report only
	python run_tests.py --coverage-only

test-watch: ## Run tests in watch mode
	poetry run pytest-watch tests/ -- -v --tb=short

test-sessions: ## Test session functionality
	poetry run pytest tests/unit/test_session_service.py tests/unit/test_sdk_session_service.py -v

test-permissions: ## Test permission system  
	poetry run pytest tests/unit/test_permission_service.py -v

test-tasks: ## Test task management
	poetry run pytest tests/unit/test_task_service.py -v

test-api: ## Test API endpoints
	poetry run pytest tests/integration/test_sessions_api.py -v

lint: ## Run linters
	poetry run ruff check app/ tests/
	@echo "✅ Linting completed"

format: ## Format code
	poetry run black app/ tests/
	poetry run ruff format app/ tests/
	@echo "✅ Code formatting completed"

type-check: ## Run type checking
	poetry run mypy app/
	@echo "✅ Type checking completed"

quality: lint type-check ## Run all code quality checks
	@echo "✅ All code quality checks completed"

ci: deps-check quality test ## Run CI pipeline (deps + quality + tests)
	@echo "🎉 CI pipeline completed successfully!"

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

docker-dev-up: ## Start development infrastructure (postgres, redis)
	docker compose -f docker-compose.dev.yml up -d

docker-dev-down: ## Stop development infrastructure
	docker compose -f docker-compose.dev.yml down

docker-dev-logs: ## Show logs from development infrastructure
	docker compose -f docker-compose.dev.yml logs -f

docker-test-up: ## Start test infrastructure (postgres-test, redis-test)
	docker compose -f docker-compose.test.yml up -d

docker-test-down: ## Stop test infrastructure
	docker compose -f docker-compose.test.yml down

docker-down-all: ## Stop all docker compose services
	docker compose -f docker-compose.dev.yml down || true
	docker compose -f docker-compose.test.yml down || true

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-downgrade: ## Downgrade one migration
	alembic downgrade -1

seed-db: ## Seed the database with default admin user and test data
	poetry run python seed_db.py

run: ## Run the application locally (foreground)
	poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-bg: ## Run the application in background with logging and hot reload
	@mkdir -p logs
	@echo "Starting API service in background..."
	nohup poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 & echo $$! > .api.pid
	@echo "API service started. PID: $$(cat .api.pid)"
	@echo "Logs: tail -f logs/api.log"

run-worker: ## Run Celery worker (foreground)
	poetry run celery -A app.celery_app worker --loglevel=info

run-worker-bg: ## Run Celery worker in background
	@mkdir -p logs
	@echo "Starting Celery worker in background..."
	nohup poetry run celery -A app.celery_app worker --loglevel=info > logs/celery-worker.log 2>&1 & echo $$! > .celery-worker.pid
	@echo "Celery worker started. PID: $$(cat .celery-worker.pid)"
	@echo "Logs: tail -f logs/celery-worker.log"

run-beat: ## Run Celery beat scheduler (foreground)
	poetry run celery -A app.celery_app beat --loglevel=info

run-beat-bg: ## Run Celery beat in background
	@mkdir -p logs
	@echo "Starting Celery beat in background..."
	nohup poetry run celery -A app.celery_app beat --loglevel=info > logs/celery-beat.log 2>&1 & echo $$! > .celery-beat.pid
	@echo "Celery beat started. PID: $$(cat .celery-beat.pid)"
	@echo "Logs: tail -f logs/celery-beat.log"

stop: ## Stop all background services
	@echo "Stopping background services..."
	@if [ -f .api.pid ]; then kill $$(cat .api.pid) 2>/dev/null || true; rm .api.pid; echo "API service stopped"; fi
	@if [ -f .celery-worker.pid ]; then kill $$(cat .celery-worker.pid) 2>/dev/null || true; rm .celery-worker.pid; echo "Celery worker stopped"; fi
	@if [ -f .celery-beat.pid ]; then kill $$(cat .celery-beat.pid) 2>/dev/null || true; rm .celery-beat.pid; echo "Celery beat stopped"; fi

status: ## Show status of background services
	@echo "Background services status:"
	@if [ -f .api.pid ]; then \
		if ps -p $$(cat .api.pid) > /dev/null 2>&1; then \
			echo "  API service: RUNNING (PID: $$(cat .api.pid))"; \
		else \
			echo "  API service: STOPPED (stale PID file)"; \
		fi \
	else \
		echo "  API service: STOPPED"; \
	fi
	@if [ -f .celery-worker.pid ]; then \
		if ps -p $$(cat .celery-worker.pid) > /dev/null 2>&1; then \
			echo "  Celery worker: RUNNING (PID: $$(cat .celery-worker.pid))"; \
		else \
			echo "  Celery worker: STOPPED (stale PID file)"; \
		fi \
	else \
		echo "  Celery worker: STOPPED"; \
	fi
	@if [ -f .celery-beat.pid ]; then \
		if ps -p $$(cat .celery-beat.pid) > /dev/null 2>&1; then \
			echo "  Celery beat: RUNNING (PID: $$(cat .celery-beat.pid))"; \
		else \
			echo "  Celery beat: STOPPED (stale PID file)"; \
		fi \
	else \
		echo "  Celery beat: STOPPED"; \
	fi

logs: ## Tail all logs
	tail -f logs/*.log

login-admin: ## Login as admin and save tokens to .env.tokens
	@python3 scripts/auth_helper.py --user admin

login-user: ## Login as regular user and save tokens to .env.tokens
	@python3 scripts/auth_helper.py --user user

setup: install migrate seed-db ## Complete development setup
	cp .env.example .env 2>/dev/null || echo ".env already exists"
	mkdir -p data/agent-workdirs/active data/agent-workdirs/archives data/reports data/backups/postgres data/backups/redis logs
	@echo "🎉 Development environment setup completed!"

initial-setup: ## Initial setup - copy env file and create directories  
	cp .env.example .env
	mkdir -p data/agent-workdirs/active data/agent-workdirs/archives data/reports data/backups/postgres data/backups/redis logs

db-reset: ## Reset database (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 5
	alembic upgrade head

db-list: ## List all data from a table (usage: make db-list TABLE=users)
	@if [ -z "$(TABLE)" ]; then \
		echo "Error: TABLE parameter required"; \
		echo "Usage: make db-list TABLE=users"; \
		echo "Available tables: users, organizations, sessions, messages, tasks, task_executions, reports, mcp_servers, hooks, audit_logs, tool_calls, working_directories"; \
		exit 1; \
	fi
	@PGPASSWORD=password psql -h localhost -p 5432 -U aiagent -d aiagent_db -x -P pager=off -c "SELECT * FROM $(TABLE);"
