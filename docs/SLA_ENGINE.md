# SLA Engine

`SlaEngine` (`backend/app/services/sla_engine.py`) classifies an application's
service-level health against its statutory processing timeline.

## Classification

Given `status`, `submitted_at` and `sla_days`:

| SLA status | Rule |
|------------|------|
| `ON_TRACK`  | elapsed < 75% of SLA window |
| `AT_RISK`   | elapsed between 75% and 100% |
| `BREACHED`  | elapsed > 100% of SLA window |
| `COMPLETED` | final states (APPROVED) |
| `NOT_STARTED` | pre-submission states (NOT_STARTED / DRAFT) |

## Output shape

```json
{
  "status": "AT_RISK",
  "sla_days": 30,
  "days_elapsed": 23.4,
  "days_remaining": 6.6,
  "deadline": "2026-09-10T00:00:00+00:00",
  "breach_probability": 0.64,
  "reason": "Days elapsed (23.4) is 78% of SLA (30 days)"
}
```

- `breach_probability` = logistic `1 / (1 + exp(-8 * (ratio - 0.85)))`.
- `deadline` = `submitted_at + sla_days`.

## HTTP

`GET /applications/{application_id}/sla` returns the evaluation for an owned
application. SLA days are taken from the approval's
`estimated_processing_days`.

`_coerce_aware` normalises naive UTC datetimes so comparisons are always
timezone-safe regardless of how a value was persisted.
