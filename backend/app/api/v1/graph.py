"""
Graph Analytics Endpoints (API v1).

Thin route layer delegating Neo4j graph traversals and recommendations
to GraphService.
"""

from fastapi import APIRouter, Query
from backend.app.services.graph_service import GraphService
from backend.app.models.schemas import (
    GraphOrderItem,
    GraphCustomerProductItem,
    CoPurchaseItem,
    RegionCategoryGraphItem,
)

router = APIRouter(prefix="/analytics/graph", tags=["Graph Analytics"])


@router.get("/customer/{customer_id}/orders", response_model=list[GraphOrderItem], summary="Orders Placed by Customer (Neo4j)")
def get_customer_orders_graph(customer_id: str):
    """Traverses (Customer)-[:PLACED]->(Order) path in Neo4j."""
    return GraphService.get_customer_orders(customer_id=customer_id)


@router.get("/customer/{customer_id}/products", response_model=list[GraphCustomerProductItem], summary="Products Purchased by Customer (Neo4j)")
def get_customer_products_graph(customer_id: str):
    """Traverses (Customer)-[:PLACED]->(:Order)-[:CONTAINS]->(Product) path in Neo4j."""
    return GraphService.get_customer_products(customer_id=customer_id)


@router.get("/product/{product_id}/copurchases", response_model=list[CoPurchaseItem], summary="Product Co-Purchasing Recommendations (Neo4j)")
def get_product_copurchases(
    product_id: str,
    limit: int = Query(10, ge=1, le=50, description="Max recommendations (1-50)"),
):
    """Traverses product co-purchasing graph for collaborative recommendations."""
    return GraphService.get_product_copurchases(product_id=product_id, limit=limit)


@router.get("/region/{region}/categories", response_model=list[RegionCategoryGraphItem], summary="Regional Category Breakdown (Neo4j)")
def get_region_categories_graph(region: str):
    """Traverses 6-hop graph hierarchy to compute regional category sales."""
    return GraphService.get_region_categories(region=region)
