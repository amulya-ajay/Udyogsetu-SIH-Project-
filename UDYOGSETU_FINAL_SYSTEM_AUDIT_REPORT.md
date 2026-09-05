# UDYOGSETU — Final System Audit Report

**Date:** 2026-09-05
**Auditor:** AI Assistant (opencode)
**Project:** Smart India Hackathon 2026 — Problem Statement 26130
**Scope:** Full-stack audit of auth/RBAC, entrepreneur flows, explore/checklist, applications/SLA, documents, compliance, business intelligence, regulatory copilot/RAG, knowledge graph, notifications, government gateway, audit logging, AI observability, security hardening, migrations, build and live deployment.

---

## 1. Verdict

# 🟢 PASS — READY

All CRITICAL and HIGH findings from this audit have been **reproduced, fixed, regression-tested, and re-verified live**. Every automated gate passes and the live API audit is **131/131 PASS (0 FAIL)**. Remaining items are LOW-severity hardening notes, documented in §7.

> Evidence labels: `CODE INSPECTED`, `UNIT TESTED`, `INTEGRATION TESTED`, `LIVE API TESTED`, `PASS`, `FAIL`, `NOT TESTED`, `NOT APPLICABLE`. No fabricated results are reported.

---

## 2. Audit Summary (What Was Tested)

| Verification | Result | Evidence |
|---|---|---|
| Backend test suite (pytest) | **189 passed, 0 failed** | `INTEGRATION TESTED` (12m50s; baseline at audit start was 181) |
| Frontend unit tests (Jest) | **3 suites / 16 passed** | `UNIT TESTED` |
| TypeScript type-check | **exit 0** | `npx tsc --noEmit` |
| Frontend production build | **success** | `npm run build` |
| Live API audit (running docker stack) | **131/131 PASS** | `LIVE API TESTED` — auth, RBAC, projects, documents, explore/checklist, applications/SLA, officer, notifications, gateway, regulatory RAG/copilot, knowledge graph, schemes, simulation, compliance, background jobs, observability, admin, frontend pages |
| Migration chain | head `0004_government_services`; **fresh-DB `alembic upgrade head` succeeds** (tested on temp DB) | `LIVE API TESTED` |
| Rate limiter | enforced — fixed window, returns `429 + retry_after` | `LIVE API TESTED` |
| Audit middleware | present; audit logs queryable via admin | `CODE INSPECTED` + `LIVE API TESTED` |
| AI observability | **now instrumented** — live summary shows `total_calls>0` after RAG/copilot queries | `LIVE API TESTED` |

---

## 3. Bugs Found & Fixed (Reproduce → Fix → Regression → Retest)

### F1 — HIGH (FIXED): Compliance score endpoint 500 + silent zero-scoring
- **Symptom (live):** `GET /api/compliance/{project_id}/score` returned 500 with `'Approval' object has no attribute 'custom_metadata'`; approvals scored 0; `/alerts` always `[]`.
- **Root cause:** `backend/app/services/compliance_tracker.py` referenced a non-existent column and compared SQLAlchemy enum columns (`a.status == 'APPROVED'`) against plain strings — always `False`. The same enum-vs-string defect existed in `backend/app/services/compliance.py:33`, zeroing the dashboard `overall_score`.
- **Fix:**
  - Added `_status_value()` normaliser (`compliance_tracker.py`) and used it for approval status, item ON_TRACK/AT_RISK, and the alerts loop.
  - Document completeness now derives from the real `approval_documents` association (distinct approval ids with attached documents) instead of a phantom attribute.
  - Fixed the same comparison in `compliance.py` dashboard.
- **Regression:** `tests/test_compliance_score_regression.py` (score>0 with 50% approved, alerts include APPROVED-near-renewal and exclude NOT_STARTED, dashboard `overall_score=50` from 1 ON_TRACK + 1 OVERDUE) + `test_api.py::TestComplianceEndpoints` (`score` 200 after analyze; owner-only 403).
- **Retest:** pytest 189 passed; live score/alerts/dashboard 200.

### F2 — HIGH (FIXED): Location simulation 500
- **Symptom (live):** `GET /api/simulate/location/{project_id}` crashed — `business_intelligence.py` passed `project.location_state` (a string) where `scenario_simulator.simulate_location_change` expected a dict `{"state": ...}`.
- **Fix:** API now passes `{"state": project.location_state}` and `_get_location_approvals` defensively accepts a dict or plain state string (never 500s on odd shapes).
- **Regression:** `test_compliance_score_regression.py` (simulator accepts a string location) + `test_api.py::TestBusinessIntelligenceEndpoints` (route returns 200; cross-user 403).
- **Retest:** pytest 189 passed; live simulation 200.

### F3 — MEDIUM (FIXED): AI observability never instrumented (spec §34)
- **Symptom (live):** `GET /observability/ai/summary` always `total_calls: 0`; `timed_ai_event`/`AIObservability` existed with **zero call sites**.
- **Fix:** Instrumented all 4 LLM paths: RAG `generate_answer`, copilot `_general_flow`, `query_resolution` (gov query explain), and document `cross-validate/explain`. Failures are logged with `success=False` and re-raised; logging is wrapped so a telemetry error never breaks the request.
- **Retest (live):** `<observability/ai/summary>` = `total_calls: 12, successful_calls: 12, failed_calls: 0` after the last audit run, proving both the path works and the counter now increments.

### F4 — Script artifacts corrected (NOT product bugs)
- `/api/health` 404 → health is `/health` (root); harness fixed to hit root.
- Malformed-UUID probe returned 403 → probe lacked an auth header (HTTPBearer 403 default); fixed to send auth → now 422.
- Admin duplicate-service probe returned 422 → `authority`/`department` have `min_length=2`; harness fixed → true **409** duplicate-slug rejection confirmed.

---

## 4. Security & Hardening Review (`CODE INSPECTED`)

| Control | Status |
|---|---|
| JWT auth (HS256, `jwt.encode/decode`, bearer) | ✓ verified live (register/login/refresh/logout, wrong-pw 401, dup-register 409) |
| Role-based access (ENTREPRENEUR / OFFICER / ADMIN) | ✓ verified live: cross-role access 403/404, BOLA project isolation 403, officer/admin surfaces blocked for entrepreneurs, admin-only explore/audit/jobs |
| Password storage | ✓ hashed (never plaintext) |
| CORS | ✓ specific origins |
| TrustedHost middleware | ✓ present |
| Rate limiting | ✓ enforced live (Redis fixed-window, 60/min/IP, 429 + `retry_after`) |
| Audit logging middleware + sanitised 500s | ✓ present; admin `/audit/logs` 200 live |
| Swagger docs | ✓ disabled in prod (`DEBUG` off → 404 live) |
| Error handling | ✓ malformed UUID 422, missing-body 422, unknown route 404, path traversal 4xx |
| Migrations instead of `create_all` | ✓ Alembic, head 0004, fresh-DB upgrade verified |

---

## 5. Live Data/Endpoints Verified (131/131)

Key live confirms (fresh unique users each run): register/login flows, duplicate/ADMIN-role registration rejection, role matrix, project CRUD + analyze + approvals + approval-graph, document upload/validate/cross-validate/explain, letter of intent + details, explore catalog (16 services) + categories + applicability + checklist (add/start/attach/submit, idempotency), applications list/detail/SLA + prediction + transitions + submit, officer list/detail/transition/sync/analytics, notifications (create/list/unread/read + BOLA 404), gov sync + statuses, gateway health/verify/submit, regulatory RAG query + chat + copilot chat + history + recent changes, knowledge graph, schemes match/details/subsidy, scenario + location simulation, compliance dashboard/items/score/alerts/requirements, background jobs, observability summary, admin explore CRUD + duplicate 409, frontend pages (`/`, `/login`, `/register`, `/dashboard`, projects/applications/explore/schemes/compliance).

---

## 6. Build & Deployment

- Docker compose stack healthy: `postgres` (healthy), `redis` (healthy), `backend` (healthy, `alembic upgr…` entrypoint), `frontend`.
- Backend rebuilt and redeployed after fixes; `/health` → `healthy`.
- CI: GitHub Actions workflow present (test → lint → docker build). Note: runner logs flag Node 20 deprecation for `actions/checkout@v4` / `docker/*` step actions — CI hygiene, not product scope.

---

## 7. Remaining Findings (LOW / hardening notes)

| # | Severity | Finding | Recommendation |
|---|---|---|---|
| G1 | LOW | `HTTPBearer` returns **403** (not 401) when the `Authorization` header is missing (FastAPI default). | Add a custom `HTTPException(401)` handler for missing credentials in a future hardening pass. |
| G2 | LOW | When `JWT_SECRET_KEY` env is empty, a per-process secret is auto-generated → tokens invalidate on restart / multi-process. | Set a stable `JWT_SECRET_KEY` in prod (compose env). |
| G3 | LOW | JWT stored in `localStorage` behind a client-side route guard (no server middleware). | Consider `httpOnly` cookie / server-side session for higher-security deployments. |
| G4 | LOW | `ComplianceItem` rows are never written by any workflow — `/api/compliance/{id}/items` returns `[]` and dashboard/adherence metrics derive from approvals only. | Add item generation on project analyze / approval transitions, or seed via worker. |
| G5 | INFO | Government gateway uses **mock sandbox adapters** (MAITRI/MPCB/MIDC etc.) as designed for the demo; no live gov credentials in code. | Swap adapters for real integrations behind the same interface at deployment. |
| G6 | INFO | `total_tokens` in AI observability always 0 (token estimation not captured). | Add provider token counts when available. |

---

## 8. SIH Readiness Checklist

- [x] Entrepreneur portal: profile, projects, analyze, approvals + dependency graph, documents + AI validation, checklist → apply → submit, SLA + tracker
- [x] Officer portal: queue, transitions, sync, analytics
- [x] Admin: catalog CRUD, audit logs, jobs, observability
- [x] Explore: 16-services catalog, applicability, guided checklist
- [x] Regulatory copilot: intent detection → RAG / Document-AI / status / schemes / tools
- [x] Government gateway: sandbox adapters + verify endpoints
- [x] Incentives: schemes match + subsidy calculator + simulation
- [x] Notifications, knowledge graph, audit trail, rate limiting
- [x] Backend tests 189 ✓ · Frontend tests 16 ✓ · type-check ✓ · build ✓ · live audit 131/131 ✓ · migrations head 0004 ✓

---

## 9. Audit Trail (artifacts)

- Regression tests: `backend/tests/test_compliance_score_regression.py` (4) + `test_api.py` additions (4).
- Code fixes: `compliance_tracker.py`, `compliance.py`, `business_intelligence.py`, `scenario_simulator.py`, `rag/pipeline.py`, `copilot_workflow.py`, `query_resolution.py`, `documents.py`.
- Live harness: `C:\Users\ajay5\AppData\Local\Temp\opencode\audit_live.py` + `audit_results.json` + `audit_run*.log`.
- Migration validation: temp DB `udyogsetu_audit` (created → `alembic upgrade head` → **dropped**).
- Live test data (audit users `audit.a/b.*@*.demo`, projects, one `audit-svc-*` explore service) left in the demo DB as harmless demonstration artifacts.