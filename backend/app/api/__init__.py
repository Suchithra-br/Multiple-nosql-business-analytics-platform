"""
API Module.

Exports the master api_router as well as individual domain routers.
"""

from backend.app.api.router import api_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.graph import router as graph_router

__all__ = [
    "api_router",
    "health_router",
    "dashboard_router",
    "analytics_router",
    "graph_router",
]
