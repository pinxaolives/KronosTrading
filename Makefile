.PHONY: help setup setup-kronos lint format typecheck test check config-check backtest paper report

UV ?= uv
RUN = $(UV) run

help:
	@echo "setup         install core + dev dependencies (no torch)"
	@echo "setup-kronos  also install torch (CPU) + Kronos deps"
	@echo "lint/format   ruff"
	@echo "typecheck     mypy (strict)"
	@echo "test          pytest (offline tests only)"
	@echo "check         lint + typecheck + test"
	@echo "config-check  validate config/default.yaml"
	@echo "backtest | paper | report   (phases 2-3, not implemented yet)"

setup:
	git submodule update --init --recursive
	$(UV) sync --python 3.11 --extra dev

setup-kronos:
	git submodule update --init --recursive
	$(UV) sync --python 3.11 --extra dev --extra kronos

lint:
	$(RUN) ruff check src tests
	$(RUN) ruff format --check src tests

format:
	$(RUN) ruff format src tests
	$(RUN) ruff check --fix src tests

typecheck:
	$(RUN) mypy

test:
	$(RUN) pytest -m "not network and not kronos"

check: lint typecheck test

config-check:
	$(RUN) kt config-check

backtest paper report:
	@echo "'$@' arrives in a later phase." && exit 1
