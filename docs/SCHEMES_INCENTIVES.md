# Schemes & Incentives

UDYOGSETU matches a factory project against Government of Maharashtra incentive
schemes and computes subsidy amounts.

## Matching

`IncentiveMatcher` (`backend/app/services/incentive_matcher.py`) scores every
active `Scheme` against a project profile and returns matches ordered by
`match_score` (0–100). Scoring factors include industry/sector overlap,
location, investment brackets, employee counts and eligibility type.

Each match includes a human-readable `match_reason` and the scheme's `benefits`.

## Subsidy calculation

`calculate_subsidy_amount(project_data, scheme)` derives the expected subsidy
from the scheme's `min_investment`, `max_investment`, `subsidy_percent`, and the
project's `investment_amount`. A capped investment base is used so the value
never exceeds the eligible bracket.

## Scheme catalog

`Scheme` rows (`app/models/__init__.py`) carry:

```
id, name, department, sector, location,
min_investment, max_investment, employee_requirement,
eligible_entity, benefits (list), incentives (JSONB),
subsidy_percent, application_period, source_url, is_active
```

Load catalogs via `app/services/data_loader.py::load_schemes(filepath)`.

## HTTP endpoints

```
GET  /schemes                                   list all schemes
POST /business-intelligence/schemes/match       match a project profile
GET  /business-intelligence/schemes/{id}        scheme details
POST /business-intelligence/schemes/{id}/calculate-subsidy
```

The copilot exposes matching through the `find_incentives` tool
(`POST /tools/execute`, see `docs/AI_FEATURES.md`).
