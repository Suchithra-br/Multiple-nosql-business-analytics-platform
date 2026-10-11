"""
API v1 Package.

Exposes route handlers for health, dashboard, analytics, and graph.
"""

from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.graph import router as graph_router

__all__ = [
    "health_router",
    "dashboard_router",
    "analytics_router",
    "graph_router",
]
