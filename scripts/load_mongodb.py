"""
MongoDB Loader & Demonstration Script.

Loads generated Phase 1 CSV datasets into the 'business_analytics' MongoDB database,
validates document counts, ensures sales reconciliation, and executes the 8 required
analytical demonstration queries.

Usage:
    python scripts/load_mongodb.py
"""

import sys
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.databases.mongodb import (
    get_mongodb_database,
    check_mongodb_connection,
    close_mongodb_connection,
)
from backend.app.repositories.mongodb_repository import (
    load_all_collections,
    validate_mongodb_data,
    MongoDBAnalytics,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scripts.load_mongodb")


def main():
    logger.info("=" * 70)
    logger.info("PHASE 2: MONGODB DATABASE IMPLEMENTATION & DATA INGESTION")
    logger.info("=" * 70)

    # 1. Connectivity Check
    is_connected, msg = check_mongodb_connection()
    if not is_connected:
        print("\n" + "=" * 70)
        print("ERROR: Could not connect to MongoDB.")
        print(msg)
        print("=" * 70 + "\n")
        sys.exit(1)

    db = get_mongodb_database()
    logger.info(f"Target Database: {db.name}")

    generated_dir = project_root / "generated_data"
    if not generated_dir.exists():
        logger.error(f"Generated data directory not found at: {generated_dir}. Run Phase 1 ETL first.")
        sys.exit(1)

    # 2. Ingest Data
    logger.info("--- Step 1: Loading Collections ---")
    counts = load_all_collections(db, generated_dir)
    print(f"\n[1] Document Counts Loaded: {counts}")

    # 3. Post-load Validation
    logger.info("--- Step 2: Validating Document Counts & Sales Totals ---")
    val_report = validate_mongodb_data(db)
    print("\n[2] MongoDB Validation Report:")
    for k, v in val_report.items():
        print(f"    - {k}: {v}")

    # 4. Verify Idempotency (run loading a second time)
    logger.info("--- Step 3: Verifying Idempotent Reloading ---")
    counts_reloaded = load_all_collections(db, generated_dir)
    for col, count in counts_reloaded.items():
        assert count == counts[col], f"Idempotency failed for {col}: expected {counts[col]}, got {count}"
    print(f"\n[3] Idempotency Verified: Re-running load produced identical counts: {counts_reloaded}")

    # 5. Demonstration Queries
    logger.info("--- Step 4: Executing 8 Required MongoDB Query Demonstrations ---")
    analytics = MongoDBAnalytics(db)

    print("\n" + "=" * 70)
    print("MONGODB ANALYTICAL QUERY DEMONSTRATIONS")
    print("=" * 70)

    # Query 1: Total sales
    q1 = analytics.get_total_sales()
    print(f"\n[Query 1: Total Sales & Orders Overview]\n{q1}")

    # Query 2: Sales by region
    q2 = analytics.get_sales_by_region()
    print("\n[Query 2: Sales by Region]")
    for r in q2:
        print(f"  {r['region']:<10}: ${r['total_sales']:>12,.2f} ({r['order_count']} orders)")

    # Query 3: Sales by category
    q3 = analytics.get_sales_by_category()
    print("\n[Query 3: Sales by Category]")
    for c in q3:
        print(f"  {c['category']:<16}: ${c['total_sales']:>12,.2f} ({c['item_count']} items)")

    # Query 4: Sales by customer segment
    q4 = analytics.get_sales_by_segment()
    print("\n[Query 4: Sales by Customer Segment]")
    for s in q4:
        print(f"  {s['segment']:<14}: ${s['total_sales']:>12,.2f} ({s['order_count']} orders)")

    # Query 5: Monthly sales sample (2018)
    q5 = analytics.get_monthly_sales(year=2018)
    print("\n[Query 5: Monthly Sales Trend (Sample Year 2018)]")
    for m in q5:
        print(f"  {m['year_month']}: ${m['total_sales']:>10,.2f} ({m['order_count']} orders)")

    # Query 6: Top 10 products by sales
    q6 = analytics.get_top_products_by_sales(limit=10)
    print("\n[Query 6: Top 10 Products by Sales Volume]")
    for i, p in enumerate(q6, 1):
        print(f"  {i:>2}. [{p['product_id']}] {p['product_name'][:45]:<45} : ${p['total_sales']:>10,.2f}")

    # Query 7: Top 10 customers by spend
    q7 = analytics.get_top_customers_by_spend(limit=10)
    print("\n[Query 7: Top 10 Customers by Lifetime Spend]")
    for i, c in enumerate(q7, 1):
        print(f"  {i:>2}. [{c['customer_id']}] {c['customer_name']:<22} ({c['primary_region']:<7}) : ${c['total_spend']:>10,.2f} in {c['order_count']} orders")

    # Query 8: Order count by shipping mode
    q8 = analytics.get_order_count_by_ship_mode()
    print("\n[Query 8: Orders Breakdown by Shipping Mode]")
    for sm in q8:
        print(f"  {sm['ship_mode']:<16}: {sm['order_count']:>5} orders (${sm['total_sales']:>12,.2f})")

    print("\n" + "=" * 70)
    print("PHASE 2 MONGODB INGESTION & QUERY VALIDATION COMPLETED SUCCESSFULLY")
    print("=" * 70)

    close_mongodb_connection()


if __name__ == "__main__":
    main()
