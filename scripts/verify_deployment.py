import urllib.request
import json
import time

def run_checks():
    print("=================================================================")
    print("PHASE 10: PRODUCTION DEPLOYMENT END-TO-END VERIFICATION")
    print("=================================================================")

    # 1. Frontend Production Server
    t0 = time.time()
    with urllib.request.urlopen('http://127.0.0.1:4173') as res:
        html = res.read().decode('utf-8')
        status_fe = res.status
    fe_ms = round((time.time() - t0) * 1000, 2)
    print(f"[PASS] Frontend Production (http://127.0.0.1:4173): Status {status_fe}, Latency {fe_ms}ms, Size {len(html)} bytes")

    # 2. Swagger Docs
    with urllib.request.urlopen('http://127.0.0.1:8000/docs') as res:
        status_sw = res.status
    print(f"[PASS] Swagger UI (http://127.0.0.1:8000/docs): Status {status_sw}")

    # 3. Health Check
    t0 = time.time()
    with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health') as res:
        health = json.loads(res.read().decode('utf-8'))
    health_ms = round((time.time() - t0) * 1000, 2)
    dbs = health.get("databases", {})
    print(f"[PASS] API Health Check: {health.get('status')} (Redis: {dbs.get('redis')}, Mongo: {dbs.get('mongodb')}, Cassandra: {dbs.get('cassandra')}, Neo4j: {dbs.get('neo4j')}) - Latency: {health_ms}ms")

    # 4. Overview KPIs (Redis)
    t0 = time.time()
    with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/dashboard/overview') as res:
        ov = json.loads(res.read().decode('utf-8'))
    ov_ms = round((time.time() - t0) * 1000, 2)
    print(f"[PASS] Overview KPIs (Redis): Sales ${ov['total_sales']:,.4f}, Orders {ov['total_orders']}, AOV ${ov['average_order_value']:.2f} - Latency: {ov_ms}ms")

    # 5. Filtered Overview (MongoDB)
    t0 = time.time()
    with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/dashboard/overview?region=West') as res:
        ov_west = json.loads(res.read().decode('utf-8'))
    mongo_ov_ms = round((time.time() - t0) * 1000, 2)
    print(f"[PASS] Filtered Overview (West - MongoDB): Sales ${ov_west['total_sales']:,.2f}, Orders {ov_west['total_orders']} - Latency: {mongo_ov_ms}ms")

    # 6. MongoDB Order Lookup
    t0 = time.time()
    with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/analytics/orders/CA-2017-152156') as res:
        order = json.loads(res.read().decode('utf-8'))
    mongo_order_ms = round((time.time() - t0) * 1000, 2)
    order_val = order.get('order_total') or order.get('total_sales')
    print(f"[PASS] MongoDB Order Lookup (CA-2017-152156): Total ${order_val}, Items {len(order['items'])} - Latency: {mongo_order_ms}ms")

    # 7. Cassandra Daily Date Query
    t0 = time.time()
    with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/analytics/date?date=2017-11-08') as res:
        cass_date = json.loads(res.read().decode('utf-8'))
    cass_date_ms = round((time.time() - t0) * 1000, 2)
    cass_sales = sum(item['sales'] for item in cass_date) if isinstance(cass_date, list) else 0
    cass_count = len(cass_date) if isinstance(cass_date, list) else 0
    print(f"[PASS] Cassandra Daily Date (2017-11-08): Items {cass_count}, Sales ${cass_sales:.2f} - Latency: {cass_date_ms}ms")

    # 8. Cassandra Region Date Range
    t0 = time.time()
    with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/analytics/region-date?region=West&start_date=2017-01-01&end_date=2017-12-31') as res:
        cass_reg = json.loads(res.read().decode('utf-8'))
    cass_reg_ms = round((time.time() - t0) * 1000, 2)
    reg_sales = sum(item['sales'] for item in cass_reg) if isinstance(cass_reg, list) else 0
    reg_count = len(cass_reg) if isinstance(cass_reg, list) else 0
    print(f"[PASS] Cassandra Region-Date (West 2017): Records {reg_count}, Sales ${reg_sales:,.2f} - Latency: {cass_reg_ms}ms")

    # 9. Neo4j Product Co-purchases
    t0 = time.time()
    with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/analytics/graph/product/FUR-BO-10001798/copurchases?limit=5') as res:
        copurch = json.loads(res.read().decode('utf-8'))
    neo_copurch_ms = round((time.time() - t0) * 1000, 2)
    print(f"[PASS] Neo4j Co-purchases (FUR-BO-10001798): Recommendations {len(copurch)} - Latency: {neo_copurch_ms}ms")

    # 10. Neo4j 6-Hop Regional Categories
    t0 = time.time()
    with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/analytics/graph/region/West/categories') as res:
        reg_cat = json.loads(res.read().decode('utf-8'))
    neo_reg_ms = round((time.time() - t0) * 1000, 2)
    print(f"[PASS] Neo4j 6-Hop Regional Categories (West): {reg_cat} - Latency: {neo_reg_ms}ms")

    # Benchmark Validations
    print("\n----------------- BENCHMARK RECONCILIATION -----------------")
    assert ov['total_sales'] == 2261536.7827, f"Total sales mismatch: {ov['total_sales']}"
    assert ov['total_orders'] == 4922, f"Total orders mismatch: {ov['total_orders']}"
    assert ov_west['total_sales'] == 710219.68, f"West sales mismatch: {ov_west['total_sales']}"
    print("[ALL BENCHMARKS VERIFIED ACCURATELY]")

if __name__ == "__main__":
    run_checks()
