#!/usr/bin/env bash
set -euo pipefail

emit() {
  printf 'docs_only=%s\ndocs_changed=%s\nfull_required=%s\n' "$1" "$2" "$3"
}

trap 'echo "classifier error; running the full matrix" >&2; emit false true true' ERR

count=0
docs_only=true
docs_changed=false

while IFS= read -r path || [ -n "$path" ]; do
  [ -z "$path" ] && continue
  count=$((count + 1))
  case "$path" in
    mkdocs.yml | pyproject.toml | \
    tests/test_example_count.py | tests/test_llms_txt.py | tests/test_recipe_index.py | \
    tests/test_recipe_table.py | tests/test_recipes.py | tests/test_requirements.py | \
    tests/_isolation.py | tests/_recipes.py | \
    scripts/gen_recipe_index.py | scripts/gen_recipe_table.py | scripts/gen_requirements.py | \
    src/azure_functions_python_cookbook/recipes.py | \
    src/azure_functions_python_cookbook/__init__.py | tools/forbid_korean.sh | \
    .github/workflows/ci-test.yml | \
    docs/*.py | docs/*.yml | docs/*.yaml | docs/*.json | \
    docs/*.toml | docs/*.js | docs/*.css | docs/*.html | docs/*.txt)
      docs_only=false
      docs_changed=true
      ;;
    src/* | tests/* | examples/* | scripts/* | tools/* | benchmarks/* | infra/* | \
    .github/* | Makefile | Dockerfile* | docker-compose* | requirements*.txt | *.lock | \
    hatch.toml | tox.ini | setup.cfg | setup.py | MANIFEST.in | .pre-commit-config.yaml | \
    host.json | local.settings*.json | *.py | *.sh)
      docs_only=false
      ;;
    *.md | docs/*.png | docs/*.jpg | docs/*.jpeg | docs/*.gif | docs/*.svg | \
    docs/*.webp | docs/*.ico)
      docs_changed=true
      ;;
    *)
      docs_only=false
      ;;
  esac
done

if [ "$count" -eq 0 ]; then
  echo "no changed files detected; running the full matrix" >&2
  emit false true true
  exit 0
fi

if [ "$docs_only" = true ]; then
  emit true true false
else
  emit false "$docs_changed" true
fi
