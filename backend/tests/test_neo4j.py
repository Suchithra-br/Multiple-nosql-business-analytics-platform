"""
Unit & Integration Tests for Neo4j Graph Database and Analytics.

Verifies:
1. Neo4j connectivity and Bolt protocol readiness.
2. Uniqueness constraints and index creation.
3. Node counts (793 Customers, 4,922 Orders, 1,861 Products, 3 Categories, 17 SubCategories, 600 Cities, 49 States, 4 Regions).
4. Schema integrity (no unsupported metrics like profit, discount, quantity).
5. Relationship counts (4,922 PLACED, 9,800 CONTAINS, 1,878 BELONGS_TO, 4,922 SHIPPED_TO, 600 IN_STATE, 49 IN_REGION).
6. Total sales reconciliation via line-item CONTAINS.sales ($2,261,536.7827).
7. Query 1: Customer -> Orders.
8. Query 2: Customer -> Products with spend calculations.
9. Query 3: Product co-purchasing graph traversal ("frequently bought together").
10. Query 4: Category sales breakdown by Region using graph path traversal.
11. Query 5: Customer category affinity.
12. Query 6: Regional product relationships.
13. Idempotent reloading verification (0 duplicate nodes/relationships).
"""

import pytest

from backend.app.databases.neo4j import (
    get_neo4j_driver,
    check_neo4j_connection,
)
from backend.app.repositories.neo4j_repository import (
    initialize_neo4j_schema,
    validate_neo4j_data,
    Neo4jAnalytics,
)

# Connectivity pre-check
neo4j_ok, neo4j_msg = check_neo4j_connection(max_retries=2, retry_delay_s=1.0)


@pytest.fixture(scope="module")
def neo4j_driver():
    """Ensure Neo4j is accessible and return singleton driver."""
    if not neo4j_ok:
        pytest.fail(f"Neo4j is not accessible: {neo4j_msg}")
    driver = get_neo4j_driver()
    initialize_neo4j_schema(driver)
    return driver


@pytest.fixture(scope="module")
def analytics(neo4j_driver):
    """Return an instance of Neo4jAnalytics."""
    return Neo4jAnalytics(neo4j_driver)


# ==============================================================================
# 1. Connection & Schema Tests
# ==============================================================================

def test_neo4j_connection():
    """Test 1: Verify Neo4j connectivity and Bolt protocol readiness."""
    is_ok, msg = check_neo4j_connection(max_retries=1)
    assert is_ok is True
    assert "successful" in msg


def test_constraints_created(neo4j_driver):
    """Test 2: Verify uniqueness constraints exist on entity labels."""
    with neo4j_driver.session() as session:
        records = session.run("SHOW CONSTRAINTS").data()
        constraint_names = {r["name"] for r in records}
        expected = {
            "customer_id_unique",
            "order_id_unique",
            "product_id_unique",
            "category_name_unique",
            "subcategory_name_unique",
            "state_name_unique",
            "region_name_unique",
        }
        assert expected.issubset(constraint_names), f"Missing constraints: {expected - constraint_names}"


def test_schema_no_unsupported_metrics(neo4j_driver):
    """Test 3: Verify nodes and relationships do not store unsupported fields (Profit, Quantity, Discount, Cost)."""
    forbidden_terms = {"profit", "discount", "quantity", "cost", "margin"}
    with neo4j_driver.session() as session:
        # Check property keys on nodes and relationships
        sample_node_props = session.run("CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey").data()
        for rec in sample_node_props:
            prop = rec["propertyKey"].lower()
            for forbidden in forbidden_terms:
                assert forbidden not in prop, f"Found forbidden property '{prop}' in graph schema"


# ==============================================================================
# 2. Node & Relationship Counts Tests
# ==============================================================================

def test_expected_node_counts(neo4j_driver):
    """Test 4: Verify core node counts match Phase 1 dataset benchmarks."""
    with neo4j_driver.session() as session:
        c_cnt = session.run("MATCH (c:Customer) RETURN count(c) AS cnt").single()["cnt"]
        o_cnt = session.run("MATCH (o:Order) RETURN count(o) AS cnt").single()["cnt"]
        p_cnt = session.run("MATCH (p:Product) RETURN count(p) AS cnt").single()["cnt"]
        cat_cnt = session.run("MATCH (c:Category) RETURN count(c) AS cnt").single()["cnt"]
        sub_cnt = session.run("MATCH (s:SubCategory) RETURN count(s) AS cnt").single()["cnt"]
        state_cnt = session.run("MATCH (s:State) RETURN count(s) AS cnt").single()["cnt"]
        reg_cnt = session.run("MATCH (r:Region) RETURN count(r) AS cnt").single()["cnt"]
        city_cnt = session.run("MATCH (c:City) RETURN count(c) AS cnt").single()["cnt"]

        assert c_cnt == 793, f"Expected 793 Customer nodes, got {c_cnt}"
        assert o_cnt == 4922, f"Expected 4,922 Order nodes, got {o_cnt}"
        assert p_cnt == 1861, f"Expected 1,861 Product nodes, got {p_cnt}"
        assert cat_cnt == 3, f"Expected 3 Category nodes, got {cat_cnt}"
        assert sub_cnt == 17, f"Expected 17 SubCategory nodes, got {sub_cnt}"
        assert state_cnt == 49, f"Expected 49 State nodes, got {state_cnt}"
        assert reg_cnt == 4, f"Expected 4 Region nodes, got {reg_cnt}"
        assert city_cnt == 600, f"Expected 600 City nodes, got {city_cnt}"


def test_expected_line_item_relationship_count(neo4j_driver):
    """Test 5: Verify Order -> Product CONTAINS relationships match 9,800 line items."""
    with neo4j_driver.session() as session:
        contains_cnt = session.run("MATCH ()-[r:CONTAINS]->() RETURN count(r) AS cnt").single()["cnt"]
        assert contains_cnt == 9800, f"Expected 9,800 CONTAINS relationships, got {contains_cnt}"


def test_graph_relationship_topology(neo4j_driver):
    """Test 6: Verify graph topology relationship counts."""
    with neo4j_driver.session() as session:
        placed_cnt = session.run("MATCH ()-[r:PLACED]->() RETURN count(r) AS cnt").single()["cnt"]
        shipped_cnt = session.run("MATCH ()-[r:SHIPPED_TO]->() RETURN count(r) AS cnt").single()["cnt"]
        in_state_cnt = session.run("MATCH ()-[r:IN_STATE]->() RETURN count(r) AS cnt").single()["cnt"]
        in_reg_cnt = session.run("MATCH ()-[r:IN_REGION]->() RETURN count(r) AS cnt").single()["cnt"]
        belongs_cnt = session.run("MATCH ()-[r:BELONGS_TO]->() RETURN count(r) AS cnt").single()["cnt"]

        assert placed_cnt == 4922, f"Expected 4,922 PLACED relationships, got {placed_cnt}"
        assert shipped_cnt == 4922, f"Expected 4,922 SHIPPED_TO relationships, got {shipped_cnt}"
        assert in_state_cnt == 600, f"Expected 600 IN_STATE relationships, got {in_state_cnt}"
        assert in_reg_cnt == 49, f"Expected 49 IN_REGION relationships, got {in_reg_cnt}"
        assert belongs_cnt == 1878, f"Expected 1,878 BELONGS_TO relationships, got {belongs_cnt}"


# ==============================================================================
# 3. Sales Reconciliation Test
# ==============================================================================

def test_sales_reconciliation(neo4j_driver):
    """Test 7: Verify total sales through CONTAINS.sales equals $2,261,536.7827."""
    val_report = validate_neo4j_data(neo4j_driver)
    assert val_report["status"] == "PASSED"
    expected_sales = 2261536.7827
    assert abs(val_report["total_sales"] - expected_sales) < 1e-2


# ==============================================================================
# 4. Graph Analytical Query Tests
# ==============================================================================

def test_query_1_customer_orders(analytics):
    """Test 8: Query 1 - Orders placed by customer."""
    cust_id = "CG-12520"
    orders = analytics.get_customer_orders(cust_id)
    assert len(orders) == 3
    order_ids = {o["order_id"] for o in orders}
    assert "CA-2017-152156" in order_ids


def test_query_2_customer_products(analytics):
    """Test 9: Query 2 - Products purchased by customer."""
    cust_id = "CG-12520"
    products = analytics.get_customer_products(cust_id)
    assert len(products) == 5
    p_ids = {p["product_id"] for p in products}
    assert "FUR-BO-10001798" in p_ids
    for p in products:
        assert p["total_spent"] > 0
        assert p["purchase_count"] >= 1


def test_query_3_product_co_purchasing(analytics):
    """Test 10: Query 3 - Products occurring in shared orders ("frequently bought together")."""
    target_pid = "FUR-BO-10001798"
    co_products = analytics.get_product_co_purchases(target_pid, limit=10)
    assert len(co_products) > 0
    # FUR-CH-10000454 was ordered together in order CA-2017-152156
    co_pids = {cp["product_id"] for cp in co_products}
    assert "FUR-CH-10000454" in co_pids
    for cp in co_products:
        assert cp["times_co_purchased"] >= 1
        assert cp["product_id"] != target_pid


def test_query_4_category_by_region(analytics):
    """Test 11: Query 4 - Category sales breakdown for region using multi-hop graph traversal."""
    cat_sales = analytics.get_category_sales_by_region("West")
    assert len(cat_sales) == 3
    categories = {cs["category"] for cs in cat_sales}
    assert categories == {"Technology", "Furniture", "Office Supplies"}
    total_west_sales = sum(cs["total_sales"] for cs in cat_sales)
    # Benchmark West regional sales is $710,219.68
    assert abs(total_west_sales - 710219.68) < 1.0


def test_query_5_customer_category_affinity(analytics):
    """Test 12: Query 5 - Categories purchased by selected customer."""
    cust_id = "CG-12520"
    affinities = analytics.get_customer_category_affinity(cust_id)
    assert len(affinities) == 2
    cats = {a["category"] for a in affinities}
    assert cats == {"Furniture", "Office Supplies"}


def test_query_6_regional_products(analytics):
    """Test 13: Query 6 - Top products purchased in selected region."""
    products = analytics.get_regional_products("East", limit=5)
    assert len(products) == 5
    for p in products:
        assert p["purchase_count"] > 0
        assert p["total_sales"] > 0


# ==============================================================================
# 5. Idempotency Test
# ==============================================================================

def test_idempotent_reload_safety(neo4j_driver):
    """Test 14: Re-merging existing relationships does not create duplicates."""
    with neo4j_driver.session() as session:
        # Re-merge a specific line item
        session.run(
            """
            MATCH (o:Order {order_id: 'CA-2017-152156'})
            MATCH (p:Product {product_id: 'FUR-BO-10001798'})
            MERGE (o)-[r:CONTAINS {row_id: 1}]->(p)
            SET r.sales = 261.96
            """
        )
        contains_cnt = session.run("MATCH ()-[r:CONTAINS]->() RETURN count(r) AS cnt").single()["cnt"]
        assert contains_cnt == 9800, f"Expected 9,800 CONTAINS rels after re-merge, got {contains_cnt}"
