# AGENTS.md

## Cursor Cloud specific instructions

This is a single-service Python FastAPI application (no monorepo, no Docker, no database).

### Service

| Service | Command | Default URL |
|---|---|---|
| FastAPI dev server | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` | `http://localhost:8000` |

### Quick reference

- **Tests:** `python3 -m pytest tests/ -v`
- **Lint:** `ruff check app/ tests/` (no project-level ruff config; default rules apply)
- **API docs (Swagger):** `http://localhost:8000/docs` when server is running

### Gotchas

- The project installs to the user site-packages (`~/.local/`). Make sure `$HOME/.local/bin` is on `PATH` so `uvicorn` and `ruff` are found.
- All data lives in `data/*.json` (flat files, no DB). Missing data files crash the app on first request, not at startup (lazy loading).
- `pyproject.toml` does not declare a `[dev]` extra; `pytest` and `ruff` must be installed separately.
