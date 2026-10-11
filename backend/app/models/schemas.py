"""
Pydantic Schemas for Multi-NoSQL Business Analytics API.

Defines concise, structured request and response models for:
- Health and database readiness diagnostics
- Dashboard overview KPIs and cached aggregations
- Top products and top customers leaderboards
- Operational MongoDB orders and customer profiles
- Query-driven Cassandra time-series slices
- Neo4j graph co-purchasing and regional network traversals
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


# ==============================================================================
# Health Diagnostics
# ==============================================================================

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall API health state ('healthy' or 'degraded')")
    databases: dict[str, str] = Field(..., description="Status of MongoDB, Redis, Cassandra, and Neo4j")


# ==============================================================================
# Dashboard Cached Metrics (Redis)
# ==============================================================================

class OverviewResponse(BaseModel):
    total_sales: float = Field(..., description="Total platform revenue from verified dataset")
    total_orders: int = Field(..., description="Total unique orders count")
    average_order_value: float = Field(..., description="Average sales revenue per order")
    last_refreshed_at: Optional[str] = Field(None, description="ISO timestamp of last cache refresh")
    average_shipping_days: Optional[float] = Field(None, description="Average shipping duration in days")
    yoy_sales_growth: Optional[float] = Field(None, description="Year-over-year sales percentage growth")
    yoy_orders_growth: Optional[float] = Field(None, description="Year-over-year orders percentage growth")
    yoy_aov_growth: Optional[float] = Field(None, description="Year-over-year AOV percentage growth")
    comparison_label: Optional[str] = Field(None, description="Year-over-year comparison period label, e.g. 2018 vs 2017")


class RegionSalesItem(BaseModel):
    region: str
    total_sales: float


class CategorySalesItem(BaseModel):
    category: str
    total_sales: float


class SegmentSalesItem(BaseModel):
    segment: str
    total_sales: float


class ShippingSalesItem(BaseModel):
    ship_mode: str
    total_sales: float
    order_count: Optional[int] = None


class MonthlySalesItem(BaseModel):
    year_month: str
    total_sales: float
    order_count: Optional[int] = None


class SubCategorySalesItem(BaseModel):
    sub_category: str
    category: str
    total_sales: float


class StateSalesItem(BaseModel):
    state: str
    region: str
    total_sales: float
    order_count: int


class TopProductItem(BaseModel):
    product_id: str
    product_name: str
    total_sales: float


class TopCustomerItem(BaseModel):
    customer_id: str
    customer_name: str
    total_spend: float


class CustomerSearchItem(BaseModel):
    customer_id: str
    customer_name: str
    segment: str
    primary_region: str


class OrderSearchItem(BaseModel):
    order_id: str
    order_date: str
    customer_name: str
    order_total: float


# ==============================================================================
# MongoDB Operational Models
# ==============================================================================

class OrderItemSchema(BaseModel):
    row_id: int
    product_id: str
    product_name: str
    category: str
    sub_category: str
    sales: float


class CustomerEmbedSchema(BaseModel):
    customer_id: str
    customer_name: str
    segment: str


class ShippingAddressSchema(BaseModel):
    country: str
    city: str
    state: str
    postal_code: Optional[str] = None
    region: str


class OrderDetailResponse(BaseModel):
    order_id: str
    order_date: str
    ship_date: str
    ship_mode: str
    customer: CustomerEmbedSchema
    shipping_address: ShippingAddressSchema
    items: list[OrderItemSchema]
    order_total: float
    order_year: int
    order_month: int
    order_quarter: str
    order_year_month: str
    shipping_days: int


class CustomerProfileResponse(BaseModel):
    customer_id: str
    customer_name: str
    segment: str
    primary_region: str
    order_count: int
    total_spend: float
    first_order_date: Optional[str] = None
    last_order_date: Optional[str] = None


# ==============================================================================
# Cassandra Time-Series Analytics
# ==============================================================================

class DateSalesItem(BaseModel):
    order_date: str
    order_id: str
    row_id: int
    product_id: str
    category: str
    sub_category: str
    region: str
    sales: float


class RegionDateSalesItem(BaseModel):
    region: str
    order_date: str
    order_id: str
    row_id: int
    category: str
    sales: float


class CategoryDateSalesItem(BaseModel):
    category: str
    order_date: str
    order_id: str
    row_id: int
    sub_category: str
    sales: float


# ==============================================================================
# Neo4j Graph Analytics
# ==============================================================================

class GraphOrderItem(BaseModel):
    order_id: str
    order_date: str
    ship_mode: str


class GraphCustomerProductItem(BaseModel):
    product_id: str
    product_name: str
    purchase_count: int
    total_spent: float


class CoPurchaseItem(BaseModel):
    product_id: str
    product_name: str
    times_co_purchased: int


class RegionCategoryGraphItem(BaseModel):
    category: str
    item_count: int
    total_sales: float


class RegionalProductItem(BaseModel):
    product_id: str
    product_name: str
    purchase_count: int
    total_sales: float
