"""Tests for the approval dependency graph + critical-path analysis."""

import uuid

import pytest

from app.models import Approval, ApprovalRule, Project, User


@pytest.fixture
async def project_with_rules(db_session):
    user = User(
        email=f"graph-{uuid.uuid4().hex[:8]}@example.com",
        name="Graph User",
        phone="9876501111",
        role="ENTREPRENEUR",
    )
    user.password_hash = "x"
    db_session.add(user)
    await db_session.flush()

    project = Project(
        user_id=user.id,
        name="Graph Project",
        company_name="Graph Corp",
    )
    db_session.add(project)
    await db_session.flush()

    return user, project


@pytest.mark.asyncio
async def test_graph_builds_nodes_and_reports_duration(db_session, project_with_rules):
    from app.services.approval_graph import ApprovalGraphService

    _user, project = project_with_rules

    r1 = ApprovalRule(
        id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
        name="Consent to Establish",
        department="MPCB",
        conditions={"type": "COMPARISON", "field": "x", "operator": "equals", "value": 1},
        dependencies=[],
        estimated_processing_days=60,
    )
    r2 = ApprovalRule(
        id=uuid.UUID("10000000-0000-0000-0000-000000000002"),
        name="Consent to Operate",
        department="MPCB",
        conditions={"type": "COMPARISON", "field": "x", "operator": "equals", "value": 1},
        dependencies=["10000000-0000-0000-0000-000000000001"],
        estimated_processing_days=45,
    )
    db_session.add_all([r1, r2])
    await db_session.flush()

    a1 = Approval(project_id=project.id, name="Consent to Establish", department="MPCB", estimated_processing_days=60)
    a2 = Approval(project_id=project.id, name="Consent to Operate", department="MPCB", estimated_processing_days=45)
    db_session.add_all([a1, a2])
    await db_session.commit()

    svc = ApprovalGraphService(db_session)
    graph = await svc.build_graph(project.id)

    assert len(graph["nodes"]) == 2
    # edge from rule1 -> rule2 exists
    assert len(graph["edges"]) == 1
    assert graph["critical_path"]["duration_days"] == 60 + 45
    assert graph["critical_path"]["approvals"]


@pytest.mark.asyncio
async def test_graph_handles_no_approvals(db_session, project_with_rules):
    from app.services.approval_graph import ApprovalGraphService

    _user, project = project_with_rules
    await db_session.commit()

    svc = ApprovalGraphService(db_session)
    graph = await svc.build_graph(project.id)
    assert graph["nodes"] == []
    assert graph["edges"] == []
    assert graph["critical_path"]["duration_days"] == 0