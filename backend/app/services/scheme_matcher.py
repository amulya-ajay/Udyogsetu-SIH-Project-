from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models import Scheme
from app.schemas import SchemeMatcher

class SchemeMatcher:
    """Scheme matching and discovery service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def find_matching_schemes(self, matcher: SchemeMatcher) -> list[dict]:
        """Find schemes matching project criteria"""
        result = await self.db.execute(
            select(Scheme).where(Scheme.is_active == True)
        )
        schemes = result.scalars().all()
        
        matches = []
        for scheme in schemes:
            score = self._calculate_match_score(scheme, matcher)
            if score > 0:
                matches.append({
                    "id": str(scheme.id),
                    "name": scheme.name,
                    "department": scheme.department,
                    "benefits": scheme.benefits,
                    "match_score": score,
                    "match_reason": self._generate_match_reason(scheme, matcher),
                })
        
        # Sort by score descending
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches
    
    def _calculate_match_score(self, scheme: Scheme, matcher: SchemeMatcher) -> float:
        """Calculate scheme match score"""
        score = 0.0
        
        # Sector match
        if scheme.sector and matcher.industry:
            if scheme.sector.lower() in matcher.industry.lower():
                score += 30
        
        # Investment range match
        if scheme.min_investment and scheme.max_investment:
            if scheme.min_investment <= matcher.investment <= scheme.max_investment:
                score += 30
        
        # Employee requirement match
        if scheme.employee_requirement:
            if matcher.employees >= scheme.employee_requirement:
                score += 20
        
        # Location match
        if scheme.location:
            score += 10
        
        return score
    
    def _generate_match_reason(self, scheme: Scheme, matcher: SchemeMatcher) -> str:
        """Generate human-readable reason for scheme match"""
        reasons = []
        
        if scheme.sector and matcher.industry:
            if scheme.sector.lower() in matcher.industry.lower():
                reasons.append(f"Your {matcher.industry} business qualifies")
        
        if scheme.min_investment and scheme.max_investment:
            if scheme.min_investment <= matcher.investment <= scheme.max_investment:
                reasons.append(f"Investment amount matches")
        
        if scheme.employee_requirement:
            if matcher.employees >= scheme.employee_requirement:
                reasons.append(f"Employee count eligible")
        
        return " | ".join(reasons) if reasons else "Good match"
    
    async def get_scheme(self, scheme_id: UUID) -> dict:
        """Get scheme details"""
        result = await self.db.execute(
            select(Scheme).where(Scheme.id == scheme_id)
        )
        scheme = result.scalar_one_or_none()
        
        if not scheme:
            return None
        
        return {
            "id": str(scheme.id),
            "name": scheme.name,
            "department": scheme.department,
            "sector": scheme.sector,
            "benefits": scheme.benefits,
            "min_investment": scheme.min_investment,
            "max_investment": scheme.max_investment,
            "source_url": scheme.source_url,
        }
