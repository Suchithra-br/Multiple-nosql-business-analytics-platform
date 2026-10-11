"""
Cassandra Database Connection Helper.

Manages cassandra-driver Cluster and Session lifecycles with environment-driven
configuration and resilient retry/readiness diagnostics.
"""

import os
import time
import logging
from typing import Optional
from cassandra.cluster import Cluster, Session
from cassandra.auth import PlainTextAuthProvider

logger = logging.getLogger("databases.cassandra")

_cluster: Optional[Cluster] = None
_session: Optional[Session] = None


def get_cassandra_hosts() -> list[str]:
    """Returns list of Cassandra host addresses from environment or ['127.0.0.1']."""
    raw = os.getenv("CASSANDRA_HOST") or os.getenv("CASSANDRA_HOSTS", "127.0.0.1")
    return [h.strip() for h in raw.split(",") if h.strip()]


def get_cassandra_port() -> int:
    """Returns Cassandra CQL native transport port from environment or 9042."""
    try:
        return int(os.getenv("CASSANDRA_PORT", "9042"))
    except ValueError:
        return 9042


def get_cassandra_keyspace() -> str:
    """Returns target Cassandra keyspace name from environment or 'business_analytics'."""
    return os.getenv("CASSANDRA_KEYSPACE", "business_analytics")


KEYSPACE_NAME = get_cassandra_keyspace()


def get_cassandra_cluster(connect_timeout: float = 10.0) -> Cluster:
    """Returns singleton cassandra.cluster.Cluster instance."""
    global _cluster
    if _cluster is None or _cluster.is_shutdown:
        hosts = get_cassandra_hosts()
        port = get_cassandra_port()
        username = os.getenv("CASSANDRA_USERNAME", "").strip()
        password = os.getenv("CASSANDRA_PASSWORD", "").strip()

        auth_provider = None
        if username and password:
            auth_provider = PlainTextAuthProvider(username=username, password=password)

        logger.info(f"Connecting to Cassandra cluster at: {hosts}:{port}")
        _cluster = Cluster(
            contact_points=hosts,
            port=port,
            auth_provider=auth_provider,
            protocol_version=5,
            connect_timeout=connect_timeout,
            control_connection_timeout=connect_timeout,
        )
    return _cluster


def get_cassandra_session(keyspace: Optional[str] = None) -> Session:
    """
    Returns an active Cassandra Session, optionally connected to a specific keyspace.
    """
    global _session
    cluster = get_cassandra_cluster()
    target_keyspace = keyspace or get_cassandra_keyspace()

    if _session is None or _session.is_shutdown:
        logger.info(f"Establishing Cassandra session...")
        _session = cluster.connect()

    if target_keyspace:
        try:
            _session.set_keyspace(target_keyspace)
        except Exception:
            # Keyspace might not be created yet during initialization
            pass

    return _session


def check_cassandra_connection(max_retries: int = 3, retry_delay_s: float = 2.0) -> tuple[bool, str]:
    """
    Checks if Cassandra is ready and accepting CQL queries.
    Implements a readiness retry loop for Docker container startup.
    
    Returns:
        tuple[bool, str]: (is_connected, message)
    """
    hosts = get_cassandra_hosts()
    port = get_cassandra_port()

    for attempt in range(1, max_retries + 1):
        try:
            session = get_cassandra_session()
            row = session.execute("SELECT cluster_name, release_version FROM system.local").one()
            c_name = row.cluster_name if row else "unknown"
            r_ver = row.release_version if row else "unknown"
            msg = f"Cassandra CQL connection successful (Cluster: '{c_name}', Version: {r_ver})"
            logger.info(msg)
            return True, msg
        except Exception as err:
            logger.warning(f"Cassandra connection attempt {attempt}/{max_retries} failed: {err}")
            if attempt < max_retries:
                time.sleep(retry_delay_s)

    actionable_msg = (
        f"Cassandra connection failed at {hosts}:{port}.\n"
        "Actionable remedy:\n"
        "1. Verify that the Cassandra Docker container is running and healthy:\n"
        "   docker compose ps cassandra\n"
        "2. If starting up, wait 30 seconds for Cassandra to complete ring joining:\n"
        "   docker logs analytics-cassandra --tail 20\n"
        "3. Confirm CASSANDRA_HOSTS and CASSANDRA_PORT in .env."
    )
    logger.error(actionable_msg)
    return False, actionable_msg


def close_cassandra_connection():
    """Safely shuts down Cassandra session and cluster connections."""
    global _session, _cluster
    if _session is not None and not _session.is_shutdown:
        logger.info("Closing Cassandra session.")
        try:
            _session.shutdown()
        except Exception:
            pass
        _session = None

    if _cluster is not None and not _cluster.is_shutdown:
        logger.info("Shutting down Cassandra cluster.")
        try:
            _cluster.shutdown()
        except Exception:
            pass
        _cluster = None
