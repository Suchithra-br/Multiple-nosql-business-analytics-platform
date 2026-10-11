"""
Redis Cache Refresh & Demonstration Script.

Pulls aggregated business analytics from the active MongoDB instance,
populates the Redis in-memory cache, verifies reconciliation, and outputs
the cached metrics via the read helper functions.

Usage:
    python scripts/refresh_redis.py
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
from backend.app.databases.redis import (
    get_redis_client,
    check_redis_connection,
    close_redis_connection,
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
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scripts.refresh_redis")


def main():
    logger.info("=" * 70)
    logger.info("PHASE 3: REDIS CACHE POPULATION & RECONCILIATION")
    logger.info("=" * 70)

    # 1. Connection Checks
    m_ok, m_msg = check_mongodb_connection()
    if not m_ok:
        print(f"\nERROR: MongoDB connection failed.\n{m_msg}\n")
        sys.exit(1)

    r_ok, r_msg = check_redis_connection()
    if not r_ok:
        print(f"\nERROR: Redis connection failed.\n{r_msg}\n")
        sys.exit(1)

    db = get_mongodb_database()
    r = get_redis_client()

    # 2. Populate Redis Cache from MongoDB
    logger.info("--- Step 1: Refreshing Redis Cache from MongoDB ---")
    rep = refresh_analytics_cache(db, r)
    print(f"\n[1] Cache Refresh Summary:\n    Status: {rep['status']}\n    Keys Updated: {rep['keys_updated']}\n    Total Sales: ${rep['total_sales']:,.4f}\n    Total Orders: {rep['total_orders']:,}\n    TTL: {rep['cache_ttl']}s")

    # 3. Verify Idempotency (run twice)
    logger.info("--- Step 2: Verifying Idempotent Cache Refresh ---")
    rep2 = refresh_analytics_cache(db, r)
    assert rep["total_sales"] == rep2["total_sales"]
    assert rep["total_orders"] == rep2["total_orders"]
    print("\n[2] Idempotency Verified: Refreshing cache a second time produced identical metrics.")

    # 4. Demonstrate Reading from Redis Cache
    logger.info("--- Step 3: Reading Cached Analytics from Redis ---")
    print("\n" + "=" * 70)
    print("CACHED ANALYTICS READ FROM REDIS")
    print("=" * 70)

    # KPIs
    kpis = get_cached_kpis(r)
    print(f"\n[Cached Overview KPIs]\n  Total Sales:         ${kpis['total_sales']:,.2f}\n  Total Orders:        {kpis['total_orders']:,}\n  Average Order Value: ${kpis['average_order_value']:,.2f}\n  Last Refreshed:      {kpis['last_refreshed_at']}")

    # Regional Sales
    regions = get_cached_sales_by_region(r)
    print("\n[Cached Sales by Region]")
    for reg, sales in sorted(regions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {reg:<10}: ${sales:>12,.2f}")

    # Category Sales
    categories = get_cached_sales_by_category(r)
    print("\n[Cached Sales by Category]")
    for cat, sales in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:<16}: ${sales:>12,.2f}")

    # Segment Sales
    segments = get_cached_sales_by_segment(r)
    print("\n[Cached Sales by Customer Segment]")
    for seg, sales in sorted(segments.items(), key=lambda x: x[1], reverse=True):
        print(f"  {seg:<14}: ${sales:>12,.2f}")

    # Shipping Summary
    shipping = get_cached_shipping_summary(r)
    print("\n[Cached Sales by Shipping Mode]")
    for mode, sales in sorted(shipping.items(), key=lambda x: x[1], reverse=True):
        print(f"  {mode:<16}: ${sales:>12,.2f}")

    # Monthly Trend (Sample)
    monthly = get_cached_monthly_sales(r)
    print(f"\n[Cached Monthly Sales Trend - Total Months: {len(monthly)}]")
    for m in monthly[-6:]:  # show last 6 months
        print(f"  {m['year_month']}: ${m['total_sales']:>10,.2f}")

    # Top 5 Products
    top_p = get_cached_top_products(r, limit=5)
    print("\n[Cached Top 5 Products by Sales]")
    for i, p in enumerate(top_p, 1):
        print(f"  {i}. [{p['product_id']}] {p['product_name'][:45]:<45}: ${p['total_sales']:>10,.2f}")

    # Top 5 Customers
    top_c = get_cached_top_customers(r, limit=5)
    print("\n[Cached Top 5 Customers by Spend]")
    for i, c in enumerate(top_c, 1):
        print(f"  {i}. [{c['customer_id']}] {c['customer_name']:<30}: ${c['total_spend']:>10,.2f}")

    print("\n" + "=" * 70)
    print("PHASE 3 REDIS CACHE REFRESH & VALIDATION COMPLETED SUCCESSFULLY")
    print("=" * 70)

    close_mongodb_connection()
    close_redis_connection()


if __name__ == "__main__":
    main()
