from datetime import datetime
from typing import Optional
import json

class ScenarioSimulator:
    """
    Simulate various scenarios to understand approval impact
    """
    
    def __init__(self):
        pass
    
    def simulate_location_change(
        self,
        original_project: dict,
        new_location: dict
    ) -> dict:
        """
        Simulate impact of changing project location
        """
        impact = {
            "scenario": "location_change",
            "original_location": original_project.get('location'),
            "new_location": new_location.get('name'),
            "changes": {
                "approvals_added": [],
                "approvals_removed": [],
                "timeline_change_days": 0,
                "cost_impact": 0,
            },
            "affected_approvals": [],
        }
        
        # Determine location-specific approvals
        location_approvals = self._get_location_approvals(new_location)
        original_approvals = self._get_location_approvals(original_project.get('location', {}))
        
        impact['changes']['approvals_added'] = [
            a for a in location_approvals
            if a not in original_approvals
        ]
        
        impact['changes']['approvals_removed'] = [
            a for a in original_approvals
            if a not in location_approvals
        ]
        
        # Calculate timeline impact
        added_days = len(impact['changes']['approvals_added']) * 30
        removed_days = len(impact['changes']['approvals_removed']) * 30
        impact['changes']['timeline_change_days'] = added_days - removed_days
        
        # Calculate cost impact
        impact['changes']['cost_impact'] = (added_days - removed_days) * 500
        
        impact['affected_approvals'] = impact['changes']['approvals_added']
        
        return impact
    
    def simulate_sector_upgrade(
        self,
        original_project: dict,
        new_sector: str
    ) -> dict:
        """
        Simulate impact of upgrading business sector/scale
        """
        impact = {
            "scenario": "sector_upgrade",
            "original_sector": original_project.get('sector'),
            "new_sector": new_sector,
            "changes": {
                "approvals_required": [],
                "estimated_additional_timeline": 0,
                "estimated_additional_cost": 0,
                "pollution_category_change": None,
            },
        }
        
        # Determine new approvals needed
        new_approvals = self._get_sector_approvals(new_sector)
        original_approvals = self._get_sector_approvals(original_project.get('sector', 'manufacturing'))
        
        additional = [a for a in new_approvals if a not in original_approvals]
        impact['changes']['approvals_required'] = additional
        
        # Estimate timeline and cost
        impact['changes']['estimated_additional_timeline'] = len(additional) * 40
        impact['changes']['estimated_additional_cost'] = len(additional) * 2000
        
        # Check pollution category change
        if self._get_pollution_category(new_sector) != self._get_pollution_category(original_project.get('sector')):
            impact['changes']['pollution_category_change'] = self._get_pollution_category(new_sector)
        
        return impact
    
    def simulate_capacity_expansion(
        self,
        original_project: dict,
        new_capacity: float
    ) -> dict:
        """
        Simulate impact of expanding production capacity
        """
        original_capacity = original_project.get('capacity', 0)
        
        impact = {
            "scenario": "capacity_expansion",
            "original_capacity": original_capacity,
            "new_capacity": new_capacity,
            "capacity_increase_percent": round(((new_capacity - original_capacity) / original_capacity * 100), 2) if original_capacity else 0,
            "changes": {
                "new_approvals_required": [],
                "modified_approvals": [],
                "timeline_extension_days": 0,
                "cost_increase": 0,
            },
        }
        
        # Determine capacity-related approval changes
        if new_capacity > original_capacity * 1.5:
            impact['changes']['new_approvals_required'] = [
                "Enhanced Environmental Assessment",
                "MPCB Consent Renewal",
                "Factory Layout Re-approval",
            ]
            impact['changes']['timeline_extension_days'] = 60
            impact['changes']['cost_increase'] = 5000
        elif new_capacity > original_capacity * 1.2:
            impact['changes']['modified_approvals'] = [
                "MPCB Consent Amendment",
                "Pollution Control Update",
            ]
            impact['changes']['timeline_extension_days'] = 30
            impact['changes']['cost_increase'] = 2000
        
        return impact
    
    def simulate_timeline_compression(
        self,
        original_project: dict,
        target_days: int
    ) -> dict:
        """
        Simulate impact of compressing approval timeline
        """
        original_timeline = original_project.get('estimated_approval_days', 180)
        compression_percent = ((original_timeline - target_days) / original_timeline * 100)
        
        impact = {
            "scenario": "timeline_compression",
            "original_timeline_days": original_timeline,
            "target_timeline_days": target_days,
            "compression_percent": round(compression_percent, 2),
            "feasibility": self._assess_timeline_feasibility(original_project, target_days),
            "recommendations": [],
        }
        
        if compression_percent > 50:
            impact['feasibility'] = "low"
            impact['recommendations'] = [
                "Consider parallel approvals where possible",
                "Engage consultant for expedited processing",
                "Pre-preparation of documents is critical",
            ]
        elif compression_percent > 30:
            impact['feasibility'] = "medium"
            impact['recommendations'] = [
                "Plan parallel processing of approvals",
                "Allocate dedicated resources",
                "Regular follow-up with departments",
            ]
        else:
            impact['feasibility'] = "high"
            impact['recommendations'] = [
                "Standard process should work",
                "Maintain regular follow-ups",
            ]
        
        return impact
    
    def _get_location_approvals(self, location) -> list:
        """Get approvals required for a location.

        Accepts either a dict (``{"state": ...}``) or a plain state string, so
        callers that pass ``project.location_state`` directly do not crash.
        """
        if isinstance(location, dict):
            state = (location.get('state') or '').upper()
        elif isinstance(location, str):
            state = location.upper()
        else:
            state = ''

        location_approvals = {
            'MAHARASHTRA': [
                'MPCB Consent',
                'MIDC Clearance',
                'Municipal Approval',
            ],
            'GUJARAT': [
                'GPCB Consent',
                'GIDC Clearance',
            ],
            'TAMIL_NADU': [
                'TNPCB Consent',
                'SIPCOT Clearance',
            ],
        }
        
        return location_approvals.get(state, ['General Industrial Approval'])
    
    def _get_sector_approvals(self, sector: str) -> list:
        """Get approvals required for a sector"""
        sector_lower = sector.lower()
        
        approvals = {
            'textile': [
                'Factory License',
                'MPCB Consent',
                'DGFT License',
                'Labour License',
            ],
            'chemicals': [
                'Factory License',
                'MPCB Consent',
                'SPCB Clearance',
                'Fire Permission',
            ],
            'manufacturing': [
                'Factory License',
                'Boiler Registration',
                'Labour License',
            ],
            'food': [
                'Food License',
                'Health Clearance',
                'Municipal Approval',
            ],
        }
        
        for key, value in approvals.items():
            if key in sector_lower:
                return value
        
        return ['Factory License', 'Labour License']
    
    def _get_pollution_category(self, sector: str) -> str:
        """Determine pollution category by sector"""
        sector_lower = sector.lower()
        
        if any(word in sector_lower for word in ['chemical', 'steel', 'refinery', 'textile']):
            return 'RED'
        elif any(word in sector_lower for word in ['pharmaceutical', 'food', 'beverage']):
            return 'ORANGE'
        else:
            return 'GREEN'
    
    def _assess_timeline_feasibility(self, project: dict, target_days: int) -> str:
        """Assess feasibility of target timeline"""
        original = project.get('estimated_approval_days', 180)
        
        if target_days >= original * 0.8:
            return 'high'
        elif target_days >= original * 0.5:
            return 'medium'
        else:
            return 'low'
