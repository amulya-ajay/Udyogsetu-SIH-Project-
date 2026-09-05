from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models import ComplianceItem, Project

class ComplianceService:
    """Compliance management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_compliance_dashboard(self, project_id: UUID) -> dict:
        """Get compliance dashboard with scores and metrics"""
        result = await self.db.execute(
            select(ComplianceItem).where(ComplianceItem.project_id == project_id)
        )
        items = result.scalars().all()

        if not items:
            return {
                "project_id": str(project_id),
                "overall_score": 0,
                "categories": {}
            }

        categories = {}
        for item in items:
            if item.category not in categories:
                categories[item.category] = {"total": 0, "compliant": 0}

            categories[item.category]["total"] += 1
            if (item.status.value if hasattr(item.status, "value") else item.status) == "ON_TRACK":
                categories[item.category]["compliant"] += 1

        total = sum(c["total"] for c in categories.values())
        compliant = sum(c["compliant"] for c in categories.values())
        overall_score = round((compliant / total) * 100, 2) if total else 0

        return {
            "project_id": str(project_id),
            "overall_score": overall_score,
            "categories": categories,
            "items_count": len(items),
        }
    
    async def get_compliance_items(self, project_id: UUID) -> list[ComplianceItem]:
        """Get all compliance items for a project"""
        result = await self.db.execute(
            select(ComplianceItem).where(ComplianceItem.project_id == project_id)
        )
        return result.scalars().all()
