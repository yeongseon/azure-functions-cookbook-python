# Changelog

All notable changes to this project will be documented in this file.

### Bug Fixes

- Completely remove azure_functions_knowledge dead code from tracked files 
- Db_input_output use proper @db.inject_reader decorator pattern 
- Make langgraph_agent and db_input_output resilient to optional deps 
- Remove unpublished dependency, stale SignalR refs, add missing smoke tests 
- All tests passing — add missing deps, fix API compat, remove broken SignalR examples (#40) 
- *(ci)* Remove global --cov from addopts; add dedicated smoke/e2e hatch scripts 
- *(ci)* Remove global --cov from addopts; add smoke/e2e hatch scripts 
- Resolve hatchling wheel build failure blocking docs deployment 
- *(deps)* Use unsuffixed azure-functions-openapi dep name 
- Declare wheel packages explicitly for hatchling 

### Documentation

- Add ecosystem coverage status and fix example counts (#77) 
- *(diagram)* Add category overview flowcharts to pattern index pages (#79) 
- Add llms.txt for AI-assistant discoverability (#84) 
- Add 'For AI Coding Assistants' section pointing to llms.txt (#71) 
- *(examples)* Fix phantom azfunc-scaffold references in walkthrough recipe (#63) 
- *(agents)* Standardize AGENTS.md and remove duplicate AGENT.md (#52) 
- Reflect dogfood role — cookbook exercises the full toolkit 
- Fix README titles and add doc site links for all 75 examples 
- Fix stale try/except prose in rag-knowledge-api docs and README 
- Update DESIGN.md category table to reflect 75 examples and current state 
- Fix stale recipe count and examples/README mapping reference 
- Remove stale azure-functions-knowledge-python refs, sync examples/README.md to 75 examples 
- Remove broken SignalR links after example deletion 

### Features

- *(examples)* Add scaffold walkthrough recipe (#61) 
- *(examples)* Add doctor diagnostics endpoint recipe (#59) 

### Miscellaneous Tasks

- *(deps)* Bump github/codeql-action/analyze from 4.36.2 to 4.37.0 (#68) 
- *(deps)* Bump github/codeql-action/init from 4.36.2 to 4.37.0 (#69) 
- *(deps)* Bump actions/setup-python from 6.2.0 to 6.3.0 (#65) 
- *(deps)* Bump actions/stale from 10.3.0 to 10.4.0 (#67) 
- *(ci)* Pin external actions to commit SHAs and document policy (#54) 
- *(deps)* Bump actions/checkout from 6 to 7 (#49) 
- *(deps)* Bump codecov/codecov-action from 6.0.0 to 7.0.0 (#48) 
- *(deps)* Bump github/codeql-action from 4.35.2 to 4.36.2 (#47) 
- *(deps)* Bump actions/stale from 10.2.0 to 10.3.0 (#44) 
- Unpin bandit, mypy, ruff dev deps - use latest compatible versions 
- *(deps)* Bump ruff from 0.15.10 to 0.15.12 
- *(deps)* Bump actions/setup-node from 6.3.0 to 6.4.0 
- *(deps)* Bump mypy from 1.20.0 to 1.20.2 
- *(deps)* Bump actions/upload-pages-artifact from 4 to 5 
- *(deps)* Bump github/codeql-action from 4.35.1 to 4.35.2 

### Other

- Bump version to 0.1.3 

### Refactor

- *(tests)* Extract shared import-isolation harness (#82) 
- *(tests)* Assert __version__ against importlib.metadata (#57) 

### Testing

- Enforce 95% coverage gate on the default test run (#80) 
- Raise coverage to 95%+ and enforce via AGENTS.md and pyproject.toml 

### Bug Fixes

- Oracle review — fix doc-example mismatches, stale paths, add 9 new patterns 
- Address Oracle review — correct docs, IaC, code, and tests 
- Correct EasyAuth principal structure, JWT claims, and auth recipe docs 

### Documentation

- Standardize ecosystem table in README 

### Features

- Add testing guide, service matrix, 5 AI/ML recipes, IaC templates (Bicep+Terraform) for all recipes 
- Big-bang cookbook expansion — 62 pattern recipes, 14 categories, 3-layer docs structure 
- Add cookbook recipes for db, langgraph, and scaffold 
- Add auth recipes (EasyAuth, JWT validation, multi-tenant) and production hardening 

### Miscellaneous Tasks

- *(deps)* Bump actions/setup-python from 5 to 6 
- *(deps)* Bump actions/setup-node from 4.4.0 to 6.3.0 
- *(deps)* Bump actions/upload-pages-artifact from 3 to 4 
- *(deps)* Bump actions/github-script from 8.0.0 to 9.0.0 
- *(deps)* Bump actions/upload-artifact from 7.0.0 to 7.0.1 
- *(deps)* Bump actions/deploy-pages from 4 to 5 
- *(deps)* Bump actions/checkout from 4 to 6 
- Update repo references for azure-functions-{feature}-python naming convention 
- Add llms.txt, llms-full.txt and bump ruff/mypy (#23) 
- *(deps)* Bump anchore/sbom-action from 0.23.1 to 0.24.0 (#11) 
- *(deps)* Bump github/codeql-action from 4.33.0 to 4.35.1 (#13) 
- *(deps)* Bump codecov/codecov-action from 5.5.3 to 6.0.0 (#14) 
- *(deps)* Bump mypy from 1.19.1 to 1.20.0 (#17) 
- Remove unused PyPI publish workflow 

### Bug Fixes

- Repair broken recipe links in index.md and configuration.md 
- Exclude e2e/smoke from default test run, add local.settings.json to gitignore, deduplicate import helper 

### Documentation

- Replace pip install -r requirements.txt with pip install -e . in all example READMEs 
- Add A/B/C production shapes, IaC snippets, and pyproject.toml deployment path 
- Replace architecture descriptions with mermaid diagrams 
- Add mermaid support to mkdocs configuration 
- Add configuration.md, api.md and update mkdocs nav 

### Features

- Add E2E test infrastructure with Azurite + func host 
- Overhaul cookbook with 28 production-quality examples 

### Miscellaneous Tasks

- Release v0.1.2 
- Standardize .gitignore format (#6) 
- Fix repo consistency issues (LICENSE, CI workflow, coverage threshold, ruff version, pre-commit, codecov, SBOM, CodeQL) (#5) 
- *(deps)* Bump ruff from 0.15.5 to 0.15.6 (#4) 
- *(deps)* Update mkdocstrings[python] requirement from <1.0 to <2.0 (#1) 
- *(deps)* Bump anchore/sbom-action from 0.23.0 to 0.23.1 (#3) 
- Enforce coverage fail_under = 95 in pyproject.toml 
- Add keywords to pyproject.toml 
- Add AGENTS.md, Typing classifier, test_public_api, Dev Status 4-Beta, .venv-review in .gitignore 
- Add missing workflows and unify CI patterns 

### Refactor

- Restructure all 28 examples to Blueprint pattern 

### Bug Fixes

- Remove github_actions ecosystem from dependabot config 

### Documentation

- Overhaul documentation to production quality 
- Sync translated READMEs (ko, ja, zh-CN) with English 
- Add Ecosystem section for cross-repo navigation 
- Add example-first design section to PRD 
- Improve architecture, index, and recipes with expanded content 
- Elevate documentation to production quality 
- Add translated READMEs (ko, ja, zh-CN) 
- *(readme)* Rewrite README to match ecosystem structure 
- *(readme)* Add Microsoft trademark disclaimer 

### Features

- Add 5 runnable example projects with smoke tests 

### Miscellaneous Tasks

- Add MkDocs GitHub Pages deploy workflow 
- Unify forbid-korean hook targets 
- Use trusted publishing for cookbook releases 
- Initialize cookbook repository 

### Other

- Bump version to 0.1.1 

### Styling

- Unify tooling — remove black, standardize pre-commit and Makefile 
<!-- generated by git-cliff -->
