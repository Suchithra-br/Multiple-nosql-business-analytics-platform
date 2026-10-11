"""
Cassandra Loader & Analytical Query Demonstration Script.

Initializes keyspace and query-driven tables in Cassandra, loads records from
generated_data/cleaned_sales.csv, verifies sales reconciliation, checks idempotency,
and executes the 5 required analytical queries directly in CQL.

Usage:
    python scripts/load_cassandra.py
"""

import sys
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.databases.cassandra import (
    get_cassandra_session,
    check_cassandra_connection,
    close_cassandra_connection,
)
from backend.app.repositories.cassandra_repository import (
    load_cassandra_data,
    validate_cassandra_data,
    CassandraAnalytics,
    KEYSPACE_NAME,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scripts.load_cassandra")


def main():
    logger.info("=" * 70)
    logger.info("PHASE 4: CASSANDRA TIME-SERIES & QUERY-DRIVEN ANALYTICS")
    logger.info("=" * 70)

    # 1. Connection & Readiness Check
    is_ok, msg = check_cassandra_connection(max_retries=5, retry_delay_s=3.0)
    if not is_ok:
        print(f"\nERROR: Cassandra connection failed.\n{msg}\n")
        sys.exit(1)

    session = get_cassandra_session()
    csv_file = project_root / "generated_data" / "cleaned_sales.csv"
    if not csv_file.exists():
        logger.error(f"Generated cleaned_sales.csv not found at: {csv_file}")
        sys.exit(1)

    # 2. Ingest Data
    logger.info("--- Step 1: Loading Records into Cassandra Query-Driven Tables ---")
    counts = load_cassandra_data(session, csv_file)
    print(f"\n[1] Records Loaded:\n    - sales_by_date:          {counts['sales_by_date']:,}\n    - sales_by_region_date:   {counts['sales_by_region_date']:,}\n    - sales_by_category_date: {counts['sales_by_category_date']:,}\n    - monthly_sales_rollup:   {counts['monthly_sales_rollup']:,}")

    # 3. Post-load Validation
    logger.info("--- Step 2: Validating Counts & Sales Totals ---")
    val_report = validate_cassandra_data(session)
    print("\n[2] Cassandra Validation Report:")
    for k, v in val_report.items():
        print(f"    - {k}: {v}")

    # 4. Verify Idempotency (run load a second time)
    logger.info("--- Step 3: Verifying Idempotent Reloading ---")
    counts2 = load_cassandra_data(session, csv_file)
    val_report2 = validate_cassandra_data(session)
    assert val_report["sales_by_date_count"] == val_report2["sales_by_date_count"] == 9800
    assert val_report["monthly_rollup_count"] == val_report2["monthly_rollup_count"] == 48
    print("\n[3] Idempotency Verified: Repeat load produced identical record counts (9,800) with zero duplicate rows.")

    # 5. Query Demonstrations
    logger.info("--- Step 4: Executing 5 Required CQL Analytical Queries ---")
    analytics = CassandraAnalytics(session)

    print("\n" + "=" * 70)
    print("CASSANDRA CQL QUERY-DRIVEN DEMONSTRATIONS")
    print("=" * 70)

    # Query 1: Sales for a selected date
    sample_date = "2017-11-08"
    q1 = analytics.get_sales_for_date(sample_date)
    print(f"\n[Query 1: Sales for Selected Date '{sample_date}'] (Found {len(q1)} line items)")
    for r in q1:
        print(f"  Order: {r['order_id']} | Product: {r['product_id']} | Cat: {r['category']} ({r['sub_category']}) | Sales: ${r['sales']:>8.2f}")

    # Query 2: Sales for a selected region across a date range
    reg = "West"
    s_date, e_date = "2018-01-01", "2018-01-31"
    q2 = analytics.get_sales_by_region_range(reg, s_date, e_date)
    total_q2 = sum(r["sales"] for r in q2)
    print(f"\n[Query 2: Sales for Region '{reg}' between {s_date} and {e_date}]")
    print(f"  Line Items Found: {len(q2)} | Subtotal: ${total_q2:,.2f}")
    for r in q2[:5]:  # first 5
        print(f"  Date: {r['order_date']} | Order: {r['order_id']} | Cat: {r['category']:<15} | Sales: ${r['sales']:>7.2f}")

    # Query 3: Sales for a selected category across a date range
    cat = "Technology"
    s_date3, e_date3 = "2018-06-01", "2018-06-30"
    q3 = analytics.get_sales_by_category_range(cat, s_date3, e_date3)
    total_q3 = sum(r["sales"] for r in q3)
    print(f"\n[Query 3: Sales for Category '{cat}' in June 2018]")
    print(f"  Line Items Found: {len(q3)} | Subtotal: ${total_q3:,.2f}")
    for r in q3[:5]:
        print(f"  Date: {r['order_date']} | Order: {r['order_id']} | SubCat: {r['sub_category']:<12} | Sales: ${r['sales']:>7.2f}")

    # Query 4: Monthly sales for a selected year
    year = 2018
    q4 = analytics.get_monthly_sales_for_year(year)
    total_q4 = sum(r["total_sales"] for r in q4)
    print(f"\n[Query 4: Monthly Sales Rollup for Year {year}] (Year Total: ${total_q4:,.2f})")
    for r in q4:
        print(f"  {r['order_year_month']}: ${r['total_sales']:>10,.2f} ({r['order_count']} orders)")

    # Query 5: Overall monthly sales across 2015-2018
    q5 = analytics.get_all_monthly_sales()
    total_q5 = sum(r["total_sales"] for r in q5)
    print(f"\n[Query 5: Overall Monthly Rollup Across All 4 Years (Total Months: {len(q5)})]")
    print(f"  Grand Total across all 48 months: ${total_q5:,.2f}")
    print(f"  First Month ({q5[0]['order_year_month']}):  ${q5[0]['total_sales']:>10,.2f}")
    print(f"  Latest Month ({q5[-1]['order_year_month']}): ${q5[-1]['total_sales']:>10,.2f}")

    print("\n" + "=" * 70)
    print("PHASE 4 CASSANDRA INGESTION & QUERY VALIDATION COMPLETED SUCCESSFULLY")
    print("=" * 70)

    close_cassandra_connection()


if __name__ == "__main__":
    main()
