# UDYOGSETU — Deployment Guide (Vercel + Railway)

This guide deploys UDYOGSETU with:

- **Frontend** → Vercel (Next.js 14 App Router, TypeScript)
- **Backend** → Railway (FastAPI, Python, Docker)
- **Database** → Railway PostgreSQL
- **Cache** → Railway Redis
- **Source control** → GitHub

Everything below was verified against the repository at commit
`850ee2e9` plus the deployment changes in this branch.

---

## 1. Prerequisites

- A GitHub account and the repository pushed to GitHub.
- A [Railway](https://railway.app) account (start free; connect GitHub).
- A [Vercel](https://vercel.com) account (start free; connect GitHub).
- Docker installed locally (to run the same images you deploy).
- Node 20+ and Python 3.11+ for local runs (optional if you only use Docker).

## 2. GitHub setup

```bash
git remote add origin https://github.com/<you>/udyogsetu.git
git push -u origin main
```

Nothing secret lives in the repository. `.env`, `.env.*`, certs, and the
`docker-compose.override.yml` are gitignored. Only `.env.example` files are
tracked.

## 3. Railway account/project

1. Create a **new project** on Railway.
2. Link it to your GitHub repo (authorize the app).
3. You will create three services: PostgreSQL, Redis, and the backend.

## 4. PostgreSQL creation (Railway)

1. In the project, click **+ New → Database → PostgreSQL**.
2. Railway injects the connection string automatically as the **`DATABASE_URL`**
   environment variable on every service that needs it.
3. Note the URL format Railway sets: `postgresql://user:pass@host:port/db`.
   The backend **normalizes this automatically** to `postgresql+asyncpg://`
   (verified: `alembic` and the async engine accept the driver-less URL), so
   nothing to configure.

## 5. Redis creation (Railway)

1. Click **+ New → Database → Redis**.
2. Railway injects **`REDIS_URL`** automatically.
3. Redis is used by the **rate limiter only**, and the middleware **fails open**
   if Redis is unreachable (no hard outage).

## 6. Backend service creation (Railway)

1. Click **+ New → GitHub Repo → select the repository**.
2. Delete the auto-generated start/init anything that is not the backend; create
   the backend deploy with these settings:

| Setting | Value |
|---|---|
| Root Directory | `.` (repository root) |
| Watch Paths | `backend/**,data/**,infrastructure/**` |
| Dockerfile Path | `infrastructure/docker/Dockerfile.backend` |
| Build Context | repository root (`.`) — **do not** use `backend` as context |

The build context must remain the repository root because the Dockerfile uses
root-relative paths (`COPY backend/...`, `COPY data ./data`).

## 7. Dockerfile configuration

- The backend Dockerfile is `infrastructure/docker/Dockerfile.backend`
  (multi-stage, Python 3.11, runs as non-root `appuser`).
- The frontend Dockerfile is `infrastructure/docker/Dockerfile.frontend`
  (used for local Docker demo; the hosted frontend is built by Vercel).

Builds locally:

```bash
docker build -t udyogsetu-backend -f infrastructure/docker/Dockerfile.backend .
docker build -t udyogsetu-frontend -f infrastructure/docker/Dockerfile.frontend .
```

## 8. Build context

Verified — CI and local builds use the **root** context. Do not change these
commands to `... Dockerfile.backend backend`.

## 9. Environment variables (Railway)

Set these on the **backend** service (Variables tab):

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `JWT_SECRET_KEY` | generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `CORS_ORIGINS` | JSON array, e.g. `["https://<your-app>.vercel.app"]` |
| `ALLOWED_HOSTS` | JSON array, e.g. `["localhost","127.0.0.1","<service>.<env>.up.railway.app"]` |
| `DATABASE_URL` | (auto-injected by Railway PostgreSQL) |
| `REDIS_URL` | (auto-injected by Railway Redis) |
| `PORT` | (auto-injected by Railway) |
| `UPLOAD_DIRECTORY` | `/tmp/udyogsetu/uploads` (ephemeral — see Limitations) |
| `RATE_LIMIT_ENABLED` | `true` (optional) |
| `GEMINI_API_KEY` / `GROQ_API_KEY` | optional, drop-in for real LLM |

**Important:** `ALLOWED_HOSTS` must include the Railway public domain
(`<app>.<env>.up.railway.app`) or a custom domain, otherwise every request is
rejected with HTTP 400 by `TrustedHostMiddleware`. If you add a custom domain,
add it here too.

## 10. Alembic pre-deploy migration

On the backend service: **Settings → Deploy → Pre-deploy Command**:

```
alembic upgrade head
```

- Migrations are idempotent. Head is currently `0005`.
- The **Start command must NOT run migrations** (see next section) so workers
  never race migrations.

## 11. Start command

On the backend service: **Settings → Deploy → Start Command**:

```
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

If you leave Start Command empty, the Dockerfile CMD
(`alembic upgrade head && uvicorn ... --port ${PORT:-8000}`) runs — which then
runs migrations at every container start. Use the override above when using a
pre-deploy command.

Entrypoint verified: the FastAPI app is at `app.main:app`.

## 12. Health check

- **Liveness/readiness:** `GET /health` (root path), returns
  `{"status":"healthy","version":"1.0.0","environment":"production","database":"ok"}`.
  It verifies database connectivity with `SELECT 1`.
- On Railway: **Settings → Deploy → Health Check Path = `/health`**.
- It exposes no credentials or secrets.

## 13. Railway domain

- Railway gives `<service>.<env>.up.railway.app`.
- Remember to add that host to `ALLOWED_HOSTS` (step 9).
- (Optional) Add a custom domain under Settings → Networking; add it to
  `ALLOWED_HOSTS` as well.

## 14. Vercel setup

1. **Import the repository** into Vercel.
2. Configure the project:

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Framework | Next.js |
| Install command | `npm ci` (default) |
| Build command | `npm run build` |
| Output directory | `.next` (default) |

## 15. Frontend root directory

`frontend` — Vercel only builds the frontend app; the backend is on Railway.

## 16. Frontend environment variables (Vercel)

Set on Vercel (Project → Settings → Environment Variables):

| Variable | Environment | Value |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Production | `https://<railway-backend-url>/api` |
| `NEXT_PUBLIC_API_URL` | Preview | `https://<railway-preview-url>/api` |
| `NEXT_PUBLIC_API_URL` | Development | `http://localhost:8000/api` |

Notes:

- `NEXT_PUBLIC_*` values are inlined at **build time** and shipped to the
  browser. **Never** put backend secrets here.
- The value must end in `/api` (backend routers are mounted under `/api`;
  e.g. login is `POST /api/auth/login`).
- Verified: when `NEXT_PUBLIC_API_URL` is set to a non-localhost URL at build
  time, the production bundle contains that URL and no `localhost:8000`.

## 17. CORS configuration

The backend CORS middleware already reads `CORS_ORIGINS` (JSON array) and
allows credentials. Production example:

```
CORS_ORIGINS=["https://udyogsetu.vercel.app"]
```

- Allow only the exact frontend origin(s).
- `allow_credentials=True` — never use `*` with credentials.
- Verified against the running production-mode stack: allowed origin preflight
  returns `Access-Control-Allow-Origin: <origin>`; a foreign origin gets no
  CORS headers.

## 18. First deployment

1. Push to `main` (CI runs tests, lint, Docker builds).
2. Deploy backend on Railway: it builds the image, runs pre-deploy
   `alembic upgrade head`, then starts uvicorn.
3. Deploy frontend on Vercel (or merge to the production branch configured in
   Vercel).

## 19. Database migration verification

After the backend deploys:

```bash
docker run --rm --network <network> -e DATABASE_URL="postgresql://..." udyogsetu-backend alembic current
# expected: 0005 (head)
docker run --rm --network <network> -e DATABASE_URL="postgresql://..." udyogsetu-backend alembic check
# expected: No new upgrade operations detected.
```

On Railway you can run these by overriding the start command temporarily, or
from the postgres CLI:

```sql
SELECT version_num FROM alembic_version;
-- expected: 0005
```

## 20. Health verification

```bash
curl https://<railway-backend-url>/health
# {"status":"healthy", ...,"database":"ok"}
```

If `database` is `"error"`, the app still starts but cannot reach PostgreSQL —
check the Railway Postgres deployment and `DATABASE_URL`.

## 21. Login test

```bash
curl -X POST https://<railway-backend-url>/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"entrepreneur.e2e@udyogsetu.demo","password":"E2ePass@123"}'
# returns access_token + user with role ENTREPRENEUR
```

Then open the Vercel app, log in, and confirm the dashboards load
(Entrepreneur / Officer / Admin flows were all verified end-to-end in the
audit).

## 22. Full E2E test

Not covered by hosted CDC automated checks — do it manually:

1. Register an entrepreneur → create project → analyze approvals → Explore →
   select service → apply → upload a document → validate → submit.
2. Officer login → review/transition.
3. Admin login → admin functions.
4. Negative paths: entrepreneur hitting officer/admin APIs returns 403
   (server-side RBAC; covered by backend tests).

## 23. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Every request → HTTP 400 | `ALLOWED_HOSTS` missing the Railway domain. Add `<app>.<env>.up.railway.app`. |
| Browser blocks API calls (CORS) | `CORS_ORIGINS` missing the exact Vercel origin (scheme + host). Rebuild backend. |
| `JWT_SECRET_KEY` error at startup | Production refuses to start without a strong secret. Set a `secrets.token_hex(32)` value. |
| `ModuleNotFoundError: psycopg2` | Outdated image without URL normalization — rebuild with this branch's `backend/app/core/database.py`. |
| Uploads disappear after deploy | File storage is local/ephemeral on Railway (see Limitations). |
| Slow cold starts on document/OCR | OCR/tesseract loads in-process; this is expected on a single container. |
| `alembic check` reports drift | Run this branch's migrations; head is `0005`. |

## 24. Rollback strategy

- **Backend (Railway):** open the service → Deployments → select the previous
  successful deploy → **Rollback**. Env vars follow the deployment.
- **Database:** Railway snapshots come from the dashboard (or your backup cron).
  Restoring overwrites data — restore only in prolonged outages.
- **Frontend (Vercel):** Production Deployments → pick previous → **Promote to
  Production**. Frontend and backend are decoupled, so a frontend rollback does
  not touch the API.

## 25. Current limitations

- **File storage is local and ephemeral on Railway** (uploaded documents live
  under `UPLOAD_DIRECTORY`; `Dockerfile` uses `/var/uploads` in compose with a
  volume, but Railway containers are stateless). The document pipeline still
  works within a single deploy. **Future:** move to S3/R2/Supabase Storage —
  not done because it would change the storage abstraction and is a larger
  change than this deployment task.
- **Background jobs use an in-process asyncio queue** (`app/workers/background.py`);
  job state is in-memory and is lost on restart/redeploy. OCR/embedding/RAG
  jobs run fine in a single instance. **Future:** Celery/RQ with Redis broker.
- **Government integrations are MOCK/DEMO adapters** (MAITRI, MPCB, MIDC and
  GSTIN/PAN/Udyam verification all call the bundled mock gateway). No real
  government API credentials exist.
- **AI/LLM**: defaults to a safe **mock** provider; set `GEMINI_API_KEY` /
  `GROQ_API_KEY` for real LLM answers. No custom-trained model exists.
- **Regulatory knowledge / RAG** is seeded from `data/regulations` — static,
  re-ingested at startup.
- **Single-instance assumption:** in-memory job queue + no shared storage mean
  you should keep the backend at **replicas = 1**.

---

### Quick reference — exact commands

```bash
# Local Docker (repository root)
docker compose up --build

# Backend image (root context)
docker build -t udyogsetu-backend -f infrastructure/docker/Dockerfile.backend .

# Frontend image (root context)
docker build -t udyogsetu-frontend -f infrastructure/docker/Dockerfile.frontend .

# Backend tests (from backend/)
python -m pytest tests -q          # 202 passed

# Migrations
alembic upgrade head
alembic check
```