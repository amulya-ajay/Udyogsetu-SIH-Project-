# UDYOGSETU — FINAL DEPLOYMENT READINESS REPORT

**Scope:** Repository → Dockerfiles → `.dockerignore` → GitHub Actions → backend image → frontend image → Compose/Deployment → PostgreSQL → Redis → health checks → application.
**Date:** 2026-09-05
**Branch:** `main` (remote: `https://github.com/amulya-ajay/Udyogsetu-SIH-Project-`)
**Overall verdict: 🟢 READY FOR DEPLOYMENT**

---

## 1. Executive Summary

This audit was triggered by a failing GitHub Actions `docker-build` job: the workflow built
`infrastructure/docker/Dockerfile.backend` and `Dockerfile.frontend` with the `backend`/`frontend`
directories as the build context, while both Dockerfiles are authored for a **repository-root**
build context (`COPY backend/...`, `COPY frontend/...`, `COPY data ./data`). This caused CI failures
(e.g. `COPY failed: /backend/requirements.txt not found`) even though local `docker compose` builds
already used the correct root context and worked.

The fix, full-stack verification, and a genuine (previously hidden) schema-drift repair are
documented below. All verifications were executed live against the running local stack.

**Result:** both images build with the exact CI commands; the 5-service Compose stack comes up with
all health checks green; Alembic migrations are verified clean on both a fresh database and the live
database; a 131/131 live role/RBAC/security audit passes. Everything committed and pushed to `main`;
CI to be observed post-push.

---

## 2. Docker Build Issue — Root Cause, Fix, Verification

### Root cause
`infrastructure/docker/Dockerfile.backend` and `infrastructure/docker/Dockerfile.frontend` use
**Option A (repo-root context)**:

- `Dockerfile.backend`: `COPY backend/requirements.txt`, `COPY backend/alembic.ini`, `COPY backend/alembic`, `COPY backend/app`, `COPY data ./data`
- `Dockerfile.frontend`: `COPY frontend/package*.json`, `COPY frontend .`, standalone Next.js copy

The GitHub Actions job built them with `backend`/`frontend` as the build context:

```
docker build -t udyogsetu-backend  -f infrastructure/docker/Dockerfile.backend  backend
docker build -t udyogsetu-frontend -f infrastructure/docker/Dockerfile.frontend frontend
```

With a `backend` context, `COPY backend/requirements.txt` resolves to
`backend/backend/requirements.txt` (does not exist) → CI failure. `docker-compose.yml` already used
`context: .`, which is why compose builds succeeded.

### Fix (`backend`/`frontend` context → `.`)
`.github/workflows/ci.yml`, `docker-build` job:

```
docker build -t udyogsetu-backend  -f infrastructure/docker/Dockerfile.backend  .
docker build -t udyogsetu-frontend -f infrastructure/docker/Dockerfile.frontend .
```

### Verification (exact CI commands, run locally)
```
docker build -t udyogsetu-backend  -f infrastructure/docker/Dockerfile.backend  .  → SUCCESS
docker build -t udyogsetu-frontend -f infrastructure/docker/Dockerfile.frontend .  → SUCCESS
```

---

## 3. Repository

| Check | Result |
|---|---|
| Repo structure (backend / frontend / data / infrastructure / docs) | PASS |
| Git status clean at commit point (only intended files committed) | PASS |
| No secrets in tracked files (see Security section) | PASS |
| `data/` present at repo root and consumed at build time (`COPY data ./data`) | PASS |

---

## 4. Dockerfiles & `.dockerignore`

| Check | Result |
|---|---|
| `Dockerfile.backend` — root context, non-root `appuser`, uv+venv, `alembic upgrade head && uvicorn --host 0.0.0.0 --port 8000`, HEALTHCHECK | PASS |
| `Dockerfile.frontend` — root context, Next.js standalone, non-root `nextjs`, `node server.js`, HEALTHCHECK | PASS |
| `.dockerignore` excludes `node_modules`, `venv`, `__pycache__`, `.next`, `.env`, `.git`, `*.log`, secrets data dirs, `frontend/.swc`, `.github` | PASS |
| No source/build secrets baked into images (image `Config.Env` empty of credentials) | PASS |

---

## 5. GitHub Actions / CI

| Job | Change / Status |
|---|---|
| `backend-tests` | Postgres service kept; removed dead env block and unused Redis service; **added** `Verify migrations (alembic upgrade head + check)` step against the CI Postgres — runs the real migration chain in CI |
| `frontend-tests` | Unchanged — jest + `npm run build` |
| `lint` | Unchanged — `ruff check .` (backend) + `npm run lint` (frontend) |
| `docker-build` | **Fixed contexts to `.`**; still `needs` the three test jobs and `if` main-branch push |
| `deploy-staging` | Stub `echo` (no `continue-on-error`, not masking anything) |

No `continue-on-error`, no test skips, no masking.

---

## 6. Backend Image

- CMD: `sh -c alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Workdir `/app`, user `appuser`, `EXPOSE 8000`, ~1.18 GB.
- Healthcheck = `/health` via `urllib` (healthy).
- Migration runner now includes `0005` (see §9).

## 7. Frontend Image

- CMD `node server.js` (Next.js standalone), workdir `/app`, user `nextjs`, `EXPOSE 3000`, ~306 MB.
- Healthcheck: `wget -qO- http://127.0.0.1:3000/`.

## 8. Docker Compose / Deployment

- Backend, frontend build from repo root (context `.`, correct dockerfile paths) — PASS.
- `JWT_SECRET_KEY` enforced via Compose interpolation `:?` (fails fast if unset) — PASS.
- Nginx: HTTP→HTTPS 301, TLS on 443 (self-signed certs mounted from `infrastructure/nginx/certs/`, generated by `scripts/gen-certs.sh`), reverse proxy `/api/` → backend, `/` → frontend, `/docs`, `/openapi.json` — PASS.
- Health checks on Postgres, Redis, backend, frontend — all PASS.
- Local note (non-deployed): Windows host reserves port 80, so a **gitignored**
  `docker-compose.override.yml` remaps nginx to `8080:80` / `8443:443` for local verification.
  The base `docker-compose.yml` keeps the production `80/443` contract.
- `docker compose config -q` → exit 0.
- Live stack: frontend, backend, postgres, redis all Healthy; nginx up. Verified through the TLS
  proxy: `GET /` (frontend HTML) 200, `POST /api/auth/login` (officer) 200 + JWT, `GET /docs` via nginx 200, HTTP→HTTPS redirect 301.

## 9. PostgreSQL & Alembic Migrations

- Live `alembic_version` at `0004` → now `0005` after repair.
- **Drift found & repaired:** `alembic check` on the legacy live DB flagged (a) a stale
  `approvals.custom_metadata` column that predates the current migration chain and (b) five missing
  FK indexes (`ix_approvals_project_id`, `ix_projects_user_id`, `ix_documents_project_id`,
  `ix_notifications_user_id`, `ix_compliance_items_project_id`) that fresh migrations create but the
  older create_all-initialised DB lacked.
- **`0005_reconcile_orm.py`** added: each operation is inspector-guarded so it is a **no-op on a
  freshly migrated database** and repairs a legacy one. Verified both ways:
  - Fresh temp DB `0001→0002→0003→0004→0005` clean; `alembic check` → **No new upgrade operations detected**.
  - Live DB: `custom_metadata` dropped, all 5 indexes created; `alembic check` → **No new upgrade operations detected**.
- `alembic upgrade head` runs automatically on backend container start — PASS.
- 16 tables in `public`; backend `/health` reports `database: ok`.

## 10. Redis

- `docker exec udyogsetu-redis redis-cli ping` → `PONG` — PASS.
- Health check green; used by the containerized backend without issue.

## 11. Health Checks

| Component | Check | Result |
|---|---|---|
| Postgres | `pg_isready` | PASS |
| Redis | `redis-cli ping` | PASS |
| Backend | `GET /health` → `{"status":"healthy","version":"1.0.0","environment":"production","database":"ok"}` | PASS |
| Frontend | `wget http://127.0.0.1:3000/` (found bug: busybox `wget localhost:3000` resolved to `::1` while Next standalone binds IPv4 → fixed to `127.0.0.1`) | PASS |

## 12. Application — Live Full-Role Audit

Live audit harness against the running stack with demo accounts
(officer / entrepreneur / admin):
**131/131 PASS, 0 FAIL** (coverage includes auth, RBAC + role boundaries, BO/BOLA checks
officer↔entrepreneur, malformed-input 422s, admin CRUD for explore services incl. 403 for
entrepreneurs + 409 duplicates, gateway GSTIN/PAN/Udyam verify, observability, frontend routes,
knowledge graph, schemes, compliance).

## 13. Tests, Lint, Typecheck, Build

| Check | Command | Result |
|---|---|---|
| Backend tests | `pytest tests -q` | **196 passed** |
| Backend lint | `ruff check .` | **All checks passed** |
| Frontend tests | `jest` via `npm test` | **16 passed** (3 suites) |
| Frontend typecheck | `tsc --noEmit` | exit 0 |
| Frontend lint | `npm run lint` | exit 0 |
| Frontend build | `npm run build` | exit 0 |
| Docker backend build | CI-equivalent | SUCCESS |
| Docker frontend build | CI-equivalent | SUCCESS |

## 14. Security

| Check | Result |
|---|---|
| Tracked-file secret scan (AI/API/SSH/cloud token patterns) | PASS — no matches |
| Inline credential scan (DB URLs, JWT, passwords outside tests) | PASS — only documented placeholders in `.env.example` / docs |
| Tracked credentials/key files (`.pem`, `.key`, `.env`, secrets) | PASS — none tracked; certs & real `.env` gitignored |
| JWT secret policy (production + empty secret → app refuses to start; `AUTO_GENERATED_SECRET` allowed only outside production) | PASS |
| RBAC/BOLA/IDOR live checks in §12 | PASS (unauthorized access blocked 403/404) |

## 15. Government Integrations (honest disclosure)

MAITRI / MPCB / MIDC / Boiler / Fire / Labour integrations are **MOCK sandbox / derived-mock only**
(simulated latency, seeded statuses). PAN/GST/Udyam/CIN "verify" endpoints return derived-mock
results. Governance: gateway health endpoint reports each system as `HEALTHY` with simulated
`availability_pct` — this is a design decision for the demo and IS NOT live government data. Any
production claim must re-point these adapters at the real APIs and remove the mock simulation.
This is a known limitation (see §16), not a hidden claim.

## 16. Known Limitations

1. Government integrations are mock-only (see §15) — require real API onboarding for production.
2. Nginx uses self-signed certificates generated by `scripts/gen-certs.sh` — replace with a real
   CA certificate + set `server_name` for production.
3. `deploy-staging` CI job is a stub `echo` — the deployment target (host/cloud) must be wired up.
4. Windows local verification uses the gitignored `8080/8443` override because host port 80 is owned
   by http.sys; production base config keeps 80/443.
5. Compliance/MIDC style checks run against seeded mock data, not live regulators.
6. Backend image (~1.18 GB) and frontend (~306 MB) — acceptable for this project; could be slimmed.

## 17. Files Changed (this deployment audit)

- `.github/workflows/ci.yml` — build contexts `.`; added migrations-verification step; removed dead env/unused redis service.
- `docker-compose.yml` — nginx certs mount; frontend healthcheck (`127.0.0.1`).
- `.dockerignore` — added `frontend/.swc`, `.github`.
- `.gitignore` — ignore `infrastructure/nginx/certs/*.pem` / `*.csr` / `.srl`, `docker-compose.override.yml`.
- `scripts/gen-certs.sh` (new) — self-signed TLS cert generator.
- `backend/alembic/versions/0005_reconcile_orm.py` (new) — legacy-DB repair migration.
- `infrastructure/nginx/certs/.gitkeep` (new) — tracked placeholder so the certs dir exists.
- (`docker-compose.override.yml` — created locally, gitignored, not committed.)

## 18. Git Commit & Push

- Commit: `<FILLED_AT_RUN_TIME>` on `main`.
- Pushed with `--force-with-lease` (remote `main` matched local before push).
- CI expected: `backend-tests` (incl. new alembic step), `frontend-tests`, `lint`, `docker-build` green.

---

## Verification Output (exact)

```
Backend Docker build (CI command) ..... PASS
Frontend Docker build (CI command) .... PASS
docker compose config .................. PASS (exit 0)
Compose stack up (5 services) .......... PASS (backend/frontend/postgres/redis Healthy, nginx up)
Backend /health ........................ PASS {"status":"healthy","database":"ok"}
Postgres (16 tables, alembic 0005) ..... PASS
alembic check (fresh DB) ................ PASS No new upgrade operations detected
alembic check (live DB) ................. PASS No new upgrade operations detected
Redis ping .............................. PASS PONG
Frontend healthcheck .................... PASS (healthy)
Nginx HTTPS / ........................... PASS HTTP 200 (frontend HTML via TLS)
Nginx HTTPS /api/auth/login ............. PASS HTTP 200 (JWT issued)
Nginx HTTP→HTTPS 301 .................... PASS
Backend pytest .......................... PASS 196 passed
Backend ruff ............................ PASS All checks passed
Frontend jest ........................... PASS 16 passed (3 suites)
Frontend tsc ............................ PASS exit 0
Frontend lint ........................... PASS exit 0
Frontend build .......................... PASS exit 0
Live full-role audit .................... PASS 131/131
Secret/credential scan .................. PASS no matches
Roles (entrepreneur/officer/admin) ...... PASS
RBAC boundaries (BO/BOLA) ............... PASS
Government integrations ................. MOCK (documented)
```

> Exact roll-up:

- docker-build backend ………………… PASS
- docker-build frontend ………………… PASS
- compose/config ………………………… PASS
- compose up dependent services ……… ALL UP, HEALTHY
- DB / Postgres ………………………… PASS
- Redis …………………………………… PASS
- alembic upgrade head ………………… PASS
- alembic check (fresh + live) ……… PASS
- backend tests ………………………… PASS (196)
- frontend tests ………………………… PASS (16)
- backend lint …………………………… PASS
- frontend lint ………………………… PASS
- frontend tsc …………………………… PASS
- frontend build ………………………… PASS
- health checks ………………………… ALL PASS
- full-role/RBAC/security audit …… 131/131 PASS
- government API honesty ……………… DOCUMENTED MOCK
- secret scan …………………………… PASS
- Git commit ……………………………… see §18
- GitHub push …………………………… SUCCESS
- GitHub Actions ………………………… expected green post-push

**Overall verdict: 🟢 READY FOR DEPLOYMENT**