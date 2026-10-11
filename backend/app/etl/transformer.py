"""
ETL Transformer Module.

Derives valid temporal dimensions and creates normalized entity dataframes:
- cleaned_sales (full 9,800 transactions with derived temporal fields)
- orders (4,922 unique orders)
- order_items (9,800 transaction line items)
- customers (793 customer master profiles)
- products (1,861 product catalog records)
- locations (628 unique geographic entities)

STRICT RULE ENFORCEMENT:
Does NOT create profit, discount, quantity, profit_margin, cost, or any
unsupported/fictitious business metric.
"""

import logging
from dataclasses import dataclass
import pandas as pd
import numpy as np

logger = logging.getLogger("etl.transformer")


@dataclass
class TransformedDatasets:
    """Container holding all derived and normalized entity DataFrames."""
    cleaned_sales: pd.DataFrame
    orders: pd.DataFrame
    order_items: pd.DataFrame
    customers: pd.DataFrame
    products: pd.DataFrame
    locations: pd.DataFrame


def add_derived_temporal_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes logically derivable temporal fields from order_date and ship_date.
    
    Fields added:
    - shipping_days = (ship_date - order_date).dt.days
    - order_year = order_date.dt.year
    - order_month = order_date.dt.month
    - order_month_name = order_date.dt.month_name()
    - order_quarter = 'Q' + order_date.dt.quarter.astype(str)
    - order_year_month = order_date.dt.strftime('%Y-%m')
    """
    df = df.copy(deep=True)
    logger.info("Computing derived temporal fields...")

    shipping_diff = (df["ship_date"] - df["order_date"]).dt.days
    df["shipping_days"] = shipping_diff.astype(int)
    df["order_year"] = df["order_date"].dt.year.astype(int)
    df["order_month"] = df["order_date"].dt.month.astype(int)
    df["order_month_name"] = df["order_date"].dt.month_name()
    df["order_quarter"] = "Q" + df["order_date"].dt.quarter.astype(str)
    df["order_year_month"] = df["order_date"].dt.strftime("%Y-%m")

    logger.info(
        f"Derived fields added: shipping_days (min={df['shipping_days'].min()}, max={df['shipping_days'].max()}), "
        f"order_year ({df['order_year'].min()}-{df['order_year'].max()})."
    )
    return df


def create_orders_entity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the 'orders' entity DataFrame with 1 record per unique order_id (4,922 rows).
    """
    logger.info("Building 'orders' entity DataFrame...")

    orders = (
        df.groupby("order_id", as_index=False)
        .agg(
            order_date=("order_date", "first"),
            ship_date=("ship_date", "first"),
            ship_mode=("ship_mode", "first"),
            customer_id=("customer_id", "first"),
            country=("country", "first"),
            region=("region", "first"),
            state=("state", "first"),
            city=("city", "first"),
            postal_code=("postal_code", "first"),
            shipping_days=("shipping_days", "first"),
            order_year=("order_year", "first"),
            order_month=("order_month", "first"),
            order_month_name=("order_month_name", "first"),
            order_quarter=("order_quarter", "first"),
            order_year_month=("order_year_month", "first"),
            item_count=("row_id", "count"),
            order_total_sales=("sales", "sum"),
        )
        .sort_values(by=["order_date", "order_id"])
        .reset_index(drop=True)
    )

    orders["order_total_sales"] = orders["order_total_sales"].round(4)
    logger.info(f"Built 'orders' DataFrame: {len(orders)} unique orders, Total Sales: ${orders['order_total_sales'].sum():,.4f}")
    return orders


def create_order_items_entity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the 'order_items' entity DataFrame with 1 record per original row_id (9,800 rows).
    """
    logger.info("Building 'order_items' entity DataFrame...")

    items_cols = [
        "row_id",
        "order_id",
        "product_id",
        "product_name",
        "category",
        "sub_category",
        "sales",
    ]
    order_items = df[items_cols].copy(deep=True)
    order_items["sales"] = order_items["sales"].round(4)
    order_items = order_items.sort_values(by="row_id").reset_index(drop=True)

    logger.info(f"Built 'order_items' DataFrame: {len(order_items)} items, Total Sales: ${order_items['sales'].sum():,.4f}")
    return order_items


def create_customers_entity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the 'customers' entity DataFrame with 1 record per unique customer_id (793 rows).
    """
    logger.info("Building 'customers' entity DataFrame...")

    # Primary region per customer (region with highest spend)
    cust_region = (
        df.groupby(["customer_id", "region"])["sales"]
        .sum()
        .reset_index()
        .sort_values(["customer_id", "sales"], ascending=[True, False])
        .drop_duplicates(subset=["customer_id"])
        .set_index("customer_id")["region"]
    )

    customers = (
        df.groupby("customer_id", as_index=False)
        .agg(
            customer_name=("customer_name", "first"),
            segment=("segment", "first"),
            total_spend=("sales", "sum"),
            order_count=("order_id", "nunique"),
            first_order_date=("order_date", "min"),
            last_order_date=("order_date", "max"),
        )
        .sort_values(by="customer_id")
        .reset_index(drop=True)
    )

    customers["primary_region"] = customers["customer_id"].map(cust_region)
    customers["total_spend"] = customers["total_spend"].round(4)

    logger.info(f"Built 'customers' DataFrame: {len(customers)} unique customers, Total Spend: ${customers['total_spend'].sum():,.4f}")
    return customers


def create_products_entity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the 'products' entity DataFrame with 1 record per unique product_id (1,861 rows).
    
    Handles the 32 verified product variant name variations by setting canonical product_name
    to the most frequent name while recording variant_names_count.
    """
    logger.info("Building 'products' entity DataFrame...")

    # Canonical product name: most frequent name in dataset
    def get_canonical_name(series: pd.Series) -> str:
        mode = series.mode()
        return str(mode[0]) if not mode.empty else str(series.iloc[0])

    products = (
        df.groupby("product_id", as_index=False)
        .agg(
            product_name=("product_name", get_canonical_name),
            category=("category", "first"),
            sub_category=("sub_category", "first"),
            total_sales=("sales", "sum"),
            order_count=("order_id", "nunique"),
            variant_names_count=("product_name", "nunique"),
        )
        .sort_values(by="product_id")
        .reset_index(drop=True)
    )

    products["total_sales"] = products["total_sales"].round(4)
    logger.info(f"Built 'products' DataFrame: {len(products)} unique products, Total Sales: ${products['total_sales'].sum():,.4f}")
    return products


def create_locations_entity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the 'locations' entity DataFrame for distinct geographic points (628 rows).
    """
    logger.info("Building 'locations' entity DataFrame...")

    loc_df = (
        df.groupby(["country", "region", "state", "city", "postal_code"], as_index=False, dropna=False)
        .agg(
            total_sales=("sales", "sum"),
            order_count=("order_id", "nunique"),
            transaction_count=("row_id", "count"),
        )
        .sort_values(by=["region", "state", "city"])
        .reset_index(drop=True)
    )

    loc_df.insert(0, "location_id", [f"LOC-{i+1:04d}" for i in range(len(loc_df))])
    loc_df["total_sales"] = loc_df["total_sales"].round(4)

    logger.info(f"Built 'locations' DataFrame: {len(loc_df)} unique geographic locations.")
    return loc_df


def transform_data(cleaned_df: pd.DataFrame) -> TransformedDatasets:
    """
    Executes the full transformation pipeline:
    1. Adds derived temporal fields to cleaned transactions.
    2. Constructs normalized entity DataFrames (orders, order_items, customers, products, locations).
    
    Args:
        cleaned_df: Cleaned transaction DataFrame.
        
    Returns:
        TransformedDatasets dataclass containing all DataFrames.
    """
    logger.info("Starting dataset transformations...")

    # 1. Transactions with derived fields
    cleaned_sales = add_derived_temporal_fields(cleaned_df)

    # 2. Normalized entities
    orders = create_orders_entity(cleaned_sales)
    order_items = create_order_items_entity(cleaned_sales)
    customers = create_customers_entity(cleaned_sales)
    products = create_products_entity(cleaned_sales)
    locations = create_locations_entity(cleaned_sales)

    logger.info("All transformations completed successfully.")
    return TransformedDatasets(
        cleaned_sales=cleaned_sales,
        orders=orders,
        order_items=order_items,
        customers=customers,
        products=products,
        locations=locations,
    )
