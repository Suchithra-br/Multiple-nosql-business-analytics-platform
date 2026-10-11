"""
Unit & Integration Test Suite for FastAPI Backend Layer.

Verifies:
1. /health basic liveness endpoint.
2. /api/v1/health deep multi-database readiness diagnostics (all 4 databases).
3. /api/v1/dashboard/overview KPI response accuracy from Redis.
4. /api/v1/dashboard/regions regional sales aggregation.
5. /api/v1/dashboard/categories category sales aggregation.
6. /api/v1/dashboard/segments customer segment sales aggregation.
7. /api/v1/dashboard/shipping shipping mode breakdown.
8. /api/v1/dashboard/monthly full 48-month time-series and year filtering.
9. /api/v1/analytics/products/top Redis leaderboard with limit validation.
10. /api/v1/analytics/customers/top Redis leaderboard with limit validation.
11. /api/v1/analytics/orders/{order_id} MongoDB operational document lookup & 404 handling.
12. /api/v1/analytics/customers/{customer_id} MongoDB profile lookup & 404 handling.
13. /api/v1/analytics/date Cassandra partition-keyed daily query & 400 validation.
14. /api/v1/analytics/region-date Cassandra regional time slice & parameter validation.
15. /api/v1/analytics/category-date Cassandra category time slice & parameter validation.
16. /api/v1/analytics/graph/customer/{id}/orders Neo4j customer order traversal & 404 handling.
17. /api/v1/analytics/graph/customer/{id}/products Neo4j product affinity traversal.
18. /api/v1/analytics/graph/product/{id}/copurchases Neo4j co-purchasing recommendation & 404 handling.
19. /api/v1/analytics/graph/region/{region}/categories Neo4j 6-hop regional taxonomy aggregation.
20. OpenAPI documentation accessibility (/openapi.json, /docs).
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


# ==============================================================================
# 1. Health Endpoints
# ==============================================================================

def test_liveness_health():
    """Test 1: Verify basic liveness endpoint /health returns 200 OK."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "FastAPI" in data["message"]


def test_readiness_health():
    """Test 2: Verify deep multi-database readiness endpoint /api/v1/health."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    dbs = data["databases"]
    assert dbs["mongodb"] == "healthy"
    assert dbs["redis"] == "healthy"
    assert dbs["cassandra"] == "healthy"
    assert dbs["neo4j"] == "healthy"


# ==============================================================================
# 2. Dashboard Endpoints (Redis Cache)
# ==============================================================================

def test_dashboard_overview():
    """Test 3: Verify /api/v1/dashboard/overview returns exact benchmark KPIs."""
    res = client.get("/api/v1/dashboard/overview")
    assert res.status_code == 200
    data = res.json()
    assert abs(data["total_sales"] - 2261536.7827) < 1e-2
    assert data["total_orders"] == 4922
    assert abs(data["average_order_value"] - 459.48) < 1.0


def test_dashboard_regions():
    """Test 4: Verify /api/v1/dashboard/regions returns sales for all 4 geographic regions."""
    res = client.get("/api/v1/dashboard/regions")
    assert res.status_code == 200
    data = res.json()
    regions = {r["region"] for r in data}
    assert regions == {"West", "East", "Central", "South"}
    total_sales = sum(r["total_sales"] for r in data)
    assert abs(total_sales - 2261536.78) < 1.0


def test_dashboard_categories():
    """Test 5: Verify /api/v1/dashboard/categories returns sales for 3 categories."""
    res = client.get("/api/v1/dashboard/categories")
    assert res.status_code == 200
    data = res.json()
    cats = {c["category"] for c in data}
    assert cats == {"Technology", "Furniture", "Office Supplies"}
    total_sales = sum(c["total_sales"] for c in data)
    assert abs(total_sales - 2261536.78) < 1.0


def test_dashboard_segments():
    """Test 6: Verify /api/v1/dashboard/segments returns sales for 3 customer segments."""
    res = client.get("/api/v1/dashboard/segments")
    assert res.status_code == 200
    data = res.json()
    segs = {s["segment"] for s in data}
    assert segs == {"Consumer", "Corporate", "Home Office"}


def test_dashboard_shipping():
    """Test 7: Verify /api/v1/dashboard/shipping returns sales for 4 shipping modes."""
    res = client.get("/api/v1/dashboard/shipping")
    assert res.status_code == 200
    data = res.json()
    modes = {m["ship_mode"] for m in data}
    assert modes == {"Standard Class", "Second Class", "First Class", "Same Day"}


def test_dashboard_monthly_all():
    """Test 8: Verify /api/v1/dashboard/monthly returns all 48 months (2015-2018)."""
    res = client.get("/api/v1/dashboard/monthly")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 48
    assert data[0]["year_month"] == "2015-01"
    assert data[-1]["year_month"] == "2018-12"


def test_dashboard_monthly_year_filter():
    """Test 9: Verify /api/v1/dashboard/monthly with year parameter filters to 12 months."""
    res = client.get("/api/v1/dashboard/monthly?year=2018")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 12
    for m in data:
        assert m["year_month"].startswith("2018-")


def test_dashboard_monthly_invalid_year():
    """Test 10: Verify /api/v1/dashboard/monthly with invalid year returns 400 Bad Request."""
    res = client.get("/api/v1/dashboard/monthly?year=2010")
    assert res.status_code == 400
    assert "Invalid year" in res.json()["detail"]


# ==============================================================================
# 3. Analytics Endpoints (Redis, MongoDB, Cassandra)
# ==============================================================================

def test_top_products():
    """Test 11: Verify /api/v1/analytics/products/top returns top products leaderboard."""
    res = client.get("/api/v1/analytics/products/top?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    assert data[0]["product_id"] == "TEC-CO-10004722"
    assert data[0]["total_sales"] > 60000.0


def test_top_products_invalid_limit():
    """Test 12: Verify /api/v1/analytics/products/top with out-of-range limit returns 422."""
    res = client.get("/api/v1/analytics/products/top?limit=500")
    assert res.status_code == 422


def test_top_customers():
    """Test 13: Verify /api/v1/analytics/customers/top returns top customers leaderboard."""
    res = client.get("/api/v1/analytics/customers/top?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    for c in data:
        assert c["total_spend"] > 0
        assert "customer_id" in c


def test_mongodb_order_lookup_success():
    """Test 14: Verify /api/v1/analytics/orders/{order_id} returns order from MongoDB."""
    res = client.get("/api/v1/analytics/orders/CA-2017-152156")
    assert res.status_code == 200
    data = res.json()
    assert data["order_id"] == "CA-2017-152156"
    assert data["order_total"] == 993.90
    assert len(data["items"]) == 2
    assert data["customer"]["customer_id"] == "CG-12520"


def test_mongodb_order_lookup_404():
    """Test 15: Verify /api/v1/analytics/orders/{order_id} with unknown ID returns 404."""
    res = client.get("/api/v1/analytics/orders/UNKNOWN-ORDER-999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_mongodb_customer_lookup_success():
    """Test 16: Verify /api/v1/analytics/customers/{customer_id} returns customer from MongoDB."""
    res = client.get("/api/v1/analytics/customers/CG-12520")
    assert res.status_code == 200
    data = res.json()
    assert data["customer_id"] == "CG-12520"
    assert data["customer_name"] == "Claire Gute"
    assert data["order_count"] == 3


def test_mongodb_customer_lookup_404():
    """Test 17: Verify /api/v1/analytics/customers/{customer_id} with unknown ID returns 404."""
    res = client.get("/api/v1/analytics/customers/UNKNOWN-CUST-999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_cassandra_date_query_success():
    """Test 18: Verify /api/v1/analytics/date returns date line items from Cassandra."""
    res = client.get("/api/v1/analytics/date?date=2017-11-08")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["order_date"] == "2017-11-08"


def test_cassandra_date_query_invalid_format():
    """Test 19: Verify /api/v1/analytics/date with invalid date string returns 400."""
    res = client.get("/api/v1/analytics/date?date=not-a-date")
    assert res.status_code == 400
    assert "Invalid date format" in res.json()["detail"]


def test_cassandra_region_date_query_success():
    """Test 20: Verify /api/v1/analytics/region-date returns regional time slice from Cassandra."""
    res = client.get("/api/v1/analytics/region-date?region=West&start_date=2018-01-01&end_date=2018-01-31")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 50
    for row in data:
        assert row["region"] == "West"
        assert "2018-01-01" <= row["order_date"] <= "2018-01-31"


def test_cassandra_region_date_query_invalid_region():
    """Test 21: Verify /api/v1/analytics/region-date with invalid region returns 400."""
    res = client.get("/api/v1/analytics/region-date?region=NorthPole&start_date=2018-01-01&end_date=2018-01-31")
    assert res.status_code == 400
    assert "Invalid region" in res.json()["detail"]


def test_cassandra_region_date_query_inverted_dates():
    """Test 22: Verify /api/v1/analytics/region-date with start_date > end_date returns 400."""
    res = client.get("/api/v1/analytics/region-date?region=West&start_date=2018-12-01&end_date=2018-01-01")
    assert res.status_code == 400
    assert "start_date must be less than or equal to end_date" in res.json()["detail"]


def test_cassandra_category_date_query_success():
    """Test 23: Verify /api/v1/analytics/category-date returns category time slice from Cassandra."""
    res = client.get("/api/v1/analytics/category-date?category=Technology&start_date=2018-06-01&end_date=2018-06-30")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 43
    for row in data:
        assert row["category"] == "Technology"
        assert "2018-06-01" <= row["order_date"] <= "2018-06-30"


def test_cassandra_category_date_query_invalid_category():
    """Test 24: Verify /api/v1/analytics/category-date with invalid category returns 400."""
    res = client.get("/api/v1/analytics/category-date?category=Groceries&start_date=2018-01-01&end_date=2018-01-31")
    assert res.status_code == 400
    assert "Invalid category" in res.json()["detail"]


# ==============================================================================
# 4. Neo4j Graph Analytics Endpoints
# ==============================================================================

def test_neo4j_customer_orders_success():
    """Test 25: Verify /api/v1/analytics/graph/customer/{id}/orders returns linked orders from Neo4j."""
    res = client.get("/api/v1/analytics/graph/customer/CG-12520/orders")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    order_ids = {o["order_id"] for o in data}
    assert "CA-2017-152156" in order_ids


def test_neo4j_customer_orders_404():
    """Test 26: Verify /api/v1/analytics/graph/customer/{id}/orders with unknown ID returns 404."""
    res = client.get("/api/v1/analytics/graph/customer/UNKNOWN-CUST-999/orders")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_neo4j_customer_products_success():
    """Test 27: Verify /api/v1/analytics/graph/customer/{id}/products returns product affinities from Neo4j."""
    res = client.get("/api/v1/analytics/graph/customer/CG-12520/products")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    for p in data:
        assert p["purchase_count"] >= 1
        assert p["total_spent"] > 0


def test_neo4j_product_copurchases_success():
    """Test 28: Verify /api/v1/analytics/graph/product/{id}/copurchases returns co-purchases from Neo4j."""
    res = client.get("/api/v1/analytics/graph/product/FUR-BO-10001798/copurchases")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    p_ids = {cp["product_id"] for cp in data}
    assert "FUR-CH-10000454" in p_ids


def test_neo4j_product_copurchases_404():
    """Test 29: Verify /api/v1/analytics/graph/product/{id}/copurchases with unknown ID returns 404."""
    res = client.get("/api/v1/analytics/graph/product/UNKNOWN-PROD-999/copurchases")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_neo4j_region_categories_success():
    """Test 30: Verify /api/v1/analytics/graph/region/{region}/categories traverses graph taxonomy."""
    res = client.get("/api/v1/analytics/graph/region/West/categories")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    cats = {c["category"] for c in data}
    assert cats == {"Technology", "Furniture", "Office Supplies"}


def test_neo4j_region_categories_invalid_region():
    """Test 31: Verify /api/v1/analytics/graph/region/{region}/categories with invalid region returns 400."""
    res = client.get("/api/v1/analytics/graph/region/Atlantis/categories")
    assert res.status_code == 400
    assert "Invalid region" in res.json()["detail"]


# ==============================================================================
# 5. Phase 8 Analytics & Search Endpoints
# ==============================================================================

def test_dashboard_subcategories_success():
    """Test 32: Verify /api/v1/dashboard/subcategories returns all 17 Superstore subcategories."""
    res = client.get("/api/v1/dashboard/subcategories")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 17
    subcats = {s["sub_category"] for s in data}
    assert "Phones" in subcats
    assert "Chairs" in subcats
    assert "Storage" in subcats
    assert data[0]["sub_category"] == "Phones"


def test_dashboard_states_success():
    """Test 33: Verify /api/v1/dashboard/states returns top 10 states by sales."""
    res = client.get("/api/v1/dashboard/states?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 10
    assert data[0]["state"] == "California"
    assert data[0]["region"] == "West"
    assert data[0]["total_sales"] > 400000.0


def test_analytics_customer_search():
    """Test 34: Verify /api/v1/analytics/customers/search matches by customer name or ID."""
    res = client.get("/api/v1/analytics/customers/search?q=Claire")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["customer_name"] == "Claire Gute"
    assert data[0]["customer_id"] == "CG-12520"


def test_analytics_order_search():
    """Test 35: Verify /api/v1/analytics/orders/search matches orders by ID."""
    res = client.get("/api/v1/analytics/orders/search?q=CA-2017-152156")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["order_id"] == "CA-2017-152156"
    assert data[0]["order_total"] == 993.9


def test_dashboard_filtered_overview():
    """Test 36: Verify /api/v1/dashboard/overview respects year and region query parameters."""
    res = client.get("/api/v1/dashboard/overview?year=2018&region=West")
    assert res.status_code == 200
    data = res.json()
    assert data["total_sales"] > 0
    assert data["total_orders"] > 0
    assert data["average_order_value"] > 0
    assert data["comparison_label"] == "2018 vs 2017"


# ==============================================================================
# 6. OpenAPI Documentation
# ==============================================================================

def test_openapi_json_accessible():
    """Test 37: Verify /openapi.json schema is generated with all 23 paths (19 baseline + 4 Phase 8 endpoints)."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert schema["info"]["title"] == "Multi-NoSQL Real-Time Business Analytics Platform API"
    assert len(schema["paths"]) == 23


def test_swagger_docs_accessible():
    """Test 38: Verify /docs Swagger UI is accessible."""
    res = client.get("/docs")
    assert res.status_code == 200
    assert "swagger-ui" in res.text.lower()
