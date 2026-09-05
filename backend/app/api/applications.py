from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.database import get_db_session
from app.core.security import get_current_user
from app.models import Approval, ApprovalStatus, Project
from app.services.project import ProjectService

router = APIRouter(prefix="/applications", tags=["applications"])


async def _resolve_approval(db: AsyncSession, user: dict, application_id: str) -> Approval:
    """Find an approval by application_id or by UUID, verifying ownership."""
    result = await db.execute(
        select(Approval).where(Approval.application_id == application_id)
    )
    approval = result.scalar_one_or_none()

    if not approval:
        try:
            result = await db.execute(
                select(Approval).where(Approval.id == UUID(application_id))
            )
            approval = result.scalar_one_or_none()
        except (ValueError, AttributeError, TypeError):
            pass

    if not approval:
        raise HTTPException(status_code=404, detail="Application not found")

    service = ProjectService(db)
    project = await service.get_project(approval.project_id)
    if not project or str(project.user_id) != str(user["sub"]):
        raise HTTPException(status_code=403, detail="Not authorized to access this application")

    return approval


def _application_payload(approval: Approval, project: Project | None) -> dict:
    return {
        "application_id": approval.application_id or str(approval.id),
        "approval_name": approval.name,
        "department": approval.department,
        "project_name": project.name if project else None,
        "status": approval.status.value if hasattr(approval.status, "value") else str(approval.status),
        "submitted_at": approval.submitted_at.isoformat() if approval.submitted_at else None,
        "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
        "estimated_processing_days": approval.estimated_processing_days,
        "risk_level": approval.risk_level,
    }


@router.get("")
async def list_applications(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List applications for the authenticated user's projects"""
    service = ProjectService(db)
    projects = await service.list_user_projects(UUID(user["sub"]))
    project_map = {str(p.id): p for p in projects}

    if not projects:
        return {"applications": []}

    result = await db.execute(
        select(Approval).where(Approval.project_id.in_([p.id for p in projects]))
    )
    approvals = result.scalars().all()

    return {
        "applications": [
            _application_payload(a, project_map.get(str(a.project_id)))
            for a in approvals
        ]
    }


@router.get("/{application_id}")
async def get_application(
    application_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get application status and details"""
    approval = await _resolve_approval(db, user, application_id)
    service = ProjectService(db)
    project = await service.get_project(approval.project_id)
    return _application_payload(approval, project)


@router.get("/{application_id}/sla")
async def get_sla_status(
    application_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get SLA status for application (spec §22)."""
    approval = await _resolve_approval(db, user, application_id)
    from app.services.sla_engine import SlaEngine
    sla = SlaEngine().evaluate(
        status=approval.status,
        submitted_at=approval.submitted_at,
        sla_days=approval.estimated_processing_days,
    )
    return {
        "application_id": approval.application_id or str(approval.id),
        "approval_name": approval.name,
        **sla,
    }


@router.get("/{application_id}/sla/prediction")
async def get_sla_prediction(
    application_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Predictive SLA breach estimate for an application (spec §23).

    This is predictive assistance combining time-based and feature-based risk;
    it is NOT a statutory determination.
    """
    approval = await _resolve_approval(db, user, application_id)
    from app.services.sla_predictor import SlaPredictor
    prediction = SlaPredictor().predict(approval)
    return {
        "application_id": approval.application_id or str(approval.id),
        "approval_name": approval.name,
        "predictive": True,
        **prediction,
    }


@router.get("/{application_id}/transitions")
async def get_possible_transitions(
    application_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List the allowed next states for an application (spec §21)."""
    approval = await _resolve_approval(db, user, application_id)
    from app.services.approval_workflow import ApprovalWorkflowEngine
    role = user.get("role", "ENTREPRENEUR")
    engine = ApprovalWorkflowEngine(role)
    return {
        "application_id": approval.application_id or str(approval.id),
        "current_status": approval.status.value if hasattr(approval.status, "value") else str(approval.status),
        "available_transitions": engine.list_possible_transitions(approval.status),
    }


@router.post("/{application_id}/transition")
async def transition_application(
    application_id: str,
    body: dict,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Request a state-machine transition (spec §21)."""
    approval = await _resolve_approval(db, user, application_id)
    target = (body or {}).get("to_status")
    if not target:
        raise HTTPException(status_code=400, detail="Missing 'to_status'")

    from app.services.approval_workflow import ApprovalWorkflowEngine, TransitionError
    engine = ApprovalWorkflowEngine(user.get("role", "ENTREPRENEUR"))
    try:
        requested_status = ApprovalStatus[target.upper()]
    except (KeyError, AttributeError) as exc:
        raise HTTPException(status_code=400, detail=f"Unknown status: {target}") from exc

    decision = engine.apply(approval, requested_status)
    if not decision.allowed:
        raise HTTPException(status_code=400, detail=decision.error or "Transition not allowed")

    await db.commit()
    await db.refresh(approval)

    # Raise a notification about the status change.
    try:
        result = await db.execute(select(Project).where(Project.id == approval.project_id))
        project = result.scalar_one_or_none()
        owner_id = str(project.user_id) if project else None
        if owner_id:
            from app.notifications.service import NotificationService
            await NotificationService(db).create(
                owner_id,
                "Application Status Updated",
                f"Your application for {approval.name} is now {decision.requested.value}.",
                category="approval",
                severity="info",
                project_id=approval.project_id,
                reference_id=str(approval.id),
            )
    except Exception:
        db.rollback()

    return {**_application_payload(approval, None), "transition": decision.to_dict()}



@router.post("/{application_id}/submit")
async def submit_application(
    application_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Transition an approval to SUBMITTED via the workflow engine (spec §21)
    and raise an in-app notification."""
    approval = await _resolve_approval(db, user, application_id)
    from app.services.approval_workflow import ApprovalWorkflowEngine
    engine = ApprovalWorkflowEngine(user.get("role", "ENTREPRENEUR"))
    decision = engine.apply(approval, ApprovalStatus.SUBMITTED)
    if not decision.allowed:
        raise HTTPException(status_code=400, detail=decision.error or "Cannot submit application in current state")
    await db.commit()
    await db.refresh(approval)

    # Track the application with the government integration layer (spec §19)
    # so live-status sync polls it. Uses the mock submission id by default.
    try:
        from app.services.gov_sync_service import GovSyncService
        from app.services.gateway_service import GatewayService
        from app.integrations.government_adapters import system_for_department
        system = system_for_department(approval.department) or "maitri"
        submission = await GatewayService().submit(system, {"sla_days": approval.estimated_processing_days or 30})
        submission_data = (submission or {}).get("data") if isinstance((submission or {}).get("data"), dict) else {}
        gov_app_id = (
            submission_data.get("application_id")
            or (submission or {}).get("application_id")
        )
        if gov_app_id:
            await GovSyncService(db).track(approval, system, gov_app_id)
    except Exception as exc:  # noqa: BLE001
        pass  # tracking is best-effort; the application was already submitted

    from app.notifications.service import NotificationService
    from app.models import Project
    try:
        result = await db.execute(select(Project).where(Project.id == approval.project_id))
        project = result.scalar_one_or_none()
        owner_id = str(project.user_id) if project else None
        if owner_id:
            await NotificationService(db).create(
                owner_id,
                "Application Submitted",
                f"Your application for {approval.name} has been submitted to {approval.department}.",
                category="approval",
                severity="info",
                project_id=approval.project_id,
                reference_id=str(approval.id),
            )
    except Exception:
        db.rollback()

    return _application_payload(approval, None)