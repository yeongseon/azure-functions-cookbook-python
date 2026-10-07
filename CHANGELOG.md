# Changelog

## [0.4.0](https://github.com/yeongseon/azure-functions-cookbook-python/compare/v0.3.2...v0.4.0) (2026-10-07)


### Features

* **python:** require Python 3.11 or newer ([#301](https://github.com/yeongseon/azure-functions-cookbook-python/issues/301)) ([f54642f](https://github.com/yeongseon/azure-functions-cookbook-python/commit/f54642f24e6693f6bcfea75899e66e77697735df)), closes [#298](https://github.com/yeongseon/azure-functions-cookbook-python/issues/298)

## [0.3.2](https://github.com/yeongseon/azure-functions-cookbook-python/compare/v0.3.1...v0.3.2) (2026-10-04)


### Bug Fixes

* **deps:** bump azure-functions-logging ([91b08ba](https://github.com/yeongseon/azure-functions-cookbook-python/commit/91b08baf2150d1c0b8f3c3ae5dfeb480c4fda77e))
* **deps:** bump azure-functions-logging from 0.12.0 to 0.12.1 in the python-dependencies group ([#284](https://github.com/yeongseon/azure-functions-cookbook-python/issues/284)) ([91b08ba](https://github.com/yeongseon/azure-functions-cookbook-python/commit/91b08baf2150d1c0b8f3c3ae5dfeb480c4fda77e))
* **examples:** import family packages directly in recipes ([#288](https://github.com/yeongseon/azure-functions-cookbook-python/issues/288)) ([80c2515](https://github.com/yeongseon/azure-functions-cookbook-python/commit/80c2515bbb1ece6f55269deee7c885da4f0b4726))
* **examples:** raise family dependency floors to working versions ([#287](https://github.com/yeongseon/azure-functions-cookbook-python/issues/287)) ([8789fbd](https://github.com/yeongseon/azure-functions-cookbook-python/commit/8789fbd3ac1edc50265491045f87f28d85fcacbd))
* **infra:** declare Linux plans in recipe Bicep files ([#290](https://github.com/yeongseon/azure-functions-cookbook-python/issues/290)) ([4f7a7a8](https://github.com/yeongseon/azure-functions-cookbook-python/commit/4f7a7a87f7ad699169f74f6dce73ad0d077ddcf8))

## [0.3.1](https://github.com/yeongseon/azure-functions-cookbook-python/compare/v0.3.0...v0.3.1) (2026-10-02)


### Bug Fixes

* **auth-jwt:** accept role arrays during authorization ([#271](https://github.com/yeongseon/azure-functions-cookbook-python/issues/271)) ([2c64ecc](https://github.com/yeongseon/azure-functions-cookbook-python/commit/2c64ecc6a7f36a48584746a65cf3c81adb859ab8))

## [0.3.0](https://github.com/yeongseon/azure-functions-cookbook-python/compare/v0.2.0...v0.3.0) (2026-10-01)


### Features

* add recipe index and find_recipe helper ([#127](https://github.com/yeongseon/azure-functions-cookbook-python/issues/127)) ([178fcff](https://github.com/yeongseon/azure-functions-cookbook-python/commit/178fcff4e21f3d30ce4f66434b42e12bd2dd2dc5))
* **examples:** add doctor diagnostics endpoint recipe ([#59](https://github.com/yeongseon/azure-functions-cookbook-python/issues/59)) ([08b8f98](https://github.com/yeongseon/azure-functions-cookbook-python/commit/08b8f98b9d1027986297ccb895795d444b1e122b)), closes [#58](https://github.com/yeongseon/azure-functions-cookbook-python/issues/58)
* **examples:** add per-example recipe.yaml metadata ([#94](https://github.com/yeongseon/azure-functions-cookbook-python/issues/94)) ([e0d3806](https://github.com/yeongseon/azure-functions-cookbook-python/commit/e0d380671d24b6d46aac107d8ab3d6f6c83dd60d))
* **examples:** add scaffold walkthrough recipe ([#61](https://github.com/yeongseon/azure-functions-cookbook-python/issues/61)) ([78747d3](https://github.com/yeongseon/azure-functions-cookbook-python/commit/78747d3ec0dd4197794af3023cc7c27b9fa940a2)), closes [#60](https://github.com/yeongseon/azure-functions-cookbook-python/issues/60) [#50](https://github.com/yeongseon/azure-functions-cookbook-python/issues/50)
* **examples:** dogfood durable-graph, knowledge, and langgraph tool-use recipes ([#100](https://github.com/yeongseon/azure-functions-cookbook-python/issues/100)) ([cf47696](https://github.com/yeongseon/azure-functions-cookbook-python/commit/cf476967cfb824e3c651124d3512a1169adb3e9c)), closes [#50](https://github.com/yeongseon/azure-functions-cookbook-python/issues/50)
* **recipes:** support multi-term keyword search in find_recipe ([#141](https://github.com/yeongseon/azure-functions-cookbook-python/issues/141)) ([5703f08](https://github.com/yeongseon/azure-functions-cookbook-python/commit/5703f0870292e8289ac80d4b7f02a2fa7af1db83))


### Bug Fixes

* add conservative version bounds to optional dependencies ([#125](https://github.com/yeongseon/azure-functions-cookbook-python/issues/125)) ([9eeeac0](https://github.com/yeongseon/azure-functions-cookbook-python/commit/9eeeac0fe1291bcf20fd94960daca901f8edd7c2))
* all tests passing — add missing deps, fix API compat, remove broken SignalR examples ([#40](https://github.com/yeongseon/azure-functions-cookbook-python/issues/40)) ([edbcfcd](https://github.com/yeongseon/azure-functions-cookbook-python/commit/edbcfcd426d6e688570c61c0040acc4965fb5e33))
* **async_job_lifecycle:** place [@validate](https://github.com/validate)_http below [@app](https://github.com/app).durable_client_input so validation runs ([496c0c3](https://github.com/yeongseon/azure-functions-cookbook-python/commit/496c0c383f3b88ba2a145db603a8083fc5e0b71b))
* **build:** fail make doctor when checks fail ([#260](https://github.com/yeongseon/azure-functions-cookbook-python/issues/260)) ([95bf85a](https://github.com/yeongseon/azure-functions-cookbook-python/commit/95bf85a90b7d8cb95fdff4ae3fa2037329e6a8cc))
* **ci:** pin a mutable action, adopt the pin linter, correct release wording and stale inputs ([#237](https://github.com/yeongseon/azure-functions-cookbook-python/issues/237)) ([661d4bb](https://github.com/yeongseon/azure-functions-cookbook-python/commit/661d4bb733f5ac6a1c405353ca344286c5fd0a62))
* **ci:** remove global --cov from addopts; add dedicated smoke/e2e hatch scripts ([ea928bc](https://github.com/yeongseon/azure-functions-cookbook-python/commit/ea928bc17930506ef7b503c2a4241cbcef93dbe8))
* **ci:** remove global --cov from addopts; add dedicated smoke/e2e hatch scripts ([ea928bc](https://github.com/yeongseon/azure-functions-cookbook-python/commit/ea928bc17930506ef7b503c2a4241cbcef93dbe8))
* **ci:** remove global --cov from addopts; add smoke/e2e hatch scripts ([1086b10](https://github.com/yeongseon/azure-functions-cookbook-python/commit/1086b103db551b63e7beaf84bbc42e035e77cf6e))
* **ci:** stop the changed-file format gate failing open ([#234](https://github.com/yeongseon/azure-functions-cookbook-python/issues/234)) ([f4c5102](https://github.com/yeongseon/azure-functions-cookbook-python/commit/f4c5102c48a09309f825dc65bf6bbf58204395de))
* **compat:** deprecate Python 3.10 ahead of its removal ([#259](https://github.com/yeongseon/azure-functions-cookbook-python/issues/259)) ([0c38fb3](https://github.com/yeongseon/azure-functions-cookbook-python/commit/0c38fb333142258e1dd8c8e8bdefa3ff44a57ae6))
* completely remove azure_functions_knowledge dead code from tracked files ([ca14d44](https://github.com/yeongseon/azure-functions-cookbook-python/commit/ca14d443bdd6f9db22dd64dc78aba38ac7d19aae))
* db_input_output use proper [@db](https://github.com/db).inject_reader decorator pattern ([bda68e2](https://github.com/yeongseon/azure-functions-cookbook-python/commit/bda68e23a8d12b6bae07b82116d764c84c540f2b))
* declare wheel packages explicitly for hatchling ([7a2e936](https://github.com/yeongseon/azure-functions-cookbook-python/commit/7a2e93627ccc51bb363fd9b05f2a1da906554a70))
* declare wheel packages explicitly for hatchling ([8d6ebe1](https://github.com/yeongseon/azure-functions-cookbook-python/commit/8d6ebe1b23950b3b9a7823a72a3c4d27d1b68122))
* **deps:** use unsuffixed azure-functions-openapi dep name ([3567f8b](https://github.com/yeongseon/azure-functions-cookbook-python/commit/3567f8b78b7220bb5ca8c3d37f70809e3f01afa7))
* **examples:** adapt db_input_output bare-array OpenAPI response ([#158](https://github.com/yeongseon/azure-functions-cookbook-python/issues/158)) ([075fa3a](https://github.com/yeongseon/azure-functions-cookbook-python/commit/075fa3a82d78bff112560107524a880cffd09e8b))
* **examples:** add context: func.Context to [@with](https://github.com/with)_context handlers ([#169](https://github.com/yeongseon/azure-functions-cookbook-python/issues/169)) ([33d4a7f](https://github.com/yeongseon/azure-functions-cookbook-python/commit/33d4a7ff41d2af87dba01252554d47dc63f45e34)), closes [#168](https://github.com/yeongseon/azure-functions-cookbook-python/issues/168)
* **examples:** restore active [@validate](https://github.com/validate)_http on binding-composed handlers ([#143](https://github.com/yeongseon/azure-functions-cookbook-python/issues/143)) ([9556a28](https://github.com/yeongseon/azure-functions-cookbook-python/commit/9556a28f20f90d228d61a2dec53842854cb1a0f7))
* **full-stack-crud-api:** package the flat-layout modules ([#262](https://github.com/yeongseon/azure-functions-cookbook-python/issues/262)) ([aee06c9](https://github.com/yeongseon/azure-functions-cookbook-python/commit/aee06c9f0b1e2268365174f30818d5b85bebb7eb))
* **langgraph:** pass required name to register() in agent examples ([#121](https://github.com/yeongseon/azure-functions-cookbook-python/issues/121)) ([0f7cbe4](https://github.com/yeongseon/azure-functions-cookbook-python/commit/0f7cbe4d36406af43bc34c4c508dfa958a8d86d5))
* make langgraph_agent and db_input_output resilient to optional deps ([3a6b15a](https://github.com/yeongseon/azure-functions-cookbook-python/commit/3a6b15a635cae28b77a0d8ef9ff5320ada8ce7f0))
* migrate scaffold_walkthrough_app to openapi 0.24 requests=/responses= ([#212](https://github.com/yeongseon/azure-functions-cookbook-python/issues/212)) ([586a0be](https://github.com/yeongseon/azure-functions-cookbook-python/commit/586a0be94445cd6bd952f8e5ebd24fedb773bbf2))
* **packaging:** ship the cookbook package in the wheel ([#261](https://github.com/yeongseon/azure-functions-cookbook-python/issues/261)) ([674e4fa](https://github.com/yeongseon/azure-functions-cookbook-python/commit/674e4fa6fcce9b6b75d7f2ff8447c667de7462eb))
* remove the uv.lock reintroduced by [#219](https://github.com/yeongseon/azure-functions-cookbook-python/issues/219) ([#243](https://github.com/yeongseon/azure-functions-cookbook-python/issues/243)) ([723365f](https://github.com/yeongseon/azure-functions-cookbook-python/commit/723365ffe16f4938bf972eb30ce1babfb953688c)), closes [#242](https://github.com/yeongseon/azure-functions-cookbook-python/issues/242)
* remove unpublished dependency, stale SignalR refs, add missing smoke tests ([1b84c61](https://github.com/yeongseon/azure-functions-cookbook-python/commit/1b84c61f74bc44a08460c51fc276e84b0246e738))
* resolve hatchling wheel build failure blocking docs deployment ([7a2e936](https://github.com/yeongseon/azure-functions-cookbook-python/commit/7a2e93627ccc51bb363fd9b05f2a1da906554a70))
* **templates:** prefill Conventional Commit prefixes in issue forms ([#239](https://github.com/yeongseon/azure-functions-cookbook-python/issues/239)) ([804cde0](https://github.com/yeongseon/azure-functions-cookbook-python/commit/804cde0846de9e9116395e365efcf8fab714a5f0))
* **tests:** assert version format instead of a hardcoded literal ([#90](https://github.com/yeongseon/azure-functions-cookbook-python/issues/90)) ([ccc5c44](https://github.com/yeongseon/azure-functions-cookbook-python/commit/ccc5c44a22095b14be8b266ceef2363e155b74a5)), closes [#89](https://github.com/yeongseon/azure-functions-cookbook-python/issues/89)
* **websocket-proxy:** keep the context parameter visible to with_context ([#264](https://github.com/yeongseon/azure-functions-cookbook-python/issues/264)) ([8f0e939](https://github.com/yeongseon/azure-functions-cookbook-python/commit/8f0e9390f5549ef77e5b8ea912f456450798003a))

## Changelog

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
