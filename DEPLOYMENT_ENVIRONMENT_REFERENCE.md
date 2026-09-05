# UDYOGSETU — Deployment Environment Reference

This is the single source of truth for every environment variable the
application reads, what it does, where it is configured, and whether it is a
secret. **No real secrets appear in this document.** All values are examples.

Sources: `backend/app/core/config.py`, `frontend/services/api.ts`,
`frontend/next.config.js`, `docker-compose.yml`.

---

## Backend variables

Configured on the **Railway backend service** (Variables tab) or the local
`.env`. `DATABASE_URL` and `REDIS_URL` are auto-injected when Railway
PostgreSQL/Redis are attached; all other variables must be set explicitly.

| Variable | Required? | Purpose | Example | Secret? | Where configured |
|---|---|---|---|---|---|
| `DATABASE_URL` | Yes | Async SQLAlchemy engine (asyncpg). Plain `postgresql://` is auto-normalized to `+asyncpg`. | `postgresql+asyncpg://u:p@host:5432/db` | Yes | Railway (auto) / root `.env` |
| `REDIS_URL` | Optional* | Rate limiter backend. App fails open if unreachable. | `redis://default:p@host:6379` | Yes | Railway (auto) / root `.env` |
| `JWT_SECRET_KEY` | Yes (prod) | Signs/verifies JWT. Production fails fast if empty or weak. | `aab36f8d...` (64 hex chars) | Yes | Railway / root `.env` |
| `JWT_ALGORITHM` | No | Token algorithm. | `HS256` | No | Railway / `.env` |
| `JWT_EXPIRATION_HOURS` | No | Token TTL. | `24` | No | Railway / `.env` |
| `ENVIRONMENT` | Yes (prod) | Env banner; gates `create_all` and docs URLs. | `production` | No | Railway / `.env` |
| `DEBUG` | No | Log level + docs + engine echo. | `false` | No | Railway / `.env` |
| `CORS_ORIGINS` | Yes (prod) | Allowed browser origins (JSON array). | `["https://udyogsetu.vercel.app"]` | No | Railway / `.env` |
| `ALLOWED_HOSTS` | Yes (prod) | TrustedHost allow-list (JSON array). Must include the Railway/custom domain. | `["localhost","127.0.0.1","app.production.up.railway.app"]` | No | Railway / `.env` |
| `PORT` | No | HTTP port; falls back to 8000. | `8080` | No | Railway (auto) |
| `UPLOAD_DIRECTORY` | No | Local file storage dir (ephemeral on Railway). | `/tmp/udyogsetu/uploads` | No | Railway / `.env` |
| `MAX_UPLOAD_SIZE_MB` | No | Upload limit. | `50` | No | Railway / `.env` |
| `RATE_LIMIT_PER_MINUTE` | No | Per-IP requests/minute. | `60` | No | Railway / `.env` |
| `RATE_LIMIT_ENABLED` | No | On/off for Redis rate limiter. | `true` | No | Railway / `.env` |
| `APP_NAME` / `APP_VERSION` | No | Display metadata. | `UDYOGSETU` / `1.0.0` | No | Railway / `.env` |
| `DATA_DIRECTORY` | No | Seed data path (baked into image as `./data`). | `./data` | No | image default |
| `GEMINI_API_KEY` | Optional | Real LLM provider (falls back to mock if unset). | `AIza...` | Yes | Railway only (server-side) |
| `GROQ_API_KEY` | Optional | Alternative LLM provider. | `gsk_...` | Yes | Railway only (server-side) |
| `OLLAMA_BASE_URL` | Optional | Local Ollama (not remote). | `http://localhost:11434` | No | Railway / `.env` |
| `DEFAULT_LLM_PROVIDER` | No | `gemini` / `groq` / `ollama` / `mock`. | `gemini` | No | Railway / `.env` |
| `EMBEDDING_MODEL` / `EMBEDDING_PROVIDER` | No | Embedding config; default `mock` needs no service. | `mock` | No | Railway / `.env` |
| `SMTP_SERVER` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | Optional | Email notifications. | `smtp.gmail.com` / `587` | Password **yes** | Railway / `.env` |

\* `REDIS_URL` is "optional" at runtime because the rate limiter fails open; but
you should always attach Railway Redis so rate limiting actually works.

### Required production set (Railway summary)

```
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=<generated 64-hex>
CORS_ORIGINS=["https://<vercel-app>.vercel.app"]
ALLOWED_HOSTS=["localhost","127.0.0.1","<railway-app>.<env>.up.railway.app"]
DATABASE_URL=<auto from Railway Postgres>
REDIS_URL=<auto from Railway Redis>
```

---

## Frontend variables

Configured on **Vercel** per environment (Project → Settings → Environment
Variables). `NEXT_PUBLIC_*` values are baked into the browser bundle at
**build time** — a change requires a redeploy, and they are visible to anyone.

| Variable | Required? | Purpose | Example | Secret? | Where configured |
|---|---|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes (prod) | Base URL of the backend API (must end in `/api`). | `https://app.production.up.railway.app/api` | No | Vercel (Prod/Preview); Dev = `http://localhost:8000/api` |

Applied by `frontend/services/api.ts` (axios baseURL). `frontend/next.config.js`
injects the same value into `NEXT_PUBLIC_API_URL` with a `localhost:8000`
fallback for local dev.

**Never** place JWT secrets, database credentials, or LLM API keys in
`NEXT_PUBLIC_*` variables.

---

## Local (Docker Compose)

Variables live in the root `.env` (gitignored; copy from `.env.example`).
`docker-compose.yml` maps:
- `POSTGRES_PASSWORD` — password for the local `postgres` service
  (default `password`).
- `JWT_SECRET_KEY` — required (compose fails if unset via `:?`).
- `ENVIRONMENT` (default `production`), `DEBUG=false`, `UPLOAD_DIRECTORY=/var/uploads`.

Local frontend container and local `NEXT_PUBLIC_API_URL` (dev) point at
`http://localhost:8000/api`.

---

## Variable → setting mapping (code)

| Variable | Code reference |
|---|---|
| `DATABASE_URL` | `backend/app/core/database.py` |
| `REDIS_URL` | `backend/app/core/ratelimit.py`, `config.py` |
| `JWT_SECRET_KEY` + JWT settings | `backend/app/core/config.py` |
| `CORS_ORIGINS` | `backend/app/main.py` (CORSMiddleware) |
| `ALLOWED_HOSTS` | `backend/app/main.py` (TrustedHostMiddleware) |
| `UPLOAD_DIRECTORY` | `backend/app/services/document_processor.py` |
| AI keys/provider | `backend/app/ai/llm_provider.py`, `embeddings.py` |
| `NEXT_PUBLIC_API_URL` | `frontend/services/api.ts`, `frontend/next.config.js` |

---

## Environment matrix

| Env var | LOCAL (compose) | RAILWAY | VERCEL |
|---|---|---|---|
| `DATABASE_URL` | `postgres` service | auto (Postgres) | — |
| `REDIS_URL` | `redis` service | auto (Redis) | — |
| `JWT_SECRET_KEY` | required | required | — |
| `CORS_ORIGINS` | localhost origins | Vercel origins | — |
| `ALLOWED_HOSTS` | localhost | Railway domains | — |
| `DEBUG` | `false` | `false` | — |
| `ENVIRONMENT` | `production` (default) | `production` | — |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api` | — | Railway URL `/api` |

`—` = not used by that side.