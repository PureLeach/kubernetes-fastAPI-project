SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help
.PHONY: help install run test cov lint fmt typecheck build up down logs k8s-apply k8s-delete k8s-lint clean

IMAGE ?= storage-service
TAG   ?= $(shell awk -F'"' '/^version = /{print $$2; exit}' pyproject.toml)

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Sync deps, install git hooks, create .env if missing
	uv sync
	uv run pre-commit install
	@test -f .env || cp example.env .env

run: ## Run the API locally (uvicorn, no Docker)
	uv run start

test: ## Run the test suite with the coverage gate
	uv run pytest

cov: ## Run the tests and open an HTML coverage report
	uv run pytest --cov-report=html
	@echo "open htmlcov/index.html"

lint: ## Run every pre-commit hook over the whole tree
	uv run pre-commit run --all-files

fmt: ## Apply ruff's formatter and autofixes
	uv run ruff check --fix .
	uv run ruff format .

typecheck: ## Run mypy
	uv run mypy --config-file=pyproject.toml .

build: ## Build the container image as $(IMAGE):$(TAG)
	docker build -t $(IMAGE):$(TAG) -t $(IMAGE):latest .

up: ## Build the image and start the docker compose stack
	docker compose up -d --build

down: ## Stop and remove the docker compose stack
	docker compose down

logs: ## Follow the compose logs
	docker compose logs -f

k8s-apply: ## Apply every manifest via kustomize
	kubectl apply -k k8s

k8s-delete: ## Remove everything this project created
	kubectl delete -k k8s --ignore-not-found

k8s-lint: ## Validate the rendered manifests against the Kubernetes schema
	kubectl kustomize k8s | kubeconform -strict -summary -kubernetes-version 1.30.0 -

clean: ## Remove caches, coverage output and build artefacts
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage coverage.xml dist build
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
