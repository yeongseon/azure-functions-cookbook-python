# Security

The Azure Functions Python Cookbook project maintains high standards for security in both its implementation and the documentation it provides. This security policy outlines how we handle security in our example code, how we manage dependencies, and the process for reporting vulnerabilities.

## Security Model

This repository is primarily a collection of documentation, architectural patterns, and code examples. It is not a runtime library or a framework that is imported into other projects. Therefore, our security model differs from traditional software libraries.

Security concerns in this project relate to:
1. The quality and security of the example code snippets provided.
2. The hygiene and security of the development dependencies used to build and test the project.
3. The accuracy and safety of the deployment guidance and infrastructure-as-code (IaC) templates.
4. The security of the CI/CD pipelines used for project maintenance.

We treat the security of our examples with the same rigor as production code, as these patterns are often copied into real-world applications.

## Reporting a Vulnerability

If you discover a security issue in this repository or its example code, please report it privately to the project maintainers. Do not open a public GitHub issue for security vulnerabilities.

### Preferred Reporting Method

The preferred way to report a vulnerability is through a GitHub Security Advisory. This provides a private, secure environment for us to discuss and resolve the issue.

Report here: https://github.com/yeongseon/azure-functions-cookbook-python/security/advisories/new

### Alternative Reporting Method

If you prefer to use email, you can reach the maintainer at:
yeongseon.choe@gmail.com

### What to Include

When reporting a vulnerability, please provide as much information as possible to help us understand and address the issue:
1. A detailed description of the vulnerability.
2. The specific files, recipes, or documentation sections affected.
3. Step-by-step instructions to reproduce the issue.
4. An assessment of the potential impact (e.g., data exposure, unauthorized access).
5. A suggested fix or mitigation if you have one.
6. Your name and how you would like to be credited in our security acknowledgments.

### Response Timeline

We take security reports seriously and aim to respond quickly:
1. Initial response: You will receive an acknowledgment of your report within 48 hours.
2. Status update: We will provide a status update on our investigation within 7 days.
3. Resolution: The timeline for resolution depends on the complexity of the issue, but we will keep you informed throughout the process.

## Supported Versions

The cookbook project follows a simple support model. Only the latest version of the repository is supported for security updates.

| Version | Supported |
| --- | --- |
| Latest (v0.1.0+) | Yes |
| All older versions | No |

If you are using patterns from older versions of the cookbook, we strongly recommend updating to the latest patterns to benefit from current security practices.

## Security in Example Code

Example code is provided for educational purposes, but it is designed to follow production-ready security practices. We aim for our recipes to include:

1. Input Validation: Examples demonstrate how to validate and sanitize data coming from external triggers.
2. Secret Management: We never include hardcoded secrets. Examples show how to use environment variables or Azure Key Vault for sensitive data.
3. Error Handling: Examples use proper error handling to avoid leaking sensitive system information in error messages.
4. Secure Defaults: We configure our samples with secure defaults (e.g., least-privileged access, encrypted communication).
5. Identity Management: We emphasize the use of Managed Identities over connection strings where possible.

Several recipes intentionally use anonymous HTTP routes. See [Anonymous endpoint classification](anonymous-endpoints.md) for which recipes are demo-only, which carry their own authentication and which need extra controls before deployment.

Users are ultimately responsible for the security of their own applications. Always perform a security audit of code before deploying it to production.

## Dependency Management

We take a proactive approach to managing the dependencies used in this repository:
1. Pinned Versions: All development and documentation dependencies are pinned to specific versions in our configuration files to ensure consistent and predictable builds.
2. Regular Updates: We periodically review and update dependencies to include the latest security patches and improvements.
3. Minimal Footprint: We strive to keep our dependency tree as small as possible to reduce the attack surface.

## Security Scanning

To ensure the integrity of our code and documentation, we use automated security scanning tools:

### Static Analysis

We use Bandit, a tool designed to find common security issues in Python code. You can run the security scan locally using the provided task:

```bash
make security
```

This command runs Bandit across the entire codebase, including all recipe examples.

### CI Integration

Our continuous integration (CI) workflows automatically run security checks on every pull request and push to the main branch. These checks include:
1. Code linting and formatting (Ruff, Black).
2. Static type checking (Mypy).
3. Security scanning (Bandit).
4. Automated tests (Pytest).

A build will fail if any high-severity security issues are detected.

## Responsible Disclosure

We are committed to the principle of responsible disclosure. This process ensures that vulnerabilities are addressed before they are publicly revealed, protecting users who may have implemented the affected patterns.

1. You report the vulnerability privately to us.
2. We investigate and confirm the issue.
3. We develop a fix or mitigation.
4. We release the update and update the documentation.
5. We publicly acknowledge the vulnerability and credit the reporter.

We ask that you do not share information about the vulnerability with third parties until we have had a reasonable amount of time to address it.

## Security Principles for Contributors

If you are contributing to this repository, please adhere to the following principles:
1. Never commit secrets, API keys, or credentials.
2. Follow the principle of least privilege in any deployment templates.
3. Ensure all user input is validated before use.
4. Use standard, well-vetted libraries for security-sensitive operations.
5. Provide clear warnings in the documentation if an example requires specific security configurations to be safe for production.

Your contributions help keep this resource safe for the entire Azure Functions community.
