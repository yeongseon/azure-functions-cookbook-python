# Azure Functions Python Cookbook

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://github.com/yeongseon/azure-functions-python-cookbook)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Practical recipes for building real-world Azure Functions with Python.

## Why Use It

Starting a new Azure Functions project often means piecing together scattered documentation,
blog posts, and sample code. This cookbook provides curated, runnable recipes that answer:

- What should I build for this scenario?
- How should the architecture look?
- How do I start from a working baseline?

## Scope

- Azure Functions Python **v2 programming model**
- Decorator-based `func.FunctionApp()` applications
- Practical recipes with runnable examples
- Architecture explanations and production notes

This repository is content-first. It is not a CLI tool.

## Recipes

- HTTP API Basic
- HTTP API with OpenAPI
- GitHub Webhook Receiver
- Queue Worker
- Timer Scheduled Job

Each recipe lives under `recipes/` and follows the `_template.md` format.

## Repository Layout

```text
recipes/           Curated recipe documents
examples/          Runnable example projects
docs/              Published documentation
```

## Development

```bash
git clone https://github.com/yeongseon/azure-functions-python-cookbook.git
cd azure-functions-python-cookbook
make install
make check-all
make docs
```

## Documentation

- Product requirements: `PRD.md`
- Design principles: `DESIGN.md`
- Contributing guide: `CONTRIBUTING.md`

## Disclaimer

This project is an independent community project and is not affiliated with,
endorsed by, or maintained by Microsoft.

Azure and Azure Functions are trademarks of Microsoft Corporation.

## License

MIT
