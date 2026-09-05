from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_project_owner
from app.core.database import get_db_session
from app.schemas import ComplianceItemResponse
from app.services.compliance import ComplianceService

router = APIRouter(prefix="/compliance", tags=["compliance"])

@router.get("/{project_id}")
async def get_compliance_dashboard(
    project_id: UUID,
    project: object = Depends(require_project_owner),
    db: AsyncSession = Depends(get_db_session)
):
    """Get compliance dashboard with scores"""
    service = ComplianceService(db)
    dashboard = await service.get_compliance_dashboard(project_id)
    return dashboard

@router.get("/{project_id}/items", response_model=list[ComplianceItemResponse])
async def get_compliance_items(
    project_id: UUID,
    project: object = Depends(require_project_owner),
    db: AsyncSession = Depends(get_db_session)
):
    """Get compliance items for a project"""
    service = ComplianceService(db)
    await service.ensure_compliance_items(project_id)
    items = await service.get_compliance_items(project_id)
    return items