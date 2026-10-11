"""
Unit & Integration Tests for Cassandra Implementation and Query-Driven Analytics.

Verifies:
1. Cassandra connectivity and cluster metadata.
2. Keyspace 'business_analytics' existence.
3. Query-driven tables creation.
4. Schema integrity (no unsupported metrics like profit, discount, quantity).
5. Data insertion counts (9,800 transactions, 48 monthly rollups).
6. Idempotency and deterministic primary key upsert behavior.
7. Query 1: Sales for selected date.
8. Query 2: Sales for region across date range.
9. Query 3: Sales for category across date range.
10. Query 4: Monthly sales for a selected year.
11. Query 5: Overall monthly sales across 2015-2018.
12. Exact sales reconciliation against Phase 1/MongoDB benchmark ($2,261,536.7827).
"""

from decimal import Decimal
from datetime import date
import pytest

from backend.app.databases.cassandra import (
    get_cassandra_session,
    check_cassandra_connection,
    KEYSPACE_NAME,
)
from backend.app.repositories.cassandra_repository import (
    initialize_cassandra_schema,
    CassandraAnalytics,
    validate_cassandra_data,
)

# Connectivity pre-check
cassandra_ok, cassandra_msg = check_cassandra_connection(max_retries=2, retry_delay_s=1.0)


@pytest.fixture(scope="module")
def cassandra_session():
    """Ensure Cassandra is reachable and return an active Session."""
    if not cassandra_ok:
        pytest.fail(f"Cassandra is not accessible: {cassandra_msg}")
    session = get_cassandra_session()
    initialize_cassandra_schema(session)
    return session


@pytest.fixture(scope="module")
def analytics(cassandra_session):
    """Return an instance of CassandraAnalytics."""
    return CassandraAnalytics(cassandra_session)


# ==============================================================================
# 1. Connection & Schema Tests
# ==============================================================================

def test_cassandra_connection():
    """Test 1: Verify Cassandra connectivity and CQL readiness."""
    is_ok, msg = check_cassandra_connection(max_retries=1)
    assert is_ok is True
    assert "Cluster:" in msg


def test_keyspace_exists(cassandra_session):
    """Test 2: Verify keyspace 'business_analytics' exists."""
    cluster_metadata = cassandra_session.cluster.metadata
    assert KEYSPACE_NAME in cluster_metadata.keyspaces
    keyspace = cluster_metadata.keyspaces[KEYSPACE_NAME]
    assert "SimpleStrategy" in type(keyspace.replication_strategy).__name__ or "SimpleStrategy" in str(keyspace.replication_strategy)


def test_tables_exist(cassandra_session):
    """Test 3: Verify the 4 query-driven tables exist in Cassandra."""
    cluster_metadata = cassandra_session.cluster.metadata
    keyspace = cluster_metadata.keyspaces[KEYSPACE_NAME]
    expected_tables = {
        "sales_by_date",
        "sales_by_region_date",
        "sales_by_category_date",
        "monthly_sales_rollup",
    }
    actual_tables = set(keyspace.tables.keys())
    assert expected_tables.issubset(actual_tables), (
        f"Missing tables: {expected_tables - actual_tables}"
    )


def test_schema_no_unsupported_metrics(cassandra_session):
    """Test 4: Verify schema does not contain unsupported fields (Profit, Quantity, Discount, Cost)."""
    cluster_metadata = cassandra_session.cluster.metadata
    keyspace = cluster_metadata.keyspaces[KEYSPACE_NAME]
    forbidden_terms = {"profit", "discount", "quantity", "cost", "margin"}

    for table_name in ["sales_by_date", "sales_by_region_date", "sales_by_category_date", "monthly_sales_rollup"]:
        table_meta = keyspace.tables[table_name]
        col_names = {col.lower() for col in table_meta.columns.keys()}
        for forbidden in forbidden_terms:
            assert forbidden not in col_names, (
                f"Found forbidden metric '{forbidden}' in table '{table_name}'"
            )


# ==============================================================================
# 2. Data Insertion & Idempotency Tests
# ==============================================================================

def test_data_insertion_counts(cassandra_session):
    """Test 5: Verify table record counts match Phase 1 dataset benchmarks."""
    count_date = cassandra_session.execute(
        f"SELECT COUNT(*) FROM {KEYSPACE_NAME}.sales_by_date"
    ).one()[0]
    count_region = cassandra_session.execute(
        f"SELECT COUNT(*) FROM {KEYSPACE_NAME}.sales_by_region_date"
    ).one()[0]
    count_cat = cassandra_session.execute(
        f"SELECT COUNT(*) FROM {KEYSPACE_NAME}.sales_by_category_date"
    ).one()[0]
    count_rollup = cassandra_session.execute(
        f"SELECT COUNT(*) FROM {KEYSPACE_NAME}.monthly_sales_rollup"
    ).one()[0]

    assert count_date == 9800, f"Expected 9,800 rows in sales_by_date, got {count_date}"
    assert count_region == 9800, f"Expected 9,800 rows in sales_by_region_date, got {count_region}"
    assert count_cat == 9800, f"Expected 9,800 rows in sales_by_category_date, got {count_cat}"
    assert count_rollup == 48, f"Expected 48 rows in monthly_sales_rollup, got {count_rollup}"


def test_repeat_loading_idempotency(cassandra_session):
    """Test 6: Verify repeat insertion with same primary keys does not duplicate records."""
    # Re-inserting an existing row with identical primary key (order_date, order_id, row_id)
    target_row = cassandra_session.execute(
        f"SELECT order_date, order_id, row_id, order_year_month, customer_id, product_id, category, sub_category, region, sales "
        f"FROM {KEYSPACE_NAME}.sales_by_date LIMIT 1"
    ).one()

    stmt = cassandra_session.prepare(f"""
        INSERT INTO {KEYSPACE_NAME}.sales_by_date (
            order_date, order_year_month, order_id, row_id,
            customer_id, product_id, category, sub_category, region, sales
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)

    # Execute re-insert
    cassandra_session.execute(stmt, [
        target_row.order_date,
        target_row.order_year_month,
        target_row.order_id,
        target_row.row_id,
        target_row.customer_id,
        target_row.product_id,
        target_row.category,
        target_row.sub_category,
        target_row.region,
        target_row.sales,
    ])

    # Row count must remain exactly 9,800
    count_date = cassandra_session.execute(
        f"SELECT COUNT(*) FROM {KEYSPACE_NAME}.sales_by_date"
    ).one()[0]
    assert count_date == 9800


# ==============================================================================
# 3. Analytical Query Tests
# ==============================================================================

def test_query_1_sales_for_date(analytics):
    """Test 7: Query 1 - Sales for a selected date."""
    target_date = "2017-11-08"
    results = analytics.get_sales_for_date(target_date)
    assert len(results) > 0
    for row in results:
        assert row["order_date"] == target_date
        assert "order_id" in row
        assert "row_id" in row
        assert "sales" in row
        assert row["sales"] > 0


def test_query_2_sales_by_region_date_range(analytics):
    """Test 8: Query 2 - Sales for a selected region across a date range."""
    region = "West"
    start_date = "2017-01-01"
    end_date = "2017-01-31"
    results = analytics.get_sales_by_region_range(region, start_date, end_date)
    assert len(results) > 0
    for row in results:
        assert row["region"] == region
        assert start_date <= row["order_date"] <= end_date
        assert "sales" in row


def test_query_3_sales_by_category_date_range(analytics):
    """Test 9: Query 3 - Sales for a selected category across a date range."""
    category = "Technology"
    start_date = "2016-01-01"
    end_date = "2016-03-31"
    results = analytics.get_sales_by_category_range(category, start_date, end_date)
    assert len(results) > 0
    for row in results:
        assert row["category"] == category
        assert start_date <= row["order_date"] <= end_date
        assert "sales" in row


def test_query_4_monthly_sales_for_year(analytics):
    """Test 10: Query 4 - Monthly sales for a selected year."""
    year = 2018
    results = analytics.get_monthly_sales_for_year(year)
    assert len(results) == 12
    # Verify ordered clustering key: 1 to 12
    months = [r["order_month"] for r in results]
    assert months == list(range(1, 13))
    for r in results:
        assert r["order_year"] == year
        assert r["total_sales"] > 0
        assert r["order_count"] > 0


def test_query_5_all_monthly_sales(analytics):
    """Test 11: Query 5 - Overall monthly sales across 2015-2018."""
    results = analytics.get_all_monthly_sales()
    assert len(results) == 48
    # Verify year bounds
    years = {r["order_year"] for r in results}
    assert years == {2015, 2016, 2017, 2018}


# ==============================================================================
# 4. Sales Reconciliation
# ==============================================================================

def test_sales_reconciliation(cassandra_session):
    """Test 12: Reconcile Cassandra total sales against benchmark ($2,261,536.7827)."""
    val_result = validate_cassandra_data(cassandra_session)
    assert val_result["status"] == "PASSED"
    assert val_result["monthly_rollup_count"] == 48
    assert val_result["sales_by_date_count"] == 9800
    assert abs(val_result["total_sales"] - 2261536.7827) < 1e-2
