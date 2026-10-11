"""Database connection clients and pool managers"""

from backend.app.databases.mongodb import (
    get_mongodb_client,
    get_mongodb_database,
    check_mongodb_connection,
    close_mongodb_connection,
)
from backend.app.databases.redis import (
    get_redis_client,
    get_redis_ttl,
    check_redis_connection,
    close_redis_connection,
)
from backend.app.databases.cassandra import (
    get_cassandra_cluster,
    get_cassandra_session,
    get_cassandra_keyspace,
    check_cassandra_connection,
    close_cassandra_connection,
)
from backend.app.databases.neo4j import (
    get_neo4j_driver,
    get_neo4j_session,
    check_neo4j_connection,
    close_neo4j_connection,
)

__all__ = [
    "get_mongodb_client",
    "get_mongodb_database",
    "check_mongodb_connection",
    "close_mongodb_connection",
    "get_redis_client",
    "get_redis_ttl",
    "check_redis_connection",
    "close_redis_connection",
    "get_cassandra_cluster",
    "get_cassandra_session",
    "get_cassandra_keyspace",
    "check_cassandra_connection",
    "close_cassandra_connection",
    "get_neo4j_driver",
    "get_neo4j_session",
    "check_neo4j_connection",
    "close_neo4j_connection",
]
