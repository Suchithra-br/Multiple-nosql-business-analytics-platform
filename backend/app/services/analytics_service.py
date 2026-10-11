"""
Analytics Service Layer.

Handles operational MongoDB lookups, Redis leaderboards with aggregation fallback,
and Apache Cassandra partition-keyed/clustering-range time-series analytics.
"""

import re
from datetime import datetime, date
from typing import Optional, Any
from backend.app.core.exceptions import ResourceNotFoundError, ValidationError
from backend.app.databases.mongodb import get_mongodb_database
from backend.app.databases.redis import get_redis_client
from backend.app.databases.cassandra import get_cassandra_session
from backend.app.repositories.redis_repository import (
    get_cached_top_products,
    get_cached_top_customers,
)
from backend.app.repositories.cassandra_repository import CassandraAnalytics
from backend.app.models.schemas import (
    TopProductItem,
    TopCustomerItem,
    CustomerSearchItem,
    OrderSearchItem,
    OrderDetailResponse,
    CustomerProfileResponse,
    DateSalesItem,
    RegionDateSalesItem,
    CategoryDateSalesItem,
)

VALID_YEARS = {2015, 2016, 2017, 2018}
VALID_REGIONS = {"West", "East", "Central", "South"}
VALID_CATEGORIES = {"Technology", "Furniture", "Office Supplies"}


class AnalyticsService:
    """Business logic for operational queries, leaderboards, and Cassandra time-series."""

    @staticmethod
    def get_top_products(
        limit: int = 10,
        year: Optional[int] = None,
        region: Optional[str] = None,
    ) -> list[TopProductItem]:
        """Retrieves top products by sales volume from Redis or MongoDB."""
        if year is not None and year not in VALID_YEARS:
            raise ValidationError(message=f"Invalid year: {year}. Supported years: {sorted(list(VALID_YEARS))}.")
        if region is not None and region not in VALID_REGIONS:
            raise ValidationError(message=f"Invalid region: '{region}'. Supported regions: {sorted(list(VALID_REGIONS))}.")

        if year is None and region is None:
            r = get_redis_client()
            data = get_cached_top_products(r, limit=limit)
            return [TopProductItem(**item) for item in data]

        db = get_mongodb_database()
        match: dict[str, Any] = {}
        if year is not None:
            match["order_year"] = year
        if region is not None:
            match["shipping_address.region"] = region

        pipeline = [
            {"$match": match},
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": "$items.product_id",
                    "product_name": {"$first": "$items.product_name"},
                    "total_sales": {"$sum": "$items.sales"},
                }
            },
            {"$sort": {"total_sales": -1}},
            {"$limit": limit},
        ]
        results = list(db.orders.aggregate(pipeline))
        return [
            TopProductItem(
                product_id=r["_id"],
                product_name=r["product_name"],
                total_sales=round(r["total_sales"], 2),
            )
            for r in results
        ]

    @staticmethod
    def get_top_customers(
        limit: int = 10,
        year: Optional[int] = None,
        region: Optional[str] = None,
    ) -> list[TopCustomerItem]:
        """Retrieves top customers by cumulative spend from Redis or MongoDB."""
        if year is not None and year not in VALID_YEARS:
            raise ValidationError(message=f"Invalid year: {year}. Supported years: {sorted(list(VALID_YEARS))}.")
        if region is not None and region not in VALID_REGIONS:
            raise ValidationError(message=f"Invalid region: '{region}'. Supported regions: {sorted(list(VALID_REGIONS))}.")

        if year is None and region is None:
            r = get_redis_client()
            data = get_cached_top_customers(r, limit=limit)
            return [TopCustomerItem(**item) for item in data]

        db = get_mongodb_database()
        match: dict[str, Any] = {}
        if year is not None:
            match["order_year"] = year
        if region is not None:
            match["shipping_address.region"] = region

        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": "$customer.customer_id",
                    "customer_name": {"$first": "$customer.customer_name"},
                    "total_spend": {"$sum": "$order_total"},
                }
            },
            {"$sort": {"total_spend": -1}},
            {"$limit": limit},
        ]
        results = list(db.orders.aggregate(pipeline))
        return [
            TopCustomerItem(
                customer_id=r["_id"],
                customer_name=r["customer_name"],
                total_spend=round(r["total_spend"], 2),
            )
            for r in results
        ]

    @staticmethod
    def search_customers(query: str, limit: int = 10) -> list[CustomerSearchItem]:
        """Performs live customer autocomplete search by name or ID in MongoDB."""
        db = get_mongodb_database()
        escaped_query = re.escape(query.strip())
        pattern = re.compile(escaped_query, re.IGNORECASE)
        cursor = db.customers.find(
            {"$or": [{"customer_name": pattern}, {"customer_id": pattern}]},
            {"_id": 0, "customer_id": 1, "customer_name": 1, "segment": 1, "primary_region": 1},
        ).limit(limit)

        return [
            CustomerSearchItem(
                customer_id=c["customer_id"],
                customer_name=c.get("customer_name", "Unknown"),
                segment=c.get("segment", "Unknown"),
                primary_region=c.get("primary_region", "Unknown"),
            )
            for c in cursor
        ]

    @staticmethod
    def search_orders(query: str, limit: int = 10) -> list[OrderSearchItem]:
        """Performs live order autocomplete search by order ID in MongoDB."""
        db = get_mongodb_database()
        escaped_query = re.escape(query.strip())
        pattern = re.compile(escaped_query, re.IGNORECASE)
        cursor = db.orders.find(
            {"order_id": pattern},
            {"_id": 0, "order_id": 1, "order_date": 1, "customer.customer_name": 1, "order_total": 1},
        ).limit(limit)

        return [
            OrderSearchItem(
                order_id=o["order_id"],
                order_date=o.get("order_date", ""),
                customer_name=o.get("customer", {}).get("customer_name", "Unknown"),
                order_total=round(float(o.get("order_total", 0.0)), 2),
            )
            for o in cursor
        ]

    @staticmethod
    def get_order_by_id(order_id: str) -> OrderDetailResponse:
        """Retrieves full order document with embedded items from MongoDB."""
        db = get_mongodb_database()
        order_doc = db.orders.find_one({"order_id": order_id}, {"_id": 0})
        if not order_doc:
            raise ResourceNotFoundError(message=f"Order '{order_id}' not found")
        return OrderDetailResponse(**order_doc)

    @staticmethod
    def get_customer_by_id(customer_id: str) -> CustomerProfileResponse:
        """Retrieves customer profile with historical orders from MongoDB."""
        db = get_mongodb_database()
        cust_doc = db.customers.find_one({"customer_id": customer_id}, {"_id": 0})
        if not cust_doc:
            raise ResourceNotFoundError(message=f"Customer '{customer_id}' not found")
        return CustomerProfileResponse(**cust_doc)

    @staticmethod
    def get_sales_by_date(date_str: str) -> list[DateSalesItem]:
        """Queries Cassandra sales_by_date table using partition key ((order_date))."""
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError(message=f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD.")

        session = get_cassandra_session()
        analytics = CassandraAnalytics(session)
        results = analytics.get_sales_for_date(parsed_date)
        return [DateSalesItem(**r) for r in results]

    @staticmethod
    def get_sales_by_region_date(region: str, start_date: str, end_date: str) -> list[RegionDateSalesItem]:
        """Queries Cassandra sales_by_region_date table using partition key and clustering range scan."""
        if region not in VALID_REGIONS:
            raise ValidationError(message=f"Invalid region: '{region}'. Supported regions: {sorted(list(VALID_REGIONS))}.")

        try:
            s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError(message="Invalid date format. Expected YYYY-MM-DD.")

        if s_date > e_date:
            raise ValidationError(message="start_date must be less than or equal to end_date.")

        session = get_cassandra_session()
        analytics = CassandraAnalytics(session)
        results = analytics.get_sales_by_region_range(region, s_date, e_date)
        return [RegionDateSalesItem(**r) for r in results]

    @staticmethod
    def get_sales_by_category_date(category: str, start_date: str, end_date: str) -> list[CategoryDateSalesItem]:
        """Queries Cassandra sales_by_category_date table using partition key and clustering range scan."""
        if category not in VALID_CATEGORIES:
            raise ValidationError(message=f"Invalid category: '{category}'. Supported categories: {sorted(list(VALID_CATEGORIES))}.")

        try:
            s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError(message="Invalid date format. Expected YYYY-MM-DD.")

        if s_date > e_date:
            raise ValidationError(message="start_date must be less than or equal to end_date.")

        session = get_cassandra_session()
        analytics = CassandraAnalytics(session)
        results = analytics.get_sales_by_category_range(category, s_date, e_date)
        return [CategoryDateSalesItem(**r) for r in results]
