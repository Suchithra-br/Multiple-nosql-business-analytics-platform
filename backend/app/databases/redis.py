"""
Redis Database Connection Helper.

Manages redis.Redis client lifecycle with environment-driven configuration
and clear, actionable error reporting.
"""

import os
import logging
from typing import Optional
import redis

logger = logging.getLogger("databases.redis")

_client: Optional[redis.Redis] = None


def get_redis_host() -> str:
    """Returns Redis host from environment or default 'localhost'."""
    return os.getenv("REDIS_HOST", "localhost")


def get_redis_port() -> int:
    """Returns Redis port from environment or default 6379."""
    try:
        return int(os.getenv("REDIS_PORT", "6379"))
    except ValueError:
        return 6379


def get_redis_password() -> Optional[str]:
    """Returns Redis password from environment if set."""
    pwd = os.getenv("REDIS_PASSWORD", "").strip()
    return pwd if pwd else None


def get_redis_db() -> int:
    """Returns Redis DB index from environment or default 0."""
    try:
        return int(os.getenv("REDIS_DB", "0"))
    except ValueError:
        return 0


def get_redis_ttl() -> int:
    """Returns Redis cache TTL in seconds from environment or default 3600."""
    ttl_val = os.getenv("REDIS_CACHE_TTL") or os.getenv("REDIS_CACHE_TTL_SECONDS") or "3600"
    try:
        return int(ttl_val)
    except ValueError:
        return 3600


def get_redis_client(timeout_s: float = 3.0) -> redis.Redis:
    """
    Returns a singleton redis.Redis instance configured with string decoding.
    
    Args:
        timeout_s: Connection timeout in seconds.
    """
    global _client
    if _client is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            logger.info("Connecting to Redis via REDIS_URL")
            _client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=timeout_s,
                socket_connect_timeout=timeout_s,
            )
        else:
            host = get_redis_host()
            port = get_redis_port()
            pwd = get_redis_password()
            db = get_redis_db()
            logger.info(f"Connecting to Redis at: {host}:{port} (db={db})")
            _client = redis.Redis(
                host=host,
                port=port,
                password=pwd,
                db=db,
                decode_responses=True,
                socket_timeout=timeout_s,
                socket_connect_timeout=timeout_s,
            )
    return _client


def check_redis_connection(timeout_s: float = 3.0) -> tuple[bool, str]:
    """
    Pings the Redis server to verify connectivity.
    
    Returns:
        tuple[bool, str]: (is_connected, message)
    """
    try:
        client = get_redis_client(timeout_s=timeout_s)
        client.ping()
        info = client.info()
        version = info.get("redis_version", "unknown")
        msg = f"Redis connection successful (Server version: {version})"
        logger.info(msg)
        return True, msg
    except (redis.ConnectionError, redis.TimeoutError) as err:
        host = get_redis_host()
        port = get_redis_port()
        msg = (
            f"Redis connection failed at {host}:{port}.\n"
            "Actionable remedy:\n"
            "1. Verify that Redis is running via Docker Compose:\n"
            "   docker compose up -d\n"
            "2. Confirm REDIS_HOST and REDIS_PORT in your environment or .env file.\n"
            f"Details: {err}"
        )
        logger.error(msg)
        return False, msg
    except Exception as err:
        msg = f"Unexpected error connecting to Redis: {err}"
        logger.error(msg)
        return False, msg


def close_redis_connection():
    """Safely closes the Redis client singleton."""
    global _client
    if _client is not None:
        logger.info("Closing Redis client connection.")
        try:
            _client.close()
        except Exception:
            pass
        _client = None
