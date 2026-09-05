# UDYOGSETU — FINAL DEPLOYMENT READINESS REPORT

**Repository:** https://github.com/amulya-ajay/Udyogsetu-SIH-Project-
**Branch:** `main`
**Audit date:** 2026-09-05
**Exact Docker context verified:** repo root `.` — locally AND in GitHub Actions

---

## 1. Executive Summary

The GitHub Actions `docker-build` job was failing because the workflow invoked
`docker build -f infrastructure/docker/Dockerfile.backend backend`, using `backend/` as the build
context while both Dockerfiles are authored for a **repository-root** context
(`COPY backend/requirements.txt`, `COPY backend/app`, `COPY backend/alembic`, `COPY data ./data`).
Compose already used the correct root context, so only CI was broken.

The workflow has been corrected to build from the repository root (`.`), identical to the command
verified locally. The fix is **live on `main`**: the two most recent CI runs (on `1c5e97b9` and
`6742e799`) are green, and the `docker-build` job in run `33977062218` executed both image builds
successfully. The failing runs (`ab4b68d`, `45be90b`) predate the fix.

**Final verdict: 🟢 READY FOR DEPLOYMENT**

## 2. Original Docker Failure

Pre-fix CI run `ab4b68d` (branches `main`) failed the backend image build with:

```text
"/backend/requirements.txt": not found
"/backend/app": not found
"/backend/alembic": not found
"/backend/alembic.ini": not found
"/data": not found
```

Tracing cause: the workflow command `docker build -t udyogsetu-backend -f
infrastructure/docker/Dockerfile.backend backend` set the build context to `backend/`, so every
`COPY backend/...` and `COPY data ...` resolved against `backend/backend/...` and `backend/data`
— none of which exist. A subsequent run (`45be90b`) additionally failed on the frontend image
because the empty `frontend/public/` directory was untracked in git and thus absent from the CI
checkout (`COPY --from=builder /app/public` → "not found").

## 3. Root Cause

1. **Context/architecture mismatch (primary):** CI used `backend`/`frontend` as build contexts;
   the Dockerfiles require the repository root. This single mistake produced all five
   `COPY ... not found` errors.
2. **Untracked empty directory (secondary, frontend):** `frontend/public/` existed only on the
   developer filesystem; git does not track empty directories, so the Actions checkout lacked it.
3. Evidence the failure was CI-only: `docker-compose.yml` already built with `context: .` and the
   local images built successfully before this audit.

## 4. Docker Build Context Analysis

Actual repository structure (verified with `git ls-tree` / filesystem):

```text
UDYOGSETU/
├── backend/            requirements.txt, app/, alembic/, alembic.ini
├── data/               (repository-level directory — used by backend image at runtime)
├── frontend/
├── infrastructure/     docker/, nginx/
├── docs/ scripts/ .github/
```

Confirmations:
- `backend/requirements.txt` ... inside `backend/`.
- `backend/app` ... inside `backend/`.
- `backend/alembic*` ... inside `backend/`.
- `data/` ... at repository root (NOT inside `backend/`).

Therefore the **preferred architecture** applies: backend Docker build must use the repository
root as context. `data/` was NOT moved into `backend/data/` (no duplication, no deletion).

## 5. Dockerfile Changes

**None required — and none applied.** The Dockerfiles retain their intended COPY paths:

```dockerfile
COPY backend/requirements.txt .
COPY backend/alembic.ini .
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY data ./data
```

## 6. .dockerignore Changes

`.dockerignore` (root) inspected:

- Does NOT exclude `backend/`, `data/`, or `infrastructure/`.
- Does NOT use a broad `**` or `*` rule.
- Excludes only junk/artifacts/secrets: `node_modules`, `venv`, `__pycache__`, `*.pyc`, `.next`,
  `dist`, `build`, `frontend/.swc`, `.env`, `.git`, `.gitignore`, `.github`, `.DS_Store`,
  `*.log`, `backend-build.log`, `coverage`, and the two optional data blobs
  `data/mock_government_data`, `data/sample_documents` (not required by the built image).
- Added this audit: `frontend/.swc`, `.github` (buildable with a root context).

Final CI build context therefore contains `backend/requirements.txt`, `backend/app/`,
`backend/alembic/`, `backend/alembic.ini`, `data/`, and `infrastructure/docker/Dockerfile.backend`.

## 7. GitHub Actions Changes

`.github/workflows/ci.yml`:

- `docker-build` backend:
  - BEFORE: `docker build -t udyogsetu-backend -f infrastructure/docker/Dockerfile.backend backend`
  - AFTER:  `docker build -t udyogsetu-backend -f infrastructure/docker/Dockerfile.backend .`
- `docker-build` frontend: `frontend` → `.` (same reason).
- Backend-tests job: added `Verify migrations (alembic upgrade head + check)` step against a real
  Postgres service; removed the dead env block and the unused Redis service.
- No `continue-on-error`, no disabled steps, no excluded tests.

Verified exhausted alternatives and rejected the "move `data/`" approach — `data/` is a
repository-level directory by design.

## 8. Backend Test Results

`python -m pytest tests -q` (fresh run, local)

```text
196 passed, 1 warning in 747.68s
```

CI `backend-tests` job on `6742e799`: **success**.

Also resolves the previously-reported legacy failure:
`TypeError: Invalid argument(s) 'pool_size', 'max_overflow' sent to create_engine()` (SQLite).
`backend/app/core/database.py:_engine_kwargs` now applies pool args **only** when
`url.startswith("postgresql")`; `tests/conftest.py` pins SQLite before app import. The 196 passing
tests prove SQLite test engines receive no PostgreSQL-only pool arguments.

## 9. Backend Lint Results

`ruff check .` (project-configured linter, backend):

```text
All checks passed!
```

CI `lint` job on `6742e799`: **success**. No blanket `noqa`, no tests excluded, no linter disabled.

## 10. Frontend Test Results

`npm test -- --ci` (jest):

```text
PASS __tests__/auth.test.ts
PASS __tests__/api-contract.test.ts
PASS __tests__/utils.test.ts
Test Suites: 3 passed, 3 total
Tests:       16 passed, 16 total
```

CI `frontend-tests` job on `6742e799`: **success**.

## 11. TypeScript Results

`npx tsc --noEmit` → **exit 0**, no errors.

## 12. Production Build Results

`npm run build` → **exit 0** (Next.js standalone output; static + dynamic routes compiled).

## 13. Docker Backend Build

Exact CI command (root context), run locally:

```bash
docker build -t udyogsetu-backend -f infrastructure/docker/Dockerfile.backend .
```

**PASS** (exit 0). Image: `python:3.11-slim`, CMD `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000`, user `appuser`, WORKDIR `/app`.

## 14. Docker Frontend Build

Exact CI command, run locally:

```bash
docker build -t udyogsetu-frontend -f infrastructure/docker/Dockerfile.frontend .
```

**PASS** (exit 0). Image: `node:20-alpine` multi-stage, Next.js standalone server, user `nextjs`.

## 15. Docker Compose

- `docker compose config -q` → **exit 0** (valid; frontend healthcheck, nginx certs mount present).
- `docker compose build` → **exit 0** (both images built via Compose, context `.`).
- `docker compose up -d` → all services running (local override 8080/8443 because Windows owns
  port 80; base compose keeps production 80/443).
- `docker compose ps`: backend healthy, frontend healthy, postgres healthy, redis healthy, nginx up.

## 16. PostgreSQL

- `pg_isready` → `accepting connections`, version 15 (Compose Postgres).
- 16 application tables present in `public`.
- Backend `/health` returns `"database": "ok"`.

## 17. Redis

- `redis-cli ping` → **PONG**.
- Redis 7 container health check green.

## 18. Alembic

- `alembic upgrade head` runs automatically at container start → head **0005**.
- `alembic check` (live DB) → **No new upgrade operations detected.**
- Migration `0005_reconcile_orm` (inspector-guarded) repairs legacy databases (drops stale
  `approvals.custom_metadata`, adds 5 missing FK indexes) and is a no-op on fresh databases —
  verified on a fresh DB (`0001→0005` clean + `alembic check` clean).
- CI now exercises the real chain against a Postgres service.

## 19. Authentication

- `POST /api/auth/login` (officer demo account) through the nginx TLS proxy → **200**, JWT issued
  (HS256, correct sub/email/role/exp), `bearer` type, `expires_in: 86400`.
- JWT policy: production with an empty/absent `JWT_SECRET_KEY` fails fast at startup
  (`config.py` validator + `AUTO_GENERATED_SECRET` only outside production); compose `:?` guard.
- Refresh/logout/register endpoints covered by the 196-test suite and the live E2E audit.

## 20. Entrepreneur

Demo entrepreneur account:
- Login → 200 + JWT. Dashboard accesses (projects, applications, compliance, explore, schemes,
  documents, chat) → 200.
- Project ownership enforced (cannot read other users' projects; random/malformed UUIDs → 404/422).
- Non-privileged actions (e.g. creating/updating explore services) → **403**.
- Status in E2E audit: **PASS**.

## 21. Officer

Demo officer account:
- Login → 200 + JWT. Officer dashboard/gateway views → 200.
- Gateway submissions and government-system health endpoint → 200.
- Can read own projects; cross-tenant access blocked (**403/404**).
- Status in E2E audit: **PASS**.

## 22. Admin

Demo admin account:
- Explore-service CRUD: create 201, duplicate 409, update 200 — all **PASS**.
- Observability/admin routes → 200.
- Privilege boundaries (entrepreneur attempting admin actions) → 403.
- Status in E2E audit: **PASS**.

## 23. RBAC

- Server-side enforcement verified, not just UI hiding: officer↔entrepreneur data isolation,
  admin-only endpoints, BO/BOLA probes (foreign project → 403/404), malformed input → 422.
- Live audit: **131/131 PASS** (`SUMMARY: 131/131 PASS 0 FAIL`).

## 24. Security

- Git: no `.env`, `.pem`, `.key`, DB dumps, API keys, tokens, or override files tracked; only
  `.env.example` with placeholders. `git grep` for AI/cloud/JWT/private-key patterns → no matches.
- Images: `docker image inspect udyogsetu-backend` → `Config.Env` contains **only base-image
  variables** (PATH, LANG, PYTHON_VERSION, ...); no secrets baked at build time. Runtime secrets are
  injected by Compose at container creation (correct pattern).
- Certificates (`infrastructure/nginx/certs/*.pem`) and `docker-compose.override.yml` are
  gitignored.
- JWT production fail-fast + strong secret kept only in the untracked local `.env`.

## 25. Government Integrations

| Integration | Status |
|---|---|
| MAITRI (Monday portal) | **MOCK** — simulated sandbox adapter (latency + seeded data) |
| MPCB | **MOCK** — simulated sandbox adapter |
| MIDC | **MOCK** — simulated sandbox adapter |
| Boiler / Fire / Labour | **MOCK DEMO** — seeded rules/checklists |
| PAN / GST / Udyam / CIN "verify" | **DEMO (derived mock)** — deterministic mock responses |
| Real government APIs | **NOT CONFIGURED** — no authorized API credentials exist for this project |

Gateway health reports each simulated system as `HEALTHY` with simulated `availability_pct`; this
is demo behavior. Production deployment must re-point adapters to real APIs with authorized
credentials. No claim is made that live government data is being used.

## 26. Files Changed

- `.github/workflows/ci.yml` — build contexts `.` (backend+frontend); added `Verify migrations`
  step (alembic upgrade head + check on Postgres service); removed dead env/Redis service.
- `backend/alembic/versions/0005_reconcile_orm.py` — new legacy-DB repair migration (guarded).
- `frontend/public/.gitkeep` — new; preserves `public/` in CI checkouts (fixed the residual CI-only
  frontend COPY failure).
- `docker-compose.yml` — nginx TLS certs mount; frontend healthcheck `127.0.0.1:3000`.
- `.dockerignore` — added `frontend/.swc`, `.github`.
- `.gitignore` — ignore `infrastructure/nginx/certs/*.pem|*.csr|.srl`, `docker-compose.override.yml`.
- `scripts/gen-certs.sh` — new self-signed cert generator.
- `infrastructure/nginx/certs/.gitkeep` — tracked placeholder.
- `UDYOGSETU_FINAL_DEPLOYMENT_READINESS_REPORT.md` — this report.

## 27. Git Commit

`main` history for this fix (commits already landed):

```text
6742e799 docs: finalize deployment readiness report with CI results and commits
1c5e97b9 fix: track frontend/public/.gitkeep so CI docker build finds /app/public
45be90b4 fix: correct Docker build contexts and reconcile CI/deployment pipeline
ab4b68db UDYOGSETU: production readiness pass - compliance seeding, JWT secret fail-fast, ...
```

## 28. GitHub Push

Pushed with `git push --force-with-lease origin main` (remote `main` matched local each time; no
force-plain needed). Verified: `origin/main == local HEAD == 6742e79984162d3242c9274b93592a0b6c395f7f`.

## 29. GitHub Actions Result

Latest run on `6742e79` (run id `33977062218`):

```text
backend-tests   -> success
frontend-tests  -> success
lint            -> success
docker-build    -> success   (steps: ... Set up Docker Buildx, Build backend image, Build frontend image ...)
deploy-staging  -> success
```

Run on `1c5e97b`: **success** as well. Pre-fix runs `ab4b68d`/`45be90b` failed and are historical.
The workflow source on `main` (fetched raw from GitHub) shows `.` contexts — CI and local builds are
identical.

## 30. Known Limitations

1. Government adapters are MOCK/DEMO; real APIs NOT CONFIGURED (no credentials available). See §25.
2. Nginx uses self-signed certs (`scripts/gen-certs.sh`) — replace with a CA-signed cert for prod.
3. `deploy-staging` job is an `echo` stub; hosting target not wired up.
4. `NEXT_PUBLIC_API_URL` is baked into the frontend at build time (currently `localhost` default);
   set to the deployed domain when building for production.
5. Local verification uses the gitignored `8080/8443` override (Windows owns port 80); the base
   compose file keeps the production 80/443 contract.

## 31. Final Readiness Verdict

**🟢 READY FOR DEPLOYMENT** — Docker build context verified identical between local and GitHub
Actions; both CI image builds and every test/lint/type/build/DB/Redis/migration/auth/RBAC/security
check pass.