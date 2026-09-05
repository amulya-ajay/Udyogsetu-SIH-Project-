# Demo Data & Walkthrough

UDYOGSETU ships a one-click demo seeder so the SIH judging flow works end to end
without manual data entry.

## Seeding demo data

```bash
python scripts/seed_demo.py
```

The seeder (`scripts/seed_demo.py`) creates, **idempotently**:

1. A demo entrepreneur user —
   - email: `demo@abctextiles.in`
   - password: `Demo@12345`
   - (overridable via `DEMO_EMAIL` / `DEMO_PASSWORD` env vars)
2. The **ABC Textiles Pvt Ltd - New Dyes Unit** project (Pune, Maharashtra;
   high pollution, boiler, 50 employees, ₹2 Cr investment).
3. Applicable approvals via `ApprovalEngine.determine_approvals` (only the first
   time — approvals are never duplicated on re-run).
4. Submittal of the first few approvals, tracked against the matching mock
   government systems.
5. Two demo documents with extracted fields (`mpcb_consent_to_establish.pdf`,
   `factory_license_DISH.pdf`) for the Doc-AI flow.

## Suggested demo walkthrough

1. **Login** as `demo@abctextiles.in`.
2. **Project dashboard** — open the ABC Textiles project; review its profile.
3. **Approvals** — see the determined approvals and the dependency graph
   (`GET /projects/{id}/approval-graph`).
4. **Applications** — inspect `GET /applications/{id}/transitions`, then
   `POST /applications/{id}/sla` to see the SLA health.
5. **Copilot** — `POST /chat/query` with e.g.
   `"What is the status of my MPCB consent?"` (status flow) or
   `"I need to set up a dyeing unit, what do I require?"` (regulation flow).
6. **Documents** — `GET /documents/project/{id}/cross-validate/explain` to see
   extracted-field narratives.
7. **Query resolution** — `GET /synchronization/{id}/query-resolution` to let AI
   explain a government query (e.g. the MPCB ETP capacity query).
8. **Gateway health** — `GET /gateway/health` to see per-system availability.

## Resetting

Re-running the seeder is safe: the user, project, approvals and documents are
all deduplicated. Drop the database to start completely fresh.
