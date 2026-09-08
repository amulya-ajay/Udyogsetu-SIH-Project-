# UDYOGSETU — Technical Approach & Methodology

UDYOGSETU is a full-stack "ease of doing business" platform that guides
entrepreneurs through government approvals, incentives and compliance for new
industrial projects, and equips government officers with review, analytics and
decision tools. This document describes how the system is engineered — the
architecture, technology choices, and the methodology behind each feature
area.

---

## 1. System Overview

| Aspect | Approach |
|---|---|
| Product | Unified clearance / business-facilitation portal (entrepreneur + officer + admin roles) |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2 (async), Alembic, asyncpg, Redis |
| Frontend | Next.js 15 (App Router), React, TypeScript, Tailwind CSS, TanStack React Query |
| Database | PostgreSQL (local/Docker/Neon), SQLite (tests only) |
| AI/OCR | RAG pipeline, Tesseract OCR, provider-agnostic LLM wrapper (Gemini/Groq/Ollama/Mock) |
| Gov integrations | Contract-based adapters against a deterministic mock government API |
| Deploy | Docker Compose (Postgres + Redis + backend + frontend + nginx), CI on GitHub Actions, Render/Neon-friendly |

The methodology is **API-first, async throughout**, with deterministic
rule-based reasoning for approvals, RAG-based retrieval for regulatory
answers, and idempotent seed/cleanup so the system can be reset and demoed
repeatably.

---

## 2. High-Level Architecture

```
 Browser
   |
   | HTTPS
   v
 nginx (TLS, 301 http->https, reverse proxy)
   |                         |
   v                         v
 Next.js frontend (:3000)  FastAPI backend (:8000, /api)
   |                    |         |           |          |
 axios + React Query    |         |           |          +---> Redis (rate limit)
   |                    +---> SQLAlchemy async (asyncpg)  +---> Background workers
   |                              |                              (asyncio queue)
   |                              v
   |                     PostgreSQL  (Alembic migrations)
   |
   +---> LLM providers: Gemini / Groq / Ollama / Mock  (RAG + copilot)
   +---> Tesseract OCR  (document extraction)
   +---> Government gateway -> 6+ mock agency adapters (Maitri, MPCB, MIDC, Boiler, Fire, Labour, ...)
```

Key frontend entry points: `/dashboard/new-project` (5-step onboarding wizard),
`/dashboard/[projectId]` (approvals graph, documents, compliance, copilot,
schemes), `/dashboard/officer` (review + analytics), `/auth/login`,
`/auth/register`.

---

## 3. Technology Stack & Rationale

### Backend
- **FastAPI** — async native, OpenAPI generation, Pydantic validation. `/docs`
  and `/redoc` exposed only when `DEBUG=true`.
- **SQLAlchemy 2.0 async + asyncpg** — a single async engine
  (`backend/app/core/database.py`) with connection pooling
  (`pool_size=20`, `max_overflow=10`, `pool_pre_ping`, `pool_recycle=300`).
- **Alembic** — authoritative schema management (migrations `0001`–`0005`),
  never `create_all()` in production.
- **Pydantic v2 + pydantic-settings** — typed, env-driven configuration with
  production fail-fast validation.
- **Redis + token-bucket rate limiting** — `core/ratelimit.py`, fails **open**
  if Redis is unreachable so a transient cache failure never blocks the API.

### Frontend
- **Next.js App Router + TypeScript** — Strict TS, typed API contracts.
- **axios interceptors** — auto `Bearer` token injection, 401 → redirect to
  `/login` (`frontend/services/api.ts`).
- **TanStack React Query 5** — server-state caching, optimistic/invalidate
  patterns (`frontend/lib/providers.tsx`).
- **Tailwind CSS + Radix UI + reactflow + recharts** — UI primitives,
  approval dependency graph, and officer dashboard charts.
- **react-hook-form + zod** — validated multi-step wizard forms.

### Why this composition
Everything that can degrade is degraded gracefully: AI falls back to a
grounded mock, rate limiting fails open, seed failures don't block startup,
and the async stack keeps long-running background work (document processing,
RAG ingest) off the request path.

---

## 4. Backend Structure & Request Pipeline

`backend/app/`:

| Path | Purpose |
|---|---|
| `main.py` | App factory, lifespan, middleware stack, router mounting, `/health` |
| `api/` | 21 routers assembled in `api/routes.py` under `/api` |
| `core/` | `config` (settings), `database` (engine + URL normalization), `security` (JWT/bcrypt), `ratelimit` |
| `models/` | SQLAlchemy models + enums |
| `schemas/` | Pydantic request/response schemas |
| `services/` | Business logic (auth, projects, compliance, incentives, scenarios, docs, gateway, analytics, ...) |
| `rules/` | Deterministic approval-determinination engine |
| `rag/` | Retrieval-augmented generation pipeline |
| `integrations/` | Government adapters + mock government API shim |
| `ai/` | LLM provider abstraction, embeddings, OCR, copilot tools |
| `workers/` | In-process asyncio background queue + task definitions |
| `workflows/` | Multi-step copilot orchestration |
| `audit/`, `notifications/` | Audit-log persistence and in-app notifications |

### Middleware stack (bottom-up)
1. **CORS** — strict `settings.CORS_ORIGINS` allow-list, no wildcard.
2. **TrustedHost** — rejects unknown `Host` headers via `ALLOWED_HOSTS`
   (returns HTTP 400, defeating DNS-rebinding).
3. **Rate limit** — Redis token bucket when enabled; `/api/health` and
   docs paths excluded.
4. **Audit middleware** — persists `AuditLog` for authenticated mutations.
5. **Request-ID + response time** — every request logged with
   `X-Request-ID` / `X-Response-Time`.
6. **Global exception handler** — 500 with `request_id` correlation.

### Lifespan methodology
- Non-production: `Base.metadata.create_all()` for fast local iteration.
- **Production: schema strictly via Alembic** (`create_all` suppressed) —
  the running containers execute `alembic upgrade head` before uvicorn starts.
- Idempotent `_seed_data()` loads approval rules, incentive schemes,
  regulation knowledge and service explorer data from `data/` (JSON/MD),
  continuing startup if seeding fails.

### /health
`{"status", "version", "environment", "database"}` backed by a real
`SELECT 1` — the source of truth for the Docker healthcheck and platform
health checks.

---

## 5. Data Model & Persistence

Models (in `backend/app/models/__init__.py`):
**User, Project, Approval, ApprovalRule, Document, ComplianceItem, KnowledgeDocument,
KnowledgeChunk, GovernmentApplication, Scheme, GovernmentService, AuditLog,
Notification, AIEventLog** (+ `approval_documents` association table).

Core relationships:
- `User` (role: ENTREPRENEUR / OFFICER / ADMIN) → owns `Project`s.
- `Project` → `Approval`, `Document`, `ComplianceItem`.
- `Approval` ↔ `Document` (many-to-many); `Approval` ↔ `GovernmentApplication`
  (one-to-one government file tracking).
- `ApprovalRule` → `GovernmentService` (templates that the rules engine
  instantiates per project).
- `KnowledgeDocument` → `KnowledgeChunk` (JSONB `embedding`).

Persistence conventions:
- Naive-UTC everywhere (`datetime.utcnow()`), ISO strings end with `Z`;
  JWT comparisons are timezone-aware.
- Seed data lives under `data/`: `approvals/approval_rules.json`,
  `schemes/schemes.json`, `regulations/*.md`, `services/explore_services.json`,
  plus `sample_documents/`, `mock_government_data/`, `rag_evaluation/`.

---

## 6. Feature Methodology

### 6.1 Authentication, authorization & RBAC
- **JWT (HS256)**, 24h expiry, claims `{sub, email, role}`; created in
  `core/security.py`.
- **bcrypt** for password hashing.
- Dependencies gating routes (`api/deps.py`): `require_auth`,
  `require_officer` (OFFICER|ADMIN), `require_admin`.
- **Self-registration is entrepreneur-only** (`RoleRegistrationForbidden`
  otherwise) — officers/admins are provisioned via seed scripts.

### 6.2 Approval determination — deterministic rules engine
`rules/approval_engine.py` evaluates **AND/OR/NOT/COMPARISON condition trees**
against project attributes to decide each applicable approval, materializes
`Approval` rows, and produces a **dependency graph** (nodes/edges) rendered by
React Flow in the UI. This mirrors how officers would reason about an
application in a transparent, auditable, non-LLM way.

### 6.3 Application tracking, transitions & SLA
- Owner-scoped application tracking with status transitions and SLA tracking
  (`services/sla_engine.py`) + a gradient-boosted **SLA predictor**
  (`services/sla_predictor.py`) that estimates remaining time per step.
- Officer review endpoints move applications through their lifecycle.

### 6.4 Documents: upload, validation, OCR extraction
- Upload validates type and size (`MAX_UPLOAD_SIZE_MB=50`, PDF/PNG/JPEG/WEBP/
  TXT/DOC/DOCX/XLS/XLSX/CSV) and sanitizes filenames.
- **OCR** via Tesseract (`ai/ocr.py`, PIL + pytesseract; graceful mock
  fallback). Extraction (`document_processor.py`) pulls structured fields,
  and `document_intelligence.py` performs cross-document validation.
- Processing runs through the background queue; jobs polled at `/api/jobs`.

### 6.5 Regulatory Copilot — RAG methodology
`rag/pipeline.py`:
1. **Ingest** — chapter documents are chunked (approx. 500/50 tokens) and
   embedded; embeddings persist as JSONB via `KnowledgeChunk`.
2. **Retrieve** — keyword + cosine-similarity ranking, restricted to
   currently-effective regulations.
3. **Generate** — prompt assembly + LLM answer with citations, routed through
   the provider fallback chain.
4. Copilot multi-step orchestration in `workflows/copilot_workflow.py` with
   tool execution exposed at `/api/tools`; AI telemetry logged (cost/latency/
   success) in `AIEventLog` via `/api/observability`.

### 6.6 LLM provider fallback chain
`ai/llm_provider.py` supports **Gemini 1.5-flash, Groq**
(server-side API keys), **Ollama** (self-hosted), and **MockLLMProvider**
(grounded, deterministic). `fallback_chain()` degrades in that order and
always ends in mock, so the copilot works offline. Embeddings default to a
deterministic `MockEmbeddingProvider`; `sentence-transformers`
(`all-MiniLM-L6-v2`) is the optional production-quality provider and the
target storage is **pgvector** (JSONB column acts as the interim store).

### 6.7 Incentive & scheme matching
- `incentive_matcher.py` scores schemes 0–100 (sector, state, investment,
  employment, ownership) and computes subsidy amounts including bonus
  percentages.
- `scheme_matcher.py` + `/api/schemes` surfaces ranked matches; the simulator
  shows "what if" subsidy outcomes.

### 6.8 Scenario simulator
`scenario_simulator.py` models the impact of **location change, sector
upgrade, capacity expansion, and timeline compression** on approvals,
incentives and compliance burden — giving entrepreneurs a planning sandbox.

### 6.9 Compliance tracker & regulatory change
- `compliance.py` / `compliance_tracker.py` — post-approval obligations,
  alerting, and compliance scoring (`/api/compliance`, `/compliance/{id}/score`).
- `regulatory_change.py` — detects and surfaces regulation updates that affect
  live projects.

### 6.10 Government gateway (mock, contract-first)
- `integrations/government_adapters.py` defines adapters for **6 agencies** —
  **Maitri (DISH factory), MPCB, MIDC, Boiler, Fire, Labour** — behind a
  `GovernmentAPIGateway`.
- `integrations/mock_gov_api.py` implements the wire contract: HTTP-style
  envelopes (`system`, `timestamp`, `request_id`), token auth, service
  discovery, apply/status lifecycle, GSTIN/PAN/Udyam verification, scheme
  eligibility and deterministic clearance pools (9 systems: `maitri mpcb midc
  boiler fire labour gst esic dea`).
- This lets the entire product flow (submit application → agency review →
  status → clearance) work end-to-end today and swap in real APIs later by
  replacing adapter implementations, not app logic.

### 6.11 Background workers
`workers/background.py` — in-process `asyncio.Queue` with four workers,
`JobStatus` lifecycle (PENDING → RUNNING → COMPLETED/FAILED), surfaced at
`/api/jobs`. Keeps document OCR, RAG ingest, and other heavy work off the
request path. Jobs are in-memory, so the backend must run as a **single
replica** (documented in DEPLOYMENT.md); the future path is Celery/RQ with a
Redis broker.

### 6.12 Audit & observability
- Every authenticated mutation is recorded to `AuditLog` (audit middleware).
- `AIEventLog` captures non-sensitive LLM telemetry; `/api/observability`
  exposes it for cost/latency/error monitoring.

---

## 7. Frontend Methodology

- **API contracts live in typed modules** (`frontend/services/`); axios
  interceptors centralize auth/timeout/error handling.
- **Server state with React Query** — dashboards and tables invalidate/refetch
  on mutation, minimizing manual state churn.
- **Page structure mirrors work streams**: onboarding wizard (new project),
  project workspace (approvals graph, documents, copilot, schemes, compliance),
  applications (entrepreneur) and officer workspace (reviews + analytics).
- **Quality gates**: `next build`, `next lint` (ESLint 8 + config-next),
  `tsc --noEmit`, and Jest 29 unit/contract tests for the API client, auth
  utilities, and frontend helpers.

---

## 8. Security Approach

| Control | Implementation |
|---|---|
| Secrets | Environment-driven; production fails fast on missing/weak `JWT_SECRET_KEY` (≥32 chars, no placeholders). `.env.example` files carry placeholders only; secrets never committed. |
| AuthN | bcrypt; short-lived JWT; `AUTO_GENERATED_SECRET` warns if a dev secret was auto-created. |
| AuthZ | Role-based dependency guards on every protected router. |
| CORS | Strict origin allow-list (`CORS_ORIGINS`), no wildcard. |
| Host validation | `TrustedHostMiddleware` against `ALLOWED_HOSTS`. |
| Abuse | Redis rate limiter (token bucket), fails open on Redis outage. |
| Injection | ORM/SQLAlchemy parameterization; validation via Pydantic. |
| Uploads | Type/size allow-list, sanitized filenames. |
| Audit | Full mutation audit trail. |
| TLS | Terminated at nginx (TLS 1.2/1.3, HTTP→HTTPS 301). |

### Database URL handling (provider-compatibility methodology)
`normalize_database_url()` in `core/database.py` makes provider-generated
PostgreSQL URLs (Neon, Render, Railway) work with asyncpg by **introspecting
the installed driver at runtime** rather than hardcoding assumptions:
1. `postgresql://` / `postgres://` → `postgresql+asyncpg://` (avoids the
   uninstalled synchronous psycopg2 dialect).
2. `sslmode=<value>` → `ssl=<value>` (asyncpg's `ssl` parameter accepts the
   same libpq vocabulary — TLS requirement preserved, never dropped).
3. `channel_binding` is removed — asyncpg has no channel-binding negotiation,
   so it cannot be honored; encryption is still enforced via `ssl`. Connection
   remains SCRAM-SHA-256, which Neon supports.
4. Any remaining query parameter not in the installed `asyncpg.connect()`
   signature is dropped with a logged warning, so providers can add more
   libpq-only options without breaking startup.
5. Valid asyncpg parameters and credentials/host/port/database/password are
   preserved exactly. The same normalization feeds the app engine **and**
   Alembic migrations.

---

## 9. Testing Methodology

- **Backend (pytest, ~213 tests across 24 files)** — API contracts, RBAC
  guards, compliance scoring, approval-graph construction, background jobs,
  demo seed idempotency, deployment hardening (CORS/JWT/URL normalization),
  document explanation/intelligence, explore service, gov sync, JWT policy,
  knowledge graph, notifications, officer analytics, RAG evaluation,
  regulatory change, services, SLA prediction, copilot tools/workflow, gateway
  + SLA, AI observability. Runs on SQLite via conftest bootstrap.
- **Migrations** — CI runs `alembic upgrade head` + `alembic check` against a
  real PostgreSQL service; containers do the same at boot.
- **Frontend (Jest, 16 cases + build/lint/tsc)** — API-client contract, auth
  utilities, and helper functions.
- **CI (`.github/workflows/ci.yml`)** runs `backend-tests`, `frontend-tests`,
  `lint`, `docker-build`, and a `deploy-staging` stub on every push.

---

## 10. Deployment Methodology

- **Docker Compose** — `postgres` (15-alpine, healthcheck), `redis`
  (7-alpine), `backend` (multi-stage Python 3.11, Tesseract, CMD
  `alembic upgrade head && uvicorn`), `frontend` (Node 20,
  `.next/standalone`), `nginx` (TLS reverse proxy). Named volumes for
  postgres/redis/uploads. `docker-compose.override.yml` (gitignored) maps
  nginx to 8080/8443 on local Windows.
- **CI/CD** — GitHub Actions on `main`; staging deploy job scaffolds platform
  deploys.
- **Target platforms** — production is Render/Neon-ready (see §8 URL
  handling); `deploy/` also ships a free Hugging Face Spaces + Neon + Upstash
  kit and a free single-VM kit, both with `setup-vm.sh`/`backup.sh`
  automation and full runbooks (`deploy/README.md`,
  `deploy/HUGGINGFACE_SPACES.md`, `DEPLOYMENT.md`,
  `DEPLOYMENT_ENVIRONMENT_REFERENCE.md`).

---

## 11. Assumptions & Known Limitations

- **Government integrations are MOCK** — deterministic, contract-shaped shims
  (not live MPIDC/MPCB/... APIs). Production rollout replaces adapter bodies.
- **AI is provider-agnostic with mock fallback** — set `GEMINI_API_KEY` /
  `GROQ_API_KEY` (server-side only) for real answers; embedding default is a
  deterministic mock (sentence-transformers/pgvector for scale).
- **Workers are in-process** → single-replica backend; horizontal scaling
  requires a queue broker (Celery/RQ).
- **Deployed ephemeral disks** (free HF Spaces) reset uploaded documents on
  rebuild; object storage is the planned fix.
- Demo seed accounts (idempotent, `scripts/seed_demo.py`): entrepreneur
  `demo@abctextiles.in`, officer `officer@udoyogsetu.demo`, admin
  `admin@udoyogsetu.demo` (documented in project guides; for local demos only).

---

## 12. Key File Map

| Concern | Path |
|---|---|
| API factory & middleware | `backend/app/main.py` |
| Settings & fail-fast validation | `backend/app/core/config.py` |
| Async engine & URL normalization | `backend/app/core/database.py` |
| JWT / bcrypt / RBAC deps | `backend/app/core/security.py`, `backend/app/api/deps.py` |
| Approval rules engine | `backend/app/rules/approval_engine.py` |
| RAG pipeline | `backend/app/rag/pipeline.py` |
| Document OCR & processing | `backend/app/ai/ocr.py`, `backend/app/services/document_processor.py` |
| Incentive/scenario/compliance | `backend/app/services/{incentive_matcher,scenario_simulator,compliance_tracker,sla_engine}.py` |
| Gov adapters & mock API | `backend/app/integrations/{government_adapters,mock_gov_api}.py` |
| Background workers | `backend/app/workers/{background,tasks}.py` |
| Migrations | `backend/alembic/` |
| Frontend API layer | `frontend/services/api.ts`, `frontend/lib/providers.tsx` |
| CI | `.github/workflows/ci.yml` |
| Deploy kits | `deploy/`, `DEPLOYMENT.md` |