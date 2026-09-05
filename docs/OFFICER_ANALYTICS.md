# Officer Analytics

Officer-facing dashboards aggregate approval data across all departments to help
regulators triage workload, risk and SLA health.

## Service

`app/services/officer_analytics.py` provides:

- `overview()` — headline counts (total, pending, approved, rejected, at-risk).
- `by_department()` — grouped metrics per department (volume, approval rate,
  avg processing days, risk).
- `status_distribution()` — rollup of approvals per `ApprovalStatus`.
- `full()` — a combined payload for a single-screen dashboard.

`elapsed_days` and `_as_utc` helpers normalise timezone-aware calculations.

## HTTP endpoints

```
GET /officer/full
GET /officer/overview
GET /officer/by-department
GET /officer/status-distribution
```

These require an authenticated user (officer/admin). Combine with
`docs/SLA_ENGINE.md` to surface at-risk applications for proactive follow-up.

## Business intelligence

Related project-insight endpoints:

```
GET  /business-intelligence/compliance/{project_id}/score
GET  /business-intelligence/compliance/{project_id}/alerts
GET  /business-intelligence/compliance/approval/{approval_id}
POST /business-intelligence/simulate/scenario
GET  /business-intelligence/simulate/location/{project_id}
```

Scenario simulation (`app/services/scenario_simulator.py`) models the impact of
location changes, sector upgrades, capacity expansion and timeline compression on
the required approval set.
