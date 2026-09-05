"""Officer/administrator analytics.

Aggregates data across all projects and approvals to surface department
bottlenecks, SLA performance, and application throughput for the officer
dashboard.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Approval


class OfficerAnalyticsService:
    """Compute cross-system officer-level metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _all_approvals(self) -> list:
        rows = await self.db.execute(select(Approval))
        return list(rows.scalars().all())

    async def overview(self) -> dict:
        approvals = await self._all_approvals()
        total = len(approvals)
        pending = [a for a in approvals if a.status.value not in ("APPROVED", "REJECTED")]
        breached = []
        for a in pending:
            sla = a.estimated_processing_days or 60
            base = a.submitted_at or a.created_at
            if not base:
                continue
            elapsed = max(0, (datetime.now(timezone.utc) - _as_utc(base)).days)
            if elapsed > sla:
                breached.append(a)

        processing = [elapsed_days(a) for a in approvals if a.status.value == "APPROVED"]
        avg = round(sum(processing) / len(processing), 1) if processing else 0

        return {
            "total_applications": total,
            "pending_review": len(pending),
            "sla_breaches": len(breached),
            "avg_processing_days": avg,
            "approved": sum(1 for a in approvals if a.status.value == "APPROVED"),
        }

    async def by_department(self) -> list[dict]:
        approvals = await self._all_approvals()
        by_dept: dict[str, dict] = {}
        for a in approvals:
            d = a.department or "Unknown"
            entry = by_dept.setdefault(d, {"department": d, "total": 0, "approved": 0, "pending": 0, "sla_breaches": 0, "avg_days": []})
            entry["total"] += 1
            status = a.status.value
            if status == "APPROVED":
                entry["approved"] += 1
                entry["avg_days"].append(elapsed_days(a))
            elif status in ("APPROVED", "REJECTED"):
                pass
            else:
                entry["pending"] += 1
            sla = a.estimated_processing_days or 60
            base = a.submitted_at or a.created_at
            if a.status.value not in ("APPROVED", "REJECTED") and base:
                if (datetime.now(timezone.utc) - _as_utc(base)).days > sla:
                    entry["sla_breaches"] += 1

        result = []
        for entry in by_dept.values():
            entry["avg_days"] = round(sum(entry["avg_days"]) / len(entry["avg_days"]), 1) if entry["avg_days"] else 0
            entry["backlog"] = entry["pending"]
            result.append(entry)
        result.sort(key=lambda e: (e["sla_breaches"], e["pending"]), reverse=True)
        return result

    async def status_distribution(self) -> list[dict]:
        approvals = await self._all_approvals()
        counts: dict[str, int] = {}
        for a in approvals:
            s = a.status.value
            counts[s] = counts.get(s, 0) + 1
        return [{"status": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]


def elapsed_days(approval) -> int:
    base = approval.submitted_at or approval.created_at
    if not base:
        return 0
    return max(0, (datetime.now(timezone.utc) - _as_utc(base)).days)


def _as_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)