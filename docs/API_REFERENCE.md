# UDYOGSETU API Reference

Base URL: `http://localhost:8000/api`

## Authentication

All endpoints (except `/auth/*`, `/health`) require a Bearer token:
```
Authorization: Bearer <jwt_token>
```

### Auth Endpoints
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login, returns access_token
- `POST /auth/refresh` - Refresh access token

---

## Projects

### Create Project
```
POST /projects
{
  "name": "My Project",
  "company_name": "ABC Pvt Ltd",
  "sector": "Textile",
  "location_state": "Maharashtra",
  ...
}
```

### List My Projects
```
GET /projects
```

### Get Project
```
GET /projects/{project_id}
```

### Analyze Project (generates approvals)
```
POST /projects/{project_id}/analyze
```

### Get Project Approvals
```
GET /projects/{project_id}/approvals
```

### Get Approval Dependency Graph
```
GET /projects/{project_id}/approval-graph
```
Returns nodes, edges, and critical path.

### Get Project Documents
```
GET /projects/{project_id}/documents
```

---

## Documents

### Upload Document
```
POST /documents/upload?project_id={project_id}
Content-Type: multipart/form-data
```

### Get Document
```
GET /documents/{document_id}
```

### Validate Document (OCR + extraction)
```
POST /documents/{document_id}/validate
```

### Reprocess Document (async background job)
```
POST /documents/{document_id}/reprocess
```

### Cross-Document Validation
```
GET /documents/project/{project_id}/cross-validate
```
Returns GREEN/YELLOW/RED findings.

### Cross-Document Validation + AI Explanation
```
GET /documents/project/{project_id}/cross-validate/explain
```
Returns findings plus human-readable narratives and per-field actions
(Doc-AI explanation).

### Job Status
```
GET /jobs/{job_id}
```

---

## Regulatory Copilot

### Query
```
POST /chat/query
{
  "question": "What licenses do I need?",
  "project_id": "uuid"
}
```
Returns: `{ intent, engine, answer, sources, confidence, ... }`

### History
```
GET /chat/history/{project_id}
```

### Regulatory (gov status / submit / aggregate)
```
GET  /regulatory/government/{system}/status/{application_id}
POST /regulatory/government/submit
GET  /regulatory/government/all-statuses/{project_id}
POST /regulatory/query
POST /regulatory/chat
```

---

## Compliance

### Dashboard
```
GET /compliance/{project_id}
```

---

## Schemes

### List All Schemes
```
GET /schemes
```

### Match Schemes
```
POST /business-intelligence/schemes/match
{
  "sector": "Textile",
  "location": "Maharashtra",
  "investment_amount": 10000000,
  "employee_count": 50
}
```

### Scheme Details / Subsidy Calculation
```
GET  /business-intelligence/schemes/{scheme_id}
POST /business-intelligence/schemes/{scheme_id}/calculate-subsidy
```

---

## Applications

### List Applications
```
GET /applications
```

### Get Application
```
GET /applications/{application_id}
```

### Get SLA Status
```
GET /applications/{application_id}/sla
```

### List Possible Transitions
```
GET /applications/{application_id}/transitions
```

### Apply a State Transition
```
POST /applications/{application_id}/transition
{
  "to_status": "SUBMITTED"
}
```
Validates against the approval workflow state machine (see
`docs/APPROVAL_WORKFLOW.md`).

### Submit Application
```
POST /applications/{application_id}/submit
```
Transitions to SUBMITTED, submits to the government gateway, and starts status
tracking.

---

## Business Intelligence

### Scenario Simulation
```
POST /business-intelligence/simulate
{
  "scenario": "capacity_expansion",
  "project_id": "uuid",
  "params": {}
}
```

### Compliance Score
```
GET /business-intelligence/compliance-score/{project_id}
```

---

## Government Gateway

### System Health
```
GET /gateway/health
```

### List Services (per system)
```
GET /gateway/{system}/services
```

### Application Status
```
GET /gateway/{system}/status/{application_id}
```

### Submit to System
```
POST /gateway/{system}/submit
```

### Business Verification
```
GET /gateway/verify/{kind}/{value}
```
kinds: gstin, pan, udyam, scheme, clearance

---

## Synchronization (Gov status sync + AI query resolution)

### Trigger Sync
```
POST /synchronization/sync
```

### Track an Approval Against a Gov System
```
POST /synchronization/{approval_id}/track
{
  "system": "mpcb",
  "government_application_id": "MPCB-123456"
}
```

### AI Query Resolution
```
GET /synchronization/{approval_id}/query-resolution
```
Explains a government query with relevant documents and regulatory context.

---

## Tools (controlled AI tool-calling)

### List Available Tools
```
GET /tools
```

### Execute a Tool
```
POST /tools/execute
{
  "tool": "get_approval_status",
  "arguments": { "project_id": "uuid" }
}
```
Tools: `get_project_profile`, `get_approval_status`, `search_documents`,
`check_compliance`, `find_incentives`.

## Notifications

### List Notifications
```
GET /notifications
```

### Unread Count
```
GET /notifications/unread-count
```

### Mark Read
```
POST /notifications/{notification_id}/read
```

### Mark All Read
```
POST /notifications/read-all
```

---

## Officer Analytics

### Full Dashboard
```
GET /officer/full
```

### Overview
```
GET /officer/overview
```

### By Department
```
GET /officer/by-department
```

### Status Distribution
```
GET /officer/status-distribution
```

---

## Audit

### Audit Logs
```
GET /audit/logs?limit=100&user_id=...
```

---

## Health

```
GET /health
```