"""
API v1 endpoints for the Tesla CRM application.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["v1"])

# Import and include endpoint routers here
# from .endpoints import chat, leads, metrics
# router.include_router(chat.router)
# router.include_router(leads.router)
# router.include_router(metrics.router)
