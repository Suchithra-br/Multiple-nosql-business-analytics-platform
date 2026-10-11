"""
Phase 5 CLI Script: Load and Validate Neo4j Graph Database.

Executes:
1. Connection and readiness check to Neo4j Docker container.
2. Uniqueness constraint initialization.
3. Idempotent bulk graph ingestion (nodes & relationships).
4. Full node count, relationship count, and sales reconciliation.
5. Repeat loading verification (idempotency check).
6. Execution of the 6 required graph analytics Cypher queries.
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scripts.load_neo4j")

# Ensure repository root is on sys.path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.databases.neo4j import (
    get_neo4j_driver,
    check_neo4j_connection,
    close_neo4j_connection,
)
from backend.app.repositories.neo4j_repository import (
    initialize_neo4j_schema,
    load_neo4j_data,
    validate_neo4j_data,
    Neo4jAnalytics,
)


def main():
    logger.info("=" * 70)
    logger.info("PHASE 5: NEO4J GRAPH DATABASE INTEGRATION & ANALYTICS")
    logger.info("=" * 70)

    # 1. Connectivity Check
    is_ready, conn_msg = check_neo4j_connection(max_retries=5, retry_delay_s=2.0)
    if not is_ready:
        logger.error(f"Cannot proceed with Neo4j ingestion:\n{conn_msg}")
        sys.exit(1)

    driver = get_neo4j_driver()

    cleaned_csv = project_root / "generated_data" / "cleaned_sales.csv"
    products_csv = project_root / "generated_data" / "products.csv"

    if not cleaned_csv.exists():
        logger.error(f"Required data file missing: {cleaned_csv}")
        sys.exit(1)

    # 2. Initial Ingestion
    logger.info("\n--- Step 1: Loading Nodes and Relationships into Neo4j ---")
    val_report = load_neo4j_data(
        driver=driver,
        cleaned_sales_csv_path=cleaned_csv,
        products_csv_path=products_csv,
        batch_size=1000,
    )

    # 3. Idempotency Check
    logger.info("\n--- Step 2: Testing Repeat Loading Idempotency ---")
    val_report_2 = load_neo4j_data(
        driver=driver,
        cleaned_sales_csv_path=cleaned_csv,
        products_csv_path=products_csv,
        batch_size=1000,
    )

    # Verify identical counts
    assert val_report["node_counts"] == val_report_2["node_counts"], "Node counts differed after repeat load!"
    assert val_report["relationship_counts"] == val_report_2["relationship_counts"], "Relationship counts differed after repeat load!"
    assert val_report["total_sales"] == val_report_2["total_sales"], "Total sales differed after repeat load!"
    logger.info("Idempotency VERIFIED: Repeat load produced identical node and relationship counts with 0 duplicates.")

    # 4. Run Demonstration Cypher Queries
    logger.info("\n--- Step 3: Demonstrating 6 Required Graph Queries ---")
    analytics = Neo4jAnalytics(driver)

    print("\n" + "=" * 70)
    print("NEO4J GRAPH ANALYTICS DEMONSTRATIONS")
    print("=" * 70)

    # Query 1: Customer -> Orders
    test_cust = "CG-12520"
    cust_orders = analytics.get_customer_orders(test_cust)
    print(f"\n[Query 1: Orders placed by Customer '{test_cust}'] (Found {len(cust_orders)} orders)")
    for o in cust_orders[:3]:
        print(f"  Order: {o['order_id']} | Date: {o['order_date']} | Mode: {o['ship_mode']}")

    # Query 2: Customer -> Products
    cust_products = analytics.get_customer_products(test_cust)
    print(f"\n[Query 2: Products purchased by Customer '{test_cust}'] (Found {len(cust_products)} distinct products)")
    for p in cust_products[:3]:
        print(f"  Product: {p['product_id']} | Spend: ${p['total_spent']:>8,.2f} | Purchased: {p['purchase_count']} times | {p['product_name'][:40]}")

    # Query 3: Product co-purchase
    test_prod = "FUR-BO-10001798"
    co_purchases = analytics.get_product_co_purchases(test_prod, limit=5)
    print(f"\n[Query 3: Products frequently co-purchased with '{test_prod}']")
    for cp in co_purchases:
        print(f"  Co-purchased {cp['times_co_purchased']} times | {cp['product_id']} | {cp['product_name'][:45]}")

    # Query 4: Category by Region
    test_region = "West"
    cat_sales = analytics.get_category_sales_by_region(test_region)
    print(f"\n[Query 4: Category Sales Breakdown in Region '{test_region}']")
    for cs in cat_sales:
        print(f"  Category: {cs['category']:<16} | Items: {cs['item_count']:>5} | Sales: ${cs['total_sales']:>10,.2f}")

    # Query 5: Customer Category Affinity
    cat_affinity = analytics.get_customer_category_affinity(test_cust)
    print(f"\n[Query 5: Category Affinity for Customer '{test_cust}']")
    for ca in cat_affinity:
        print(f"  Category: {ca['category']:<16} | Items: {ca['items_purchased']:>3} | Spend: ${ca['total_spent']:>8,.2f}")

    # Query 6: Regional Product Relationships
    reg_products = analytics.get_regional_products("East", limit=5)
    print(f"\n[Query 6: Top Products in Region 'East']")
    for rp in reg_products:
        print(f"  Product: {rp['product_id']} | Sales: ${rp['total_sales']:>8,.2f} | Items: {rp['purchase_count']} | {rp['product_name'][:40]}")

    print("\n" + "=" * 70)
    print("NEO4J INGESTION & VALIDATION REPORT")
    print("=" * 70)
    print(f"Status: {val_report['status']}")
    print(f"Total Reconciled Sales: ${val_report['total_sales']:,.4f}")
    print("\nNode Counts by Label:")
    for label, count in val_report["node_counts"].items():
        print(f"  - {label:<14}: {count:>6,}")
    print("\nRelationship Counts by Type:")
    for rtype, count in val_report["relationship_counts"].items():
        print(f"  - {rtype:<14}: {count:>6,}")
    print("=" * 70)

    close_neo4j_connection()
    logger.info("Neo4j loading process completed successfully.")


if __name__ == "__main__":
    main()
