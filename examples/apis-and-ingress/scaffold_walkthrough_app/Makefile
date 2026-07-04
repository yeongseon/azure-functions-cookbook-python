VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
DEV_EXTRAS := [dev]
INCLUDE_RUFF := 1
INCLUDE_MYPY := 1
INCLUDE_PYTEST := 1

.PHONY: install
install:
	python3 -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip
	$(PIP) install -e .$(DEV_EXTRAS)

.PHONY: lint
lint:
ifeq ($(INCLUDE_RUFF),1)
	$(PYTHON) -m ruff check .
else
	@echo "Ruff is not enabled for the strict preset."
endif

.PHONY: format
format:
ifeq ($(INCLUDE_RUFF),1)
	$(PYTHON) -m ruff format .
else
	@echo "Ruff is not enabled for the strict preset."
endif

.PHONY: typecheck
typecheck:
ifeq ($(INCLUDE_MYPY),1)
	$(PYTHON) -m mypy .
else
	@echo "mypy is not enabled for the strict preset."
endif

.PHONY: test
test:
ifeq ($(INCLUDE_PYTEST),1)
	$(PYTHON) -m pytest
else
	@echo "pytest is not enabled for the strict preset."
endif

.PHONY: check-all
check-all:
ifeq ($(INCLUDE_RUFF),1)
	$(PYTHON) -m ruff check .
endif
ifeq ($(INCLUDE_MYPY),1)
	$(PYTHON) -m mypy .
endif
ifeq ($(INCLUDE_PYTEST),1)
	$(PYTHON) -m pytest
endif
ifeq ($(INCLUDE_RUFF)$(INCLUDE_MYPY)$(INCLUDE_PYTEST),000)
	@echo "No extra quality tooling is enabled for the strict preset."
endif

.PHONY: doctor
doctor:
	$(PYTHON) -m azure_functions_doctor check .
