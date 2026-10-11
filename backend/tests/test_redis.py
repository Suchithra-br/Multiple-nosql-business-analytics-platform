"""
Focused Unit & Integration Tests for Redis Caching Layer.

Verifies:
1. Redis connectivity and configuration.
2. KPI cache creation and retrieval.
3. Regional, category, segment, and monthly analytics caching.
4. Top products and customers sorted sets.
5. Cache refresh idempotency.
6. Exact MongoDB-to-Redis sales and orders reconciliation.
7. TTL expiration configuration.
"""

import pytest

from backend.app.databases.mongodb import get_mongodb_database, check_mongodb_connection
from backend.app.databases.redis import (
    get_redis_client,
    check_redis_connection,
    get_redis_ttl,
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
    KEY_KPIS,
    KEY_SALES_REGION,
    KEY_SALES_CATEGORY,
    KEY_TOP_PRODUCTS,
    KEY_TOP_CUSTOMERS,
)

# Connectivity pre-checks
mongo_ok, mongo_msg = check_mongodb_connection(timeout_ms=1000)
redis_ok, redis_msg = check_redis_connection(timeout_s=1.0)


@pytest.fixture(scope="module")
def setup_services():
    """Ensure both MongoDB and Redis are active and cache is refreshed before tests."""
    if not mongo_ok:
        pytest.fail(f"MongoDB not available: {mongo_msg}")
    if not redis_ok:
        pytest.fail(f"Redis not available: {redis_msg}")

    db = get_mongodb_database()
    r = get_redis_client()
    refresh_analytics_cache(db, r, ttl=3600)
    return db, r


def test_redis_connection(setup_services):
    """Test 1: Verify Redis connectivity and ping."""
    is_ok, msg = check_redis_connection()
    assert is_ok is True
    assert "Server version" in msg


def test_kpi_cache_creation_and_retrieval(setup_services):
    """Test 2 & 3: Verify KPI hash creation and retrieval."""
    _, r = setup_services
    kpis = get_cached_kpis(r)
    assert kpis["total_orders"] == 4922
    assert abs(kpis["total_sales"] - 2261536.7827) < 1e-4
    assert kpis["average_order_value"] == round(2261536.7827 / 4922, 4)
    assert "last_refreshed_at" in kpis


def test_regional_sales_caching(setup_services):
    """Test 4: Verify regional sales hash and 4 distinct regions."""
    _, r = setup_services
    regions = get_cached_sales_by_region(r)
    assert len(regions) == 4
    for expected_reg in ["West", "East", "Central", "South"]:
        assert expected_reg in regions
        assert regions[expected_reg] > 0
    # Sum matches total sales
    assert abs(sum(regions.values()) - 2261536.7827) < 1e-2


def test_category_sales_caching(setup_services):
    """Test 5: Verify category sales hash and 3 distinct categories."""
    _, r = setup_services
    cats = get_cached_sales_by_category(r)
    assert len(cats) == 3
    for expected_cat in ["Technology", "Furniture", "Office Supplies"]:
        assert expected_cat in cats
        assert cats[expected_cat] > 0
    assert abs(sum(cats.values()) - 2261536.7827) < 1e-2


def test_segment_sales_caching(setup_services):
    """Verify customer segment sales hash and 3 distinct segments."""
    _, r = setup_services
    segs = get_cached_sales_by_segment(r)
    assert len(segs) == 3
    for expected_seg in ["Consumer", "Corporate", "Home Office"]:
        assert expected_seg in segs
        assert segs[expected_seg] > 0
    assert abs(sum(segs.values()) - 2261536.7827) < 1e-2


def test_monthly_sales_caching(setup_services):
    """Verify chronological monthly sales array across all 48 months (2015-2018)."""
    _, r = setup_services
    months = get_cached_monthly_sales(r)
    assert len(months) == 48
    assert months[0]["year_month"] == "2015-01"
    assert months[-1]["year_month"] == "2018-12"
    assert abs(sum(m["total_sales"] for m in months) - 2261536.7827) < 1e-2


def test_top_products_caching(setup_services):
    """Test 6: Verify top products sorted set and name mapping."""
    _, r = setup_services
    top_p = get_cached_top_products(r, limit=10)
    assert len(top_p) == 10
    # Scores descending
    for i in range(len(top_p) - 1):
        assert top_p[i]["total_sales"] >= top_p[i + 1]["total_sales"]
    assert top_p[0]["product_id"] == "TEC-CO-10004722"
    assert "Canon imageCLASS" in top_p[0]["product_name"]


def test_top_customers_caching(setup_services):
    """Test 7: Verify top customers sorted set and name mapping."""
    _, r = setup_services
    top_c = get_cached_top_customers(r, limit=10)
    assert len(top_c) == 10
    # Scores descending
    for i in range(len(top_c) - 1):
        assert top_c[i]["total_spend"] >= top_c[i + 1]["total_spend"]
    assert top_c[0]["customer_id"] == "SM-20320"
    assert "Sean Miller" in top_c[0]["customer_name"]


def test_shipping_summary_caching(setup_services):
    """Verify shipping mode summary hash."""
    _, r = setup_services
    ship = get_cached_shipping_summary(r)
    assert len(ship) == 4
    for expected_mode in ["Standard Class", "Second Class", "First Class", "Same Day"]:
        assert expected_mode in ship
        assert ship[expected_mode] > 0


def test_cache_refresh_idempotency(setup_services):
    """Test 8: Verify cache refresh operation is repeatable and idempotent."""
    db, r = setup_services
    rep1 = refresh_analytics_cache(db, r, ttl=3600)
    rep2 = refresh_analytics_cache(db, r, ttl=3600)
    assert rep1["total_sales"] == rep2["total_sales"]
    assert rep1["total_orders"] == rep2["total_orders"]
    assert rep1["keys_updated"] == rep2["keys_updated"]


def test_sales_reconciliation_mongo_vs_redis(setup_services):
    """Test 9: Verify exact MongoDB to Redis sales and orders reconciliation."""
    db, r = setup_services
    # Mongo truth
    mongo_pipeline = [
        {"$group": {"_id": None, "total_sales": {"$sum": "$order_total"}, "total_orders": {"$sum": 1}}}
    ]
    mongo_total = list(db.orders.aggregate(mongo_pipeline))[0]
    mongo_sales = float(mongo_total["total_sales"])
    mongo_orders = int(mongo_total["total_orders"])

    # Redis cached
    kpis = get_cached_kpis(r)
    assert abs(kpis["total_sales"] - mongo_sales) < 1e-4
    assert kpis["total_orders"] == mongo_orders
    assert abs(kpis["total_sales"] - 2261536.7827) < 1e-4
    assert kpis["total_orders"] == 4922


def test_cache_ttl_behavior(setup_services):
    """Test 10: Verify TTL expiration is applied to cached keys."""
    _, r = setup_services
    configured_ttl = get_redis_ttl()
    ttl_kpis = r.ttl(KEY_KPIS)
    assert 0 < ttl_kpis <= configured_ttl
    ttl_regions = r.ttl(KEY_SALES_REGION)
    assert 0 < ttl_regions <= configured_ttl
    ttl_top = r.ttl(KEY_TOP_PRODUCTS)
    assert 0 < ttl_top <= configured_ttl
