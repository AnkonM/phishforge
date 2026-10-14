.PHONY: dev demo test test-core test-server test-web build start seed install

VENV := .venv/bin

install:
	python3 -m venv .venv
	$(VENV)/pip install -q -r requirements.txt -r server/requirements.txt
	cd web && npm install

seed:
	$(VENV)/python scripts/seed_runs.py

## One command, development: backend (reload) + frontend (Vite), both live.
dev:
	bash scripts/dev.sh

## Same as dev, but forces the mock provider (no live API calls possible).
demo:
	PHISHFORGE_DEMO=1 bash scripts/dev.sh

## Original pipeline suite (must stay untouched/passing) + Console backend suite.
test-core:
	$(VENV)/python -m pytest tests/ -v

test-server:
	$(VENV)/python -m pytest server/tests/ -v

test-web:
	cd web && npx tsc -b --noEmit && npx oxlint src && npx vitest run

test: test-core test-server test-web

## Production frontend build (output: web/dist).
build:
	cd web && npm run build

## Serve the built SPA + API from one FastAPI process (run `make build` first).
start: build
	$(VENV)/python -m server.main
