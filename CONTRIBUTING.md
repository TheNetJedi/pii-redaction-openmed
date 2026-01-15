# Contributing to PII Redaction Tool

Thank you for your interest in contributing! We welcome improvements to the codebase, documentation, and model performance.

## Development Workflow

1.  **Fork the repository**.
2.  **Create a branch** for your feature or fix.
3.  **Local Setup**:
    - Backend: `cd api && uv pip install -e .`
    - Frontend: `cd web && bun install`
4.  **Make changes**.
5.  **Test**: Ensure `pytest` passes in `api/`.
6.  **Submit a Pull Request**.

## Project Structure

- `api/`: FastAPI backend and core logic (`api/services`).
- `web/`: React frontend.
- `cli/`: Command-line interface tool.
- `docs/`: Documentation.

## Coding Standards

- **Python**: We use `ruff` for linting and formatting. Run `ruff format .` in `api/`.
- **TypeScript**: Use Prettier and ESLint.
- **Commits**: Please use conventional commits (e.g., `feat: add new redaction method`).

## Adding New Models

To add support for a new HuggingFace model:
1.  Update `api/config.py` allowed models list (if constrained).
2.  Update `docs/configuration.md`.
3.  Ensure the model is compatible with the `ner` pipeline in `openmed`.
