# HyerEnrichment — common local-dev targets
# Free Docker stack: api, worker, redis, postgres, social-analyzer, google-maps-scraper

.PHONY: help setup up down test smoke migrate

.DEFAULT_GOAL := help

BACKEND_DIR := backend
DOCKER_DIR := backend/docker
FREE_STACK := api worker redis postgres social-analyzer google-maps-scraper

help: ## List available targets
	@echo "Targets:"
	@echo "  setup    Copy backend/.env.example -> backend/.env if missing; pip install -e . in backend"
	@echo "  up       Start free Docker stack (backend/docker)"
	@echo "  down     Stop Docker Compose stack (backend/docker)"
	@echo "  test     Run pytest in backend"
	@echo "  smoke    Run backend/scripts/smoke_test.py"
	@echo "  migrate  Run Alembic upgrade head in backend"
	@echo "  help     Show this help"

setup: ## Env file + editable backend install
	@if [ ! -f $(BACKEND_DIR)/.env ]; then \
		cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env; \
		echo "Created $(BACKEND_DIR)/.env from .env.example"; \
	else \
		echo "$(BACKEND_DIR)/.env already exists - skipping copy"; \
	fi
	cd $(BACKEND_DIR) && pip install -e .

up: ## Start documented free Compose stack
	cd $(DOCKER_DIR) && docker compose up --build $(FREE_STACK)

down: ## Stop Compose stack
	cd $(DOCKER_DIR) && docker compose down

test: ## Run backend pytest
	cd $(BACKEND_DIR) && pytest tests

smoke: ## Quick health smoke test
	python $(BACKEND_DIR)/scripts/smoke_test.py

migrate: ## Apply Alembic migrations
	cd $(BACKEND_DIR) && alembic upgrade head
