"""
Unit and Integration Tests for MongoDB Implementation.

Separates offline document construction unit tests from live database integration tests.
"""

from pathlib import Path
import pytest
import pandas as pd

from backend.app.databases.mongodb import (
    get_mongodb_database,
    check_mongodb_connection,
    get_mongodb_uri,
    get_mongodb_database_name,
)
from backend.app.repositories.mongodb_repository import (
    safe_postal_code,
    build_order_documents,
    build_customer_documents,
    build_product_documents,
    build_location_documents,
    load_all_collections,
    validate_mongodb_data,
    create_indexes,
    MongoDBAnalytics,
)

project_root = Path(__file__).resolve().parents[2]
gen_dir = project_root / "generated_data"

# Check if live MongoDB server is available
is_mongo_online, mongo_status_msg = check_mongodb_connection(timeout_ms=1000)


# ==============================================================================
# 1. Offline Unit Tests (Run without MongoDB)
# ==============================================================================

def test_safe_postal_code():
    """Ensure safe_postal_code returns None for missing values and clean 5-digit strings for valid codes."""
    assert safe_postal_code(None) is None
    assert safe_postal_code("") is None
    assert safe_postal_code("nan") is None
    assert safe_postal_code("NaN") is None
    assert safe_postal_code(42420.0) == "42420"
    assert safe_postal_code(6824.0) == "06824"
    assert safe_postal_code("06824") == "06824"


def test_build_order_documents_structure():
    """Ensure order document structure conforms strictly to specifications with embedded items."""
    orders = build_order_documents(
        orders_csv_path=gen_dir / "orders.csv",
        order_items_csv_path=gen_dir / "order_items.csv",
        customers_csv_path=gen_dir / "customers.csv",
    )
    assert len(orders) == 4922

    first = orders[0]
    # Check top-level keys
    for k in ["_id", "order_id", "order_date", "ship_date", "ship_mode", "customer", "shipping_address", "items", "order_total"]:
        assert k in first

    # Check nested customer
    assert "customer_id" in first["customer"]
    assert "customer_name" in first["customer"]
    assert "segment" in first["customer"]

    # Check nested address
    assert "country" in first["shipping_address"]
    assert "region" in first["shipping_address"]
    assert "city" in first["shipping_address"]
    assert "state" in first["shipping_address"]

    # Check embedded items
    assert len(first["items"]) > 0
    item = first["items"][0]
    for ik in ["row_id", "product_id", "product_name", "category", "sub_category", "sales"]:
        assert ik in item

    # Check that order_total matches sum of line items
    calculated_total = round(sum(it["sales"] for it in first["items"]), 4)
    assert first["order_total"] == calculated_total

    # Verify no prohibited metrics
    for prohibited in ["profit", "discount", "quantity", "cost", "profit_margin"]:
        assert prohibited not in first
        assert prohibited not in item


def test_build_customer_documents_structure():
    """Ensure customer documents are constructed cleanly with expected benchmark counts."""
    customers = build_customer_documents(gen_dir / "customers.csv")
    assert len(customers) == 793
    c = customers[0]
    for k in ["_id", "customer_id", "customer_name", "segment", "primary_region", "order_count", "total_spend"]:
        assert k in c


def test_build_product_documents_structure():
    """Ensure product documents use canonical names and match benchmark counts."""
    products = build_product_documents(gen_dir / "products.csv")
    assert len(products) == 1861
    p = products[0]
    for k in ["_id", "product_id", "product_name", "category", "sub_category", "total_sales"]:
        assert k in p


def test_build_location_documents_structure():
    """Ensure location documents contain 628 entries and preserve null postal codes."""
    locations = build_location_documents(gen_dir / "locations.csv")
    assert len(locations) == 628
    burlington = [l for l in locations if l["city"] == "Burlington" and l["state"] == "Vermont"]
    assert len(burlington) == 1
    assert burlington[0]["postal_code"] is None


# ==============================================================================
# 2. Live Database Integration Tests (Requires Active MongoDB)
# ==============================================================================

@pytest.mark.skipif(not is_mongo_online, reason=f"MongoDB not available: {mongo_status_msg}")
class TestMongoDBLiveIntegration:
    """Integration test suite against a running MongoDB instance."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Connects to database before running live tests."""
        self.db = get_mongodb_database("business_analytics")

    def test_database_connection(self):
        """Verify live MongoDB connection and database configuration."""
        assert get_mongodb_database_name() == "business_analytics"
        is_ok, msg = check_mongodb_connection()
        assert is_ok is True
        assert "Server version" in msg

    def test_collection_counts(self):
        """Verify document counts match Phase 1 benchmarks."""
        assert self.db.orders.count_documents({}) == 4922
        assert self.db.customers.count_documents({}) == 793
        assert self.db.products.count_documents({}) == 1861
        assert self.db.locations.count_documents({}) == 628

    def test_embedded_items_count(self):
        """Verify all 9,800 order items are embedded inside the 4,922 order documents."""
        pipeline = [
            {"$project": {"cnt": {"$size": "$items"}}},
            {"$group": {"_id": None, "total": {"$sum": "$cnt"}}},
        ]
        res = list(self.db.orders.aggregate(pipeline))
        assert res[0]["total"] == 9800

    def test_sales_reconciliation(self):
        """Verify the sum of all order_total values matches $2,261,536.7827."""
        pipeline = [{"$group": {"_id": None, "total": {"$sum": "$order_total"}}}]
        res = list(self.db.orders.aggregate(pipeline))
        total_sales = res[0]["total"]
        assert abs(total_sales - 2261536.7827) < 1e-4

    def test_null_postal_code_preserved(self):
        """Verify Burlington, VT postal code is stored as null in MongoDB."""
        burlington = self.db.orders.find_one({
            "shipping_address.city": "Burlington",
            "shipping_address.state": "Vermont",
        })
        assert burlington is not None
        assert burlington["shipping_address"]["postal_code"] is None

    def test_indexes_created(self):
        """Verify indexes exist on the collections."""
        indexes_orders = self.db.orders.index_information()
        assert "order_id_1" in indexes_orders
        assert indexes_orders["order_id_1"].get("unique") is True
        assert "customer.customer_id_1" in indexes_orders
        assert "order_date_1" in indexes_orders
        assert "shipping_address.region_1" in indexes_orders

        indexes_cust = self.db.customers.index_information()
        assert "customer_id_1" in indexes_cust
        assert indexes_cust["customer_id_1"].get("unique") is True

    def test_idempotent_reloading(self):
        """Verify loading again does not create duplicate documents."""
        initial_counts = {
            "orders": self.db.orders.count_documents({}),
            "customers": self.db.customers.count_documents({}),
            "products": self.db.products.count_documents({}),
            "locations": self.db.locations.count_documents({}),
        }
        # Run loading
        reloaded_counts = load_all_collections(self.db, gen_dir)
        for col, count in reloaded_counts.items():
            assert count == initial_counts[col]

    def test_analytics_queries(self):
        """Verify the MongoDB demonstration aggregation queries return valid data."""
        analytics = MongoDBAnalytics(self.db)

        # Query 1: Total sales
        q1 = analytics.get_total_sales()
        assert q1["total_sales"] == 2261536.78
        assert q1["total_orders"] == 4922

        # Query 2: Sales by region
        q2 = analytics.get_sales_by_region()
        assert len(q2) == 4
        regions = {r["region"]: r["total_sales"] for r in q2}
        assert "West" in regions
        assert "East" in regions

        # Query 3: Sales by category
        q3 = analytics.get_sales_by_category()
        assert len(q3) == 3
        cats = {c["category"]: c["total_sales"] for c in q3}
        assert "Technology" in cats
        assert "Furniture" in cats
        assert "Office Supplies" in cats

        # Query 6: Top 10 products
        q6 = analytics.get_top_products_by_sales(limit=10)
        assert len(q6) == 10
        assert q6[0]["product_id"] == "TEC-CO-10004722"  # Canon imageCLASS

        # Query 7: Top 10 customers
        q7 = analytics.get_top_customers_by_spend(limit=10)
        assert len(q7) == 10
        assert q7[0]["customer_id"] == "SM-20320"  # Sean Miller
