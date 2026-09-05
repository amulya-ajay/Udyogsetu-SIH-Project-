"""Notifications API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import get_current_user
from app.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    unread_only: bool = False,
    limit: int = 50,
):
    service = NotificationService(db)
    notifications = await service.list_for_user(user["sub"], unread_only=unread_only, limit=limit)
    return {"notifications": [n.to_dict() for n in notifications], "unread": await service.unread_count(user["sub"])}


@router.get("/unread-count")
async def unread_count(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = NotificationService(db)
    return {"unread": await service.unread_count(user["sub"])}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = NotificationService(db)
    ok = await service.mark_read(user["sub"], notification_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "read"}


@router.post("/read-all")
async def mark_all_read(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    service = NotificationService(db)
    count = await service.mark_all_read(user["sub"])
    return {"marked": count}