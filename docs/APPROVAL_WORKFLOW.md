# Application Workflow (State Machine)

The approval lifecycle is governed by `ApprovalWorkflowEngine`
(`backend/app/services/approval_workflow.py`). Every transition is declared in a
central `WORKFLOW` table, role-gated, and validated before application.

## States

`ApprovalStatus` enum (`app/models/__init__.py`):

```
NOT_STARTED → DRAFT → SUBMITTED → UNDER_REVIEW → INSPECTION → APPROVED
                                   │       └──────► QUERY_RAISED
                                   └──────► QUERY_RAISED
QUERY_RAISED → SUBMITTED / APPROVED / REJECTED
APPROVED → EXPIRED
NOT_STARTED → CANCELED (from DRAFT), CANCELED → NOT_STARTED
```

## Transitions

| From | To | Action | Actors |
|------|----|--------|--------|
| NOT_STARTED | DRAFT | Start application | ENTREPRENEUR, OFFICER, ADMIN |
| NOT_STARTED | SUBMITTED | Direct submit | ENTREPRENEUR, OFFICER, ADMIN |
| DRAFT | SUBMITTED | Submit application | ENTREPRENEUR, OFFICER, ADMIN |
| DRAFT | CANCELED | Cancel application | ENTREPRENEUR, OFFICER, ADMIN |
| CANCELED | NOT_STARTED | Re-open | ENTREPRENEUR, OFFICER, ADMIN |
| SUBMITTED | UNDER_REVIEW | Begin review | OFFICER, ADMIN |
| SUBMITTED | QUERY_RAISED | Raise query | OFFICER, ADMIN |
| UNDER_REVIEW | INSPECTION | Schedule inspection | OFFICER, ADMIN |
| UNDER_REVIEW | QUERY_RAISED | Raise query | OFFICER, ADMIN |
| QUERY_RAISED | SUBMITTED | Resubmit with answer | ENTREPRENEUR |
| QUERY_RAISED | APPROVED | Approve | OFFICER, ADMIN |
| UNDER_REVIEW | APPROVED | Approve | OFFICER, ADMIN |
| INSPECTION | APPROVED | Approve after inspection | OFFICER, ADMIN |
| SUBMITTED | APPROVED | Approve | OFFICER, ADMIN |
| INSPECTION | REJECTED | Reject | OFFICER, ADMIN |
| UNDER_REVIEW | REJECTED | Reject | OFFICER, ADMIN |
| QUERY_RAISED | REJECTED | Reject | OFFICER, ADMIN |
| SUBMITTED | REJECTED | Reject | OFFICER, ADMIN |
| APPROVED | EXPIRED | Mark expired | ADMIN |
| NOT_STARTED | APPROVED | Fast-track approval | ADMIN |

## Engine API

- `engine.apply(approval, to_status)` — validates a transition, applies side
  effects (`submitted_at`, `approved_at`, `is_active`) and returns a
  `WorkflowDecision`.
- `engine.list_possible_transitions(status)` — available next transitions.
- `TransitionError` — raised when a transition is not allowed; surfaced as HTTP
  400 by `app/api/applications.py`.

## HTTP endpoints

- `GET  /applications/{id}/transitions` — list possible transitions.
- `POST /applications/{id}/transition` — request a state change (body:
  `{"to_status": "SUBMITTED"}`).
- `POST /applications/{id}/submit` — convenience wrapper to `SUBMITTED` that
  also submits to the government gateway and tracks the application.

## Design

Transitions are declarative and role-gated, so adding a workflow step is a
one-line addition to `WORKFLOW`. The engine is reused by both the HTTP layer and
the government sync service (`gov_sync_service.py`) to reflect external status
changes without drilling through the API.
