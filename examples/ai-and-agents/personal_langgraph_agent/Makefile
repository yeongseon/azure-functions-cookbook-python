VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python

.PHONY: install lint typecheck test check-all
install:
	uv venv $(VENV_DIR)
	uv pip install --python $(PYTHON) -e ".[dev]"

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy .

test:
	$(PYTHON) -m pytest

check-all: lint typecheck test
