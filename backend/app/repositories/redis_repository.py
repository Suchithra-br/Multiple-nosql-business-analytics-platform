"""
Redis Repository & Caching Module.

Handles:
1. Transforming MongoDB analytical aggregations into fast Redis cache structures.
2. Writing Hashes and Sorted Sets with configurable TTLs.
3. Reading cached KPI metrics for future API endpoints.
4. Cache refresh and data reconciliation between MongoDB and Redis.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
import redis
from pymongo.database import Database

from backend.app.databases.redis import get_redis_ttl
from backend.app.repositories.mongodb_repository import MongoDBAnalytics

logger = logging.getLogger("repositories.redis")

# Canonical Redis Key Names
KEY_KPIS = "dashboard:kpis"
KEY_SALES_REGION = "dashboard:sales:region"
KEY_SALES_CATEGORY = "dashboard:sales:category"
KEY_SALES_SEGMENT = "dashboard:sales:segment"
KEY_SALES_SHIPPING = "dashboard:sales:shipping"
KEY_SALES_MONTHLY = "dashboard:sales:monthly"
KEY_TOP_PRODUCTS = "dashboard:top_products"
KEY_PRODUCT_NAMES = "dashboard:product_names"
KEY_TOP_CUSTOMERS = "dashboard:top_customers"
KEY_CUSTOMER_NAMES = "dashboard:customer_names"

ALL_DASHBOARD_KEYS = [
    KEY_KPIS,
    KEY_SALES_REGION,
    KEY_SALES_CATEGORY,
    KEY_SALES_SEGMENT,
    KEY_SALES_SHIPPING,
    KEY_SALES_MONTHLY,
    KEY_TOP_PRODUCTS,
    KEY_PRODUCT_NAMES,
    KEY_TOP_CUSTOMERS,
    KEY_CUSTOMER_NAMES,
]


# ==============================================================================
# Cache Invalidation & Refresh
# ==============================================================================

def refresh_analytics_cache(
    db: Database,
    r: redis.Redis,
    ttl: Optional[int] = None,
) -> dict[str, Any]:
    """
    Recalculates analytics from MongoDB, writes them into Redis cache,
    sets TTL expiration, and verifies exact sales reconciliation.
    
    Args:
        db: Active pymongo Database ('business_analytics').
        r: Active redis.Redis client.
        ttl: Optional TTL override in seconds (defaults to REDIS_CACHE_TTL env).
        
    Returns:
        dict[str, Any]: Report of updated keys and reconciled totals.
    """
    cache_ttl = ttl if ttl is not None else get_redis_ttl()
    logger.info(f"Refreshing Redis analytics cache from MongoDB (TTL: {cache_ttl}s)...")

    analytics = MongoDBAnalytics(db)

    # 1. Fetch exact unrounded total sales & orders from MongoDB
    pipeline_total = [
        {"$group": {"_id": None, "total_sales": {"$sum": "$order_total"}, "total_orders": {"$sum": 1}}}
    ]
    total_res = list(db.orders.aggregate(pipeline_total))[0]
    raw_mongo_sales = float(total_res["total_sales"])
    mongo_orders_count = int(total_res["total_orders"])
    avg_order_val = raw_mongo_sales / mongo_orders_count if mongo_orders_count > 0 else 0.0

    # 2. Fetch category, region, segment, and monthly breakdowns
    region_data = analytics.get_sales_by_region()
    cat_data = analytics.get_sales_by_category()
    seg_data = analytics.get_sales_by_segment()
    monthly_data = analytics.get_monthly_sales(year=None)
    top_prods = analytics.get_top_products_by_sales(limit=100)
    top_custs = analytics.get_top_customers_by_spend(limit=100)
    ship_data = analytics.get_order_count_by_ship_mode()

    # 3. Pipeline write into Redis
    pipe = r.pipeline(transaction=True)

    # 3a. Overall KPIs (Hash)
    pipe.delete(KEY_KPIS)
    pipe.hset(
        KEY_KPIS,
        mapping={
            "total_sales": str(raw_mongo_sales),
            "total_orders": str(mongo_orders_count),
            "average_order_value": str(round(avg_order_val, 4)),
            "last_refreshed_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    # 3b. Regional sales (Hash)
    pipe.delete(KEY_SALES_REGION)
    region_map = {item["region"]: str(item["total_sales"]) for item in region_data}
    pipe.hset(KEY_SALES_REGION, mapping=region_map)

    # 3c. Category sales (Hash)
    pipe.delete(KEY_SALES_CATEGORY)
    cat_map = {item["category"]: str(item["total_sales"]) for item in cat_data}
    pipe.hset(KEY_SALES_CATEGORY, mapping=cat_map)

    # 3d. Segment sales (Hash)
    pipe.delete(KEY_SALES_SEGMENT)
    seg_map = {item["segment"]: str(item["total_sales"]) for item in seg_data}
    pipe.hset(KEY_SALES_SEGMENT, mapping=seg_map)

    # 3e. Shipping mode sales (Hash)
    pipe.delete(KEY_SALES_SHIPPING)
    ship_map = {item["ship_mode"]: str(item["total_sales"]) for item in ship_data}
    pipe.hset(KEY_SALES_SHIPPING, mapping=ship_map)

    # 3f. Monthly sales (Hash of year_month -> sales)
    pipe.delete(KEY_SALES_MONTHLY)
    monthly_map = {item["year_month"]: str(item["total_sales"]) for item in monthly_data}
    pipe.hset(KEY_SALES_MONTHLY, mapping=monthly_map)

    # 3g. Top Products (Sorted Set: score=sales, member=product_id + name mapping)
    pipe.delete(KEY_TOP_PRODUCTS)
    pipe.delete(KEY_PRODUCT_NAMES)
    prod_zset = {p["product_id"]: float(p["total_sales"]) for p in top_prods}
    prod_names = {p["product_id"]: p["product_name"] for p in top_prods}
    pipe.zadd(KEY_TOP_PRODUCTS, prod_zset)
    pipe.hset(KEY_PRODUCT_NAMES, mapping=prod_names)

    # 3h. Top Customers (Sorted Set: score=spend, member=customer_id + name mapping)
    pipe.delete(KEY_TOP_CUSTOMERS)
    pipe.delete(KEY_CUSTOMER_NAMES)
    cust_zset = {c["customer_id"]: float(c["total_spend"]) for c in top_custs}
    cust_names = {c["customer_id"]: f"{c['customer_name']} ({c['primary_region']})" for c in top_custs}
    pipe.zadd(KEY_TOP_CUSTOMERS, cust_zset)
    pipe.hset(KEY_CUSTOMER_NAMES, mapping=cust_names)

    # 3i. Apply TTL on all created keys
    if cache_ttl > 0:
        for k in ALL_DASHBOARD_KEYS:
            pipe.expire(k, cache_ttl)

    # Execute pipeline atomically
    pipe.execute()

    # 4. Reconciliation check
    redis_total_sales = float(r.hget(KEY_KPIS, "total_sales"))  # type: ignore
    redis_total_orders = int(r.hget(KEY_KPIS, "total_orders"))  # type: ignore

    diff_sales = abs(redis_total_sales - raw_mongo_sales)
    if diff_sales > 1e-4:
        raise ValueError(
            f"Redis reconciliation failed: Mongo=${raw_mongo_sales:.4f}, Redis=${redis_total_sales:.4f}"
        )
    if redis_total_orders != mongo_orders_count:
        raise ValueError(
            f"Redis order count mismatch: Mongo={mongo_orders_count}, Redis={redis_total_orders}"
        )

    logger.info(f"Redis cache refreshed successfully. Total Sales: ${redis_total_sales:,.4f} verified.")
    return {
        "status": "SUCCESS",
        "keys_updated": len(ALL_DASHBOARD_KEYS),
        "total_sales": redis_total_sales,
        "total_orders": redis_total_orders,
        "cache_ttl": cache_ttl,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }


# ==============================================================================
# Cache Read Functions (Used by Future API Layer)
# ==============================================================================

def get_cached_kpis(r: redis.Redis) -> dict[str, Any]:
    """Retrieves overall KPIs from Redis hash."""
    data = r.hgetall(KEY_KPIS)
    if not data:
        return {}
    return {
        "total_sales": float(data.get("total_sales", 0.0)),
        "total_orders": int(data.get("total_orders", 0)),
        "average_order_value": float(data.get("average_order_value", 0.0)),
        "last_refreshed_at": data.get("last_refreshed_at", ""),
    }


def get_cached_sales_by_region(r: redis.Redis) -> dict[str, float]:
    """Retrieves regional sales from Redis hash."""
    data = r.hgetall(KEY_SALES_REGION)
    return {k: float(v) for k, v in data.items()}


def get_cached_sales_by_category(r: redis.Redis) -> dict[str, float]:
    """Retrieves category sales from Redis hash."""
    data = r.hgetall(KEY_SALES_CATEGORY)
    return {k: float(v) for k, v in data.items()}


def get_cached_sales_by_segment(r: redis.Redis) -> dict[str, float]:
    """Retrieves customer segment sales from Redis hash."""
    data = r.hgetall(KEY_SALES_SEGMENT)
    return {k: float(v) for k, v in data.items()}


def get_cached_shipping_summary(r: redis.Redis) -> dict[str, float]:
    """Retrieves shipping mode sales from Redis hash."""
    data = r.hgetall(KEY_SALES_SHIPPING)
    return {k: float(v) for k, v in data.items()}


def get_cached_monthly_sales(r: redis.Redis) -> list[dict[str, Any]]:
    """Retrieves monthly sales sorted chronologically from Redis."""
    data = r.hgetall(KEY_SALES_MONTHLY)
    # Sort chronologically by year_month
    sorted_months = sorted(data.items(), key=lambda x: x[0])
    return [{"year_month": k, "total_sales": float(v)} for k, v in sorted_months]


def get_cached_top_products(r: redis.Redis, limit: int = 10) -> list[dict[str, Any]]:
    """Retrieves top products with scores and names from Redis sorted set."""
    # zrevrange withscores
    items = r.zrevrange(KEY_TOP_PRODUCTS, 0, limit - 1, withscores=True)
    names = r.hgetall(KEY_PRODUCT_NAMES)
    result = []
    for pid, score in items:
        result.append({
            "product_id": pid,
            "product_name": names.get(pid, pid),
            "total_sales": float(score),
        })
    return result


def get_cached_top_customers(r: redis.Redis, limit: int = 10) -> list[dict[str, Any]]:
    """Retrieves top customers with scores and names from Redis sorted set."""
    items = r.zrevrange(KEY_TOP_CUSTOMERS, 0, limit - 1, withscores=True)
    names = r.hgetall(KEY_CUSTOMER_NAMES)
    result = []
    for cid, score in items:
        result.append({
            "customer_id": cid,
            "customer_name": names.get(cid, cid),
            "total_spend": float(score),
        })
    return result
