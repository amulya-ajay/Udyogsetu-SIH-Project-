# UDYOGSETU — System Architecture

UDYOGSETU (SIH 2026 · Problem Statement 26130 · Government of Maharashtra) is a
full-stack industrial **approval determination + compliance** platform for
setting up factories in Maharashtra. It turns a basic web app into an
intelligent system that:

1. Determines the exact approvals an investor needs from their project profile.
2. Guides submission through a governed application workflow with SLA tracking.
3. Mines Indian regulations with a RAG pipeline that supports document versioning.
4. Autonomously extracts & cross-validates uploaded certificates via Doc-AI.
5. Tracks live status against mocked government systems and auto-syncs approvals.
6. Surfaces officer analytics and AI-assisted query resolution.

---

## 1. High-level topology

```
┌────────────┐   HTTP   ┌──────────────┐
│  React SPA │ ───────► │  FastAPI API │
│  (:3000)   │          │   (:8000)    │
└────────────┘          └──────┬───────┘
                               │ SQLAlchemy (async)
                    ┌──────────┴───────────┐
                    │   PostgreSQL (prod)  │
                    │   SQLite (tests)     │
                    └──────────────────────┘
                               │
                               │ mock adapters
                    ┌──────────┴──────────────────┐
                    │  Government Gateway        │
                    │  (MPCB/Maitri/Boiler/Fire/ │
                    │   MIDC/Labour/GST/ESIC)    │
                    └─────────────────────────────┘
```

Dockerised components: `backend`, `frontend`, `postgres`, `redis`, `nginx`.

## 2. Backend layers

```
backend/app/
├── api/            HTTP layer (FastAPI routers + auth deps)
├── services/       Application services (orchestration logic)
├── rules/          Approval determination engine
├── rag/            RAG pipeline (ingest, chunk, retrieve, evaluate)
├── ai/             LLM provider abstraction, tool-calling
├── workflows/      Copilot intent routing + workflow
├── integrations/   Government API adapters (mock + real-shaped)
├── core/           Config, security, database, background workers
├── models/         SQLAlchemy ORM models
└── schemas/        Pydantic request/response schemas
```

## 3. Key subsystems

| Subsystem | Location | Purpose |
|-----------|----------|---------|
| Approval Engine | `app/rules/approval_engine.py` | Rule-based determination of applicable approvals |
| Approval Workflow | `app/services/approval_workflow.py` | State machine governing approval lifecycle |
| SLA Engine | `app/services/sla_engine.py` | ON_TRACK / AT_RISK / BREACHED classification |
| RAG Pipeline | `app/rag/pipeline.py` | Ingest + chunk + retrieval with effective-dating |
| Doc-AI | `app/services/document_processor.py` + `document_intelligence.py` | Extract + cross-validate certificates |
| Gov Sync | `app/services/gov_sync_service.py` | Poll gateway, reconcile approval status |
| Copilot | `app/workflows/copilot_workflow.py` | Intent routing to engines (rules/RAG/schemes…) |
| Tool Calling | `app/ai/tools.py` + `app/services/copilot_tools.py` | Allow-listed LLM tools |
| Incentives | `app/services/incentive_matcher.py` | Scheme matching + subsidy calc |
| Officer Analytics | `app/services/officer_analytics.py` | Aggregated department/status views |

## 4. Cross-cutting concerns

- **Auth**: JWT bearer tokens issued by `app/core/security.py`; roles
  `ENTREPRENEUR`, `OFFICER`, `ADMIN`. Ownership enforced via `app/api/deps.py`.
- **Config**: `app/core/config.py`, overridable via environment.
- **Persistence**: async SQLAlchemy; PostgreSQL in Docker, SQLite in tests.
- **Rate limiting**: backed by Redis, disabled under tests.

## 5. Data flow — new factory onboarding

```
POST /projects ──► Project row
POST /projects/{id}/analyze ──► ApprovalEngine.determine_approvals ──► Approvals (NOT_STARTED)
POST /applications/{id}/submit ──► workflow: NOT_STARTED → SUBMITTED
                                    + gateway submit + gov sync track
GET  /applications/{id}/sla ──► SlaEngine.evaluate
GET  /synchronization/{id}/query-resolution ──► AI explanation of gov query
```

See `docs/APPROVAL_WORKFLOW.md`, `docs/SLA_ENGINE.md`, `docs/AI_FEATURES.md` and
`docs/GOVERNMENT_GATEWAY.md` for detail.
