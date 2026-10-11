"""
Centralized API Router.

Mounts versioned API routers (v1) under their canonical prefixes.
Preserves existing API contract and endpoint paths without breaking changes.
"""

from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.graph import router as graph_router

api_router = APIRouter()

# Health endpoints (/health and /api/v1/health)
api_router.include_router(health_router)

# Version 1 Analytics & Dashboard sub-routers under /api/v1
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(dashboard_router)
api_v1.include_router(analytics_router)
api_v1.include_router(graph_router)

api_router.include_router(api_v1)
