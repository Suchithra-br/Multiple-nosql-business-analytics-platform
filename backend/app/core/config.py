"""
Application Configuration Module.

Centralizes environment configuration using standard os.getenv with verified defaults.
Reads configuration for MongoDB, Redis, Cassandra, Neo4j, CORS, and API settings.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Settings:
    """Immutable application settings container."""

    # API Metadata
    APP_NAME: str = "Multi-NoSQL Real-Time Business Analytics Platform API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("API_ENV", os.getenv("ENVIRONMENT", "development"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # Server Bindings
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # CORS Configuration
    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
            ).split(",")
            if origin.strip()
        ]
    )

    # MongoDB Settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "business_analytics")

    # Redis Settings
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_CACHE_TTL_SECONDS: int = int(os.getenv("REDIS_CACHE_TTL") or os.getenv("REDIS_CACHE_TTL_SECONDS", "3600"))

    # Cassandra Settings
    CASSANDRA_HOSTS: List[str] = field(
        default_factory=lambda: [
            h.strip()
            for h in (os.getenv("CASSANDRA_HOST") or os.getenv("CASSANDRA_HOSTS", "127.0.0.1")).split(",")
            if h.strip()
        ]
    )
    CASSANDRA_PORT: int = int(os.getenv("CASSANDRA_PORT", "9042"))
    CASSANDRA_KEYSPACE: str = os.getenv("CASSANDRA_KEYSPACE", "business_analytics")
    CASSANDRA_USERNAME: str = os.getenv("CASSANDRA_USERNAME", "")
    CASSANDRA_PASSWORD: str = os.getenv("CASSANDRA_PASSWORD", "")

    # Neo4j Settings
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "superstore_password_123")


# Singleton instance
settings = Settings()
