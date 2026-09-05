"""Tests for the officer analytics aggregation."""

import uuid

import pytest

from app.models import Approval, User, Project
from app.models import ApprovalStatus


@pytest.fixture
async def populated(db_session):
    user = User(
        email=f"off-{uuid.uuid4().hex[:8]}@example.com",
        name="Officer Test",
        phone="9876502222",
        role="ENTREPRENEUR",
    )
    user.password_hash = "x"
    db_session.add(user)
    await db_session.flush()

    project = Project(user_id=user.id, name="P", company_name="C")
    db_session.add(project)
    await db_session.flush()

    db_session.add_all([
        Approval(project_id=project.id, name="A", department="MPCB", estimated_processing_days=30),
        Approval(project_id=project.id, name="B", department="Factory", status=ApprovalStatus.APPROVED, estimated_processing_days=10),
        Approval(project_id=project.id, name="C", department="MPCB", estimated_processing_days=60),
    ])
    await db_session.commit()


@pytest.mark.asyncio
async def test_overview_counts(populated, db_session):
    from app.services.officer_analytics import OfficerAnalyticsService
    svc = OfficerAnalyticsService(db_session)
    overview = await svc.overview()
    assert overview["total_applications"] == 3
    assert overview["approved"] == 1
    assert overview["pending_review"] == 2


@pytest.mark.asyncio
async def test_by_department_aggregates(populated, db_session):
    from app.services.officer_analytics import OfficerAnalyticsService
    svc = OfficerAnalyticsService(db_session)
    departments = await svc.by_department()
    mpcb = [d for d in departments if d["department"] == "MPCB"]
    factory = [d for d in departments if d["department"] == "Factory"]
    assert mpcb and mpcb[0]["total"] == 2 and mpcb[0]["pending"] == 2
    assert factory and factory[0]["approved"] == 1


@pytest.mark.asyncio
async def test_status_distribution(populated, db_session):
    from app.services.officer_analytics import OfficerAnalyticsService
    svc = OfficerAnalyticsService(db_session)
    dist = await svc.status_distribution()
    total = sum(d["count"] for d in dist)
    assert total == 3