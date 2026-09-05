from fastapi import APIRouter

from app.api import (
    applications,
    audit,
    auth,
    business_intelligence,
    chat,
    compliance,
    documents,
    explore,
    gateway,
    knowledge_graph,
    notifications,
    observability,
    officer,
    officer_applications,
    projects,
    regulatory,
    schemes,
    synchronization,
    tools_api,
    workers_api,
)

router = APIRouter()

router.include_router(auth.router)
router.include_router(projects.router)
router.include_router(documents.router)
router.include_router(chat.router)
router.include_router(compliance.router)
router.include_router(schemes.router)
router.include_router(applications.router)
router.include_router(regulatory.router)
router.include_router(business_intelligence.router)
router.include_router(gateway.router)
router.include_router(audit.router)
router.include_router(workers_api.router)
router.include_router(notifications.router)
router.include_router(officer.router)
router.include_router(tools_api.router)
router.include_router(synchronization.router)
router.include_router(observability.router)
router.include_router(knowledge_graph.router)
router.include_router(explore.router)
router.include_router(officer_applications.router)
