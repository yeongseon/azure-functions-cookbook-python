# Contributing

Welcome to the Azure Functions Python Cookbook. This project provides a collection of production ready recipes and example projects for the Azure Functions Python v2 programming model. We welcome contributions that help developers build more reliable, scalable, and maintainable serverless applications. Whether you are fixing a typo, improving a recipe, or adding a completely new architectural pattern, your input is valued. Our focus areas include performance optimization, security best practices, and idiomatic Python usage within the Azure Functions ecosystem.

As this project grows, we aim to cover more complex scenarios such as event driven microservices, data processing pipelines, and advanced integration patterns. Your expertise in these areas is highly appreciated. By contributing to this cookbook, you help other developers avoid common pitfalls and adopt best practices from the start.

## Prerequisites

Before contributing, ensure you have the following tools and knowledge:

1.  Python 3.10 or higher.
2.  Git for version control.
3.  GNU Make for running development commands.
4.  Familiarity with the Azure Functions Python v2 model (decorator-based).
5.  Basic understanding of serverless architectural patterns.
6.  Experience with cloud native application development.
7.  Knowledge of common Azure services like Service Bus, Storage, and Event Hubs.

## Development Setup

Follow these steps to set up your local development environment:

```bash
git clone https://github.com/yeongseon/azure-functions-python-cookbook.git
cd azure-functions-python-cookbook
make install
```

The `make install` command handles dependency installation and sets up the virtual environment using Hatch, which is the primary build system for this project. This ensures that all contributors have a consistent and reproducible development environment. Using a standardized environment helps prevent "it works on my machine" issues.

## Development Commands

We use a Makefile to provide a consistent interface for common tasks. Use the following commands during development:

| Command | Description |
|---------|-------------|
| make install | Install dependencies and set up environment |
| make format | Format code with ruff |
| make lint | Run linter and type checker |
| make test | Run test suite |
| make check-all | Run all checks (lint, test, security) |
| make docs | Build documentation site |
| make docs-serve | Serve documentation locally |
| make security | Run security scan with bandit |

## Contribution Types

You can contribute to the cookbook in several ways:

### Recipe Improvements
Recipes are the core of this repository. You can improve them by clarifying technical language, adding missing sections, or fixing inaccuracies in the implementation details. Every recipe should be practical and production aware. This includes updating code snippets to use the latest best practices and ensuring that all explanations are easy to follow.

### Example Projects
Example projects provide runnable code that demonstrates a recipe in action. Adding new examples or improving existing ones helps users understand how to apply the patterns in real world scenarios. Ensure that any new example project follows the established repository structure and includes a README.md file that explains how to deploy and test the code.

### Documentation
Documentation is vital for the success of the project. If you find gaps in the published documentation or areas where the explanation is unclear, we encourage you to submit updates. This includes both the core documentation and individual recipe files. High quality documentation is as important as the code itself.

### Repository Tooling
We are always looking to improve our CI pipelines, testing frameworks, and build processes. If you have suggestions for better validation or automation, please share them. We use GitHub Actions for our continuous integration and delivery. Improving the tooling makes it easier for everyone to contribute.

## Recipe Guidelines

To maintain consistency across the cookbook, every recipe must follow a strict contract. When creating or updating a recipe, ensure it includes the following sections as defined in the `_template.md` file:

1.  Overview: A concise summary of the recipe and the problem it solves.
2.  When to use: Specific scenarios where this pattern is appropriate.
3.  Architecture: A description of the components and their interactions.
4.  Project structure: A map of the files and directories involved.
5.  Run locally: Step by step instructions for testing the code on a local machine.
6.  Production considerations: Guidance on scaling, security, and monitoring.
7.  Scaffold guidance: How to start a new project based on this recipe.

Adhering to this structure ensures that users can quickly find the information they need across different recipes.

## Pull Request Process

When you are ready to submit your changes, follow this process:

1.  Fork the repository and create a new branch for your feature or fix.
2.  Make your changes, ensuring they align with the project goals.
3.  Run `make check-all` to verify that your code passes all linting, testing, and security checks.
4.  Open a Pull Request against the main branch.
5.  Provide a clear description of the changes, including why they are necessary and any relevant issue numbers.
6.  Wait for feedback from the maintainers and address any requested changes.
7.  Once approved, your changes will be merged into the main branch.

## Code Style

Consistency in code style makes the repository easier to maintain. We enforce the following standards:

1.  Linting: We use Ruff for fast, modern linting.
2.  Formatting: We use Black to ensure a consistent code layout.
3.  Type Checking: We use Mypy for static type analysis.
4.  Line Length: The maximum line length is set to 100 characters.

Running `make format` will automatically apply the required formatting to your code. This helps keep the codebase clean and professional for everyone.

## Commit Messages

We follow the Conventional Commits specification for all commit messages. This helps in generating changelogs and understanding the project history. Use the following prefixes:

- `feat:` for a new feature.
- `fix:` for a bug fix.
- `docs:` for documentation updates.
- `build:` for changes that affect the build system or dependencies.
- `test:` for adding or correcting tests.
- `chore:` for maintenance tasks that do not modify source or test files.

Example: `feat: add recipe for durable entities in python`

## Code of Conduct

This project adheres to a standard Code of Conduct to ensure a welcoming environment for all contributors. For more details, please refer to the `CODE_OF_CONDUCT.md` file in the root of the repository. We expect all participants to behave professionally and treat others with respect.

The cookbook is a community effort, and we appreciate your time and dedication to making it a better resource for Azure Functions developers. If you have any questions, feel free to open an issue for discussion. We aim to respond to all contributions in a timely manner and provide constructive feedback.

Thank you for helping us build a comprehensive resource for the Azure Functions Python community. Your contributions make a significant difference in helping developers build better serverless solutions.

Final Note: Please ensure that all your contributions are original work or that you have the necessary permissions to include them in this repository.
