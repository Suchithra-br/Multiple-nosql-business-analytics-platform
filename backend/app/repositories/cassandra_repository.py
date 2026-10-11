"""
Cassandra Repository & Analytics Module.

Handles:
1. Keyspace and query-driven table DDL initialization.
2. Fast, idempotent bulk data ingestion using prepared statements.
3. Query-driven analytical queries (date slicing, regional time-series, category trends, monthly rollups).
4. Sales and transaction count reconciliation against Phase 1 benchmarks.
"""

import logging
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date
from typing import Any, Optional
import pandas as pd
from cassandra.cluster import Session
from cassandra.concurrent import execute_concurrent_with_args

logger = logging.getLogger("repositories.cassandra")

KEYSPACE_NAME = "business_analytics"

# DDL Statements
CREATE_KEYSPACE_CQL = f"""
CREATE KEYSPACE IF NOT EXISTS {KEYSPACE_NAME}
WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
"""

CREATE_SALES_BY_DATE_CQL = f"""
CREATE TABLE IF NOT EXISTS {KEYSPACE_NAME}.sales_by_date (
    order_date date,
    order_year_month text,
    order_id text,
    row_id int,
    customer_id text,
    product_id text,
    category text,
    sub_category text,
    region text,
    sales decimal,
    PRIMARY KEY ((order_date), order_id, row_id)
) WITH CLUSTERING ORDER BY (order_id ASC, row_id ASC);
"""

CREATE_SALES_BY_REGION_DATE_CQL = f"""
CREATE TABLE IF NOT EXISTS {KEYSPACE_NAME}.sales_by_region_date (
    region text,
    order_date date,
    order_year_month text,
    order_id text,
    row_id int,
    customer_id text,
    product_id text,
    category text,
    sub_category text,
    sales decimal,
    PRIMARY KEY ((region), order_date, order_id, row_id)
) WITH CLUSTERING ORDER BY (order_date ASC, order_id ASC, row_id ASC);
"""

CREATE_SALES_BY_CATEGORY_DATE_CQL = f"""
CREATE TABLE IF NOT EXISTS {KEYSPACE_NAME}.sales_by_category_date (
    category text,
    order_date date,
    order_year_month text,
    order_id text,
    row_id int,
    product_id text,
    sub_category text,
    region text,
    customer_id text,
    sales decimal,
    PRIMARY KEY ((category), order_date, order_id, row_id)
) WITH CLUSTERING ORDER BY (order_date ASC, order_id ASC, row_id ASC);
"""

CREATE_MONTHLY_ROLLUP_CQL = f"""
CREATE TABLE IF NOT EXISTS {KEYSPACE_NAME}.monthly_sales_rollup (
    order_year int,
    order_month int,
    order_year_month text,
    total_sales decimal,
    order_count int,
    PRIMARY KEY ((order_year), order_month)
) WITH CLUSTERING ORDER BY (order_month ASC);
"""


# ==============================================================================
# Schema Initialization
# ==============================================================================

def initialize_cassandra_schema(session: Session):
    """Creates the keyspace and the 4 query-driven tables in Cassandra."""
    logger.info("Initializing Cassandra keyspace and tables...")
    session.execute(CREATE_KEYSPACE_CQL)
    session.set_keyspace(KEYSPACE_NAME)
    session.execute(CREATE_SALES_BY_DATE_CQL)
    session.execute(CREATE_SALES_BY_REGION_DATE_CQL)
    session.execute(CREATE_SALES_BY_CATEGORY_DATE_CQL)
    session.execute(CREATE_MONTHLY_ROLLUP_CQL)
    logger.info("Cassandra schema initialized successfully.")


# ==============================================================================
# Idempotent Data Ingestion
# ==============================================================================

def load_cassandra_data(
    session: Session,
    cleaned_sales_csv_path: str | Path,
) -> dict[str, int]:
    """
    Loads transaction records and monthly rollups from cleaned_sales.csv.
    Uses prepared statements and deterministic primary keys to ensure idempotency.
    
    Returns:
        dict[str, int]: Processed record counts per table.
    """
    csv_path = Path(cleaned_sales_csv_path).resolve()
    logger.info(f"Loading data into Cassandra from: {csv_path}")

    # Ensure schema exists and set keyspace
    initialize_cassandra_schema(session)

    df = pd.read_csv(csv_path)
    total_rows = len(df)
    logger.info(f"Read {total_rows} records from {csv_path.name}")

    # 1. Prepare statements
    stmt_by_date = session.prepare(f"""
        INSERT INTO {KEYSPACE_NAME}.sales_by_date (
            order_date, order_year_month, order_id, row_id,
            customer_id, product_id, category, sub_category, region, sales
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)

    stmt_by_region = session.prepare(f"""
        INSERT INTO {KEYSPACE_NAME}.sales_by_region_date (
            region, order_date, order_year_month, order_id, row_id,
            customer_id, product_id, category, sub_category, sales
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)

    stmt_by_cat = session.prepare(f"""
        INSERT INTO {KEYSPACE_NAME}.sales_by_category_date (
            category, order_date, order_year_month, order_id, row_id,
            product_id, sub_category, region, customer_id, sales
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)

    stmt_rollup = session.prepare(f"""
        INSERT INTO {KEYSPACE_NAME}.monthly_sales_rollup (
            order_year, order_month, order_year_month, total_sales, order_count
        ) VALUES (?, ?, ?, ?, ?)
    """)

    # 2. Build parameter lists
    params_date = []
    params_region = []
    params_cat = []

    for _, r in df.iterrows():
        # Parse date strictly into python date
        d_val: date = datetime.strptime(str(r["order_date"]).strip(), "%Y-%m-%d").date()
        sales_val = Decimal(str(r["sales"]))
        row_id_val = int(r["row_id"])
        order_id_val = str(r["order_id"]).strip()
        cust_id_val = str(r["customer_id"]).strip()
        prod_id_val = str(r["product_id"]).strip()
        cat_val = str(r["category"]).strip()
        subcat_val = str(r["sub_category"]).strip()
        reg_val = str(r["region"]).strip()
        ym_val = str(r["order_year_month"]).strip()

        params_date.append((
            d_val, ym_val, order_id_val, row_id_val,
            cust_id_val, prod_id_val, cat_val, subcat_val, reg_val, sales_val
        ))
        params_region.append((
            reg_val, d_val, ym_val, order_id_val, row_id_val,
            cust_id_val, prod_id_val, cat_val, subcat_val, sales_val
        ))
        params_cat.append((
            cat_val, d_val, ym_val, order_id_val, row_id_val,
            prod_id_val, subcat_val, reg_val, cust_id_val, sales_val
        ))

    # 3. Concurrent execution for high throughput
    logger.info("Executing concurrent inserts into sales_by_date...")
    execute_concurrent_with_args(session, stmt_by_date, params_date, concurrency=50)

    logger.info("Executing concurrent inserts into sales_by_region_date...")
    execute_concurrent_with_args(session, stmt_by_region, params_region, concurrency=50)

    logger.info("Executing concurrent inserts into sales_by_category_date...")
    execute_concurrent_with_args(session, stmt_by_cat, params_cat, concurrency=50)

    # 4. Compute and insert monthly rollup
    logger.info("Computing and inserting monthly_sales_rollup...")
    monthly_grouped = df.groupby(["order_year", "order_month", "order_year_month"])
    params_rollup = []
    for (yr, mo, ym), group in monthly_grouped:
        month_sales = Decimal(str(round(group["sales"].sum(), 4)))
        order_count = int(group["order_id"].nunique())
        params_rollup.append((int(yr), int(mo), str(ym), month_sales, order_count))

    execute_concurrent_with_args(session, stmt_rollup, params_rollup, concurrency=20)

    logger.info(f"Loaded {total_rows} items into 3 analytical tables and {len(params_rollup)} monthly rollups.")
    return {
        "sales_by_date": total_rows,
        "sales_by_region_date": total_rows,
        "sales_by_category_date": total_rows,
        "monthly_sales_rollup": len(params_rollup),
    }


# ==============================================================================
# Analytical Queries
# ==============================================================================

class CassandraAnalytics:
    """Implements the 5 required query-driven analytical queries directly in CQL."""

    _PREPARED_STMT_CACHE: dict[tuple[int, str], Any] = {}

    def __init__(self, session: Session):
        self.session = session
        self.session.set_keyspace(KEYSPACE_NAME)

    def _prepare(self, cql: str):
        """Caches prepared statements per session to avoid redundant PREPARE round-trips."""
        cql_clean = " ".join(cql.strip().split())
        cache_key = (id(self.session), cql_clean)
        if cache_key not in self._PREPARED_STMT_CACHE:
            self._PREPARED_STMT_CACHE[cache_key] = self.session.prepare(cql)
        return self._PREPARED_STMT_CACHE[cache_key]

    def get_sales_for_date(self, target_date: str | date) -> list[dict[str, Any]]:
        """
        Query 1: Sales for a selected date.
        Uses partition key (order_date).
        """
        cql_date = target_date if isinstance(target_date, date) else datetime.strptime(target_date, "%Y-%m-%d").date()
        stmt = self._prepare(f"""
            SELECT order_date, order_id, row_id, product_id, category, sub_category, region, sales
            FROM {KEYSPACE_NAME}.sales_by_date
            WHERE order_date = ?
        """)
        rows = self.session.execute(stmt, [cql_date])
        return [
            {
                "order_date": str(r.order_date),
                "order_id": r.order_id,
                "row_id": r.row_id,
                "product_id": r.product_id,
                "category": r.category,
                "sub_category": r.sub_category,
                "region": r.region,
                "sales": float(r.sales),
            }
            for r in rows
        ]

    def get_sales_by_region_range(
        self,
        region: str,
        start_date: str | date,
        end_date: str | date,
    ) -> list[dict[str, Any]]:
        """
        Query 2: Sales for a selected region across a date range.
        Uses partition key (region) and clustering key range scan (order_date >= and <=).
        """
        s_date = start_date if isinstance(start_date, date) else datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = end_date if isinstance(end_date, date) else datetime.strptime(end_date, "%Y-%m-%d").date()
        stmt = self._prepare(f"""
            SELECT region, order_date, order_id, row_id, category, sales
            FROM {KEYSPACE_NAME}.sales_by_region_date
            WHERE region = ? AND order_date >= ? AND order_date <= ?
        """)
        rows = self.session.execute(stmt, [region, s_date, e_date])
        return [
            {
                "region": r.region,
                "order_date": str(r.order_date),
                "order_id": r.order_id,
                "row_id": r.row_id,
                "category": r.category,
                "sales": float(r.sales),
            }
            for r in rows
        ]

    def get_sales_by_category_range(
        self,
        category: str,
        start_date: str | date,
        end_date: str | date,
    ) -> list[dict[str, Any]]:
        """
        Query 3: Sales for a selected category across a date range.
        Uses partition key (category) and clustering key range scan (order_date >= and <=).
        """
        s_date = start_date if isinstance(start_date, date) else datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = end_date if isinstance(end_date, date) else datetime.strptime(end_date, "%Y-%m-%d").date()
        stmt = self._prepare(f"""
            SELECT category, order_date, order_id, row_id, sub_category, sales
            FROM {KEYSPACE_NAME}.sales_by_category_date
            WHERE category = ? AND order_date >= ? AND order_date <= ?
        """)
        rows = self.session.execute(stmt, [category, s_date, e_date])
        return [
            {
                "category": r.category,
                "order_date": str(r.order_date),
                "order_id": r.order_id,
                "row_id": r.row_id,
                "sub_category": r.sub_category,
                "sales": float(r.sales),
            }
            for r in rows
        ]

    def get_monthly_sales_for_year(self, year: int) -> list[dict[str, Any]]:
        """
        Query 4: Monthly sales for a selected year.
        Uses partition key (order_year) and ordered clustering key (order_month ASC).
        """
        stmt = self._prepare(f"""
            SELECT order_year, order_month, order_year_month, total_sales, order_count
            FROM {KEYSPACE_NAME}.monthly_sales_rollup
            WHERE order_year = ?
        """)
        rows = self.session.execute(stmt, [year])
        return [
            {
                "order_year": r.order_year,
                "order_month": r.order_month,
                "order_year_month": r.order_year_month,
                "total_sales": float(r.total_sales),
                "order_count": r.order_count,
            }
            for r in rows
        ]

    def get_all_monthly_sales(self) -> list[dict[str, Any]]:
        """
        Query 5: Overall monthly sales across 2015–2018 (all 48 months).
        """
        rows = self.session.execute(f"""
            SELECT order_year, order_month, order_year_month, total_sales, order_count
            FROM {KEYSPACE_NAME}.monthly_sales_rollup
        """)
        sorted_rows = sorted(list(rows), key=lambda r: (r.order_year, r.order_month))
        return [
            {
                "order_year": r.order_year,
                "order_month": r.order_month,
                "order_year_month": r.order_year_month,
                "total_sales": float(r.total_sales),
                "order_count": r.order_count,
            }
            for r in sorted_rows
        ]


# ==============================================================================
# Validation & Reconciliation
# ==============================================================================

def validate_cassandra_data(session: Session) -> dict[str, Any]:
    """
    Validates Cassandra total sales and counts against verified benchmarks.
    
    Raises:
        ValueError: If any validation check fails.
    """
    logger.info("Validating Cassandra data against Phase 1 benchmarks...")
    session.set_keyspace(KEYSPACE_NAME)

    analytics = CassandraAnalytics(session)

    # 1. Total monthly sales sum across 48 months
    monthly_rows = analytics.get_all_monthly_sales()
    if len(monthly_rows) != 48:
        raise ValueError(f"Expected 48 monthly rollups, found {len(monthly_rows)}")

    cassandra_total_sales = sum(m["total_sales"] for m in monthly_rows)
    expected_sales = 2261536.7827
    if abs(cassandra_total_sales - expected_sales) > 1e-2:
        raise ValueError(
            f"Cassandra total sales mismatch: expected ${expected_sales:.4f}, got ${cassandra_total_sales:.4f}"
        )

    # 2. Check table row counts
    count_date = session.execute(f"SELECT COUNT(*) FROM {KEYSPACE_NAME}.sales_by_date").one()[0]
    count_region = session.execute(f"SELECT COUNT(*) FROM {KEYSPACE_NAME}.sales_by_region_date").one()[0]
    count_cat = session.execute(f"SELECT COUNT(*) FROM {KEYSPACE_NAME}.sales_by_category_date").one()[0]

    if count_date != 9800 or count_region != 9800 or count_cat != 9800:
        raise ValueError(
            f"Table row counts mismatch: sales_by_date={count_date}, "
            f"sales_by_region_date={count_region}, sales_by_category_date={count_cat} (expected 9,800)"
        )

    logger.info(f"Cassandra Validation PASSED: 9,800 transactions, 48 rollups, ${cassandra_total_sales:,.2f} total sales.")
    return {
        "status": "PASSED",
        "sales_by_date_count": count_date,
        "sales_by_region_date_count": count_region,
        "sales_by_category_date_count": count_cat,
        "monthly_rollup_count": len(monthly_rows),
        "total_sales": round(cassandra_total_sales, 4),
    }
