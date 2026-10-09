#!/usr/bin/env bash
set -euo pipefail

paths=(docs src README.md CONTRIBUTING.md AGENTS.md DESIGN.md PRD.md CHANGELOG.md)
existing=()
for path in "${paths[@]}"; do
  if [ -e "$path" ]; then
    existing+=("$path")
  fi
done

if grep -RInIP '[\x{AC00}-\x{D7A3}]' "${existing[@]}"; then
  echo "Korean characters detected. Please use English only." >&2
  exit 1
fi
