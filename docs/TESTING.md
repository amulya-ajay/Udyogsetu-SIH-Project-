# Testing

UDYOGSETU uses **pytest** (async, `pytest-asyncio`) for the backend and **Jest /
React Testing Library** for the frontend.

## Backend

Run the whole suite from the `backend/` directory:

```bash
..\venv\Scripts\python.exe -m pytest tests -q      # ~95+ tests, ~200s
```

Run a single file:

```bash
..\venv\Scripts\python.exe -m pytest tests/test_workflow_sla.py -v
```

> The suite **must** run from `backend/` (so that `app` is importable).
> Running from the repository root fails with `ModuleNotFoundError: app`.

### Test infrastructure

- `backend/tests/conftest.py` points the app at a throwaway **file-backed
  SQLite** database, compiles Postgres `UUID`/`JSONB` types for SQLite,
  disables rate limiting, and resets the schema before every test.
- Tests use `TestClient` for the HTTP layer and the `db_session` async fixture
  for service-level tests.

### Coverage areas

| File | Covers |
|------|--------|
| `test_api.py` | HTTP endpoints, auth flows |
| `test_services.py` | service-layer behaviour, rule determination |
| `test_document_intelligence.py` | doc extraction & cross-validation |
| `test_workflow_gateway.py` | gateway + copilot flows |
| `test_workflow_sla.py` | application workflow transitions + SLA |
| `test_gov_sync.py` | government status sync + query resolution |
| `test_tool_calling.py` | controlled LLM tools |
| `test_rag_evaluation.py` | RAG retrieval, versioning, JSON-safety |
| `test_document_explanation.py` | AI mismatch narratives |
| `test_demo_seed.py` | demo data seeder idempotency |
| `test_notifications.py` | notification service |
| `test_approval_graph.py` | dependency graph + critical path |
| `test_officer_analytics.py` | officer dashboards |
| `test_background_workers.py` | background jobs |

## Frontend

```bash
npm test        # from the frontend/ directory
```

## CI

`.github/workflows/ci.yml` runs the backend and frontend suites on pull
requests / pushes to main.
