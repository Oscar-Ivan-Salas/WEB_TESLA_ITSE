"""
API v1 endpoints for the Tesla CRM application.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["v1"])

# Import and include endpoint routers
from .endpoints import chat, leads, metrics, dashboard

router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(leads.router, prefix="/leads", tags=["leads"])
router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
