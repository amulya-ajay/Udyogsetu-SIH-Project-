# Government Gateway & Status Synchronization

UDYOGSETU talks to external government systems through a thin gateway layer
(`backend/app/integrations/government_adapters.py`). Every system implements the
`GovernmentIntegrationAdapter` ABC (`authenticate`, `get_services`,
`get_application_status`, `submit_application`).

## Adapters & systems

| System key | Adapter | Department route (via `system_for_department`) |
|------------|---------|-------------------------------------------------|
| `maitri` | `MaitriAdapter` | factory, industrial safety |
| `mpcb` | `MpcbAdapter` | mpcb, pollution |
| `midc` | `MidcAdapter` | midc |
| `boiler` | `BoilerAdapter` | boiler, steam boilers |
| `fire` | `FireAdapter` | fire |
| `labour` | `LabourAdapter` | labour |
| `gst` | (verifier) | gst |
| `esic` | (verifier) | esic |

The adapters emit realistic **mock** status transitions (e.g. MPCB raises a
`QUERY_RAISED` with `"ETP capacity details required"`, Boiler goes
`UNDER_REVIEW`, Fire reaches `INSPECTION`) so the demo flow mirrors reality.

## GatewayService

`app/services/gateway_service.py` wraps the gateway with retries and health
snapshots:

- `submit(system, application_data)` → `{data: {application_id, status, ...}}`
- `get_status(system, application_id)` → `{data: {status, query, ...}}`
- `verify(kind, value)` → verify GSTIN / PAN / Udyam / Scheme / Clearance
- `system_health()` → per-system availability
- `_with_retry(coro, system, retries=2, timeout=10.0)` → resilient polling

## Synchronization service

`app/services/gov_sync_service.py` reconciles external status with internal
approval state:

- `track(approval, system, gov_application_id)` — upsert a
  `GovernmentApplication` link.
- `sync_one(record)` — poll status, map to an internal `ApprovalStatus`, apply
  via the workflow engine, raise a notification on change.
- `sync_all()`, `sync_for_project(project_id)` — batch reconciliation.

The status map (`_STATUS_MAP`) bridges government statuses such as
`SUBMITTED`, `UNDER_REVIEW`, `QUERY_RAISED`, `APPROVED`, `REJECTED`.

## HTTP endpoints

```
GET  /gateway/systems
GET  /gateway/health
GET  /gateway/{system}/services
GET  /gateway/{system}/status/{application_id}
POST /gateway/{system}/submit
GET  /gateway/verify/{kind}/{value}
POST /synchronization/sync
POST /synchronization/{approval_id}/track
GET  /synchronization/{approval_id}/query-resolution
```

## Regulatory status views

- `GET /regulatory/government/{system}/status/{application_id}`
- `POST /regulatory/government/submit`
- `GET /regulatory/government/all-statuses/{project_id}` — one consolidated
  view of every tracked system for a project.

## Development notes

The adapters are deterministic-ish mocks; swap `MpcbAdapter` etc. for real HTTP
adapters behind the same ABC to go live without changing callers.
