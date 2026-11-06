SHELL := /bin/bash

.PHONY: help up down logs ps migrate migration-create server-dev client-dev test-server test-client export-openapi generate-types types

help:
	@echo "AD. Sentry Makefile Commands:"
	@echo "-----------------------------------"
	@echo "  make infra-up        - Start infrastructure services (DB, Redis) via Docker Compose"
	@echo "  make infra-down      - Stop infrastructure services"
	@echo "  make infra-logs      - Tail infrastructure container logs"
	@echo "  make migrate         - Run pending database migrations (Alembic)"
	@echo "  make migration-create msg='description' - Generate a new Alembic migration"
	@echo "  make server-dev      - Run FastAPI backend development server"
	@echo "  make client-dev      - Run Vite React frontend development server"
	@echo "  make test-server     - Run backend pytest suite"
	@echo "  make test-client     - Run frontend test suite"
	@echo "  make export-openapi  - Export OpenAPI spec to client/openapi.json"
	@echo "  make generate-types  - Generate TypeScript definitions from client/openapi.json"
	@echo "  make types           - Export OpenAPI spec and generate TypeScript definitions"

up:
	docker compose -f infra/docker-compose.yml --env-file ./server/.env up -d 

down:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

ps:
	docker compose -f infra/docker-compose.yml ps

migrate:
	cd server && .venv/bin/alembic upgrade head

migrationcreate:
	cd server && .venv/bin/alembic revision --autogenerate -m "$(msg)"

migration-rollback:
	cd server && .venv/bin/alembic downgrade -1

server-dev:
	cd server && .venv/bin/fastapi dev

client-dev:
	cd client && pnpm dev

test-server:
	cd server && .venv/bin/pytest

test-client:
	cd client && pnpm test --run

export-openapi:
	cd server && uv run python scripts/export_openapi.py

generate-types:
	cd client && pnpm generate-types

types: export-openapi generate-types
