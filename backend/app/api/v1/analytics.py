"""
Analytics & Operational Query Endpoints (API v1).

Thin route layer delegating Redis leaderboards, MongoDB operational document lookups,
and Apache Cassandra time-series queries to AnalyticsService.
"""

from typing import Optional
from fastapi import APIRouter, Query
from backend.app.services.analytics_service import AnalyticsService
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

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ==============================================================================
# Leaderboard Analytics
# ==============================================================================

@router.get("/products/top", response_model=list[TopProductItem], summary="Top Products Leaderboard")
def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of products to return (1-100)"),
    year: Optional[int] = Query(None, description="Optional calendar year filter (2015-2018)"),
    region: Optional[str] = Query(None, description="Optional region filter (West, East, Central, South)"),
):
    """Retrieves top products ranked by cumulative sales revenue."""
    return AnalyticsService.get_top_products(limit=limit, year=year, region=region)


@router.get("/customers/top", response_model=list[TopCustomerItem], summary="Top Customers Leaderboard")
def get_top_customers(
    limit: int = Query(10, ge=1, le=100, description="Number of customers to return (1-100)"),
    year: Optional[int] = Query(None, description="Optional calendar year filter (2015-2018)"),
    region: Optional[str] = Query(None, description="Optional region filter (West, East, Central, South)"),
):
    """Retrieves top customers ranked by cumulative spend."""
    return AnalyticsService.get_top_customers(limit=limit, year=year, region=region)


# ==============================================================================
# Search & Operational Document Lookups (MongoDB)
# ==============================================================================

@router.get("/customers/search", response_model=list[CustomerSearchItem], summary="Customer Search / Autocomplete (MongoDB)")
def search_customers(
    q: str = Query(..., min_length=1, description="Customer name or ID search query"),
    limit: int = Query(10, ge=1, le=20, description="Max search results to return"),
):
    """Searches customer records by name or customer ID for live autocomplete."""
    return AnalyticsService.search_customers(query=q, limit=limit)


@router.get("/orders/search", response_model=list[OrderSearchItem], summary="Order Search / Autocomplete (MongoDB)")
def search_orders(
    q: str = Query(..., min_length=1, description="Order ID search query"),
    limit: int = Query(10, ge=1, le=20, description="Max search results to return"),
):
    """Searches orders by order ID prefix for live autocomplete."""
    return AnalyticsService.search_orders(query=q, limit=limit)


@router.get("/orders/{order_id}", response_model=OrderDetailResponse, summary="Operational Order Lookup (MongoDB)")
def get_order_by_id(order_id: str):
    """Retrieves full denormalized order document with embedded items."""
    return AnalyticsService.get_order_by_id(order_id=order_id)


@router.get("/customers/{customer_id}", response_model=CustomerProfileResponse, summary="Customer Profile Lookup (MongoDB)")
def get_customer_by_id(customer_id: str):
    """Retrieves customer business profile and order history."""
    return AnalyticsService.get_customer_by_id(customer_id=customer_id)


# ==============================================================================
# Cassandra Time-Series Analytics
# ==============================================================================

@router.get("/date", response_model=list[DateSalesItem], summary="Daily Sales Slice (Cassandra)")
def get_sales_for_date(
    date: str = Query(..., description="Target order date (YYYY-MM-DD), e.g. '2017-11-08'"),
):
    """Queries Cassandra sales_by_date table using partition key ((order_date))."""
    return AnalyticsService.get_sales_by_date(date_str=date)


@router.get("/region-date", response_model=list[RegionDateSalesItem], summary="Regional Time-Series Slice (Cassandra)")
def get_sales_by_region_date(
    region: str = Query(..., description="Geographic region: West, East, Central, South"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Queries Cassandra sales_by_region_date table using partition key and clustering range."""
    return AnalyticsService.get_sales_by_region_date(region=region, start_date=start_date, end_date=end_date)


@router.get("/category-date", response_model=list[CategoryDateSalesItem], summary="Category Time-Series Slice (Cassandra)")
def get_sales_by_category_date(
    category: str = Query(..., description="Category: Technology, Furniture, Office Supplies"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Queries Cassandra sales_by_category_date table using partition key and clustering range."""
    return AnalyticsService.get_sales_by_category_date(category=category, start_date=start_date, end_date=end_date)
