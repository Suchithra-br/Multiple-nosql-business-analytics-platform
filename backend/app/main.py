"""
Multi-NoSQL Real-Time Business Analytics Platform - FastAPI Application.

Orchestrates polyglot query-driven API access across:
- MongoDB (Operational Document Store)
- Redis (Real-Time In-Memory KPI Cache)
- Apache Cassandra (Partition-Keyed Time-Series Analytics)
- Neo4j (Graph Relationship Traversal & Recommendations)
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.logging_config import setup_logging
from backend.app.core.error_handlers import register_error_handlers
from backend.app.api.router import api_router

from backend.app.databases.mongodb import close_mongodb_connection, check_mongodb_connection
from backend.app.databases.redis import close_redis_connection, check_redis_connection
from backend.app.databases.cassandra import close_cassandra_connection, check_cassandra_connection
from backend.app.databases.neo4j import close_neo4j_connection, check_neo4j_connection

# Initialize centralized logging
setup_logging(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup diagnostics and graceful database connection shutdown.
    Eagerly warms database connection singletons to eliminate cold-start latency.
    """
    logger.info("Initializing Multi-NoSQL FastAPI application...")

    # Non-blocking connectivity probe
    mongo_ok, _ = check_mongodb_connection(timeout_ms=1000)
    redis_ok, _ = check_redis_connection(timeout_s=1.0)
    cass_ok, _ = check_cassandra_connection(max_retries=1)
    neo_ok, _ = check_neo4j_connection(max_retries=1)

    logger.info(
        f"Startup Readiness — MongoDB: {'OK' if mongo_ok else 'WARN'}, "
        f"Redis: {'OK' if redis_ok else 'WARN'}, "
        f"Cassandra: {'OK' if cass_ok else 'WARN'}, "
        f"Neo4j: {'OK' if neo_ok else 'WARN'}"
    )

    yield  # Application processes requests here

    logger.info("Shutting down database connections cleanly...")
    close_mongodb_connection()
    close_redis_connection()
    close_cassandra_connection()
    close_neo4j_connection()
    logger.info("All database connections closed cleanly.")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "REST API layer demonstrating polyglot persistence across MongoDB (documents), "
            "Redis (KPI cache), Apache Cassandra (time-series), and Neo4j (relationship graph)."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS using centralized environment configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"^https?://.*\.trycloudflare\.com$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register centralized exception handlers
    register_error_handlers(app)

    # Mount master versioned API router
    app.include_router(api_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Uvicorn server on http://{settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run("backend.app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
