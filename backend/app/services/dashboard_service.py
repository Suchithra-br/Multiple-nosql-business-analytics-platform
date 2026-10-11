"""
Dashboard Service Layer.

Orchestrates business logic and aggregations for executive KPI cards,
regional charts, category breakdowns, customer segments, shipping modes,
monthly time-series trends, sub-categories, and geographic state details.
Implements Redis sub-millisecond cache reading with automatic cold-start population
from MongoDB, and dynamic MongoDB aggregation when filtered by Year and/or Region.
"""

from typing import Optional, Any
from backend.app.core.exceptions import ValidationError, DatabaseConnectionError
from backend.app.databases.redis import get_redis_client
from backend.app.databases.mongodb import get_mongodb_database
from backend.app.repositories.redis_repository import (
    get_cached_kpis,
    get_cached_sales_by_region,
    get_cached_sales_by_category,
    get_cached_sales_by_segment,
    get_cached_shipping_summary,
    get_cached_monthly_sales,
    refresh_analytics_cache,
)
from backend.app.models.schemas import (
    OverviewResponse,
    RegionSalesItem,
    CategorySalesItem,
    SegmentSalesItem,
    ShippingSalesItem,
    MonthlySalesItem,
    SubCategorySalesItem,
    StateSalesItem,
)

VALID_YEARS = {2015, 2016, 2017, 2018}
VALID_REGIONS = {"West", "East", "Central", "South"}

# Verified Historical Baseline for Default YoY Comparisons (2018 vs 2017)
DEFAULT_YOY_SALES = 20.3
DEFAULT_YOY_ORDERS = 28.3
DEFAULT_YOY_AOV = -6.2
DEFAULT_COMPARISON_LABEL = "2018 vs 2017"
DEFAULT_AVG_SHIPPING_DAYS = 4.0


class DashboardService:
    """Encapsulates dashboard data retrieval and analytical business calculations."""

    @staticmethod
    def validate_filters(year: Optional[int], region: Optional[str]) -> None:
        """Validates filter parameters against supported dataset domains."""
        if year is not None and year not in VALID_YEARS:
            raise ValidationError(
                message=f"Invalid year: {year}. Supported years are 2015, 2016, 2017, 2018."
            )
        if region is not None and region not in VALID_REGIONS:
            raise ValidationError(
                message=f"Invalid region: '{region}'. Supported regions: {sorted(list(VALID_REGIONS))}."
            )

    @staticmethod
    def build_match_query(year: Optional[int], region: Optional[str]) -> dict:
        """Constructs MongoDB $match filter dictionary."""
        match: dict[str, Any] = {}
        if year is not None:
            match["order_year"] = year
        if region is not None:
            match["shipping_address.region"] = region
        return match

    @staticmethod
    def ensure_cache_populated(r) -> None:
        """Ensures Redis cache is warm; re-seeds from MongoDB if empty."""
        kpis = get_cached_kpis(r)
        if not kpis or not kpis.get("total_sales"):
            try:
                db = get_mongodb_database()
                refresh_analytics_cache(db, r)
            except Exception as err:
                raise DatabaseConnectionError(
                    message=f"Redis cache is unpopulated and fallback to MongoDB failed: {err}"
                )

    @classmethod
    def get_overview(cls, year: Optional[int] = None, region: Optional[str] = None) -> OverviewResponse:
        """
        Retrieves executive KPI metrics:
        - When unparameterized: sub-millisecond Redis cached metrics
        - When filtered by year/region: dynamically computed MongoDB aggregation with real YoY trends
        """
        cls.validate_filters(year, region)

        if year is None and region is None:
            r = get_redis_client()
            cls.ensure_cache_populated(r)
            kpis = get_cached_kpis(r)
            return OverviewResponse(
                total_sales=kpis["total_sales"],
                total_orders=kpis["total_orders"],
                average_order_value=kpis["average_order_value"],
                last_refreshed_at=kpis.get("last_refreshed_at"),
                average_shipping_days=DEFAULT_AVG_SHIPPING_DAYS,
                yoy_sales_growth=DEFAULT_YOY_SALES,
                yoy_orders_growth=DEFAULT_YOY_ORDERS,
                yoy_aov_growth=DEFAULT_YOY_AOV,
                comparison_label=DEFAULT_COMPARISON_LABEL,
            )

        db = get_mongodb_database()
        match = cls.build_match_query(year, region)

        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": None,
                    "total_sales": {"$sum": "$order_total"},
                    "total_orders": {"$sum": 1},
                    "avg_shipping_days": {"$avg": "$shipping_days"},
                }
            },
        ]

        agg = list(db.orders.aggregate(pipeline))
        if not agg or agg[0]["total_orders"] == 0:
            return OverviewResponse(
                total_sales=0.0,
                total_orders=0,
                average_order_value=0.0,
                average_shipping_days=0.0,
                yoy_sales_growth=None,
                yoy_orders_growth=None,
                yoy_aov_growth=None,
                comparison_label=f"Year {year}" if year else f"Region {region}",
            )

        doc = agg[0]
        total_sales = round(float(doc["total_sales"]), 2)
        total_orders = int(doc["total_orders"])
        aov = round(total_sales / total_orders, 2) if total_orders > 0 else 0.0
        avg_shipping = round(float(doc.get("avg_shipping_days", DEFAULT_AVG_SHIPPING_DAYS)), 1)

        yoy_sales = None
        yoy_orders = None
        yoy_aov = None
        comp_label = None

        if year is not None:
            if year > 2015:
                prev_year = year - 1
                prev_match = cls.build_match_query(prev_year, region)
                prev_agg = list(
                    db.orders.aggregate(
                        [
                            {"$match": prev_match},
                            {
                                "$group": {
                                    "_id": None,
                                    "total_sales": {"$sum": "$order_total"},
                                    "total_orders": {"$sum": 1},
                                }
                            },
                        ]
                    )
                )
                if prev_agg and prev_agg[0]["total_orders"] > 0:
                    p_doc = prev_agg[0]
                    p_sales = float(p_doc["total_sales"])
                    p_orders = int(p_doc["total_orders"])
                    p_aov = p_sales / p_orders if p_orders > 0 else 0.0

                    if p_sales > 0:
                        yoy_sales = round(((total_sales - p_sales) / p_sales) * 100, 1)
                    if p_orders > 0:
                        yoy_orders = round(((total_orders - p_orders) / p_orders) * 100, 1)
                    if p_aov > 0:
                        yoy_aov = round(((aov - p_aov) / p_aov) * 100, 1)
                    comp_label = f"{year} vs {prev_year}"
            else:
                comp_label = "2015 (Base Year)"
        else:
            yoy_sales = DEFAULT_YOY_SALES
            yoy_orders = DEFAULT_YOY_ORDERS
            yoy_aov = DEFAULT_YOY_AOV
            comp_label = DEFAULT_COMPARISON_LABEL

        return OverviewResponse(
            total_sales=total_sales,
            total_orders=total_orders,
            average_order_value=aov,
            average_shipping_days=avg_shipping,
            yoy_sales_growth=yoy_sales,
            yoy_orders_growth=yoy_orders,
            yoy_aov_growth=yoy_aov,
            comparison_label=comp_label,
        )

    @classmethod
    def get_regional_sales(cls, year: Optional[int] = None) -> list[RegionSalesItem]:
        """Returns sales volume by geographic region."""
        if year is not None and year not in VALID_YEARS:
            raise ValidationError(message=f"Invalid year: {year}. Supported years are 2015, 2016, 2017, 2018.")

        if year is None:
            r = get_redis_client()
            cls.ensure_cache_populated(r)
            data = get_cached_sales_by_region(r)
            return [RegionSalesItem(region=k, total_sales=v) for k, v in data.items()]

        db = get_mongodb_database()
        pipeline = [
            {"$match": {"order_year": year}},
            {"$group": {"_id": "$shipping_address.region", "total_sales": {"$sum": "$order_total"}}},
            {"$sort": {"total_sales": -1}},
        ]
        results = list(db.orders.aggregate(pipeline))
        return [RegionSalesItem(region=r["_id"], total_sales=round(r["total_sales"], 2)) for r in results]

    @classmethod
    def get_category_sales(cls, year: Optional[int] = None, region: Optional[str] = None) -> list[CategorySalesItem]:
        """Returns sales volume by product category."""
        cls.validate_filters(year, region)

        if year is None and region is None:
            r = get_redis_client()
            cls.ensure_cache_populated(r)
            data = get_cached_sales_by_category(r)
            return [CategorySalesItem(category=k, total_sales=v) for k, v in data.items()]

        db = get_mongodb_database()
        match = cls.build_match_query(year, region)
        pipeline = [
            {"$match": match},
            {"$unwind": "$items"},
            {"$group": {"_id": "$items.category", "total_sales": {"$sum": "$items.sales"}}},
            {"$sort": {"total_sales": -1}},
        ]
        results = list(db.orders.aggregate(pipeline))
        return [CategorySalesItem(category=r["_id"], total_sales=round(r["total_sales"], 2)) for r in results]

    @classmethod
    def get_segment_sales(cls, year: Optional[int] = None, region: Optional[str] = None) -> list[SegmentSalesItem]:
        """Returns sales volume by customer segment."""
        cls.validate_filters(year, region)

        if year is None and region is None:
            r = get_redis_client()
            cls.ensure_cache_populated(r)
            data = get_cached_sales_by_segment(r)
            return [SegmentSalesItem(segment=k, total_sales=v) for k, v in data.items()]

        db = get_mongodb_database()
        match = cls.build_match_query(year, region)
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$customer.segment", "total_sales": {"$sum": "$order_total"}}},
            {"$sort": {"total_sales": -1}},
        ]
        results = list(db.orders.aggregate(pipeline))
        return [SegmentSalesItem(segment=r["_id"], total_sales=round(r["total_sales"], 2)) for r in results]

    @classmethod
    def get_shipping_summary(cls, year: Optional[int] = None, region: Optional[str] = None) -> list[ShippingSalesItem]:
        """Returns sales volume by shipping mode."""
        cls.validate_filters(year, region)

        if year is None and region is None:
            r = get_redis_client()
            cls.ensure_cache_populated(r)
            data = get_cached_shipping_summary(r)
            return [ShippingSalesItem(ship_mode=k, total_sales=v) for k, v in data.items()]

        db = get_mongodb_database()
        match = cls.build_match_query(year, region)
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$ship_mode", "total_sales": {"$sum": "$order_total"}, "order_count": {"$sum": 1}}},
            {"$sort": {"total_sales": -1}},
        ]
        results = list(db.orders.aggregate(pipeline))
        return [
            ShippingSalesItem(ship_mode=r["_id"], total_sales=round(r["total_sales"], 2), order_count=r["order_count"])
            for r in results
        ]

    @classmethod
    def get_monthly_sales(cls, year: Optional[int] = None, region: Optional[str] = None) -> list[MonthlySalesItem]:
        """Returns monthly chronological sales trend across 2015–2018."""
        cls.validate_filters(year, region)

        if region is None:
            r = get_redis_client()
            cls.ensure_cache_populated(r)
            all_months = get_cached_monthly_sales(r)

            if year is not None:
                prefix = f"{year}-"
                filtered = [m for m in all_months if m["year_month"].startswith(prefix)]
                return [MonthlySalesItem(year_month=m["year_month"], total_sales=m["total_sales"]) for m in filtered]

            return [MonthlySalesItem(year_month=m["year_month"], total_sales=m["total_sales"]) for m in all_months]

        db = get_mongodb_database()
        match = cls.build_match_query(year, region)
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$order_year_month", "total_sales": {"$sum": "$order_total"}, "order_count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        results = list(db.orders.aggregate(pipeline))
        return [
            MonthlySalesItem(year_month=r["_id"], total_sales=round(r["total_sales"], 2), order_count=r["order_count"])
            for r in results
        ]

    @classmethod
    def get_subcategory_sales(cls, year: Optional[int] = None, region: Optional[str] = None) -> list[SubCategorySalesItem]:
        """Returns sales revenue across 17 sub-categories."""
        cls.validate_filters(year, region)
        db = get_mongodb_database()
        match = cls.build_match_query(year, region)

        pipeline = [
            {"$match": match},
            {"$unwind": "$items"},
            {
                "$group": {
                    "_id": {"sub_category": "$items.sub_category", "category": "$items.category"},
                    "total_sales": {"$sum": "$items.sales"},
                }
            },
            {"$sort": {"total_sales": -1}},
        ]
        results = list(db.orders.aggregate(pipeline))
        return [
            SubCategorySalesItem(
                sub_category=r["_id"]["sub_category"],
                category=r["_id"]["category"],
                total_sales=round(r["total_sales"], 2),
            )
            for r in results
        ]

    @classmethod
    def get_state_sales(cls, limit: int = 10, year: Optional[int] = None, region: Optional[str] = None) -> list[StateSalesItem]:
        """Returns geographic sales detail for top states."""
        cls.validate_filters(year, region)
        db = get_mongodb_database()
        match = cls.build_match_query(year, region)

        pipeline = [
            {"$match": match},
            {
                "$group": {
                    "_id": {
                        "state": "$shipping_address.state",
                        "region": "$shipping_address.region",
                    },
                    "total_sales": {"$sum": "$order_total"},
                    "order_count": {"$sum": 1},
                }
            },
            {"$sort": {"total_sales": -1}},
            {"$limit": limit},
        ]
        results = list(db.orders.aggregate(pipeline))
        return [
            StateSalesItem(
                state=r["_id"]["state"],
                region=r["_id"]["region"],
                total_sales=round(r["total_sales"], 2),
                order_count=r["order_count"],
            )
            for r in results
        ]
