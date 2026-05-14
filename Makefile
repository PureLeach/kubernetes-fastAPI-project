SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help
.PHONY: help install run test lint up down

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Sync deps, install git hooks, create .env if missing
	uv sync
	uv run pre-commit install
	@test -f .env || cp example.env .env

run: ## Run the API locally (uvicorn, no Docker)
	uv run start

test: ## Run the test suite
	uv run pytest

lint: ## Run ruff + ruff-format + mypy + baseline pre-commit hooks
	uv run pre-commit run --all-files

up: ## Build the image and start the docker compose stack
	docker compose up -d --build

down: ## Stop and remove the docker compose stack
	docker compose down
