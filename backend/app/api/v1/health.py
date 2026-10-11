"""
Health Diagnostics Endpoints (API v1).

Provides:
- Liveness check (GET /health)
- Deep multi-database readiness diagnostics (GET /api/v1/health)
"""

from fastapi import APIRouter
from backend.app.models.schemas import HealthResponse
from backend.app.databases.mongodb import check_mongodb_connection
from backend.app.databases.redis import check_redis_connection
from backend.app.databases.cassandra import check_cassandra_connection
from backend.app.databases.neo4j import check_neo4j_connection

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Basic API Liveness Check")
def health_liveness():
    """Simple health check confirming that the FastAPI process is active."""
    return {"status": "ok", "message": "FastAPI backend is running"}


@router.get("/api/v1/health", response_model=HealthResponse, summary="Multi-NoSQL Database Readiness Diagnostics")
def health_readiness():
    """
    Checks real-time connectivity to all four NoSQL databases:
    - MongoDB (Document store)
    - Redis (In-memory KPI cache)
    - Cassandra (Time-series analytical store)
    - Neo4j (Graph store)
    """
    mongo_ok, _ = check_mongodb_connection(timeout_ms=1000)
    redis_ok, _ = check_redis_connection(timeout_s=1.0)
    cassandra_ok, _ = check_cassandra_connection(max_retries=1)
    neo4j_ok, _ = check_neo4j_connection(max_retries=1)

    db_status = {
        "mongodb": "healthy" if mongo_ok else "unhealthy",
        "redis": "healthy" if redis_ok else "unhealthy",
        "cassandra": "healthy" if cassandra_ok else "unhealthy",
        "neo4j": "healthy" if neo4j_ok else "unhealthy",
    }

    all_healthy = all(v == "healthy" for v in db_status.values())
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        databases=db_status,
    )
