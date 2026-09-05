# Local Setup & Running

## Prerequisites

- Docker & Docker Compose (quick start), **or**
- Python 3.11+, Node.js 18+, PostgreSQL 15+, Redis 7+ (local dev)

## Option A — Docker (recommended)

```bash
cp .env.example .env          # then set JWT_SECRET_KEY
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

> On Windows, the `nginx` container listening on port 80 may fail to bind; the
> app remains reachable directly on :3000 / :8000. This is non-blocking.

## Option B — Local development

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Configuration

Copy `.env.example` to `.env` and set at least:

- `DATABASE_URL` — Postgres async connection string
- `JWT_SECRET_KEY` — generate with
  `python -c "import secrets; print(secrets.token_hex(32))"`
- `REDIS_URL`
- `CORS_ORIGINS`, `ALLOWED_HOSTS`

LLM/embeddings default to deterministic mocks (`EMBEDDING_PROVIDER=mock`), so no
API keys are required for the app to run.

## Loading reference data

Approval rules, incentive schemes and regulation knowledge documents are loaded
from `data/` via `backend/app/services/data_loader.py`:

- `load_approval_rules(filepath)`
- `load_schemes(filepath)`
- `load_knowledge_documents(directory)`

## Seeding the demo project

```bash
python scripts/seed_demo.py
```

See `docs/DEMO_WALKTHROUGH.md` for the demo flow and credentials.

## Running tests

See `docs/TESTING.md`. Backend tests run from `backend/`
(`..\venv\Scripts\python.exe -m pytest tests -q`); frontend tests via `npm test`.

## Deployment

See `docs/DEPLOYMENT.md`.
