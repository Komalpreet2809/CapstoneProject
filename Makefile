# VoiceServe developer commands. `make help` lists them.
# Recipes avoid shell-specific syntax so they run under sh (Linux, macOS, Git Bash) and
# cmd.exe (GNU Make on Windows) alike.

COMPOSE ?= docker compose
UV ?= uv

.DEFAULT_GOAL := help
.PHONY: help up down restart logs ps smoke seed install test e2e openapi lint fmt hooks clean

# $(info) prints from make itself; plain `echo` is not an executable on Windows.
help:
	$(info VoiceServe make targets)
	$(info - up       build and start every service, wait until healthy, then run smoke checks)
	$(info - down     stop the stack (data volume kept))
	$(info - restart  down then up)
	$(info - logs     follow logs; one service with: make logs s=gateway)
	$(info - ps       show service status)
	$(info - smoke    check every service answers and is ready)
	$(info - seed     replace the Mini UMS data with freshly generated synthetic data)
	$(info - install  install Python and JS dependencies for local development)
	$(info - test     run the Python test suite)
	$(info - e2e      re-seed, then run the browser tests against the running stack)
	$(info - openapi  regenerate docs/api/openapi.json after a deliberate API change)
	$(info - lint     ruff, mypy, eslint and tsc)
	$(info - fmt      auto-format and auto-fix Python code)
	$(info - hooks    install the pre-commit hooks (secret scan, ruff, hygiene))
	$(info - clean    stop the stack and delete its data volume)

up:
	$(COMPOSE) up -d --build --wait --wait-timeout 300
	$(UV) run --no-project scripts/smoke.py --wait 30

down:
	$(COMPOSE) down

restart: down up

logs:
	$(COMPOSE) logs -f --tail=100 $(s)

ps:
	$(COMPOSE) ps

smoke:
	$(UV) run --no-project scripts/smoke.py

seed:
	$(COMPOSE) exec -T mini-ums-api python -m mini_ums_api.seed

install:
	$(UV) sync --all-packages
	npm --prefix apps/mini_ums_web ci
	npm --prefix apps/dashboard ci
	npm --prefix apps/widget ci

# API tests need the `make up` database; REQUIRE_DB turns a missing one into a failure.
test: export REQUIRE_DB = 1
test:
	$(UV) run --all-packages pytest

# Browser tests change data, so they start from a fresh seed.
e2e: seed
	npm --prefix apps/mini_ums_web run e2e

openapi:
	$(UV) run --all-packages python -m mini_ums_api.contract docs/api/openapi.json

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run --all-packages mypy
	npm --prefix apps/mini_ums_web run lint
	npm --prefix apps/dashboard run lint
	npm --prefix apps/widget run lint

fmt:
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

hooks:
	$(UV) run pre-commit install

clean:
	$(COMPOSE) down -v --remove-orphans
