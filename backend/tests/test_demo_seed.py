"""Tests for the demo data seeder (spec §43)."""

import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

import pytest

from app.models import (
    ApprovalRule, User, Project, Approval, Document, UserRole,
)
from app.core.database import AsyncSessionLocal


@pytest.fixture
async def seed_rules(db_session):
    rules = [
        ApprovalRule(
            name="MPCB Consent to Establish (CTE)",
            department="MPCB",
            sector="Textile",
            conditions={
                "type": "OR",
                "conditions": [
                    {"type": "COMPARISON", "field": "has_boiler", "operator": "equals", "value": True},
                    {"type": "COMPARISON", "field": "hazardous_materials", "operator": "equals", "value": True},
                ],
            },
            is_mandatory=True,
            required_documents=["CTE application", "Site plan"],
            dependencies=[],
            estimated_processing_days=30,
            renewal_period_days=365,
            risk_level="HIGH",
            source="MPCB",
        ),
        ApprovalRule(
            name="Factory License (DISH)",
            department="DISH",
            sector="Textile",
            conditions={"type": "COMPARISON", "field": "employees", "operator": "greater_than", "value": 10},
            is_mandatory=True,
            required_documents=["Factory registration", "PID"],
            dependencies=["MPCB Consent to Establish (CTE)"],
            estimated_processing_days=15,
            renewal_period_days=365,
            risk_level="MEDIUM",
            source="DISH",
        ),
    ]
    db_session.add_all(rules)
    await db_session.commit()
    yield


async def test_seed_demo_creates_user_project_approvals_docs(seed_rules):
    import scripts.seed_demo as seeder

    report = await seeder.seed()

    assert report["email"] == "demo@abctextiles.in"
    assert report["project_id"]

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from uuid import UUID as _UUID
        user = (await db.execute(select(User).where(User.email == "demo@abctextiles.in"))).scalar_one()
        assert user.role == UserRole.ENTREPRENEUR

        project = (await db.execute(select(Project).where(Project.id == _UUID(report["project_id"])))).scalar_one()
        assert project.company_name == "ABC Textiles Pvt Ltd"

        approvals = (await db.execute(select(Approval).where(Approval.project_id == project.id))).scalars().all()
        assert len(approvals) >= 2

        docs = (await db.execute(select(Document).where(Document.project_id == project.id))).scalars().all()
        assert len(docs) == 2


async def test_seed_demo_is_idempotent(seed_rules):
    import scripts.seed_demo as seeder

    first = await seeder.seed()
    second = await seeder.seed()

    assert second["user_created"] is False
    assert second["project_created"] is False
    assert second["project_id"] == first["project_id"]

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from uuid import UUID as _UUID
        users = (await db.execute(select(User).where(User.email == "demo@abctextiles.in"))).scalars().all()
        assert len(users) == 1

        projects = (await db.execute(select(Project).where(Project.id == _UUID(first["project_id"])))).scalars().all()
        assert len(projects) == 1

        approvals = (await db.execute(select(Approval).where(Approval.project_id == _UUID(first["project_id"])))).scalars().all()
        assert len(approvals) == first["approvals_determined"]
