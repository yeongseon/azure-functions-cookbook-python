# Architecture

## Positioning

The cookbook sits at the discovery layer of the broader Azure Functions Python workflow.

```text
Cookbook -> Scaffold -> Development
```

## Repository Structure

- `recipes/`: source recipe content
- `examples/`: runnable sample projects
- `docs/`: published documentation
- `src/`: repository package metadata and future automation hooks

## Design Intent

- Keep recipes independent and easy to read
- Keep examples grounded in real Azure Functions Python v2 patterns
- Keep CLI integration optional until the recipe catalog is stable
