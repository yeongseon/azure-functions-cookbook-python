#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"

printf 'docs_only=false\ndocs_changed=true\nfull_required=true\ncompat_required=true\n' > "$GITHUB_OUTPUT"

changed_files=$(mktemp) || exit 0
classification=$(mktemp) || exit 0
trap 'rm -f "$changed_files" "$classification"' EXIT

tools/ci_changed_files.sh "$changed_files" || exit 0
tools/ci_classify_changes.sh < "$changed_files" > "$classification" || exit 0
cat "$classification" >> "$GITHUB_OUTPUT" || exit 0

# The pre-merge compatibility gate is for pull requests only; scheduled and post-release runs
# of e2e-toolkit.yml cover `main`. A classifier failure leaves the fail-closed `true` above.
if [ "${EVENT_NAME:-}" = pull_request ]; then
  tools/ci_classify_compat.sh < "$changed_files" >> "$GITHUB_OUTPUT" || exit 0
else
  printf 'compat_required=false\n' >> "$GITHUB_OUTPUT"
fi
