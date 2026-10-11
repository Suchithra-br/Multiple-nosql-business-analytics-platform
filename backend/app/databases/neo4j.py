"""
Neo4j Graph Database Connection Helper.

Manages Neo4j GraphDatabase Driver lifecycle with environment-driven
configuration and resilient retry/readiness diagnostics.
"""

import os
import time
import logging
from typing import Optional
from neo4j import GraphDatabase, Driver, Session

logger = logging.getLogger("databases.neo4j")

_driver: Optional[Driver] = None


def get_neo4j_uri() -> str:
    """Returns Neo4j Bolt connection URI from environment or default."""
    return os.getenv("NEO4J_URI", "bolt://localhost:7687")


def get_neo4j_user() -> str:
    """Returns Neo4j username from environment or 'neo4j'."""
    return os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", "neo4j")


def get_neo4j_password() -> str:
    """Returns Neo4j password from environment or 'password123'."""
    return os.getenv("NEO4J_PASSWORD", "password123")


def get_neo4j_database() -> str:
    """Returns target Neo4j database name from environment or 'neo4j'."""
    return os.getenv("NEO4J_DATABASE", "neo4j")


def get_neo4j_driver(max_connection_lifetime: int = 3600) -> Driver:
    """
    Returns a singleton neo4j.Driver instance.
    """
    global _driver
    if _driver is None:
        uri = get_neo4j_uri()
        user = get_neo4j_user()
        password = get_neo4j_password()
        logger.info(f"Connecting to Neo4j at: {uri} as user: '{user}'")
        _driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_lifetime=max_connection_lifetime,
        )
    return _driver


def get_neo4j_session() -> Session:
    """Returns a new Neo4j Session bound to the configured database."""
    driver = get_neo4j_driver()
    db_name = get_neo4j_database()
    return driver.session(database=db_name)


def check_neo4j_connection(max_retries: int = 3, retry_delay_s: float = 2.0) -> tuple[bool, str]:
    """
    Checks if Neo4j is ready and accepting Bolt/Cypher queries.
    Implements a readiness retry loop for Docker container startup.
    
    Returns:
        tuple[bool, str]: (is_connected, message)
    """
    uri = get_neo4j_uri()
    user = get_neo4j_user()

    for attempt in range(1, max_retries + 1):
        try:
            driver = get_neo4j_driver()
            driver.verify_connectivity()
            with driver.session(database=get_neo4j_database()) as session:
                result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions").single()
                v_name = result["name"] if result else "Neo4j"
                versions = result["versions"] if result else ["unknown"]
                v_str = versions[0] if versions else "unknown"
                msg = f"Neo4j connection successful ({v_name} Version: {v_str} via {uri})"
                logger.info(msg)
                return True, msg
        except Exception as err:
            logger.warning(f"Neo4j connection attempt {attempt}/{max_retries} failed: {err}")
            if attempt < max_retries:
                time.sleep(retry_delay_s)

    actionable_msg = (
        f"Neo4j connection failed at {uri} for user '{user}'.\n"
        "Actionable remedy:\n"
        "1. Verify that the Neo4j Docker container is running and healthy:\n"
        "   docker compose ps neo4j\n"
        "2. Inspect Neo4j logs:\n"
        "   docker logs analytics-neo4j --tail 20\n"
        "3. Confirm NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in .env."
    )
    logger.error(actionable_msg)
    return False, actionable_msg


def close_neo4j_connection():
    """Safely shuts down the Neo4j driver connection."""
    global _driver
    if _driver is not None:
        logger.info("Closing Neo4j driver.")
        try:
            _driver.close()
        except Exception:
            pass
        _driver = None
