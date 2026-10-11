"""
Unit tests for ETL transformer module.
"""

import pandas as pd
import pytest

from backend.app.etl.transformer import (
    add_derived_temporal_fields,
    create_orders_entity,
    create_order_items_entity,
    create_customers_entity,
    create_products_entity,
    create_locations_entity,
    transform_data,
)


@pytest.fixture
def sample_cleaned_df():
    """Returns sample cleaned data representing 2 orders and 3 items."""
    return pd.DataFrame([
        {
            "row_id": 1,
            "order_id": "CA-2017-1001",
            "order_date": pd.Timestamp("2017-11-08"),
            "ship_date": pd.Timestamp("2017-11-11"),
            "ship_mode": "Second Class",
            "customer_id": "CG-12520",
            "customer_name": "Claire Gute",
            "segment": "Consumer",
            "country": "United States",
            "city": "Henderson",
            "state": "Kentucky",
            "postal_code": "42420",
            "region": "South",
            "product_id": "FUR-BO-10001798",
            "category": "Furniture",
            "sub_category": "Bookcases",
            "product_name": "Bush Somerset Collection Bookcase",
            "sales": 261.96,
        },
        {
            "row_id": 2,
            "order_id": "CA-2017-1001",
            "order_date": pd.Timestamp("2017-11-08"),
            "ship_date": pd.Timestamp("2017-11-11"),
            "ship_mode": "Second Class",
            "customer_id": "CG-12520",
            "customer_name": "Claire Gute",
            "segment": "Consumer",
            "country": "United States",
            "city": "Henderson",
            "state": "Kentucky",
            "postal_code": "42420",
            "region": "South",
            "product_id": "FUR-CH-10000454",
            "category": "Furniture",
            "sub_category": "Chairs",
            "product_name": "Hon Deluxe Fabric Upholstered Stacking Chairs",
            "sales": 731.94,
        },
        {
            "row_id": 3,
            "order_id": "CA-2018-2002",
            "order_date": pd.Timestamp("2018-04-15"),
            "ship_date": pd.Timestamp("2018-04-20"),
            "ship_mode": "Standard Class",
            "customer_id": "AA-10480",
            "customer_name": "Andrew Allen",
            "segment": "Consumer",
            "country": "United States",
            "city": "Burlington",
            "state": "Vermont",
            "postal_code": None,  # Missing postal code
            "region": "East",
            "product_id": "OFF-PA-10002365",
            "category": "Office Supplies",
            "sub_category": "Paper",
            "product_name": "Xerox 1967",
            "sales": 15.552,
        },
    ])


def test_add_derived_temporal_fields(sample_cleaned_df):
    """Ensure derived fields are calculated correctly from order_date and ship_date."""
    df_derived = add_derived_temporal_fields(sample_cleaned_df)

    # Check calculated fields
    assert "shipping_days" in df_derived.columns
    assert "order_year" in df_derived.columns
    assert "order_month" in df_derived.columns
    assert "order_month_name" in df_derived.columns
    assert "order_quarter" in df_derived.columns
    assert "order_year_month" in df_derived.columns

    # Verify values
    assert df_derived.loc[0, "shipping_days"] == 3
    assert df_derived.loc[0, "order_year"] == 2017
    assert df_derived.loc[0, "order_month"] == 11
    assert df_derived.loc[0, "order_month_name"] == "November"
    assert df_derived.loc[0, "order_quarter"] == "Q4"
    assert df_derived.loc[0, "order_year_month"] == "2017-11"

    # Verify prohibited fields are strictly absent
    for prohibited in ["profit", "discount", "quantity", "cost", "margin", "customer_age"]:
        assert prohibited not in df_derived.columns


def test_create_orders_entity(sample_cleaned_df):
    """Ensure orders table aggregates items, preserves order-level sales sum, and deduplicates order IDs."""
    df_derived = add_derived_temporal_fields(sample_cleaned_df)
    orders = create_orders_entity(df_derived)

    assert len(orders) == 2  # 2 distinct orders
    assert orders.loc[orders["order_id"] == "CA-2017-1001", "item_count"].values[0] == 2
    assert orders.loc[orders["order_id"] == "CA-2017-1001", "order_total_sales"].values[0] == round(261.96 + 731.94, 4)

    # Total sales preservation across orders
    assert round(orders["order_total_sales"].sum(), 4) == round(sample_cleaned_df["sales"].sum(), 4)


def test_create_customers_entity(sample_cleaned_df):
    """Ensure customers table aggregates spend and counts correctly."""
    df_derived = add_derived_temporal_fields(sample_cleaned_df)
    customers = create_customers_entity(df_derived)

    assert len(customers) == 2  # 2 distinct customers
    cg = customers[customers["customer_id"] == "CG-12520"].iloc[0]
    assert cg["total_spend"] == round(261.96 + 731.94, 4)
    assert cg["order_count"] == 1
    assert cg["primary_region"] == "South"


def test_create_products_entity(sample_cleaned_df):
    """Ensure products table has 1 record per product ID and canonical product name."""
    df_derived = add_derived_temporal_fields(sample_cleaned_df)
    products = create_products_entity(df_derived)

    assert len(products) == 3  # 3 distinct products
    assert round(products["total_sales"].sum(), 4) == round(sample_cleaned_df["sales"].sum(), 4)


def test_transform_data_pipeline(sample_cleaned_df):
    """Ensure transform_data orchestrates all entity creations successfully."""
    datasets = transform_data(sample_cleaned_df)

    assert len(datasets.cleaned_sales) == 3
    assert len(datasets.orders) == 2
    assert len(datasets.order_items) == 3
    assert len(datasets.customers) == 2
    assert len(datasets.products) == 3
    assert len(datasets.locations) == 2  # Henderson, KY and Burlington, VT
