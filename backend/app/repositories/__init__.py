"""Data access repositories for MongoDB, Redis, Cassandra, and Neo4j"""

from backend.app.repositories.mongodb_repository import (
    build_order_documents,
    build_customer_documents,
    build_product_documents,
    build_location_documents,
    create_indexes,
    load_all_collections,
    validate_mongodb_data,
    MongoDBAnalytics,
)
from backend.app.repositories.redis_repository import (
    refresh_analytics_cache,
    get_cached_kpis,
    get_cached_sales_by_region,
    get_cached_sales_by_category,
    get_cached_sales_by_segment,
    get_cached_shipping_summary,
    get_cached_monthly_sales,
    get_cached_top_products,
    get_cached_top_customers,
    ALL_DASHBOARD_KEYS,
)
from backend.app.repositories.cassandra_repository import (
    initialize_cassandra_schema,
    load_cassandra_data,
    validate_cassandra_data,
    CassandraAnalytics,
    KEYSPACE_NAME,
)
from backend.app.repositories.neo4j_repository import (
    initialize_neo4j_schema,
    load_neo4j_data,
    validate_neo4j_data,
    Neo4jAnalytics,
)

__all__ = [
    "build_order_documents",
    "build_customer_documents",
    "build_product_documents",
    "build_location_documents",
    "create_indexes",
    "load_all_collections",
    "validate_mongodb_data",
    "MongoDBAnalytics",
    "refresh_analytics_cache",
    "get_cached_kpis",
    "get_cached_sales_by_region",
    "get_cached_sales_by_category",
    "get_cached_sales_by_segment",
    "get_cached_shipping_summary",
    "get_cached_monthly_sales",
    "get_cached_top_products",
    "get_cached_top_customers",
    "ALL_DASHBOARD_KEYS",
    "initialize_cassandra_schema",
    "load_cassandra_data",
    "validate_cassandra_data",
    "CassandraAnalytics",
    "KEYSPACE_NAME",
    "initialize_neo4j_schema",
    "load_neo4j_data",
    "validate_neo4j_data",
    "Neo4jAnalytics",
]
