"""
MongoDB Database Connection Helper.

Manages MongoClient lifecycle with environment-driven configuration
and clear, actionable error reporting.
"""

import os
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger("databases.mongodb")

_client: Optional[MongoClient] = None


def get_mongodb_uri() -> str:
    """Returns MongoDB connection URI from environment or default local URI."""
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017")


def get_mongodb_database_name() -> str:
    """Returns MongoDB database name from environment or default 'business_analytics'."""
    return os.getenv("MONGODB_DATABASE", "business_analytics")


def get_mongodb_client(timeout_ms: int = 3000) -> MongoClient:
    """
    Returns a singleton MongoClient instance.
    
    Args:
        timeout_ms: Server selection timeout in milliseconds.
    """
    global _client
    if _client is None:
        uri = get_mongodb_uri()
        logger.info(f"Connecting to MongoDB at: {uri}")
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=timeout_ms,
            connectTimeoutMS=timeout_ms,
        )
    return _client


def get_mongodb_database(db_name: Optional[str] = None) -> Database:
    """
    Returns the target MongoDB database.
    
    Args:
        db_name: Optional database name override.
    """
    client = get_mongodb_client()
    target_name = db_name or get_mongodb_database_name()
    return client[target_name]


def check_mongodb_connection(timeout_ms: int = 3000) -> tuple[bool, str]:
    """
    Pings the MongoDB server to verify connectivity.
    
    Returns:
        tuple[bool, str]: (is_connected, message)
    """
    try:
        client = get_mongodb_client(timeout_ms=timeout_ms)
        client.admin.command("ping")
        server_info = client.server_info()
        version = server_info.get("version", "unknown")
        msg = f"MongoDB connection successful (Server version: {version})"
        logger.info(msg)
        return True, msg
    except (ConnectionFailure, ServerSelectionTimeoutError) as err:
        uri = get_mongodb_uri()
        msg = (
            f"MongoDB connection failed at {uri}.\n"
            "Actionable remedy:\n"
            "1. Verify that MongoDB is running locally or start the Docker container:\n"
            "   docker start analytics-mongodb\n"
            "   (or run: docker run -d -p 27017:27017 --name mongodb mongo:latest)\n"
            "2. Confirm the MONGODB_URI in your environment or .env file.\n"
            f"Details: {err}"
        )
        logger.error(msg)
        return False, msg
    except Exception as err:
        msg = f"Unexpected error connecting to MongoDB: {err}"
        logger.error(msg)
        return False, msg


def close_mongodb_connection():
    """Safely closes the MongoClient singleton."""
    global _client
    if _client is not None:
        logger.info("Closing MongoDB client connection.")
        _client.close()
        _client = None
