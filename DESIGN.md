# Design

## Overview

Azure Functions Python Cookbook is a content-first repository that helps developers discover proven Azure Functions implementation patterns before they commit to a project structure.

## Design Principles

- Start from a developer problem, not from a library feature.
- Keep recipes focused on one use case and one architectural story.
- Pair each recipe with an example that can evolve into a scaffold starter later.
- Preserve independence from the other repositories at the documentation level.

## Information Architecture

The repository is organized into three layers:

1. `recipes/`
   - Source recipe documents
   - Architecture, use cases, pitfalls, and scaffold guidance
2. `examples/`
   - Runnable or near-runnable sample projects
3. `docs/`
   - Published documentation and navigation structure

## Future Extension Points

- Recipe search and tagging
- Scaffold command mapping
- Static gallery experience
- Automated validation of recipe examples
