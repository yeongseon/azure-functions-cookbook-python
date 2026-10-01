VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
HATCH := $(VENV_DIR)/bin/hatch

.PHONY: bootstrap
bootstrap:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV_DIR); \
	fi
	@echo "Ensuring Hatch is installed in virtual environment..."
	@$(PIP) install --upgrade pip > /dev/null
	@$(PIP) install hatch > /dev/null
	@echo "Hatch installed at $(HATCH)"

.PHONY: ensure-hatch
ensure-hatch: bootstrap

.PHONY: install
install: ensure-hatch
	@$(HATCH) env create
	@if [ -n "$$CI" ]; then \
		echo "CI detected: skipping pre-commit hook installation"; \
	else \
		$(MAKE) precommit-install; \
	fi

.PHONY: shell
shell: ensure-hatch
	@$(HATCH) shell

.PHONY: reset
reset: clean-all install
	@echo "Project reset complete."

.PHONY: hatch-clean
hatch-clean: ensure-hatch
	@$(HATCH) env remove || echo "No hatch environment to remove"

.PHONY: format
format: ensure-hatch
	@$(HATCH) run format

.PHONY: format-check
format-check: ensure-hatch
	@$(HATCH) run format-check

.PHONY: style
style: ensure-hatch
	@$(HATCH) run style

.PHONY: typecheck
typecheck: ensure-hatch
	@$(HATCH) run typecheck

.PHONY: lint
lint: ensure-hatch
	@$(HATCH) run lint

.PHONY: lint-workflows
lint-workflows: ensure-hatch
	@$(HATCH) run python tools/lint_hatch_matrix.py
.PHONY: security
security: ensure-hatch
	@$(HATCH) run security

.PHONY: check
check: ensure-hatch
	@$(MAKE) lint
	@$(MAKE) lint-workflows
	@$(MAKE) typecheck
	@echo "Lint and type check passed."

.PHONY: check-all
check-all: ensure-hatch
	@$(MAKE) check
	@$(MAKE) test
	@$(MAKE) security
	@echo "All checks passed including tests and security scan."

.PHONY: precommit
precommit: ensure-hatch
	@$(HATCH) run precommit

.PHONY: precommit-install
precommit-install: ensure-hatch
	@$(HATCH) run precommit-install

.PHONY: test
test: ensure-hatch
	@echo "Running tests..."
	@$(HATCH) run test

.PHONY: new-recipe
new-recipe: ensure-hatch
ifndef CAT
	$(error CAT is not set. Usage: make new-recipe CAT=apis-and-ingress NAME=my_recipe)
endif
ifndef NAME
	$(error NAME is not set. Usage: make new-recipe CAT=apis-and-ingress NAME=my_recipe)
endif
	@$(HATCH) run python scripts/new_recipe.py --category "$(CAT)" --name "$(NAME)"

.PHONY: cov
cov: ensure-hatch
	@$(HATCH) run cov
	@echo "Open htmlcov/index.html in your browser to view the coverage report."
	@echo "coverage.xml generated for Codecov upload."

.PHONY: build
build: ensure-hatch
	@$(HATCH) build

.PHONY: publish-test
publish-test: ensure-hatch
	@$(HATCH) publish --repo test

.PHONY: version
version: ensure-hatch
	@echo "Current version:"
	@$(HATCH) version

.PHONY: docs
docs:
	@if [ -n "$$CI" ]; then \
		echo "CI detected: running MkDocs directly"; \
		python -m pip install --upgrade pip > /dev/null 2>&1 || true; \
		pip install "mkdocs<2.0" "mkdocs-material<10.0" "mkdocstrings[python]<1.0" > /dev/null 2>&1; \
		mkdocs build; \
	else \
		$(MAKE) ensure-hatch > /dev/null; \
		$(HATCH) run mkdocs build; \
	fi

.PHONY: docs-serve
docs-serve: ensure-hatch
	@$(HATCH) run docs

.PHONY: clean
clean:
	@rm -rf *.egg-info dist build __pycache__ .pytest_cache

.PHONY: clean-all
clean-all: clean
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	@rm -rf .mypy_cache .ruff_cache .pytest_cache .coverage coverage.xml htmlcov .DS_Store $(VENV_DIR) site

.PHONY: help
help:
	@echo "Available commands:" && \
	grep -E '^\.PHONY: ' Makefile | cut -d ':' -f2 | xargs -n1 echo "  - make"

.PHONY: doctor
doctor: ensure-hatch
	@echo "Checking project health..."
	@$(MAKE) check-all && echo "All checks passed." || { echo "Some checks failed."; exit 1; }
