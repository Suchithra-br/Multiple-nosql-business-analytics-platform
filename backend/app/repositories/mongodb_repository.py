"""
MongoDB Repository & Service Module.

Handles:
1. Transforming Phase 1 CSV datasets into embedded document models.
2. Idempotent bulk loading into MongoDB collections (orders, customers, products, locations).
3. Index creation for optimized querying.
4. Post-load verification and sales reconciliation.
5. Analytical query demonstrations via MongoDB aggregation pipelines.
"""

import logging
from pathlib import Path
from typing import Any, Optional
import pandas as pd
from pymongo import ReplaceOne, ASCENDING, DESCENDING
from pymongo.database import Database

logger = logging.getLogger("repositories.mongodb")


# ==============================================================================
# Document Building Utilities
# ==============================================================================

def safe_postal_code(val: Any) -> Optional[str]:
    """Ensures missing postal code is None (null) and not 'nan' string."""
    if pd.isna(val) or val is None or str(val).strip() in ("", "nan", "NaN", "None"):
        return None
    try:
        numeric = int(float(val))
        return f"{numeric:05d}"
    except (ValueError, TypeError):
        s = str(val).strip()
        return s if s else None


def build_order_documents(
    orders_csv_path: str | Path,
    order_items_csv_path: str | Path,
    customers_csv_path: str | Path,
) -> list[dict[str, Any]]:
    """
    Constructs 4,922 order documents with embedded line items and nested customer/address.
    """
    logger.info("Reading orders, order_items, and customers CSVs...")
    orders_df = pd.read_csv(orders_csv_path)
    items_df = pd.read_csv(order_items_csv_path)
    customers_df = pd.read_csv(customers_csv_path)

    # Customer lookup dictionary
    cust_lookup = customers_df.set_index("customer_id")[["customer_name", "segment"]].to_dict("index")

    # Group items by order_id
    items_by_order: dict[str, list[dict[str, Any]]] = {}
    for _, row in items_df.iterrows():
        oid = str(row["order_id"]).strip()
        item_doc = {
            "row_id": int(row["row_id"]),
            "product_id": str(row["product_id"]).strip(),
            "product_name": str(row["product_name"]).strip(),
            "category": str(row["category"]).strip(),
            "sub_category": str(row["sub_category"]).strip(),
            "sales": round(float(row["sales"]), 4),
        }
        items_by_order.setdefault(oid, []).append(item_doc)

    order_docs: list[dict[str, Any]] = []
    for _, row in orders_df.iterrows():
        oid = str(row["order_id"]).strip()
        cid = str(row["customer_id"]).strip()
        cust_info = cust_lookup.get(cid, {})

        order_items = items_by_order.get(oid, [])
        # Recalculate order_total strictly from actual line-item sales
        calculated_total = round(sum(item["sales"] for item in order_items), 4)

        doc = {
            "_id": oid,
            "order_id": oid,
            "order_date": str(row["order_date"]).strip(),
            "ship_date": str(row["ship_date"]).strip(),
            "ship_mode": str(row["ship_mode"]).strip(),
            "customer": {
                "customer_id": cid,
                "customer_name": cust_info.get("customer_name", ""),
                "segment": cust_info.get("segment", ""),
            },
            "shipping_address": {
                "country": str(row["country"]).strip(),
                "city": str(row["city"]).strip(),
                "state": str(row["state"]).strip(),
                "postal_code": safe_postal_code(row.get("postal_code")),
                "region": str(row["region"]).strip(),
            },
            "items": order_items,
            "order_total": calculated_total,
            "order_year": int(row["order_year"]),
            "order_month": int(row["order_month"]),
            "order_quarter": str(row["order_quarter"]).strip(),
            "order_year_month": str(row["order_year_month"]).strip(),
            "shipping_days": int(row["shipping_days"]),
        }
        order_docs.append(doc)

    logger.info(f"Built {len(order_docs)} order documents with embedded line items.")
    return order_docs


def build_customer_documents(customers_csv_path: str | Path) -> list[dict[str, Any]]:
    """Constructs 793 customer master documents."""
    df = pd.read_csv(customers_csv_path)
    cust_docs: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        cid = str(row["customer_id"]).strip()
        doc = {
            "_id": cid,
            "customer_id": cid,
            "customer_name": str(row["customer_name"]).strip(),
            "segment": str(row["segment"]).strip(),
            "primary_region": str(row["primary_region"]).strip(),
            "order_count": int(row["order_count"]),
            "total_spend": round(float(row["total_spend"]), 4),
        }
        cust_docs.append(doc)
    logger.info(f"Built {len(cust_docs)} customer documents.")
    return cust_docs


def build_product_documents(products_csv_path: str | Path) -> list[dict[str, Any]]:
    """Constructs 1,861 product master documents using canonical product name."""
    df = pd.read_csv(products_csv_path)
    prod_docs: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        pid = str(row["product_id"]).strip()
        doc = {
            "_id": pid,
            "product_id": pid,
            "product_name": str(row["product_name"]).strip(),
            "category": str(row["category"]).strip(),
            "sub_category": str(row["sub_category"]).strip(),
            "total_sales": round(float(row["total_sales"]), 4),
        }
        prod_docs.append(doc)
    logger.info(f"Built {len(prod_docs)} product documents.")
    return prod_docs


def build_location_documents(locations_csv_path: str | Path) -> list[dict[str, Any]]:
    """Constructs 628 geographic location documents."""
    df = pd.read_csv(locations_csv_path)
    loc_docs: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        lid = str(row["location_id"]).strip()
        doc = {
            "_id": lid,
            "location_id": lid,
            "country": str(row["country"]).strip(),
            "region": str(row["region"]).strip(),
            "state": str(row["state"]).strip(),
            "city": str(row["city"]).strip(),
            "postal_code": safe_postal_code(row.get("postal_code")),
            "total_sales": round(float(row["total_sales"]), 4),
            "order_count": int(row["order_count"]),
        }
        loc_docs.append(doc)
    logger.info(f"Built {len(loc_docs)} location documents.")
    return loc_docs


# ==============================================================================
# Database Loading & Indexing
# ==============================================================================

def create_indexes(db: Database) -> dict[str, list[str]]:
    """
    Creates only essential indexes on collections.
    """
    logger.info("Creating indexes on collections...")
    created: dict[str, list[str]] = {}

    # orders indexes
    db.orders.create_index([("order_id", ASCENDING)], unique=True)
    db.orders.create_index([("customer.customer_id", ASCENDING)])
    db.orders.create_index([("order_date", ASCENDING)])
    db.orders.create_index([("shipping_address.region", ASCENDING)])
    created["orders"] = ["order_id (unique)", "customer.customer_id", "order_date", "shipping_address.region"]

    # customers indexes
    db.customers.create_index([("customer_id", ASCENDING)], unique=True)
    created["customers"] = ["customer_id (unique)"]

    # products indexes
    db.products.create_index([("product_id", ASCENDING)], unique=True)
    db.products.create_index([("category", ASCENDING)])
    db.products.create_index([("sub_category", ASCENDING)])
    created["products"] = ["product_id (unique)", "category", "sub_category"]

    # locations indexes
    db.locations.create_index([("location_id", ASCENDING)], unique=True)
    created["locations"] = ["location_id (unique)"]

    logger.info("All indexes successfully established.")
    return created


def load_all_collections(
    db: Database,
    generated_data_dir: str | Path,
) -> dict[str, int]:
    """
    Loads orders, customers, products, and locations into MongoDB.
    Uses bulk ReplaceOne with upsert=True to guarantee idempotency.
    
    Returns:
        dict[str, int]: Document counts per collection.
    """
    gen_dir = Path(generated_data_dir).resolve()
    logger.info(f"Loading data into MongoDB from: {gen_dir}")

    # 1. Build document collections
    order_docs = build_order_documents(
        orders_csv_path=gen_dir / "orders.csv",
        order_items_csv_path=gen_dir / "order_items.csv",
        customers_csv_path=gen_dir / "customers.csv",
    )
    cust_docs = build_customer_documents(gen_dir / "customers.csv")
    prod_docs = build_product_documents(gen_dir / "products.csv")
    loc_docs = build_location_documents(gen_dir / "locations.csv")

    # 2. Idempotent bulk upsert into orders
    logger.info("Upserting orders collection...")
    order_ops = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in order_docs]
    db.orders.bulk_write(order_ops, ordered=False)

    # 3. Idempotent bulk upsert into customers
    logger.info("Upserting customers collection...")
    cust_ops = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in cust_docs]
    db.customers.bulk_write(cust_ops, ordered=False)

    # 4. Idempotent bulk upsert into products
    logger.info("Upserting products collection...")
    prod_ops = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in prod_docs]
    db.products.bulk_write(prod_ops, ordered=False)

    # 5. Idempotent bulk upsert into locations
    logger.info("Upserting locations collection...")
    loc_ops = [ReplaceOne({"_id": d["_id"]}, d, upsert=True) for d in loc_docs]
    db.locations.bulk_write(loc_ops, ordered=False)

    # 6. Create indexes
    create_indexes(db)

    counts = {
        "orders": db.orders.count_documents({}),
        "customers": db.customers.count_documents({}),
        "products": db.products.count_documents({}),
        "locations": db.locations.count_documents({}),
    }
    logger.info(f"Loading complete. Document counts: {counts}")
    return counts


# ==============================================================================
# Validation & Reconciliation
# ==============================================================================

def validate_mongodb_data(db: Database) -> dict[str, Any]:
    """
    Validates document counts, embedded line item counts, and sales totals.
    
    Raises:
        ValueError: If any benchmark or validation check fails.
    """
    logger.info("Validating loaded MongoDB collections against Phase 1 benchmarks...")

    # Document counts
    orders_count = db.orders.count_documents({})
    cust_count = db.customers.count_documents({})
    prod_count = db.products.count_documents({})
    loc_count = db.locations.count_documents({})

    expected_benchmarks = {
        "orders": (orders_count, 4922),
        "customers": (cust_count, 793),
        "products": (prod_count, 1861),
        "locations": (loc_count, 628),
    }
    for entity, (actual, expected) in expected_benchmarks.items():
        if actual != expected:
            raise ValueError(f"MongoDB count mismatch for {entity}: expected {expected}, got {actual}")

    # Count total embedded items
    pipeline_items = [
        {"$project": {"item_count": {"$size": "$items"}}},
        {"$group": {"_id": None, "total_items": {"$sum": "$item_count"}}},
    ]
    items_res = list(db.orders.aggregate(pipeline_items))
    total_embedded_items = items_res[0]["total_items"] if items_res else 0
    if total_embedded_items != 9800:
        raise ValueError(f"Total embedded order items mismatch: expected 9,800, got {total_embedded_items}")

    # Total sales reconciliation
    pipeline_sales = [
        {"$group": {"_id": None, "total_sales": {"$sum": "$order_total"}}}
    ]
    sales_res = list(db.orders.aggregate(pipeline_sales))
    total_sales = sales_res[0]["total_sales"] if sales_res else 0.0

    expected_sales = 2261536.7827
    if abs(total_sales - expected_sales) > 1e-4:
        raise ValueError(f"Sales reconciliation mismatch: expected ${expected_sales:.4f}, got ${total_sales:.4f}")

    # Check that missing Burlington postal codes are null
    burlington_doc = db.orders.find_one({"shipping_address.city": "Burlington", "shipping_address.state": "Vermont"})
    if burlington_doc:
        pc = burlington_doc.get("shipping_address", {}).get("postal_code")
        if pc is not None:
            raise ValueError(f"Burlington postal code should be null, found: {pc}")

    # Verify no prohibited metrics
    sample_order = db.orders.find_one()
    prohibited_fields = ["profit", "discount", "quantity", "cost", "profit_margin"]
    for field in prohibited_fields:
        if field in sample_order or (sample_order.get("items") and field in sample_order["items"][0]):
            raise ValueError(f"Prohibited metric '{field}' found in order document!")

    logger.info(f"MongoDB Validation PASSED: 4,922 orders, 9,800 items, ${total_sales:,.4f} total sales.")
    return {
        "status": "PASSED",
        "orders_count": orders_count,
        "customers_count": cust_count,
        "products_count": prod_count,
        "locations_count": loc_count,
        "total_embedded_items": total_embedded_items,
        "total_sales": round(total_sales, 4),
    }


# ==============================================================================
# Analytical Query Demonstrations
# ==============================================================================

class MongoDBAnalytics:
    """Provides the 8 required MongoDB demonstration aggregation queries."""

    def __init__(self, db: Database):
        self.db = db

    def get_total_sales(self) -> dict[str, Any]:
        """Query 1: Total sales and order count across the platform."""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_sales": {"$sum": "$order_total"},
                    "total_orders": {"$sum": 1},
                }
            }
        ]
        res = list(self.db.orders.aggregate(pipeline))
        if res:
            return {
                "total_sales": round(res[0]["total_sales"], 2),
                "total_orders": res[0]["total_orders"],
                "avg_order_value": round(res[0]["total_sales"] / res[0]["total_orders"], 2),
            }
        return {"total_sales": 0.0, "total_orders": 0, "avg_order_value": 0.0}

    def get_sales_by_region(self) -> list[dict[str, Any]]:
        """Query 2: Sales and order counts grouped by shipping region."""
        pipeline = [
            {
                "$group": {
                    "_id": "$shipping_address.region",
                    "total_sales": {"$sum": "$order_total"},
                    "order_count": {"$sum": 1},
                }
            },
            {"$sort": {"total_sales": -1}},
            {
                "$project": {
                    "_id": 0,
                    "region": "$_id",
                    "total_sales": {"$round": ["$total_sales", 2]},
                    "order_count": 1,
                }
            },
        ]
        return list(self.db.orders.aggregate(pipeline))

    def get_sales_by_category(self) -> list[dict[str, Any]]:
        """Query 3: Sales grouped by product category (unwinding embedded items)."""
        pipeline = [
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": "$items.category",
                    "total_sales": {"$sum": "$items.sales"},
                    "item_count": {"$sum": 1},
                }
            },
            {"$sort": {"total_sales": -1}},
            {
                "$project": {
                    "_id": 0,
                    "category": "$_id",
                    "total_sales": {"$round": ["$total_sales", 2]},
                    "item_count": 1,
                }
            },
        ]
        return list(self.db.orders.aggregate(pipeline))

    def get_sales_by_segment(self) -> list[dict[str, Any]]:
        """Query 4: Sales grouped by customer segment."""
        pipeline = [
            {
                "$group": {
                    "_id": "$customer.segment",
                    "total_sales": {"$sum": "$order_total"},
                    "order_count": {"$sum": 1},
                }
            },
            {"$sort": {"total_sales": -1}},
            {
                "$project": {
                    "_id": 0,
                    "segment": "$_id",
                    "total_sales": {"$round": ["$total_sales", 2]},
                    "order_count": 1,
                }
            },
        ]
        return list(self.db.orders.aggregate(pipeline))

    def get_monthly_sales(self, year: Optional[int] = None) -> list[dict[str, Any]]:
        """Query 5: Chronological monthly sales trends, optionally filtered by year."""
        match_stage = {"$match": {"order_year": year}} if year else {"$match": {}}
        pipeline = [
            match_stage,
            {
                "$group": {
                    "_id": {
                        "year": "$order_year",
                        "month": "$order_month",
                        "year_month": "$order_year_month",
                    },
                    "total_sales": {"$sum": "$order_total"},
                    "order_count": {"$sum": 1},
                }
            },
            {"$sort": {"_id.year": 1, "_id.month": 1}},
            {
                "$project": {
                    "_id": 0,
                    "year_month": "$_id.year_month",
                    "year": "$_id.year",
                    "month": "$_id.month",
                    "total_sales": {"$round": ["$total_sales", 2]},
                    "order_count": 1,
                }
            },
        ]
        return list(self.db.orders.aggregate(pipeline))

    def get_top_products_by_sales(self, limit: int = 10) -> list[dict[str, Any]]:
        """Query 6: Top products by sales volume using the products collection."""
        pipeline = [
            {"$sort": {"total_sales": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "product_id": 1,
                    "product_name": 1,
                    "category": 1,
                    "sub_category": 1,
                    "total_sales": {"$round": ["$total_sales", 2]},
                }
            },
        ]
        return list(self.db.products.aggregate(pipeline))

    def get_top_customers_by_spend(self, limit: int = 10) -> list[dict[str, Any]]:
        """Query 7: Top customers by lifetime spend using the customers collection."""
        pipeline = [
            {"$sort": {"total_spend": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "customer_id": 1,
                    "customer_name": 1,
                    "segment": 1,
                    "primary_region": 1,
                    "order_count": 1,
                    "total_spend": {"$round": ["$total_spend", 2]},
                }
            },
        ]
        return list(self.db.customers.aggregate(pipeline))

    def get_order_count_by_ship_mode(self) -> list[dict[str, Any]]:
        """Query 8: Order count and sales volume breakdown by shipping mode."""
        pipeline = [
            {
                "$group": {
                    "_id": "$ship_mode",
                    "order_count": {"$sum": 1},
                    "total_sales": {"$sum": "$order_total"},
                }
            },
            {"$sort": {"order_count": -1}},
            {
                "$project": {
                    "_id": 0,
                    "ship_mode": "$_id",
                    "order_count": 1,
                    "total_sales": {"$round": ["$total_sales", 2]},
                }
            },
        ]
        return list(self.db.orders.aggregate(pipeline))
