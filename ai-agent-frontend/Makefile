# =================================================================
# AI Agent Frontend Makefile
# =================================================================
# Development commands for the Next.js AI Agent Frontend
#
# Usage: make <command>
# Example: make dev, make build, make stop
# =================================================================

.PHONY: help
.DEFAULT_GOAL := help

# =================================================================
# Configuration
# =================================================================

# Project directory
ROOT_DIR := $(shell pwd)

# Log directory for background processes
LOG_DIR ?= $(ROOT_DIR)/logs

# Port configuration
FRONTEND_PORT ?= 3000

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
CYAN := \033[0;36m
NC := \033[0m

# =================================================================
# Help System
# =================================================================

help: ## Display this help message
	@echo "$(BLUE)═══════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  AI Agent Frontend - Development Commands$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(GREEN)<target>$(NC)\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

# =================================================================
# Setup Commands
# =================================================================

##@ Setup

install: ## Install dependencies
	@echo "$(CYAN)Installing dependencies...$(NC)"
	@npm install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

setup: install ## Initial setup (install dependencies)
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Configure .env.local if needed"
	@echo "  2. Run: make dev"
	@echo ""

# =================================================================
# Development Commands
# =================================================================

##@ Development

dev: ## Start development server (foreground)
	@echo "$(CYAN)Starting Next.js development server...$(NC)"
	@npm run dev

dev-bg: stop ## Start development server in background
	@echo "$(CYAN)Starting Next.js development server in background...$(NC)"
	@mkdir -p $(LOG_DIR)
	@: > $(LOG_DIR)/dev.log
	@nohup npm run dev >> $(LOG_DIR)/dev.log 2>&1 & echo $$! > $(LOG_DIR)/dev.pid
	@sleep 3
	@if [ -f "$(LOG_DIR)/dev.pid" ] && ps -p $$(cat $(LOG_DIR)/dev.pid) > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Development server started (PID: $$(cat $(LOG_DIR)/dev.pid))$(NC)"; \
		echo "$(CYAN)→ Frontend: http://localhost:$(FRONTEND_PORT)$(NC)"; \
		echo "$(CYAN)→ Logs: $(LOG_DIR)/dev.log$(NC)"; \
		echo "$(CYAN)→ Stop: make stop$(NC)"; \
	else \
		echo "$(RED)✗ Failed to start development server$(NC)"; \
		tail -20 $(LOG_DIR)/dev.log; \
		exit 1; \
	fi

stop: ## Stop background development server
	@echo "$(CYAN)Stopping development server...$(NC)"
	@if [ -f "$(LOG_DIR)/dev.pid" ]; then \
		PID=$$(cat $(LOG_DIR)/dev.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "$(YELLOW)Killing process $$PID$(NC)"; \
			kill -15 $$PID 2>/dev/null || true; \
			sleep 2; \
			if ps -p $$PID > /dev/null 2>&1; then \
				echo "$(YELLOW)Force killing process $$PID$(NC)"; \
				kill -9 $$PID 2>/dev/null || true; \
			fi; \
		fi; \
		rm -f $(LOG_DIR)/dev.pid; \
		echo "$(GREEN)✓ Development server stopped$(NC)"; \
	else \
		echo "$(YELLOW)No PID file found. Checking for processes on port $(FRONTEND_PORT)...$(NC)"; \
		lsof -ti:$(FRONTEND_PORT) | xargs -r kill -9 2>/dev/null || true; \
		echo "$(GREEN)✓ Port $(FRONTEND_PORT) cleaned$(NC)"; \
	fi

restart: stop dev-bg ## Restart background development server

logs: ## Tail development server logs
	@if [ -f "$(LOG_DIR)/dev.log" ]; then \
		echo "$(CYAN)Tailing logs (Ctrl+C to stop)...$(NC)"; \
		tail -f $(LOG_DIR)/dev.log; \
	else \
		echo "$(YELLOW)No log file found at $(LOG_DIR)/dev.log$(NC)"; \
	fi

status: ## Check development server status
	@echo ""
	@echo "$(CYAN)AI Agent Frontend Status:$(NC)"
	@echo ""
	@if [ -f "$(LOG_DIR)/dev.pid" ]; then \
		PID=$$(cat $(LOG_DIR)/dev.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "  $(GREEN)✓ Running$(NC) (PID: $$PID)"; \
			echo "  $(CYAN)→ http://localhost:$(FRONTEND_PORT)$(NC)"; \
		else \
			echo "  $(RED)✗ Not running$(NC) (stale PID file)"; \
			rm -f $(LOG_DIR)/dev.pid; \
		fi \
	else \
		echo "  $(YELLOW)✗ Not running$(NC)"; \
	fi
	@echo ""

# =================================================================
# Build Commands
# =================================================================

##@ Build

build: ## Build for production
	@echo "$(CYAN)Building for production...$(NC)"
	@npm run build
	@echo "$(GREEN)✓ Build complete!$(NC)"

start: build ## Start production server
	@echo "$(CYAN)Starting production server...$(NC)"
	@npm run start

preview: build ## Preview production build
	@echo "$(CYAN)Starting production preview...$(NC)"
	@npm run start

# =================================================================
# Quality Commands
# =================================================================

##@ Code Quality

lint: ## Run ESLint
	@echo "$(CYAN)Running ESLint...$(NC)"
	@npm run lint

lint-fix: ## Fix ESLint issues automatically
	@echo "$(CYAN)Fixing ESLint issues...$(NC)"
	@npm run lint -- --fix
	@echo "$(GREEN)✓ Linting complete$(NC)"

type-check: ## Run TypeScript type checking
	@echo "$(CYAN)Running TypeScript type check...$(NC)"
	@npm run type-check

format: ## Format code with Prettier (if configured)
	@echo "$(CYAN)Formatting code...$(NC)"
	@npx prettier --write "src/**/*.{js,jsx,ts,tsx,json,css,md}"
	@echo "$(GREEN)✓ Formatting complete$(NC)"

format-check: ## Check code formatting
	@echo "$(CYAN)Checking code formatting...$(NC)"
	@npx prettier --check "src/**/*.{js,jsx,ts,tsx,json,css,md}"

check: lint type-check ## Run all checks (lint + type-check)
	@echo "$(GREEN)✓ All checks passed$(NC)"

# =================================================================
# Testing Commands
# =================================================================

##@ Testing

test: ## Run tests (if configured)
	@echo "$(CYAN)Running tests...$(NC)"
	@npm test || echo "$(YELLOW)No tests configured$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(CYAN)Running tests in watch mode...$(NC)"
	@npm test -- --watch || echo "$(YELLOW)No tests configured$(NC)"

test-coverage: ## Run tests with coverage
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	@npm test -- --coverage || echo "$(YELLOW)No tests configured$(NC)"

# =================================================================
# Cleanup Commands
# =================================================================

##@ Cleanup

clean: ## Clean build artifacts and caches
	@echo "$(CYAN)Cleaning build artifacts...$(NC)"
	@rm -rf .next
	@rm -rf out
	@rm -rf node_modules/.cache
	@rm -rf $(LOG_DIR)
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean ## Clean everything including node_modules
	@echo "$(CYAN)Removing node_modules...$(NC)"
	@rm -rf node_modules
	@rm -rf package-lock.json
	@echo "$(GREEN)✓ Deep cleanup complete$(NC)"

# =================================================================
# Utility Commands
# =================================================================

##@ Utilities

info: ## Display project information
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  AI Agent Frontend - Project Information$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(CYAN)Project Details:$(NC)"
	@echo "  Name:             ai-agent-frontend"
	@echo "  Framework:        Next.js 14"
	@echo "  Language:         TypeScript"
	@echo "  Port:             $(FRONTEND_PORT)"
	@echo ""
	@echo "$(CYAN)Key Technologies:$(NC)"
	@echo "  - Next.js (React Framework)"
	@echo "  - TypeScript"
	@echo "  - Tailwind CSS"
	@echo "  - shadcn/ui components"
	@echo "  - React Query"
	@echo "  - Zustand (State Management)"
	@echo ""
	@echo "$(CYAN)Environment:$(NC)"
	@echo "  Node:             $$(node --version 2>&1 || echo 'Not installed')"
	@echo "  npm:              $$(npm --version 2>&1 || echo 'Not installed')"
	@echo ""
	@echo "$(CYAN)Useful URLs:$(NC)"
	@echo "  Development:      http://localhost:$(FRONTEND_PORT)"
	@echo "  API Backend:      http://localhost:8888"
	@echo ""
	@echo "$(BLUE)═══════════════════════════════════════════════════════$(NC)"
	@echo ""

deps-update: ## Update dependencies to latest versions
	@echo "$(CYAN)Updating dependencies...$(NC)"
	@npm update
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

deps-check: ## Check for outdated dependencies
	@echo "$(CYAN)Checking for outdated dependencies...$(NC)"
	@npm outdated || true

open: ## Open frontend in default browser
	@echo "$(CYAN)Opening http://localhost:$(FRONTEND_PORT)$(NC)"
	@open http://localhost:$(FRONTEND_PORT) 2>/dev/null || \
		xdg-open http://localhost:$(FRONTEND_PORT) 2>/dev/null || \
		echo "$(YELLOW)Please open http://localhost:$(FRONTEND_PORT) manually$(NC)"

# =================================================================
# Quick Development Workflow
# =================================================================

##@ Quick Start

run: dev-bg ## Quick start: install and run in background (alias for dev-bg)

run-fg: dev ## Quick start: install and run in foreground (alias for dev)

all: install check build ## Run complete workflow: install, check, build
	@echo ""
	@echo "$(GREEN)✓ Complete workflow finished successfully!$(NC)"
	@echo ""
