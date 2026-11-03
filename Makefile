VENV_DIR := .venv
# The interpreter you select: it builds the virtual environment, `make doctor` checks it and
# `make install-ci` installs into it.
PYTHON ?= python3
PIP := $(VENV_DIR)/bin/pip
HATCH := $(VENV_DIR)/bin/hatch

# POSIX sh helper: a tool counts only if `command -v` resolves it to an executable regular file.
# dash's `command -v ./path` accepts any existing path, and `-x` alone is also true for a directory.
HAVE := have() { p="$$(command -v "$$1")"; [ -f "$$p" ] && [ -x "$$p" ]; };

# Idempotent: creates .venv and installs Hatch only while they are missing; never upgrades pip.
.PHONY: bootstrap
bootstrap:
	@test -d "$(VENV_DIR)" || { echo "Creating virtual environment..."; $(PYTHON) -m venv "$(VENV_DIR)"; }
	@$(HAVE) have "$(HATCH)" || { echo "Installing Hatch..."; "$(PIP)" install --disable-pip-version-check --quiet hatch; }

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

# Installs into the selected interpreter (PYTHON), never into Hatch's default environment.
.PHONY: install-ci
install-ci:
	@$(PYTHON) -m pip install -e ".[dev]"

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
	@$(HATCH) run python tools/lint_workflow_pins.py
.PHONY: security
security: ensure-hatch
	@$(HATCH) run security
	@$(MAKE) security-static SECURITY_PYTHON="$(HATCH) run python"

# Additive security policy interface; plain Python supports minimal CI scanner jobs.
SECURITY_PYTHON ?= python3
.PHONY: security-manifest security-static security-semgrep security-dependencies security-dependencies-report security-host
security-manifest:
	@$(SECURITY_PYTHON) -m tools.recipe_security

security-static:
	@$(SECURITY_PYTHON) -m tools.security_evidence all

security-semgrep:
	@$(SECURITY_PYTHON) -m tools.security_evidence semgrep --outcome "$$SCANNER_OUTCOME" --output security-results/semgrep || status=$$?; \
	test "$${status:-0}" -eq 3 -o "$${status:-0}" -eq 0

security-dependencies:
	@$(SECURITY_PYTHON) -m tools.dependency_audit_policy

security-dependencies-report:
	@$(SECURITY_PYTHON) -m tools.dependency_audit_policy --reporting

security-host: ensure-hatch
	@COOKBOOK_RUN_PAID_AI_HOST=true $(HATCH) run pytest tests/test_paid_ai_host_security.py --no-cov -q

.PHONY: recipe-tests docs-strict
recipe-tests: ensure-hatch
	@$(HATCH) run python scripts/run_recipe_tests.py

docs-strict: ensure-hatch
	@$(HATCH) run mkdocs build --strict

# `lint` already runs the type check (hatch script `lint` = style + typecheck), so mypy runs once.
.PHONY: generated-check
generated-check: ensure-hatch
	@$(HATCH) run python scripts/gen_recipe_index.py --check
	@$(HATCH) run python scripts/gen_recipe_table.py --check
	@$(HATCH) run python scripts/gen_requirements.py --check

.PHONY: check
check: lint lint-workflows generated-check
	@echo "Lint, type check, workflow lints and generated-file checks passed."

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

# Full local verification. A required lane fails on a skipped or xfailed test
# (tools/pytest_fail_on_skip.py) and pytest exits 5 when a lane selects nothing. PYTEST_ADDOPTS is
# set, not appended to, so a stray value in the caller's environment cannot deselect tests.
FAIL_ON_SKIP := -p tools.pytest_fail_on_skip

# Emulator lanes: the e2e fixtures start Azurite and `func start` themselves (tests/e2e/conftest.py).
.PHONY: integration
integration: ensure-hatch
	@$(HAVE) missing=""; for tool in func azurite; do have "$$tool" || missing="$$missing $$tool"; done; \
	[ -z "$$missing" ] || { echo "integration: missing required tool(s):$$missing (see make doctor)"; exit 2; }
	@PYTEST_ADDOPTS="$(FAIL_ON_SKIP)" $(HATCH) run smoke
	@PYTEST_ADDOPTS="$(FAIL_ON_SKIP)" $(HATCH) run e2e

.PHONY: bicep
bicep: ensure-hatch
	@$(HATCH) run python tools/compile_bicep_templates.py

# Needs network (it clones the pinned worker) and the worker's runtime requirements, which live in
# the `worker` Hatch environment (pyproject.toml) rather than in the recipes' dev extras.
.PHONY: worker-registration
worker-registration: ensure-hatch
	@PYTEST_ADDOPTS="$(FAIL_ON_SKIP)" $(HATCH) run worker:registration

# Each part runs once and the first failure stops the run. Serial even under `make -j`: the lanes
# share Azurite's fixed ports and the Hatch environments. `check-all` is the narrower everyday gate
# and keeps its meaning.
.NOTPARALLEL: verify
.PHONY: verify
verify: check test recipe-tests bicep worker-registration integration build docs-strict
	@echo "Full local verification passed."

.PHONY: new-recipe
new-recipe: ensure-hatch
ifndef CAT
	$(error CAT is not set. Usage: make new-recipe CAT=apis-and-ingress NAME=my_recipe DIFFICULTY=Beginner)
endif
ifndef NAME
	$(error NAME is not set. Usage: make new-recipe CAT=apis-and-ingress NAME=my_recipe DIFFICULTY=Beginner)
endif
ifndef DIFFICULTY
	$(error DIFFICULTY is not set. Usage: make new-recipe CAT=apis-and-ingress NAME=my_recipe DIFFICULTY=Beginner (one of Beginner, Intermediate, Advanced))
endif
	@$(HATCH) run python scripts/new_recipe.py --category "$(CAT)" --name "$(NAME)" --difficulty "$(DIFFICULTY)"

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

# What `make verify` needs, checked read-only: no prerequisites, so it never installs anything,
# creates .venv or runs a test. (The product CLI is `azure-functions-doctor`, not this target.)
# Bicep is looked up the way tools/compile_bicep_templates.py does: BICEP_CLI, else PATH.
.PHONY: doctor
doctor:
	@missing=0; $(HAVE) \
	if "$(PYTHON)" -c 'import sys; sys.exit(sys.version_info < (3, 11))' > /dev/null 2>&1; then \
		echo "ok       $(PYTHON) (python >= 3.11)"; \
	else echo "MISSING  python >= 3.11 ($(PYTHON) is missing or older; select one with PYTHON=python3.11)"; missing=1; fi; \
	for tool in "$(HATCH)" uv git func azurite "$${BICEP_CLI:-bicep}"; do \
		if have "$$tool"; then echo "ok       $$tool"; \
		else echo "MISSING  $$tool"; missing=1; fi; \
	done; \
	[ $$missing -eq 0 ] || { echo "doctor: INCOMPLETE - make verify needs the MISSING tools above (Hatch: run make install)"; exit 1; }; \
	echo "doctor: ok"
