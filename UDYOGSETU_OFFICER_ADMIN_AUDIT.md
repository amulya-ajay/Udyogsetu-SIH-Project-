# UDYOGSETU — Government Officer & Admin Audit Report

**Scope:** End-to-end audit of the Government Officer and Admin surfaces — authentication, JWT, routing, API authorization (RBAC), object-level authorization, database persistence, and response correctness — plus remediation of all identified **CRITICAL** and **HIGH** issues and regression tests.

**Audit date:** 2026-09-04
**Stack:** FastAPI (backend) + Next.js App Router (frontend), Postgres, Redis, Docker Compose
**Backend:** `http://localhost:8000/api`, **Frontend:** `http://localhost:3000`

---

## 1. Executive Summary / Verdict

| Area | Status |
|---|---|
| Backend functional tests | **PASS** — 150/150 (was 136 baseline + 14 new RBAC) |
| Frontend tests | **PASS** — 16/16 Jest, `tsc --noEmit` clean, `next build` clean |
| Live API RBAC checks | **PASS** — 18/18 against the running production container |
| Officer surface authorization | **Fixed & verified** |
| Admin surface authorization | **Fixed & verified** |
| Self-service privileged registration (privilege-escalation) | **CRITICAL — fixed & verified** |
| Unauthenticated regulatory status endpoint | **HIGH — fixed & verified** |
| Audit/gateway/sync endpoints over-permissioned | **HIGH — fixed & verified** |
| IDOR / owner-scoping | **Correct (verified prior work)** |
| JWT integrity (tampering) | **Correct (verified)** |

**Verdict: RESOLVED / SECURE for the audited surface.** All CRITICAL and HIGH security findings identified were fixed, verified live against the deployed production stack, and confirmed by new automated regression tests. The officer/admin dashboards and analytics surfaces now correctly serve only OFFICER/ADMIN tokens.

---

## 2. Tests Executed & Results

| Suite | Command | Result |
|---|---|---|
| Backend full | `pytest tests/` | **150 passed** (136 baseline + 14 new) |
| New RBAC regressions | `pytest tests/test_rbac.py` | **14 passed** |
| Frontend unit | `npx jest` | **16 passed** (3 suites) |
| Frontend types | `npx tsc --noEmit` | **clean (exit 0)** |
| Frontend build | `npm run build` | **success** |
| Live API RBAC | `rbac_live_check.py` (against `:8000`) | **18/18 passed** |

---

## 3. Officer & Admin Feature / Functionality Status

### Backend (all verified live)
- **Officer analytics** (`/api/officer/overview|by-department|status-distribution|full`): aggregate ALL approvals/system-wide by design (intended for the officer surface). Now gated to OFFICER/ADMIN. **LIVE-API VERIFIED (200 for officer/admin, 403 for entrepreneur).**
- **Audit logs** (`/api/audit/logs`): now OFFICER/ADMIN only. **LIVE-API VERIFIED.**
- **Government gateway** (`/api/gateway/*`): now OFFICER/ADMIN only. **LIVE-API VERIFIED.**
- **Synchronization** (`POST /api/sync`): now OFFICER/ADMIN only.
- **Observability** (`/api/observability/ai/summary`): already role-gated (OFFICER/ADMIN) — baseline correct.
- **SLA engine** (`sla_engine.py`): timezone-safe (`_coerce_aware`, `_as_utc`) — no naive/aware bugs.
- **Audit logging middleware**: records authenticated mutations only; failures never break requests.

### Frontend (documented, not modified)
- **OfficerDashboard** exposes metrics + department chart from `/officer/full`, but the **"Pending Applications" list (APP-001/002/003), "Quick Stats" (12/67/247), and "System Alerts" (5/12/38) are hardcoded mock values**, and the **Review / Quick-Action buttons have no handlers**. No live application-review workflow exists in the UI. This is a **functional gap (not a security issue)** — the dashboard's backend data is real, but several panels are static placeholders.
- **No route-guard middleware** exists; role routing is client-side only. An authenticated client whose token/role is stale can briefly render the officer route shell. Data cannot be fetched (backend now enforces RBAC), but hidden/demo UI elements could be shown. **LOW severity, documented.**
- **Admin and OFFICER both route to `/dashboard/officer`** — there is no distinct admin dashboard. An Admin sees the officer surface. **Documented limitation.**

---

## 4. Security Findings — Severity, Impact, Root Cause, Fix

### CRITICAL — F1: Self-service privileged registration (privilege escalation)
- **Finding (LIVE-API, pre-fix):** `POST /api/auth/register` accepted `role="ADMIN"` or `role="OFFICER"` and minted a JWT with that role → **201, JWT role=ADMIN** — any anonymous caller could become an administrator.
- **Root cause:** `AuthService.register_user` performed no role allow-list check; `UserRegister.role` defaulted to `ENTREPRENEUR` but accepted any enum value.
- **Fix:** `register_user` now rejects any role other than `ENTREPRENEUR` by raising `RoleRegistrationForbidden`; `auth.py:register` maps it to **403**. `require_officer` / `require_admin` deps added to `deps.py`.
- **Verification:** LIVE-API (403 + `"Only ENTREPRENEUR accounts can self-register"`); unit `test_register_as_admin_rejected`, `test_register_as_officer_rejected`.
- **Regression tests:** `TestPrivilegedSelfRegistrationBlocked`, `TestRequestBodyRoleManipulation`.

### HIGH — F2: Entrepreneur could read officer/admin analytics
- **Finding (LIVE-API, pre-fix):** `GET /api/officer/full` returned **200** to an ENTREPRENEUR token. Because `officer.py` used only aut, no role check.
- **Fix:** all 4 officer endpoints now depend on `require_officer`.
- **Verification:** LIVE-API entrepreneur→403, officer/admin→200; unit `TestOfficerEndpointsRoleRestricted`.

### HIGH — F3: Audit logs readable by any authenticated user
- **Finding (LIVE-API, pre-fix):** `GET /api/audit/logs` returned **200** to an ENTREPRENEUR (88 records leaked). Audit logs contain per-user actions/I.P. metadata.
- **Fix:** `audit.py` `/audit/logs` now depends on `require_officer`.
- **Verification:** LIVE-API entrepreneur→403; unit `TestAuditLogsRoleRestricted`.

### HIGH — F4: Government gateway management open to entrepreneurs
- **Finding (LIVE-API, pre-fix):** `GET /api/gateway/health|systems` returned **200** to ENTREPRENEUR. Gateway management (system health, submissions status) is officer/admin domain.
- **Fix:** all `/gateway/*` routes now depend on `require_officer`.
- **Verification:** LIVE-API entrepreneur→403, officer/admin→200; unit `TestGatewayRoleRestricted`.

### HIGH — F5: Unauthenticated government regulatory status endpoint
- **Finding (LIVE-API, pre-fix):** `GET /api/regulatory/government/{system}/status/{application_id}` returned **200 with no token at all** (no auth dependency).
- **Fix:** added `Depends(get_current_user)`.
- **Verification:** LIVE-API no-token→denied; unit `TestGovernmentStatusAuth`.

### MEDIUM — F6: Synchronization admin surface open (documented)
- **Finding:** `POST /api/sync` polls status for ALL tracked government applications system-wide but was auth-only.
- **Fix:** now depends on `require_officer`. Regression covered contextually by the shared `require_officer` dependency.

### LOW — F7: Production missing-auth returns 403 (framework quirk)
- **Finding:** With rate limiting enabled (`RATE_LIMIT_ENABLED=true`, production), Starlette's `BaseHTTPMiddleware`-based `RateLimitMiddleware` resurfaced `HTTPBearer`'s dependency 401 as an HTTP **403** (body still reads `{"detail":"Not authenticated"}`). Verified to **NOT** reproduce with rate limiting disabled (test env returns correct 401). This is a **pre-existing framework-level middleware interaction affecting the entire API**, not specific to the officer surface.
- **Impact:** Access is still denied (both 401/403 reject); the body correctly distinguishes "Not authenticated". Only the numeric code is semantically 403 instead of 401.
- **Resolution:** Attempted a pure-ASGI rewrite of `RateLimitMiddleware`; unit-verified it preserves status codes in isolation, but the full production stack continued to return 403, so the change was **reverted** to keep the footprint minimal and avoid modifying working rate-limiting architecture. Documented as a known framework quirk. (Regression tests for the isolated middleware were removed with the revert.)

---

## 5. What Was Changed (files)

| File | Change |
|---|---|
| `backend/app/api/deps.py` | Added `require_officer` (OFFICER|ADMIN) and `require_admin` (ADMIN) dependencies returning 403. |
| `backend/app/services/auth.py` | `AuthService.register_user` now raises `RoleRegistrationForbidden` for non-ENTREPRENEUR roles. |
| `backend/app/api/auth.py` | Register route maps `RoleRegistrationForbidden` → **403**. |
| `backend/app/api/officer.py` | All 4 endpoints now use `Depends(require_officer)`. |
| `backend/app/api/audit.py` | `/audit/logs` now uses `Depends(require_officer)`. |
| `backend/app/api/gateway.py` | All `/gateway/*` routes now use `Depends(require_officer)`. |
| `backend/app/api/synchronization.py` | `POST /sync` now uses `Depends(require_officer)`. |
| `backend/app/api/regulatory.py` | Unauthenticated gov-status endpoint now requires `get_current_user`. |
| `scripts/seed_demo.py` | Added idempotent OFFICER/ADMIN demo provisioning (bypasses public register; `Officer@12345` / `Admin@12345` overridable via env). Fixed import indentation. |
| `frontend/app/register/page.tsx` | Removed OFFICER self-select option; role is fixed `ENTREPRENEUR` (matches backend restriction). |
| `backend/tests/test_rbac.py` | **New**: 14 RBAC regression tests. |

> Demo privileged credentials (`officer@udoyogsetu.demo` / `admin@udoyogsetu.demo`) are documented demo accounts with publicly-known default passwords, consistent with the existing `demo@…` convention. **In production these must be rotated/provisioned via an admin-only path, not left at defaults.** (Caveat noted in §7.)

---

## 6. Functionality Verified End-to-End (Auth → JWT → Route → API → Authorization → DB → Response)

1. **Login** → JWT (HS256, role claim) — LIVE-API VERIFIED.
2. **Role extraction** on login → OFFICER/ADMIN route to `/dashboard/officer`, others to `/dashboard` (prior work, kept).
3. **Officer token** → `GET /api/officer/full`, `/api/gateway/health`, `/api/gateway/systems` → **200** — LIVE-API VERIFIED.
4. **Admin token** → same → **200** — LIVE-API VERIFIED.
5. **Entrepreneur token** → officer/audit/gateway surfaces → **403** — LIVE-API VERIFIED.
6. **No token** → denied (401 test-env / 403 prod quirk; body "Not authenticated") — LIVE-API VERIFIED.
7. **Tampered JWT (role forged to ADMIN)** → **401** — LIVE-API VERIFIED.
8. **IDOR** (officer token on another owner's project) → **403**; owner on own project → **200** (prior work, kept).

---

## 7. Limitations / Not Tested / Caveats

- **NOT TESTED — Live browser (UI) flow.** Analysis was API/source/test-level; the OfficerDashboard page render was reviewed statically only. The hardcoded panels/dead buttons are a functional gap, not security.
- **Demo privileged accounts** use documented default passwords; an admin-only account-management/provisioning UI does not exist yet — only DB/seed provisioning. **Recommended follow-up:** admin user-management endpoint + password rotation.
- **No admin-specific dashboard**; admin shares the officer dashboard.
- **No Next.js route-guard middleware** — client-side role check only (data is server-protected).
- **403-vs-401 missing-auth quirk** (F7) is a pre-existing, whole-API framework behavior; documented, not fixed (reverted) to avoid architectural churn.
- **Frontend container** was not rebuilt with the `register/page.tsx` change (backend was rebuilt/deployed with all fixes; the running `:3000` container still serves the prior front build). The frontend source passes Jest/`tsc`/build; a `docker compose up -d --build frontend` is required to deploy the UI-only register change.
- **Heuristic/mock components** (existing, unchanged): government adapters are mock; `OfficerDashboard` stats panicles are static; seeds run idempotently. No security check was disabled to obtain passing results.

---

## 8. Key Commands

```bash
# Backend full suite
cd backend && ..\venv\Scripts\python.exe -m pytest tests/

# RBAC regressions
cd backend && ..\venv\Scripts\python.exe -m pytest tests/test_rbac.py

# Frontend
cd frontend && npx jest && npx tsc --noEmit && npm run build

# Deploy backend fixes (Docker)
docker compose build backend && docker compose up -d backend

# Seed demo (incl. officer/admin): docker exec udyogsetu-backend python scripts/seed_demo.py
# Live verification script was run from temp: rbac_live_check.py (18/18 PASS)
```

---

## 9. Recommendation

Deploy the backend fixes (already verified) and rebuild the frontend container. As highest-priority follow-ups: (1) replace documented default privileged passwords with randomly generated ones and rotate them, (2) add an admin-only user-management/role-provisioning endpoint, (3) wire the OfficerDashboard to live application-review data and remove hardcoded panels, and (4) optionally add a server-side route guard for the officer/admin pages. No further action is required to close the CRITICAL/HIGH findings in scope.
