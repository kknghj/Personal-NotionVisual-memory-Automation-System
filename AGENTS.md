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

### Semantic boundary workflow

When the user says **"semantic boundary workflow 기준으로 진행해줘"**, follow `docs/workflows/semantic_boundary_workflow.md`.

1. ontology / visual_candidates metadata / scoring 수정
2. boundary test 추가
3. snapshot 생성: `python tools/generate_ranking_snapshots.py --before <log> --after <log>`
4. before/after 비교·요약: `python tools/analyze_snapshot_diff.py --before <snapshot> --after <snapshot>`

Report using the workflow doc's **결과 보고 형식** (수정 파일, boundary 정책, ranking 변화, regression, ambiguity, TODO). `analyze_snapshot_diff.py` flags change candidates only — final regression/semantic judgment is human review.

### Gotchas

- The project installs to the user site-packages (`~/.local/`). Make sure `$HOME/.local/bin` is on `PATH` so `uvicorn` and `ruff` are found.
- All data lives in `data/*.json` (flat files, no DB). Missing data files crash the app on first request, not at startup (lazy loading).
- `pyproject.toml` does not declare a `[dev]` extra; `pytest` and `ruff` must be installed separately.
