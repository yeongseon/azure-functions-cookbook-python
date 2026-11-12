#!/usr/bin/env bash
# Reads changed file paths on stdin and prints `compat_required=true|false`.
#
# `true` means the pull request touches something whose compatibility with the supported toolkit
# dependency set can only be shown on a real Functions host, so the `toolkit-compat` job in
# ci-test.yml must run: the host-backed integration tests, the representative runtime recipes
# those tests start, dependency ranges and pins, and the workflows or harness that run the gate.
# Documentation-only and unrelated recipe changes print `false`. Any classifier error, and an
# empty path list, fail closed to `true`.
set -euo pipefail

trap 'echo "compat classifier error; running the compatibility gate" >&2; echo "compat_required=true"; exit 0' ERR

count=0
required=false

while IFS= read -r path || [ -n "$path" ]; do
  [ -z "$path" ] && continue
  count=$((count + 1))
  case "$path" in
    tests/e2e/* | tests/__init__.py | tests/_isolation.py | \
    tests/test_openapi_endpoint_convergence.py | tests/test_db_input_output_openapi.py | \
    examples/apis-and-ingress/full_stack_crud_api/* | \
    examples/ai-and-agents/personal_langgraph_agent/* | \
    pyproject.toml | constraints-min.txt | \
    tools/pytest_fail_on_skip.py | tools/compat_report.py | \
    tools/ci_classify_compat.sh | tools/ci_classify_workflow.sh | \
    .github/workflows/ci-test.yml | .github/workflows/e2e-toolkit.yml)
      required=true
      ;;
  esac
done

if [ "$count" -eq 0 ]; then
  echo "no changed files detected; running the compatibility gate" >&2
  required=true
fi
echo "compat_required=$required"
