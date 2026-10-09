#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"

printf 'docs_only=false\ndocs_changed=true\nfull_required=true\n' > "$GITHUB_OUTPUT"

changed_files=$(mktemp) || exit 0
classification=$(mktemp) || exit 0
trap 'rm -f "$changed_files" "$classification"' EXIT

tools/ci_changed_files.sh "$changed_files" || exit 0
tools/ci_classify_changes.sh < "$changed_files" > "$classification" || exit 0
cat "$classification" >> "$GITHUB_OUTPUT" || exit 0
