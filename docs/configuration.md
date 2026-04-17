# Configuration

`azure-functions-python-cookbook` is a documentation and example project, not a library. There is no runtime configuration API.

For configuring the tools used in recipe examples, refer to the relevant Azure documentation:

- [Azure Functions host.json reference](https://learn.microsoft.com/en-us/azure/azure-functions/functions-host-json)
- [Azure Functions local.settings.json](https://learn.microsoft.com/en-us/azure/azure-functions/functions-develop-local#local-settings-file)
- [Python v2 programming model](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)

## Local Development Configuration

When running recipes locally, set up `local.settings.json` at the project root:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

Each recipe's README notes any additional environment variables required.

## Recipe-Specific Configuration

See individual pattern documentation under [Patterns](patterns/index.md) for trigger-specific and binding-specific configuration examples.

## Related Documents

- [Getting Started](getting-started.md)
- [Usage](usage.md)
- [Troubleshooting](troubleshooting.md)
