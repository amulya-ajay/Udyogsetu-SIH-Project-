# UDYOGSETU — Explore Government Services Implementation Report

**Date**: September 5, 2026
**Status**: ✅ READY

## 1. Scope

Implementation of the integrated **Explore Government Services** module:

Discover → Check Applicability → Add to Checklist → Collect Documents → Apply → Track (SLA) → Officer Review → Government Sync.

Everything reuses the existing domain pipeline (Approvals, workflows, documents, notifications, audit, Gateway + GovSync, SLA engine). No new parallel subsystems were introduced.

## 2. What Was Built

### Backend
- **Model**: `GovernmentService` (+ `servicestatus` native PG enum, `is_active`, `gateway_system`, `is_demo`, SLA/risk/fee/eligibility fields) — `app/models/__init__.py`.
- **Migration**: `0004_government_services.py` (up `0004`, down `0003`). Creates the enum once (guarded) and the table with indexes; verified against a live Postgres container (a duplicate-`CREATE TYPE` defect found during live boot was fixed by `create_type=False` on the table column).
- **Service**: `app/services/explore_service.py`
  - Catalog query/filter (name/description/reference search, category/authority/application-mode/type filters).
  - `check_applicability` — deterministic reuse of the existing `ApprovalEngine.evaluate_rule_details` against the linked `ApprovalRule`; explicit `NOT_DETERMINED` (never fabricated) when no rule is linked.
  - Checklist/first-class application lifecycle: add-to-checklist (idempotent, keyed by `source = "explore:<slug>"`), `start_application`, attach/detach documents, `find_service_for_approval`.
  - Async-safe document reads (`await db.refresh(approval, ["documents"])`).
- **API**: `app/api/explore.py` — catalog list/categories/detail-by-slug-or-id, service document checklist (annotated with the user's existing project documents), applicability, checklist add/detail/start/attach/detach, plus admin create/patch with reserved-field guards.
- **API**: `app/api/officer_applications.py` — officer review queue (list with entrepreneur context + filters), detail (documents + government record + available transitions), workflow transitions (`to_status`), and government sync that auto-registers a tracking record on first sync when one was never created at submit time.
- **Routing**: registered `explore` + `officer_applications` routers in `app/api/routes.py`.
- **Fix (latent bug, pre-existing path)**: `POST /applications/{id}/submit` reads `application_id` from the gateway submit payload at the top level (the adapters return it top-level, not under `.data`), so `GovernmentApplication` tracking now actually creates records on submit.
- **Seed**: 16-service catalog (`data/services/explore_services.json`), idempotently loaded at startup, with services linked to existing `ApprovalRule`s by name.

### Frontend (Next.js/TS + React Query + shadcn/ui)
- **Data layer**: `types/index.ts`, `services/api.ts`, `hooks/useApi.ts` — explore, applications, and officer-review methods/hooks/types (SLA shape matches the backend `SlaEngine`).
- **Dashboard nav**: `app/dashboard/layout.tsx` — added *Explore Services* (`/dashboard/explore`) and *Applications* (`/dashboard/applications`); reserved top-level segments so the layout does not inject the project context into these pages.
- **New pages**:
  - `app/dashboard/explore/page.tsx` — search + category + application-mode filters, service cards.
  - `app/dashboard/explore/[serviceId]/page.tsx` — service detail (badges, fees, eligibility) + `features/ExploreApply.tsx` wizard (project pick → applicability decision → add to checklist → start → drag/drop upload + attach → submit; `REDIRECT` services shown as external-portal notices).
  - `app/dashboard/applications/page.tsx` — stats + status filter + list.
  - `app/dashboard/applications/[applicationId]/page.tsx` — SLA box, detail grid, entrepreneur transition actions.
  - `app/dashboard/officer/applications/page.tsx` — officer review queue.
  - `app/dashboard/officer/applications/[applicationId]/page.tsx` — detail with entrepreneur context, government-sync panel, officer transitions.

## 3. Architecture & Reuse
- A checklisted service **is** an `Approval` row (`source="explore:<slug>"`, `NOT_STARTED`) — the whole downstream lifecycle (submit, SLA, officer review, notifications, audit, gateway sync) is the existing one.
- Applicability uses the single rule engine (`ApprovalEngine`) over the linked `ApprovalRule`; no second rules implementation.
- Sync uses the existing `GatewayService` + `GovSyncService` + `GovernmentApplication`; no fake data — demo services stay labelled `is_demo`.

## 4. Security
- All explore/applications/officer endpoints sit behind auth; project ownership checks (`get_owned_project`) prevent BOLA on checklist/applicability/docs.
- Officer/Admin endpoints use `require_officer`/ADMIN dependency; privileged roles cannot self-register.
- Documents attach requires ownership of the document's project.

## 5. Tests
- **Backend**: full suite **181 passed** (`backend`, `..\venv\Scripts\python.exe -m pytest`). `tests/test_explore.py` adds **31 tests**: catalog/search/filter, categories, detail-by-slug-and-UUID, documents, applicability (applicable/not, `NOT_DETERMINED`, ownership-403), checklist lifecycle + idempotency, attach/detach + cross-user 403, full submit flow, officer list/detail/transition/invalid-400/auth-401, auto-track on officer sync, admin create/update/dup-409/guarded PATCH.
  - Note: this run took ~12:13 against the docker-hosted Postgres (baseline ~2:20); no test changes caused it — it is environment I/O.
- **Frontend**: `npx tsc --noEmit` clean, `npm run test` 16 passed, `npm run build` succeeds (all new routes pre-rendered).

## 6. Live Container E2E (spec §36)
Rebuilt backend + frontend images; `alembic upgrade head` + startup seeding verified in logs. Seeded `OFFICER`/`ADMIN` demo users (`officer.e2e@udyogsetu.demo`, `admin.e2e@udyogsetu.demo` / `E2ePass@123`) through a trusted path inside the container.
Scripted full lifecycle against the live API — **29/29 checks passed**:
catalog list/categories → applicability (`APPLICABLE`) → service detail/documents → add to checklist (idempotent) → start (`DRAFT`) → upload + attach document → submit (`SUBMITTED`) → applications list + SLA (`ON_TRACK`) → officer queue + detail → `UNDER_REVIEW` → `APPROVED` → government sync (auto-track created `GovernmentApplication`, `synced:1`, `system=maitri`, `current_status=QUERY_RAISED`) → entrepreneur notifications → officer audit logs → project approvals include the checklist item.

## 7. Known Notes / Deliberate Scoping
- **Copilot/regulatory intents** are not routed into Explore at query time; catalog applicability is deterministic per service. Documented as out-of-scope.
- A standalone notifications **page** was not built (the notifications API/badges already exist); noted as future polish, not a gap in the module.
- `POST /applications`/officer lists return `{applications: [...]}` wrappers and officer transitions take `to_status` — frontend and E2E both conform.
- Live demo users are created on the dev stack; production provisioning should go through the trusted admin path.

## 8. Verdict

**READY** — backend fully green (181 tests incl. 31 explore), frontend type-safe/build-clean with 16 passing tests, and the complete live-docker E2E passes end to end.