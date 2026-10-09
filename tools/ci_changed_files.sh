#!/usr/bin/env bash
set -euo pipefail

event_name=${EVENT_NAME:?EVENT_NAME is required}
output=${1:?output path is required}

if [ "$event_name" = pull_request ]; then
  : "${BASE_SHA:?BASE_SHA is required}"
  : "${HEAD_SHA:?HEAD_SHA is required}"
  git diff --name-only --no-renames "$BASE_SHA...$HEAD_SHA" > "$output"
  exit 0
fi

: "${BEFORE_SHA:?BEFORE_SHA is required}"
: "${SHA:?SHA is required}"
if [[ "$BEFORE_SHA" =~ ^0+$ ]]; then
  exit 1
fi
git cat-file -e "$BEFORE_SHA^{commit}"
git cat-file -e "$SHA^{commit}"
git merge-base --is-ancestor "$BEFORE_SHA" "$SHA"
git diff --name-only --no-renames "$BEFORE_SHA" "$SHA" > "$output"
