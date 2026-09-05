"""Officer analytics API."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_officer
from app.core.database import get_db_session
from app.services.officer_analytics import OfficerAnalyticsService

router = APIRouter(prefix="/officer", tags=["officer-analytics"])


@router.get("/overview")
async def officer_overview(
    user: dict = Depends(require_officer),
    db: AsyncSession = Depends(get_db_session),
):
    svc = OfficerAnalyticsService(db)
    return await svc.overview()


@router.get("/by-department")
async def officer_by_department(
    user: dict = Depends(require_officer),
    db: AsyncSession = Depends(get_db_session),
):
    svc = OfficerAnalyticsService(db)
    return {"departments": await svc.by_department()}


@router.get("/status-distribution")
async def officer_status_distribution(
    user: dict = Depends(require_officer),
    db: AsyncSession = Depends(get_db_session),
):
    svc = OfficerAnalyticsService(db)
    return {"distribution": await svc.status_distribution()}


@router.get("/full")
async def officer_full_dashboard(
    user: dict = Depends(require_officer),
    db: AsyncSession = Depends(get_db_session),
):
    svc = OfficerAnalyticsService(db)
    return {
        "overview": await svc.overview(),
        "departments": await svc.by_department(),
        "distribution": await svc.status_distribution(),
    }