# Sibling cross-validation

The **E2E Toolkit Matrix** workflow tests the cookbook against two dependency
axes: the latest compatible PyPI releases and every toolkit sibling's `main`
branch. Both axes run OpenAPI convergence/byte-consistency guards plus the
smoke and local Functions-host tiers.

Sibling release workflows should dispatch `sibling-release` after publishing:

```bash
gh api --method POST \
  repos/yeongseon/azure-functions-cookbook-python/dispatches \
  -f event_type=sibling-release \
  -f 'client_payload[package]=azure-functions-openapi' \
  -f 'client_payload[version]=0.30.0'
```

The caller needs a fine-grained PAT scoped only to this cookbook with
**Contents: read and write** permission, stored as a secret in the releasing
sibling. GitHub's default `GITHUB_TOKEN` is repository-scoped and cannot
dispatch another repository. The cookbook workflow itself uses only
`contents: read`, receives no caller secrets, and requires no Azure credentials.

The event payload is informational; every release dispatch runs both axes so a
fresh release is compared with current sibling source consistently.
