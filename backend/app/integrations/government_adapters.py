from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID
import json
import random
from datetime import datetime, timedelta

class GovernmentIntegrationAdapter(ABC):
    """Base class for government system integrations"""
    
    @abstractmethod
    async def authenticate(self):
        """Authenticate with government system"""
        pass
    
    @abstractmethod
    async def get_services(self) -> list[dict]:
        """Get available services"""
        pass
    
    @abstractmethod
    async def get_application_status(self, application_id: str) -> dict:
        """Get application status"""
        pass
    
    @abstractmethod
    async def submit_application(self, application_data: dict) -> dict:
        """Submit application"""
        pass


class MaitriAdapter(GovernmentIntegrationAdapter):
    """Adapter for MAITRI system integration"""
    
    async def authenticate(self):
        return {"status": "authenticated", "system": "MAITRI"}
    
    async def get_services(self) -> list[dict]:
        return [
            {"id": "factory_license", "name": "Factory License", "department": "Factory"},
            {"id": "building_approval", "name": "Building Approval", "department": "Building"},
        ]
    
    async def get_application_status(self, application_id: str) -> dict:
        statuses = ['NOT_STARTED', 'SUBMITTED', 'UNDER_REVIEW', 'QUERY_RAISED', 'APPROVED']
        return {
            "application_id": application_id,
            "system": "MAITRI",
            "status": random.choice(statuses),
            "submitted_at": (datetime.utcnow() - timedelta(days=10)).isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "sla_days": 30,
            "days_elapsed": 10,
        }
    
    async def submit_application(self, application_data: dict) -> dict:
        return {
            "application_id": f"MAITRI-{random.randint(100000, 999999)}",
            "status": "SUBMITTED",
            "submitted_at": datetime.utcnow().isoformat(),
            "message": "Application submitted successfully to MAITRI",
        }


class MpcbAdapter(GovernmentIntegrationAdapter):
    """Adapter for MPCB (Maharashtra Pollution Control Board) integration"""
    
    async def authenticate(self):
        return {"status": "authenticated", "system": "MPCB"}
    
    async def get_services(self) -> list[dict]:
        return [
            {"id": "consent_establish", "name": "Consent to Establish", "department": "MPCB"},
            {"id": "consent_operate", "name": "Consent to Operate", "department": "MPCB"},
        ]
    
    async def get_application_status(self, application_id: str) -> dict:
        return {
            "application_id": application_id,
            "system": "MPCB",
            "status": "QUERY_RAISED",
            "query": "ETP capacity details required",
            "submitted_at": (datetime.utcnow() - timedelta(days=20)).isoformat(),
            "sla_days": 60,
            "days_elapsed": 20,
        }
    
    async def submit_application(self, application_data: dict) -> dict:
        return {
            "application_id": f"MPCB-{random.randint(100000, 999999)}",
            "status": "SUBMITTED",
            "submitted_at": datetime.utcnow().isoformat(),
            "message": "Application submitted to MPCB for review",
        }


class MidcAdapter(GovernmentIntegrationAdapter):
    """Adapter for MIDC (Maharashtra Industrial Development Corporation) integration"""
    
    async def authenticate(self):
        return {"status": "authenticated", "system": "MIDC"}
    
    async def get_services(self) -> list[dict]:
        return [
            {"id": "plot_allotment", "name": "Plot Allotment", "department": "MIDC"},
            {"id": "industrial_area", "name": "Industrial Area Services", "department": "MIDC"},
        ]
    
    async def get_application_status(self, application_id: str) -> dict:
        return {
            "application_id": application_id,
            "system": "MIDC",
            "status": "APPROVED",
            "approved_date": (datetime.utcnow() - timedelta(days=5)).isoformat(),
        }
    
    async def submit_application(self, application_data: dict) -> dict:
        return {
            "application_id": f"MIDC-{random.randint(100000, 999999)}",
            "status": "SUBMITTED",
            "submitted_at": datetime.utcnow().isoformat(),
        }


class BoilerAdapter(GovernmentIntegrationAdapter):
    """Adapter for Boiler Registration system integration"""
    
    async def authenticate(self):
        return {"status": "authenticated", "system": "Boiler"}
    
    async def get_services(self) -> list[dict]:
        return [
            {"id": "boiler_registration", "name": "Boiler Registration", "department": "Boiler Safety"},
        ]
    
    async def get_application_status(self, application_id: str) -> dict:
        return {
            "application_id": application_id,
            "system": "Boiler",
            "status": "UNDER_REVIEW",
            "submitted_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
            "expected_completion": (datetime.utcnow() + timedelta(days=10)).isoformat(),
        }
    
    async def submit_application(self, application_data: dict) -> dict:
        return {
            "application_id": f"BOILER-{random.randint(100000, 999999)}",
            "status": "SUBMITTED",
            "submitted_at": datetime.utcnow().isoformat(),
        }


class FireAdapter(GovernmentIntegrationAdapter):
    """Adapter for Fire Safety Department integration"""
    
    async def authenticate(self):
        return {"status": "authenticated", "system": "Fire"}
    
    async def get_services(self) -> list[dict]:
        return [
            {"id": "fire_permission", "name": "Fire Safety Permission", "department": "Fire"},
        ]
    
    async def get_application_status(self, application_id: str) -> dict:
        return {
            "application_id": application_id,
            "system": "Fire",
            "status": "INSPECTION",
            "inspection_date": (datetime.utcnow() + timedelta(days=3)).isoformat(),
        }
    
    async def submit_application(self, application_data: dict) -> dict:
        return {
            "application_id": f"FIRE-{random.randint(100000, 999999)}",
            "status": "SUBMITTED",
            "submitted_at": datetime.utcnow().isoformat(),
        }


class LabourAdapter(GovernmentIntegrationAdapter):
    """Adapter for Labour Department integration"""
    
    async def authenticate(self):
        return {"status": "authenticated", "system": "Labour"}
    
    async def get_services(self) -> list[dict]:
        return [
            {"id": "labour_license", "name": "Labour License", "department": "Labour"},
            {"id": "esi_registration", "name": "ESI Registration", "department": "Labour"},
        ]
    
    async def get_application_status(self, application_id: str) -> dict:
        return {
            "application_id": application_id,
            "system": "Labour",
            "status": "APPROVED",
            "approved_date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        }
    
    async def submit_application(self, application_data: dict) -> dict:
        return {
            "application_id": f"LABOUR-{random.randint(100000, 999999)}",
            "status": "SUBMITTED",
            "submitted_at": datetime.utcnow().isoformat(),
        }


class GovernmentAPIGateway:
    """Gateway for managing all government integrations"""
    
    def __init__(self):
        self.adapters = {
            'maitri': MaitriAdapter(),
            'mpcb': MpcbAdapter(),
            'midc': MidcAdapter(),
            'boiler': BoilerAdapter(),
            'fire': FireAdapter(),
            'labour': LabourAdapter(),
        }
    
    async def get_application_status(self, system: str, application_id: str) -> dict:
        """Get application status from specific government system"""
        adapter = self.adapters.get(system.lower())
        if not adapter:
            raise ValueError(f"Unknown system: {system}")
        
        return await adapter.get_application_status(application_id)
    
    async def submit_application(self, system: str, application_data: dict) -> dict:
        """Submit application to specific government system"""
        adapter = self.adapters.get(system.lower())
        if not adapter:
            raise ValueError(f"Unknown system: {system}")
        
        return await adapter.submit_application(application_data)
    
    async def get_all_statuses(self, application_ids: dict) -> dict:
        """
        Get status from all government systems
        application_ids: {"system": "application_id", ...}
        """
        results = {}
        
        for system, app_id in application_ids.items():
            try:
                results[system] = await self.get_application_status(system, app_id)
            except Exception as e:
                results[system] = {"error": str(e)}
        
        return results


_DEPARTMENT_TO_SYSTEM = {
    "mpcb": "mpcb",
    "pollution": "mpcb",
    "factory": "maitri",
    "industrial safety": "maitri",
    "fire": "fire",
    "boiler": "boiler",
    "steam boilers": "boiler",
    "midc": "midc",
    "labour": "labour",
    "gst": "gst",
    "esic": "esic",
}


def system_for_department(department: str | None) -> str | None:
    """Map a department name onto a government integration system key."""
    if not department:
        return None
    lowered = department.lower()
    for token, system in _DEPARTMENT_TO_SYSTEM.items():
        if token in lowered:
            return system
    return None
