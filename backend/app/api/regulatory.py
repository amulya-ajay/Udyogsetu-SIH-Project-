from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_project_owner
from app.core.database import get_db_session
from app.core.security import get_current_user
from app.integrations.government_adapters import GovernmentAPIGateway
from app.models import Approval
from app.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/regulatory", tags=["regulatory"])


class RegulatoryQuery(BaseModel):
    query: str
    project_id: str


class GovernmentSubmission(BaseModel):
    system: str
    data: dict = {}


def _parse_project_id(project_id: str) -> UUID | None:
    try:
        return UUID(project_id)
    except (ValueError, AttributeError, TypeError):
        return None


@router.post("/query")
async def query_regulatory_knowledge(
    req: RegulatoryQuery,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    project_id = _parse_project_id(req.project_id)
    if project_id:
        await require_project_owner(project_id, user, db)

    pipeline = RAGPipeline(db)
    result = await pipeline.generate_answer(req.query)
    return {
        "query": req.query,
        "answer": result["answer"],
        "confidence": result["confidence"],
        "sources": result["sources"],
        "evidence": result["evidence"],
    }


@router.post("/chat")
async def chat_with_copilot(
    req: RegulatoryQuery,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    project_id = _parse_project_id(req.project_id)
    if project_id:
        await require_project_owner(project_id, user, db)

    pipeline = RAGPipeline(db)
    result = await pipeline.generate_answer(req.query)
    return {
        "response": result["answer"],
        "confidence": result["confidence"],
        "sources": result["sources"],
    }


@router.get("/government/{system}/status/{application_id}")
async def get_government_status(
    system: str,
    application_id: str,
    user: dict = Depends(get_current_user),
):
    gateway = GovernmentAPIGateway()
    try:
        result = await gateway.get_application_status(system, application_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/government/submit")
async def submit_to_government(
    req: GovernmentSubmission,
    user: dict = Depends(get_current_user),
):
    gateway = GovernmentAPIGateway()
    try:
        result = await gateway.submit_application(req.system, req.data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/government/all-statuses/{project_id}")
async def get_all_government_statuses(
    project_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    project_uuid = _parse_project_id(project_id)
    if not project_uuid:
        raise HTTPException(status_code=404, detail="Project not found")

    await require_project_owner(project_uuid, user, db)

    result = await db.execute(
        select(Approval).where(Approval.project_id == project_uuid)
    )
    approvals = result.scalars().all()

    gateway = GovernmentAPIGateway()

    app_ids = {}
    for approval in approvals:
        system = approval.department.lower().replace(" ", "_")
        if system in gateway.adapters:
            app_ids[system] = approval.application_id or f"{system}-pending"

    statuses = await gateway.get_all_statuses(app_ids)

    return {
        "project_id": project_id,
        "statuses": statuses,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/change/recent")
async def recent_regulatory_changes(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    limit: int = 20,
):
    """List recently published regulation versions (spec §30)."""
    from app.services.regulatory_change import RegulatoryChangeService
    return {"changes": await RegulatoryChangeService(db).recent_changes(limit=min(limit, 100))}


@router.get("/change/{document_id}")
async def regulatory_change_diff(
    document_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Describe changes between a regulation and the version it supersedes."""
    from app.services.regulatory_change import RegulatoryChangeService
    doc_uuid = UUID(document_id) if _valid_uuid(document_id) else None
    if not doc_uuid:
        raise HTTPException(status_code=400, detail="Invalid document id")
    return await RegulatoryChangeService(db).diff(doc_uuid)


def _valid_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False