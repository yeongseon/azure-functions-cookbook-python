VENV_DIR := .venv
PYTHON ?= python
HATCH ?= hatch
ifeq ($(CI),)
RUN := $(HATCH) run python
else
RUN := $(PYTHON)
endif
MAINTENANCE_PYTHON = $(shell environment=$$($(HATCH) env find 2>/dev/null); if test -n "$$environment" && test -x "$$environment/bin/python"; then echo "$$environment/bin/python"; elif test -x "$$VIRTUAL_ENV/bin/python"; then echo "$$VIRTUAL_ENV/bin/python"; elif test -x .venv/bin/python; then echo .venv/bin/python; else command -v python3.11 || command -v python3; fi)

.PHONY: bootstrap ensure-hatch install install-ci shell reset hatch-clean
bootstrap ensure-hatch:
	@command -v $(HATCH) >/dev/null || { echo "Install Hatch once in an isolated tool environment"; exit 1; }
install: ensure-hatch
	@$(HATCH) env create
	@if [ -z "$$CI" ]; then $(MAKE) precommit-install; fi
install-ci:
	@$(PYTHON) -m pip install $(INSTALL_FLAGS) -e ".[dev,docs]"
shell: ensure-hatch
	@$(HATCH) shell
reset: clean-all install
hatch-clean: ensure-hatch
	@$(HATCH) env remove

.PHONY: format format-check style lint typecheck security lint-workflows generated-check check check-all
format:
	@$(RUN) -m ruff format src tests scripts tools/verification*.py
format-check:
	@$(RUN) -m ruff format --check src tests scripts tools/verification*.py
style: lint format-check
lint:
	@$(RUN) -m ruff check src tests tools/verification*.py
	@$(RUN) -m ruff check --target-version py311 --select I,F,UP,FA examples scripts
typecheck:
	@$(RUN) -m mypy src tests tools/verification*.py scripts/run_recipe_tests.py
security:
	@$(RUN) -m bandit -r src
lint-workflows:
	@$(RUN) tools/lint_hatch_matrix.py
	@$(RUN) tools/lint_workflow_pins.py
generated-check:
	@$(RUN) scripts/gen_recipe_index.py --check
	@$(RUN) scripts/gen_recipe_table.py --check
	@$(RUN) scripts/gen_requirements.py --check
check:
	@$(RUN) -m tools.verification focused check -m tools.verification_quality
check-all: verify

.PHONY: test integration verify report clean bicep worker-registration smoke
test integration verify bicep worker-registration smoke:
	@$(RUN) -m tools.verification $@
report clean:
	@$(MAINTENANCE_PYTHON) -m tools.verification $@
.PHONY: doctor
doctor:
	@$(MAINTENANCE_PYTHON) -m tools.verification doctor

.PHONY: recipe-tests
recipe-tests:
	@$(RUN) -m scripts.run_recipe_tests
.PHONY: cov e2e-azure build docs docs-serve
cov: test
e2e-azure:
	@$(RUN) -m tools.verification azure-e2e
build:
	@$(RUN) -m tools.verification focused build -m build
docs:
	@$(RUN) -m tools.verification focused docs -m mkdocs build --strict
docs-serve:
	@$(RUN) -m mkdocs serve

.PHONY: new-recipe
new-recipe:
ifndef CAT
	$(error CAT is not set. Usage: make new-recipe CAT=apis-and-ingress NAME=my_recipe DIFFICULTY=Beginner)
endif
ifndef NAME
	$(error NAME is not set. Usage: make new-recipe CAT=apis-and-ingress NAME=my_recipe DIFFICULTY=Beginner)
endif
ifndef DIFFICULTY
	$(error DIFFICULTY is not set. Usage: make new-recipe CAT=apis-and-ingress NAME=my_recipe DIFFICULTY=Beginner)
endif
	@$(RUN) scripts/new_recipe.py --category "$(CAT)" --name "$(NAME)" --difficulty "$(DIFFICULTY)"

.PHONY: precommit precommit-install publish-test version clean-all help
precommit precommit-install: ensure-hatch
	@$(HATCH) run $@
publish-test: ensure-hatch
	@$(HATCH) publish --repo test
version: ensure-hatch
	@$(HATCH) version
clean-all: clean
	@find . -type d -name "__pycache__" -not -path "./.git/*" -exec rm -rf {} +
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -not -path "./.git/*" -delete
	@rm -rf .DS_Store $(VENV_DIR)
help:
	@echo "Canonical: install install-ci doctor lint format-check format typecheck security check test integration verify e2e-azure report clean"
	@echo "check-all: exact alias of verify; focused commands produce PARTIAL evidence"
