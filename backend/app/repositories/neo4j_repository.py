"""
Neo4j Graph Repository & Graph Analytics Module.

Handles:
1. Graph schema constraint and index creation.
2. Fast, idempotent node and relationship ingestion from Phase 1 data using Cypher MERGE.
3. Graph analytical queries (co-purchasing, customer-product graphs, regional category breakdowns).
4. Graph metrics, node/relationship counts, and sales reconciliation against Phase 1 benchmarks.
"""

import logging
from pathlib import Path
from typing import Any, Optional
import pandas as pd
from neo4j import Driver, Session

logger = logging.getLogger("repositories.neo4j")


# ==============================================================================
# Constraint & Index Management
# ==============================================================================

CONSTRAINTS = [
    "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE;",
    "CREATE CONSTRAINT order_id_unique IF NOT EXISTS FOR (o:Order) REQUIRE o.order_id IS UNIQUE;",
    "CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE;",
    "CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (cat:Category) REQUIRE cat.category IS UNIQUE;",
    "CREATE CONSTRAINT subcategory_name_unique IF NOT EXISTS FOR (sub:SubCategory) REQUIRE sub.sub_category IS UNIQUE;",
    "CREATE CONSTRAINT state_name_unique IF NOT EXISTS FOR (s:State) REQUIRE s.state IS UNIQUE;",
    "CREATE CONSTRAINT region_name_unique IF NOT EXISTS FOR (r:Region) REQUIRE r.region IS UNIQUE;",
]

INDEXES = [
    "CREATE INDEX city_name_idx IF NOT EXISTS FOR (c:City) ON (c.city);",
]


def initialize_neo4j_schema(driver: Driver, database: Optional[str] = None):
    """Creates uniqueness constraints and indexes on graph nodes."""
    logger.info("Initializing Neo4j graph constraints and indexes...")
    with driver.session(database=database) as session:
        for cql in CONSTRAINTS:
            session.run(cql)
        for cql in INDEXES:
            session.run(cql)
    logger.info("Neo4j schema constraints initialized successfully.")


# ==============================================================================
# Idempotent Data Ingestion
# ==============================================================================

def load_neo4j_data(
    driver: Driver,
    cleaned_sales_csv_path: str | Path,
    products_csv_path: Optional[str | Path] = None,
    database: Optional[str] = None,
    batch_size: int = 1000,
) -> dict[str, Any]:
    """
    Loads nodes and relationships from Phase 1 generated data into Neo4j.
    Uses parameterized Cypher MERGE queries to guarantee 100% idempotency.
    
    Returns:
        dict: Ingestion summary containing node and relationship counts.
    """
    csv_path = Path(cleaned_sales_csv_path).resolve()
    logger.info(f"Loading graph data into Neo4j from: {csv_path}")

    # Ensure schema constraints exist before bulk loading
    initialize_neo4j_schema(driver, database=database)

    df = pd.read_csv(csv_path)
    logger.info(f"Read {len(df)} transaction records from {csv_path.name}")

    # Determine canonical product names from products.csv if available
    prod_canonical_map = {}
    if products_csv_path:
        prod_path = Path(products_csv_path).resolve()
        if prod_path.exists():
            prod_df = pd.read_csv(prod_path)
            prod_canonical_map = dict(zip(prod_df["product_id"], prod_df["product_name"]))
            logger.info(f"Loaded {len(prod_canonical_map)} canonical product names from products.csv")

    with driver.session(database=database) as session:
        # 1. Categories & Sub-Categories
        logger.info("Creating Category and SubCategory nodes and BELONGS_TO relationships...")
        cat_subcat_pairs = df[["category", "sub_category"]].drop_duplicates().to_dict(orient="records")
        session.run(
            """
            UNWIND $batch AS row
            MERGE (cat:Category {category: row.category})
            MERGE (sub:SubCategory {sub_category: row.sub_category})
            MERGE (sub)-[:BELONGS_TO]->(cat)
            """,
            batch=cat_subcat_pairs,
        )

        # 2. Geographic Hierarchy: Region -> State -> City
        logger.info("Creating Region, State, City nodes and hierarchy relationships...")
        geo_records = df[["region", "state", "city"]].drop_duplicates().to_dict(orient="records")
        session.run(
            """
            UNWIND $batch AS row
            MERGE (r:Region {region: row.region})
            MERGE (s:State {state: row.state})
            MERGE (s)-[:IN_REGION]->(r)
            MERGE (c:City {city: row.city, state: row.state})
            MERGE (c)-[:IN_STATE]->(s)
            """,
            batch=geo_records,
        )

        # 3. Customer nodes
        logger.info("Creating Customer nodes...")
        cust_records = df[["customer_id", "customer_name", "segment"]].drop_duplicates("customer_id").to_dict(orient="records")
        for i in range(0, len(cust_records), batch_size):
            batch = cust_records[i : i + batch_size]
            session.run(
                """
                UNWIND $batch AS row
                MERGE (c:Customer {customer_id: row.customer_id})
                ON CREATE SET c.customer_name = row.customer_name, c.segment = row.segment
                ON MATCH SET c.customer_name = row.customer_name, c.segment = row.segment
                """,
                batch=batch,
            )

        # 4. Product nodes (using canonical product name for the 32 variants)
        logger.info("Creating Product nodes and BELONGS_TO SubCategory relationships...")
        prod_unique = df[["product_id", "sub_category"]].drop_duplicates("product_id")
        prod_records = []
        for _, r in prod_unique.iterrows():
            pid = str(r["product_id"]).strip()
            pname = prod_canonical_map.get(pid, str(r.get("product_name", pid)))
            prod_records.append({
                "product_id": pid,
                "product_name": pname,
                "sub_category": str(r["sub_category"]).strip(),
            })

        for i in range(0, len(prod_records), batch_size):
            batch = prod_records[i : i + batch_size]
            session.run(
                """
                UNWIND $batch AS row
                MERGE (p:Product {product_id: row.product_id})
                ON CREATE SET p.product_name = row.product_name
                ON MATCH SET p.product_name = row.product_name
                WITH p, row
                MATCH (sub:SubCategory {sub_category: row.sub_category})
                MERGE (p)-[:BELONGS_TO]->(sub)
                """,
                batch=batch,
            )

        # 5. Order nodes & Customer -> Order, Order -> City relationships
        logger.info("Creating Order nodes and PLACED / SHIPPED_TO relationships...")
        order_records = df[["order_id", "order_date", "ship_mode", "customer_id", "city", "state"]].drop_duplicates("order_id").to_dict(orient="records")
        for i in range(0, len(order_records), batch_size):
            batch = order_records[i : i + batch_size]
            session.run(
                """
                UNWIND $batch AS row
                MERGE (o:Order {order_id: row.order_id})
                ON CREATE SET o.order_date = row.order_date, o.ship_mode = row.ship_mode
                ON MATCH SET o.order_date = row.order_date, o.ship_mode = row.ship_mode
                WITH o, row
                MATCH (cust:Customer {customer_id: row.customer_id})
                MERGE (cust)-[:PLACED]->(o)
                WITH o, row
                MATCH (c:City {city: row.city, state: row.state})
                MERGE (o)-[:SHIPPED_TO]->(c)
                """,
                batch=batch,
            )

        # 6. Order Items: (:Order)-[:CONTAINS {row_id, sales}]->(:Product)
        logger.info("Creating Order -> Product CONTAINS relationships with line-item sales...")
        item_records = []
        for _, r in df.iterrows():
            item_records.append({
                "row_id": int(r["row_id"]),
                "order_id": str(r["order_id"]).strip(),
                "product_id": str(r["product_id"]).strip(),
                "sales": float(r["sales"]),
            })

        for i in range(0, len(item_records), batch_size):
            batch = item_records[i : i + batch_size]
            session.run(
                """
                UNWIND $batch AS row
                MATCH (o:Order {order_id: row.order_id})
                MATCH (p:Product {product_id: row.product_id})
                MERGE (o)-[rel:CONTAINS {row_id: row.row_id}]->(p)
                SET rel.sales = row.sales
                """,
                batch=batch,
            )

    logger.info("Neo4j graph loading completed successfully.")
    return validate_neo4j_data(driver, database=database)


# ==============================================================================
# Graph Analytics Queries
# ==============================================================================

class Neo4jAnalytics:
    """Implements the 6 required relationship-driven Cypher graph queries."""

    def __init__(self, driver: Driver, database: Optional[str] = None):
        self.driver = driver
        self.database = database

    def get_customer_orders(self, customer_id: str) -> list[dict[str, Any]]:
        """
        Query 1: Customer -> Orders.
        Finds all orders placed by a selected customer.
        """
        cql = """
        MATCH (c:Customer {customer_id: $customer_id})-[:PLACED]->(o:Order)
        RETURN o.order_id AS order_id, o.order_date AS order_date, o.ship_mode AS ship_mode
        ORDER BY o.order_date DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cql, customer_id=customer_id)
            return [dict(record) for record in result]

    def get_customer_products(self, customer_id: str) -> list[dict[str, Any]]:
        """
        Query 2: Customer -> Products.
        Finds products purchased by a selected customer with spend metrics.
        """
        cql = """
        MATCH (c:Customer {customer_id: $customer_id})-[:PLACED]->(o:Order)-[r:CONTAINS]->(p:Product)
        RETURN DISTINCT p.product_id AS product_id,
                        p.product_name AS product_name,
                        count(r) AS purchase_count,
                        round(sum(r.sales), 4) AS total_spent
        ORDER BY total_spent DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cql, customer_id=customer_id)
            return [dict(record) for record in result]

    def get_product_co_purchases(self, product_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Query 3: Product co-purchase ("Frequently bought together").
        Finds products that occur in the same orders as a selected product.
        """
        cql = """
        MATCH (p1:Product {product_id: $product_id})<-[:CONTAINS]-(o:Order)-[:CONTAINS]->(p2:Product)
        WHERE p1 <> p2
        RETURN p2.product_id AS product_id,
                        p2.product_name AS product_name,
                        count(DISTINCT o) AS times_co_purchased
        ORDER BY times_co_purchased DESC, product_id ASC
        LIMIT $limit
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cql, product_id=product_id, limit=limit)
            return [dict(record) for record in result]

    def get_category_sales_by_region(self, region: str) -> list[dict[str, Any]]:
        """
        Query 4: Category by Region.
        Finds sales grouped by category for a selected region using graph traversal
        (Region <- State <- City <- Order -> Product -> SubCategory -> Category).
        """
        cql = """
        MATCH (r:Region {region: $region})<-[:IN_REGION]-(:State)<-[:IN_STATE]-(:City)<-[:SHIPPED_TO]-(o:Order)-[rel:CONTAINS]->(p:Product)-[:BELONGS_TO]->(sub:SubCategory)-[:BELONGS_TO]->(cat:Category)
        RETURN cat.category AS category,
               count(rel) AS item_count,
               round(sum(rel.sales), 4) AS total_sales
        ORDER BY total_sales DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cql, region=region)
            return [dict(record) for record in result]

    def get_customer_category_affinity(self, customer_id: str) -> list[dict[str, Any]]:
        """
        Query 5: Customer category affinity.
        Finds which categories a selected customer has purchased from.
        """
        cql = """
        MATCH (c:Customer {customer_id: $customer_id})-[:PLACED]->(o:Order)-[r:CONTAINS]->(p:Product)-[:BELONGS_TO]->(sub:SubCategory)-[:BELONGS_TO]->(cat:Category)
        RETURN cat.category AS category,
               count(r) AS items_purchased,
               round(sum(r.sales), 4) AS total_spent
        ORDER BY total_spent DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cql, customer_id=customer_id)
            return [dict(record) for record in result]

    def get_regional_products(self, region: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Query 6: Regional product relationships.
        Finds top products purchased in a selected region.
        """
        cql = """
        MATCH (r:Region {region: $region})<-[:IN_REGION]-(:State)<-[:IN_STATE]-(:City)<-[:SHIPPED_TO]-(o:Order)-[rel:CONTAINS]->(p:Product)
        RETURN p.product_id AS product_id,
               p.product_name AS product_name,
               count(rel) AS purchase_count,
               round(sum(rel.sales), 4) AS total_sales
        ORDER BY total_sales DESC
        LIMIT $limit
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(cql, region=region, limit=limit)
            return [dict(record) for record in result]


# ==============================================================================
# Validation & Reconciliation
# ==============================================================================

def validate_neo4j_data(driver: Driver, database: Optional[str] = None) -> dict[str, Any]:
    """
    Validates Neo4j node counts, relationship counts, and sales reconciliation
    against Phase 1 benchmarks ($2,261,536.7827).
    
    Raises:
        ValueError: If any validation rule fails.
    """
    logger.info("Validating Neo4j graph data against Phase 1 benchmarks...")
    with driver.session(database=database) as session:
        # 1. Node Counts
        node_counts = {}
        for label in ["Customer", "Order", "Product", "Category", "SubCategory", "City", "State", "Region"]:
            res = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt").single()
            node_counts[label] = res["cnt"] if res else 0

        # Assert key node counts
        assert node_counts["Customer"] == 793, f"Expected 793 Customer nodes, got {node_counts['Customer']}"
        assert node_counts["Order"] == 4922, f"Expected 4,922 Order nodes, got {node_counts['Order']}"
        assert node_counts["Product"] == 1861, f"Expected 1,861 Product nodes, got {node_counts['Product']}"
        assert node_counts["Category"] == 3, f"Expected 3 Category nodes, got {node_counts['Category']}"
        assert node_counts["SubCategory"] == 17, f"Expected 17 SubCategory nodes, got {node_counts['SubCategory']}"
        assert node_counts["State"] == 49, f"Expected 49 State nodes, got {node_counts['State']}"
        assert node_counts["Region"] == 4, f"Expected 4 Region nodes, got {node_counts['Region']}"
        assert node_counts["City"] == 600, f"Expected 600 City nodes, got {node_counts['City']}"

        # 2. Relationship Counts
        rel_counts = {}
        for rtype in ["PLACED", "CONTAINS", "BELONGS_TO", "SHIPPED_TO", "IN_STATE", "IN_REGION"]:
            res = session.run(f"MATCH ()-[r:{rtype}]->() RETURN count(r) AS cnt").single()
            rel_counts[rtype] = res["cnt"] if res else 0

        assert rel_counts["PLACED"] == 4922, f"Expected 4,922 PLACED rels, got {rel_counts['PLACED']}"
        assert rel_counts["CONTAINS"] == 9800, f"Expected 9,800 CONTAINS rels, got {rel_counts['CONTAINS']}"
        assert rel_counts["BELONGS_TO"] == 1878, f"Expected 1,878 BELONGS_TO rels, got {rel_counts['BELONGS_TO']}"
        assert rel_counts["SHIPPED_TO"] == 4922, f"Expected 4,922 SHIPPED_TO rels, got {rel_counts['SHIPPED_TO']}"
        assert rel_counts["IN_STATE"] == 600, f"Expected 600 IN_STATE rels, got {rel_counts['IN_STATE']}"
        assert rel_counts["IN_REGION"] == 49, f"Expected 49 IN_REGION rels, got {rel_counts['IN_REGION']}"

        # 3. Total Sales Reconciliation via CONTAINS.sales
        sales_res = session.run("MATCH ()-[r:CONTAINS]->() RETURN sum(r.sales) AS total_sales").single()
        total_sales = float(sales_res["total_sales"]) if sales_res and sales_res["total_sales"] is not None else 0.0

        expected_sales = 2261536.7827
        if abs(total_sales - expected_sales) > 1e-2:
            raise ValueError(
                f"Neo4j total sales reconciliation failed: expected ${expected_sales:.4f}, got ${total_sales:.4f}"
            )

        logger.info(f"Neo4j Validation PASSED: {node_counts['Customer']} Customers, {node_counts['Order']} Orders, {rel_counts['CONTAINS']} Line Items, ${total_sales:,.2f} Total Sales.")
        return {
            "status": "PASSED",
            "node_counts": node_counts,
            "relationship_counts": rel_counts,
            "total_sales": round(total_sales, 4),
        }
