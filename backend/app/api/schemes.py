from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.api.deps import require_auth
from app.models import Scheme

router = APIRouter(prefix="/schemes", tags=["schemes"])

@router.get("")
async def list_schemes(
    user: dict = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
):
    """List all available schemes"""
    result = await db.execute(
        select(Scheme)
        .where(Scheme.is_active == True)  # noqa: E712
        .order_by(Scheme.name)
    )
    schemes = result.scalars().all()
    return {
        "schemes": [
            {
                "id": str(scheme.id),
                "name": scheme.name,
                "department": scheme.department,
                "sector": scheme.sector,
                "location": scheme.location,
                "min_investment": scheme.min_investment,
                "max_investment": scheme.max_investment,
                "eligible_entity": scheme.eligible_entity,
                "employee_requirement": scheme.employee_requirement,
                "benefits": scheme.benefits or [],
                "application_period": scheme.application_period,
                "required_documents": scheme.required_documents or [],
                "source_url": scheme.source_url,
            }
            for scheme in schemes
        ]
    }