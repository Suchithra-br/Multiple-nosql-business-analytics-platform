"""
Graph Service Layer.

Orchestrates Neo4j property graph traversals for customer order paths,
product purchase affinities, collaborative co-purchasing ("frequently bought together"),
and multi-hop regional taxonomy hierarchies.
"""

from backend.app.core.exceptions import ResourceNotFoundError, ValidationError
from backend.app.databases.neo4j import get_neo4j_driver
from backend.app.repositories.neo4j_repository import Neo4jAnalytics
from backend.app.models.schemas import (
    GraphOrderItem,
    GraphCustomerProductItem,
    CoPurchaseItem,
    RegionCategoryGraphItem,
)

VALID_REGIONS = {"West", "East", "Central", "South"}


class GraphService:
    """Encapsulates graph database querying and validation."""

    @staticmethod
    def verify_customer_exists(driver, customer_id: str) -> None:
        """Verifies customer node presence in Neo4j; raises 404 if absent."""
        with driver.session() as session:
            record = session.run(
                "MATCH (c:Customer {customer_id: $id}) RETURN c.customer_id AS id",
                id=customer_id,
            ).single()
            if not record:
                raise ResourceNotFoundError(
                    message=f"Customer '{customer_id}' not found in graph database"
                )

    @staticmethod
    def verify_product_exists(driver, product_id: str) -> None:
        """Verifies product node presence in Neo4j; raises 404 if absent."""
        with driver.session() as session:
            record = session.run(
                "MATCH (p:Product {product_id: $id}) RETURN p.product_id AS id",
                id=product_id,
            ).single()
            if not record:
                raise ResourceNotFoundError(
                    message=f"Product '{product_id}' not found in graph database"
                )

    @classmethod
    def get_customer_orders(cls, customer_id: str) -> list[GraphOrderItem]:
        """Traverses (Customer)-[:PLACED]->(Order) path in Neo4j."""
        driver = get_neo4j_driver()
        cls.verify_customer_exists(driver, customer_id)
        analytics = Neo4jAnalytics(driver)
        results = analytics.get_customer_orders(customer_id)
        return [GraphOrderItem(**r) for r in results]

    @classmethod
    def get_customer_products(cls, customer_id: str) -> list[GraphCustomerProductItem]:
        """Traverses (Customer)-[:PLACED]->(:Order)-[:CONTAINS]->(Product) path in Neo4j."""
        driver = get_neo4j_driver()
        cls.verify_customer_exists(driver, customer_id)
        analytics = Neo4jAnalytics(driver)
        results = analytics.get_customer_products(customer_id)
        return [GraphCustomerProductItem(**r) for r in results]

    @classmethod
    def get_product_copurchases(cls, product_id: str, limit: int = 10) -> list[CoPurchaseItem]:
        """Traverses (p1:Product)<-[:CONTAINS]-(o:Order)-[:CONTAINS]->(p2:Product) path in Neo4j."""
        driver = get_neo4j_driver()
        cls.verify_product_exists(driver, product_id)
        analytics = Neo4jAnalytics(driver)
        results = analytics.get_product_co_purchases(product_id, limit=limit)
        return [CoPurchaseItem(**r) for r in results]

    @classmethod
    def get_region_categories(cls, region: str) -> list[RegionCategoryGraphItem]:
        """Traverses complete 6-hop graph hierarchy for regional category analytics."""
        if region not in VALID_REGIONS:
            raise ValidationError(
                message=f"Invalid region: '{region}'. Supported regions: {sorted(list(VALID_REGIONS))}."
            )
        driver = get_neo4j_driver()
        analytics = Neo4jAnalytics(driver)
        results = analytics.get_category_sales_by_region(region)
        return [RegionCategoryGraphItem(**r) for r in results]
