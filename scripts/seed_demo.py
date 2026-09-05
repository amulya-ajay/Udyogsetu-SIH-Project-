"""Seed a rich demo dataset (spec §43) so the SIH demo flows are one-click.

Creates (idempotently):
  * a demo entrepreneur user, ABC Textiles Pvt Ltd
  * the "ABC Textiles Pvt Ltd - New Dyes Unit" project
  * applicable approvals via the ApprovalEngine
  * submittal of a selection of approvals, tracked against the mock gov systems
  * a few demo business documents (with extracted fields for the doc-AI flow)

Run:
    python scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))  # ensures `app` is importable


async def seed() -> dict:
    from sqlalchemy import select
    from app.models import (
        UserRole, Project, Approval, Document, ApprovalStatus, User,
    )
    from app.core.database import AsyncSessionLocal
    from app.core.security import hash_password
    from app.services.auth import AuthService
    from app.services.project import ProjectService
    from app.schemas import UserRegister, ProjectOnboarding
    from app.rules.approval_engine import ApprovalEngine
    from app.services.gov_sync_service import GovSyncService
    from app.services.gateway_service import GatewayService
    from app.integrations.government_adapters import system_for_department

    DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "demo@abctextiles.in")
    DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Demo@12345")

    async with AsyncSessionLocal() as db:
        # 1. Demo user (idempotent)
        auth = AuthService(db)
        try:
            user = await auth.register_user(UserRegister(
                email=DEMO_EMAIL,
                name="Rohit Sharma",
                phone="9876543210",
                password=DEMO_PASSWORD,
                role=UserRole.ENTREPRENEUR,
            ))
            created_user = True
        except ValueError:
            user = await auth.get_user_by_email(DEMO_EMAIL)
            created_user = False

        # 1b. Demo officer + admin provisioning (idempotent). These bypass the
        # public self-registration path (which is ENTREPRENEUR-only) and are the
        # sanctioned way to create privileged accounts for the demo.
        privileged = {
            ("officer@udoyogsetu.demo", "Officer", UserRole.OFFICER, os.environ.get("OFFICER_PASSWORD", "Officer@12345")),
            ("admin@udoyogsetu.demo", "Admin", UserRole.ADMIN, os.environ.get("ADMIN_PASSWORD", "Admin@12345")),
        }
        created_privileged = []
        for priv_email, priv_name, priv_role, priv_password in privileged:
            result = await db.execute(select(User).where(User.email == priv_email))
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(User(
                    email=priv_email,
                    name=priv_name,
                    phone="9876500000",
                    password_hash=hash_password(priv_password),
                    role=priv_role,
                    is_active=True,
                ))
                created_privileged.append(priv_role.value)
        if created_privileged:
            await db.commit()

        # 2. Project (idempotent by name)
        svc = ProjectService(db)
        existing = await svc.list_user_projects(user.id)
        project = next((p for p in existing if p.name == "ABC Textiles Pvt Ltd - New Dyes Unit"), None)
        if project is None:
            project = await svc.create_project(ProjectOnboarding(
                project_name="ABC Textiles Pvt Ltd - New Dyes Unit",
                company_name="ABC Textiles Pvt Ltd",
                business_type="manufacturing",
                industry="Textile",
                sector="Textile",
                project_stage="implementation",
                investment_amount=350000000,
                location_state="Maharashtra",
                location_district="Nashik",
                location_city="Nashik",
                location_industrial_area="MIDC Ambad",
                location_midc_estate="Ambad",
                land_type="industrial_plot",
                employees=120,
                production_type="Textile processing",
                hazardous_materials=True,
                has_boiler=True,
                electricity_load=1200,
                water_consumption=250,
                pollution_potential="high",
                building_type="industrial",
                is_new=True,
            ), user_id=user.id)
            created_project = True
        else:
            created_project = False

        # 3. Determine applicable approvals (only if none exist yet - idempotent)
        result = await db.execute(
            select(Approval).where(Approval.project_id == project.id)
        )
        approval_rows = result.scalars().all()
        if not approval_rows:
            engine = ApprovalEngine(db)
            await engine.determine_approvals(project.id)
            result = await db.execute(
                select(Approval).where(Approval.project_id == project.id)
            )
            approval_rows = result.scalars().all()

        # 4. Set the demo status story (spec §43) per department/system,
        #    submitting + tracking those approvals against the mock gov systems:
        #      MIDC  -> APPROVED      Fire -> APPROVED      DISH -> UNDER_REVIEW (processing)
        #      MPCB  -> QUERY_RAISED  Boiler -> NOT_STARTED others -> SUBMITTED
        gov_service = GovSyncService(db)
        _demo_status_by_system = {
            "midc": "APPROVED",
            "fire": "APPROVED",
            "maitri": "UNDER_REVIEW",   # DISH / factory licence
            "mpcb": "QUERY_RAISED",     # Consent to Establish query
            "boiler": "NOT_STARTED",
        }
        submitted = 0
        for approval in approval_rows:
            system = system_for_department(approval.department) or "maitri"
            demo_status = _demo_status_by_system.get(system, "SUBMITTED")

            if demo_status == "NOT_STARTED":
                approval.status = ApprovalStatus.NOT_STARTED
                continue

            approval.status = ApprovalStatus[str(demo_status)]
            approval.submitted_at = approval.submitted_at or datetime.now(timezone.utc)
            if demo_status == "APPROVED":
                approval.approved_at = approval.approved_at or datetime.now(timezone.utc)
            try:
                sub = await GatewayService().submit(system, {"sla_days": approval.estimated_processing_days or 30})
                gov_id = ((sub or {}).get("data") or {}).get("application_id")
                if gov_id:
                    await gov_service.track(approval, system, gov_id)
                    submitted += 1
            except Exception:
                pass
        await db.commit()

        # 5. Demo documents (with extracted fields for the doc-AI flow)
        demo_docs = [
            {
                "file_name": "mpcb_consent_to_establish.pdf",
                "content_type": "application/pdf",
                "doc_type": "MPCB CONSENT",
                "fields": {
                    "document_type": "MPCB CONSENT",
                    "name": "ABC Textiles Pvt Ltd",
                    "registration_number": "MPCB-PNE-2024-001",
                    "expiry_date": "2027-04-15",
                    "authority": "MPCB",
                },
            },
            {
                "file_name": "factory_license_DISH.pdf",
                "content_type": "application/pdf",
                "doc_type": "FACTORY LICENSE",
                "fields": {
                    "document_type": "FACTORY LICENSE",
                    "name": "ABC Textiles Pvt Ltd",
                    "registration_number": "FL-2024-PN-5582",
                    "issue_date": "2024-01-15",
                    "expiry_date": "2025-01-14",
                    "authority": "DISH",
                },
            },
        ]
        seed_docs = 0
        for d in demo_docs:
            result = await db.execute(
                select(Document).where(
                    Document.project_id == project.id,
                    Document.file_name == d["file_name"],
                )
            )
            if result.scalar_one_or_none() is None:
                db.add(Document(
                    project_id=project.id,
                    file_name=d["file_name"],
                    file_path=f"demo/{d['file_name']}",
                    file_type=d["content_type"],
                    file_size=1024,
                    status="PROCESSING",
                    extracted_fields=d["fields"],
                    custom_metadata={"document_type": d["doc_type"], "demo": True},
                ))
                seed_docs += 1
        await db.commit()

        return {
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "user_created": created_user,
            "project_created": created_project,
            "project_id": str(project.id),
            "approvals_determined": len(approval_rows),
            "approvals_submitted": submitted,
            "demo_documents_seeded": seed_docs,
            "officer_email": "officer@udoyogsetu.demo",
            "admin_email": "admin@udoyogsetu.demo",
            "privileged_created": created_privileged,
        }


def main() -> int:
    report = asyncio.run(seed())
    print("=" * 60)
    print("DEMO DATA SEEDED")
    print("=" * 60)
    print(f"Login email : {report['email']}")
    print(f"Password    : {report['password']}")
    print(f"Officer login : {report['officer_email']}")
    print(f"Admin login   : {report['admin_email']}")
    print(f"Project ID  : {report['project_id']}")
    print(f"Approvals   : {report['approvals_determined']} determined, "
          f"{report['approvals_submitted']} submitted")
    print(f"Demo docs   : {report['demo_documents_seeded']}")
    print(f"Privileged accounts created: {report['privileged_created'] or 'none (existed)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
