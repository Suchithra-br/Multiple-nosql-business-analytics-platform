"""
Dashboard KPI & Aggregation Endpoints (API v1).

Thin route layer delegating executive KPI cards, charts, and breakdown logic
to DashboardService.
"""

from typing import Optional
from fastapi import APIRouter, Query
from backend.app.services.dashboard_service import DashboardService
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

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=OverviewResponse, summary="Executive Dashboard KPI Overview")
def get_dashboard_overview(
    year: Optional[int] = Query(None, description="Optional calendar year filter (2015-2018)"),
    region: Optional[str] = Query(None, description="Optional region filter (West, East, Central, South)"),
):
    """Returns platform-wide KPIs with YoY comparisons."""
    return DashboardService.get_overview(year=year, region=region)


@router.get("/regions", response_model=list[RegionSalesItem], summary="Regional Sales Breakdown")
def get_dashboard_regions(
    year: Optional[int] = Query(None, description="Optional calendar year filter (2015-2018)"),
):
    """Returns sales volume by geographic region."""
    return DashboardService.get_regional_sales(year=year)


@router.get("/categories", response_model=list[CategorySalesItem], summary="Category Sales Breakdown")
def get_dashboard_categories(
    year: Optional[int] = Query(None, description="Optional calendar year filter (2015-2018)"),
    region: Optional[str] = Query(None, description="Optional region filter (West, East, Central, South)"),
):
    """Returns sales volume by product category."""
    return DashboardService.get_category_sales(year=year, region=region)


@router.get("/segments", response_model=list[SegmentSalesItem], summary="Customer Segment Sales Breakdown")
def get_dashboard_segments(
    year: Optional[int] = Query(None, description="Optional calendar year filter (2015-2018)"),
    region: Optional[str] = Query(None, description="Optional region filter (West, East, Central, South)"),
):
    """Returns sales volume by customer segment."""
    return DashboardService.get_segment_sales(year=year, region=region)


@router.get("/shipping", response_model=list[ShippingSalesItem], summary="Shipping Mode Breakdown")
def get_dashboard_shipping(
    year: Optional[int] = Query(None, description="Optional calendar year filter (2015-2018)"),
    region: Optional[str] = Query(None, description="Optional region filter (West, East, Central, South)"),
):
    """Returns sales volume by shipping mode."""
    return DashboardService.get_shipping_summary(year=year, region=region)


@router.get("/monthly", response_model=list[MonthlySalesItem], summary="Monthly Sales Time-Series")
def get_dashboard_monthly(
    year: Optional[int] = Query(None, description="Optional calendar year filter (2015-2018)"),
    region: Optional[str] = Query(None, description="Optional region filter (West, East, Central, South)"),
):
    """Returns monthly chronological sales trend across 2015-2018."""
    return DashboardService.get_monthly_sales(year=year, region=region)


@router.get("/subcategories", response_model=list[SubCategorySalesItem], summary="Sub-Category Sales Breakdown")
def get_dashboard_subcategories(
    year: Optional[int] = Query(None, description="Optional calendar year filter (2015-2018)"),
    region: Optional[str] = Query(None, description="Optional region filter (West, East, Central, South)"),
):
    """Returns sales revenue across all 17 Superstore sub-categories."""
    return DashboardService.get_subcategory_sales(year=year, region=region)


@router.get("/states", response_model=list[StateSalesItem], summary="Top States by Sales Volume")
def get_dashboard_states(
    year: Optional[int] = Query(None, description="Optional calendar year filter (2015-2018)"),
    region: Optional[str] = Query(None, description="Optional region filter (West, East, Central, South)"),
    limit: int = Query(10, ge=1, le=50, description="Top N states to return (default 10)"),
):
    """Returns geographic sales detail for top states."""
    return DashboardService.get_state_sales(limit=limit, year=year, region=region)
