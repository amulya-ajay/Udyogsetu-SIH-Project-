"""Notifications engine (in-app).

Creates notifications for user-facing events (approval status changes, SLA
alerts, renewals, compliance due dates) and exposes unread/read management.
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Approval, Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Create and query in-app notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str | UUID,
        title: str,
        message: str,
        category: str = "general",
        severity: str = "info",
        project_id: str | UUID | None = None,
        reference_id: str | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=UUID(str(user_id)),
            title=title,
            message=message,
            category=category,
            severity=severity,
            project_id=UUID(str(project_id)) if project_id else None,
            reference_id=reference_id,
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def list_for_user(
        self,
        user_id: str | UUID,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == UUID(str(user_id)))
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        rows = await self.db.execute(stmt)
        return list(rows.scalars().all())

    async def unread_count(self, user_id: str | UUID) -> int:
        rows = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == UUID(str(user_id)), Notification.is_read.is_(False))
        )
        return len(list(rows.scalars().all()))

    async def mark_read(self, user_id: str | UUID, notification_id: str | UUID) -> bool:
        result = await self.db.execute(
            update(Notification)
            .where(
                Notification.id == UUID(str(notification_id)),
                Notification.user_id == UUID(str(user_id)),
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount > 0

    async def mark_all_read(self, user_id: str | UUID) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == UUID(str(user_id)), Notification.is_read.is_(False))
            .values(is_read=True, read_at=datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount

    # ------------------------------------------------------------------
    # Domain triggers
    # ------------------------------------------------------------------
    async def notify_approval_status(self, approval: Approval):
        """Create a notification when an approval's status is relevant."""
        status = approval.status.value if hasattr(approval.status, "value") else str(approval.status)
        owner_id = None
        try:
            from app.models import Project
            result = await self.db.execute(select(Project).where(Project.id == approval.project_id))
            project = result.scalar_one_or_none()
            owner_id = project.user_id if project else None
        except Exception as exc:  # noqa: BLE001 - owner lookup must not raise out of the trigger
            logger.debug("Owner lookup failed for approval %s: %s", approval.id, exc)
        if not owner_id:
            return

        if status in ("SUBMITTED", "APPROVED", "REJECTED", "QUERY_RAISED"):
            cat = "approval"
            sev = "success" if status == "APPROVED" else ("error" if status == "REJECTED" else "warning")
            try:
                await self.create(
                    owner_id,
                    f"Approval {status.replace('_', ' ').title()}",
                    f"Your application for {approval.name} is now {status.replace('_', ' ').lower()}.",
                    category=cat,
                    severity=sev,
                    project_id=approval.project_id,
                    reference_id=str(approval.id),
                )
            except Exception:  # noqa: BLE001
                logger.warning("Failed to create notification for %s", approval.id)

    async def sla_alert_for_project(self, project_id: UUID) -> None:
        """Notify the owner about approvals approaching/over their SLA."""
        rows = await self.db.execute(
            select(Approval).where(Approval.project_id == project_id)
        )
        approvals = list(rows.scalars().all())
        for a in approvals:
            status = a.status.value if hasattr(a.status, "value") else str(a.status)
            if status not in ("SUBMITTED", "UNDER_REVIEW"):
                continue
            est = a.estimated_processing_days or 0
            submitted = a.submitted_at
            if not submitted:
                continue
            elapsed = (datetime.utcnow() - submitted).days
            if elapsed >= est > 0:
                await self.notify_approval_status(a)