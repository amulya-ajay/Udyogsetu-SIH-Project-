# UDYOGSETU - Production Deployment Readiness Report

**Target platform:** Vercel (frontend) | Railway (backend) | Railway PostgreSQL | Railway Redis
**Base commit:** `850ee2e9` + the deployment-prep changes in this branch.

Status legend: PASS (verified) / FAIL (blocking) / WARNING (works, caveat) / NOT TESTED / NOT APPLICABLE

---

## Executive Summary

UDYOGSETU is ready to deploy to **Railway (backend + PostgreSQL + Redis)** and
**Vercel (frontend)**. Every locally-testable gate passes: backend tests (202),
frontend tests (16), lint, TypeScript, Next.js production build, both Docker
builds, production-mode Docker startup, Alembic migrations against live
PostgreSQL, CORS, health, and authentication. Two production-hardening fixes
were applied (production `create_all` suppression; Railway `DATABASE_URL`
driver normalization) plus a strict production JWT-secret policy.

Live deployment to the actual Railway and Vercel accounts is
**NOT TESTED - requires external deployment**, so the platform verdict is
GREEN for repository readiness with known limitations (see below).

## Architecture

- `frontend/` Next.js 14 App Router + TypeScript + axios + TanStack React Query
- `backend/` FastAPI + async SQLAlchemy + asyncpg + Alembic + Redis rate limiter
  - Entrypoint `app.main:app`; migrations via Alembic (head `0005`)
- `infrastructure/docker/Dockerfile.backend` (Python 3.11, root context, non-root)
- `infrastructure/docker/Dockerfile.frontend` (Node 20 standalone, root context)
- `data/` seed data (approval rules, schemes, regulations, explore services)
- `docker-compose.yml` local dev/demo stack (postgres + redis + backend + frontend + nginx)
- Routers mounted under `/api` (login = `POST /api/auth/login`); `GET /health`
  at root; `/docs` disabled when `DEBUG=false`.

## Repository Findings

| Item | Finding |
|---|---|
| Backend entrypoint | `app.main:app` (verified) |
| Frontend build/start | `next build` / `next start` (standalone output) |
| HTTP port | `uvicorn --port ${PORT:-8000}` (Railway `PORT` supported) |
| Config source | `backend/app/core/config.py` (pydantic-settings) |
| Frontend API var | `NEXT_PUBLIC_API_URL` (`frontend/services/api.ts`) |
| DB URL format | `DATABASE_URL`; `postgresql://` auto-normalized to `+asyncpg` |
| Redis usage | Rate limiter only; fails open if Redis is unreachable |
| Migrations | head `0005`; `alembic/env.py` reads `settings.DATABASE_URL` |
| Uploads | local filesystem under `UPLOAD_DIRECTORY` (ephemeral on Railway) |
| Background jobs | in-process asyncio queue (`app/workers/background.py`) |
| Gov gateway | mock/demo adapters, no credentials |
| LLM | provider chain ending in a safe mock fallback; keys server-side |

## Changes Made

| Change | Reason |
|---|---|
| `backend/app/main.py`: `create_all` runs only outside production | Schema must be Alembic-controlled in production |
| `backend/app/core/config.py`: production JWT secret must be >= 32 chars and not a placeholder (fail-fast) | No insecure production defaults |
| `backend/app/core/database.py` + `alembic/env.py`: normalize `postgresql://` -> `postgresql+asyncpg://` | Railway injects a driver-less `DATABASE_URL`; async engine otherwise tried psycopg2 (not installed) |
| `infrastructure/docker/Dockerfile.backend`: `--port ${PORT:-8000}` | Railway `PORT` support |
| `backend/.env.example`, `frontend/.env.example` created; root `.env.example` refreshed | Placeholders only, no secrets |
| `backend/tests/test_deployment_hardening.py` added | CORS, JWT fail-fast/weak-secret, URL normalization regression coverage |

No working module was rewritten, no `data/` moved, build contexts remain the
repository root.

## Status Summary

| Area | Status |
|---|---|
| Docker Readiness | PASS |
| Railway Readiness | WARNING (config documented; live platform not tested) |
| Vercel Readiness | WARNING (build verified; live platform not tested) |
| PostgreSQL Readiness | PASS |
| Redis Readiness | PASS |
| Alembic / Migrations | PASS |
| Environment Variables | PASS |
| CORS | PASS |
| Authentication | PASS |
| RBAC | PASS |
| Security | PASS |
| Health Checks | PASS |
| Frontend Build | PASS |
| Backend Tests | PASS (202) |
| Docker Build | PASS |
| E2E Testing | WARNING (131/131 pre-change; post-change gates re-verified) |
| Government API Status | PASS (correctly MOCK) |
| AI / LLM Status | PASS (mock fallback documented) |
| File Storage Status | WARNING (ephemeral on Railway) |
| Background Worker Status | WARNING (in-memory; single instance) |

## Docker Readiness - PASS

- Backend image builds from root context; frontend image builds from root context.
- Non-root `appuser`; no `.env` or secrets baked into images.
- GitHub Actions `docker-build` job uses the correct root-context commands.

## Railway Readiness - WARNING (not live-tested)

- Dockerfile path `infrastructure/docker/Dockerfile.backend`, root directory `.`
  documented. Pre-deploy `alembic upgrade head`; start
  `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`.
- Driver-less `postgresql://` DATABASE_URL simulated against a live PostgreSQL:
  `alembic current` -> `0005`, `alembic check` -> "No new upgrade operations detected."
- NOT TESTED (requires external deployment): actual Railway build/pre-deploy with
  Railway PostgreSQL and Redis attached.

## Vercel Readiness - WARNING (not live-tested)

- Jest 16/16, ESLint clean, `tsc --noEmit` clean, `next build` success.
- Verified that building with `NEXT_PUBLIC_API_URL=<railway-url>/api` inlines the
  URL and removes localhost from the bundle.
- NOT TESTED (requires external deployment): deploying to a real Vercel project.

## PostgreSQL Readiness - PASS

- Healthy, `SELECT 1` ok, 16 tables; fresh migration chain and live
  `alembic upgrade head` / `alembic check` pass.
- Timezone policy unchanged (naive-UTC columns, aware JWT comparisons).

## Redis Readiness - PASS

- Redis 7 healthy; rate limiter uses `REDIS_URL` via `redis.asyncio` and fails
  open when Redis is unavailable. Railway `REDIS_URL` format compatible.

## Alembic / Migrations - PASS

- Head `0005`; `alembic upgrade head` on fresh PostgreSQL pass;
  `alembic check` clean. `create_all` removed from production startup.

## Environment Variables - PASS

- `.env.example` (root, backend/, frontend/) contain placeholders only.
- `.env*` gitignored except `.env.example`; secrets never committed.
- Deployed set documented in `DEPLOYMENT_ENVIRONMENT_REFERENCE.md`.

## CORS - PASS

- `allow_origins` from `CORS_ORIGINS` (JSON array); `allow_credentials=True`.
- Verified: trusted-origin preflight echoes the origin; a foreign origin gets no
  CORS headers; authenticated requests unaffected.

## Authentication - PASS

- Register/login/JWT issuance verified live against the production-mode stack.
- Production fails fast when `JWT_SECRET_KEY` is missing or weak (tests).

## RBAC - PASS

- Covered by the 202-test suite (role separation, officer/admin-only endpoints,
  BOLA/data isolation). No UI-only authorization: server-side enforcement only.

## Security - PASS

- Repository secret scan clean (no cloud keys, GitHub tokens, private keys).
- Only `.env.example` tracked; certs/dumps ignored; `.dockerignore` excludes
  `.env`; Docker image env contains only base variables; Actions use no
  secrets.

## Health Checks - PASS

- `GET /health` returns
  `{"status":"healthy","version":"1.0.0","environment":"production","database":"ok"}`
  and verifies the database with `SELECT 1`. No secrets exposed.

## Frontend Build - PASS

- Jest 16/16; ESLint clean; `tsc --noEmit` clean; `next build` succeeds.

## Backend Tests - PASS

- `pytest tests -q` -> 202 passed (196 existing + 6 new hardening tests).
- `ruff check .` -> All checks passed.

## Docker Build - PASS

- Both images build from root context; `docker compose config -q` exit 0;
  production-mode container starts healthy and seeds data.

## E2E Testing - WARNING

- Prior integration audit: 131/131 E2E passed (entrepreneur/officer/admin,
  Explore, RBAC, BOLA). Post-change request paths re-verified live (login,
  health, CORS, suites). Full browser E2E against the hosted URLs:
  NOT TESTED (requires external deployment).

## Known Limitations

1. **File storage is local and ephemeral on Railway.** Uploaded documents live
   under `UPLOAD_DIRECTORY`; the compose stack uses a Docker volume, but Railway
   containers are stateless. Works within a single deploy. Future: S3/R2
   object storage (not performed - larger storage-abstraction change).
2. **Background jobs are in-memory.** OCR/embedding/RAG jobs use
   `BackgroundTaskManager` (asyncio queue); job state is lost on restart.
   Run the backend as a single Railway replica. Future: Celery/RQ with Redis.
3. **Government integrations are MOCK.** MAITRI/MPCB/MIDC and GSTIN/PAN/Udyam
   verification use the bundled mock gateway; no real credentials exist.
4. **AI uses a mock fallback.** Set `GEMINI_API_KEY`/`GROQ_API_KEY` for real LLM
   answers; no custom-trained model exists.
5. **RAG knowledge is static** - seeded from `data/regulations` at startup.

## Government API Status - MOCK (correctly labeled)

- MAITRI, MPCB, MIDC adapters + `MockGovAPI` gateway are simulated; no live
  authorized APIs or credentials. Documented as demo/mock, never presented as
  real integration.

## AI/LLM Status - mock fallback, documented

- Provider chain: configured provider -> fallbacks -> mock. Blank keys never
  break startup. LLM and embedding keys are server-side only.

## File Storage Status - WARNING

- `UPLOAD_DIRECTORY` local filesystem; compose uses a named volume. Railway
  storage is ephemeral. Limitation documented (see Known Limitations).

## Background Worker Status - WARNING

- In-process asyncio queue, not durable, single-host. Documented; the Railway
  backend must run with replicas = 1.

## Deployment Steps

1. Push to GitHub; verify CI (tests, lint, Docker builds) passes.
2. Railway: create project, attach PostgreSQL and Redis.
3. Backend service: Dockerfile `infrastructure/docker/Dockerfile.backend`,
   root directory `.`, pre-deploy `alembic upgrade head`,
   start `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`,
   health check `/health`.
4. Set backend variables: `JWT_SECRET_KEY`, `ENVIRONMENT=production`,
   `DEBUG=false`, `CORS_ORIGINS`, `ALLOWED_HOSTS` (include the Railway domain).
5. Vercel: import repo, root directory `frontend`, set
   `NEXT_PUBLIC_API_URL=https://<railway-url>/api` for Production/Preview.
6. Verify: `/health`, login, dashboards, upload, officer/admin flows.
   Full steps in `DEPLOYMENT.md`.

## Rollback Strategy

- Backend: Railway Deployments -> select previous deploy -> Rollback.
- Database: Railway Postgres snapshot/backup restore.
- Frontend: Vercel Production Deployments -> promote previous to Production.

## Final Verdict

**GREEN - repository is ready to deploy (Vercel + Railway), deployable with the
documented known limitations.** All locally verifiable gates pass. The actual
Railway/Vercel deploys are NOT TESTED (requires external deployment) - follow
`DEPLOYMENT.md` to complete them, then run the manual checks in the checklist
attached to the final response.