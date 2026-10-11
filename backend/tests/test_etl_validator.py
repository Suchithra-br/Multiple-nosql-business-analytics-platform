"""
Unit tests for ETL validator module.
"""

import pandas as pd
import numpy as np
import pytest

from backend.app.etl.validator import (
    validate_raw_schema,
    validate_dates_and_shipping,
    validate_business_relationships,
    validate_sales_preservation,
    validate_entity_counts,
)


@pytest.fixture
def valid_sample_df():
    """Returns a minimal valid sample DataFrame conforming to raw dataset schema."""
    return pd.DataFrame([
        {
            "Row ID": 1,
            "Order ID": "CA-2017-1001",
            "Order Date": "08/11/2017",
            "Ship Date": "11/11/2017",
            "Ship Mode": "Second Class",
            "Customer ID": "CG-12520",
            "Customer Name": "Claire Gute",
            "Segment": "Consumer",
            "Country": "United States",
            "City": "Henderson",
            "State": "Kentucky",
            "Postal Code": 42420.0,
            "Region": "South",
            "Product ID": "FUR-BO-10001798",
            "Category": "Furniture",
            "Sub-Category": "Bookcases",
            "Product Name": "Bush Somerset Collection Bookcase",
            "Sales": 261.96,
        },
        {
            "Row ID": 2,
            "Order ID": "CA-2017-1001",
            "Order Date": "08/11/2017",
            "Ship Date": "11/11/2017",
            "Ship Mode": "Second Class",
            "Customer ID": "CG-12520",
            "Customer Name": "Claire Gute",
            "Segment": "Consumer",
            "Country": "United States",
            "City": "Henderson",
            "State": "Kentucky",
            "Postal Code": 42420.0,
            "Region": "South",
            "Product ID": "FUR-CH-10000454",
            "Category": "Furniture",
            "Sub-Category": "Chairs",
            "Product Name": "Hon Deluxe Fabric Upholstered Stacking Chairs",
            "Sales": 731.94,
        },
    ])


def test_validate_raw_schema_valid(valid_sample_df):
    """Ensure valid schema passes with zero errors."""
    report = validate_raw_schema(valid_sample_df)
    assert report.is_valid is True
    assert len(report.errors) == 0
    assert report.duplicate_rows == 0
    assert report.duplicate_row_ids == 0


def test_validate_raw_schema_missing_column(valid_sample_df):
    """Ensure missing required column fails validation."""
    df_missing = valid_sample_df.drop(columns=["Sales"])
    report = validate_raw_schema(df_missing)
    assert report.is_valid is False
    assert "Sales" in report.missing_columns


def test_validate_raw_schema_duplicate_rows(valid_sample_df):
    """Ensure duplicate rows are detected."""
    df_dup = pd.concat([valid_sample_df, valid_sample_df.iloc[[0]]], ignore_index=True)
    report = validate_raw_schema(df_dup)
    assert report.is_valid is False
    assert report.duplicate_rows == 1


def test_validate_raw_schema_invalid_sales(valid_sample_df):
    """Ensure non-positive or NaN sales are flagged."""
    bad_df = valid_sample_df.copy()
    bad_df.loc[0, "Sales"] = -10.5
    report = validate_raw_schema(bad_df)
    assert report.is_valid is False
    assert report.invalid_sales_count == 1


def test_validate_dates_and_shipping(valid_sample_df):
    """Ensure date formats and shipping intervals are validated."""
    results = validate_dates_and_shipping(valid_sample_df)
    assert results["is_valid"] is True
    assert results["min_shipping_days"] == 3
    assert results["max_shipping_days"] == 3


def test_validate_dates_negative_shipping(valid_sample_df):
    """Ensure negative shipping days (ship date earlier than order date) are flagged."""
    bad_df = valid_sample_df.copy()
    bad_df.loc[0, "Ship Date"] = "01/11/2017"  # Nov 1 before Nov 8
    results = validate_dates_and_shipping(bad_df)
    assert results["is_valid"] is False
    assert len(results["errors"]) > 0


def test_validate_business_relationships_customer_consistency(valid_sample_df):
    """Ensure customer ID mapping to multiple names is detected."""
    inconsistent_df = valid_sample_df.copy()
    inconsistent_df.loc[1, "Customer Name"] = "Claire Different"
    findings = validate_business_relationships(inconsistent_df)
    assert findings["customer_name_consistent"] is False
    assert len(findings["warnings"]) > 0


def test_validate_business_relationships_order_consistency(valid_sample_df):
    """Ensure order ID mapping to different ship modes or dates is detected."""
    inconsistent_df = valid_sample_df.copy()
    inconsistent_df.loc[1, "Ship Mode"] = "First Class"
    findings = validate_business_relationships(inconsistent_df)
    assert findings["order_attributes_consistent"] is False
    assert "Ship Mode" in findings["inconsistencies"]["orders"]


def test_validate_sales_preservation():
    """Ensure sales preservation check passes on matching values and fails on discrepancies."""
    raw_val = 2261536.7827
    cleaned_val = 2261536.7827
    orders_val = 2261536.7827

    # Should pass
    assert validate_sales_preservation(raw_val, cleaned_val, orders_val) is True

    # Should fail if orders total differs
    with pytest.raises(ValueError):
        validate_sales_preservation(raw_val, cleaned_val, 2260000.0)


def test_validate_entity_counts():
    """Ensure entity counts match Phase 0 benchmark numbers."""
    cleaned_mock = pd.DataFrame(index=range(9800))
    orders_mock = pd.DataFrame(index=range(4922))
    customers_mock = pd.DataFrame(index=range(793))
    products_mock = pd.DataFrame(index=range(1861))

    counts = validate_entity_counts(cleaned_mock, orders_mock, customers_mock, products_mock)
    assert counts["transactions"] == 9800
    assert counts["orders"] == 4922
    assert counts["customers"] == 793
    assert counts["products"] == 1861

    # Should fail if counts mismatch
    with pytest.raises(ValueError):
        validate_entity_counts(cleaned_mock, pd.DataFrame(index=range(4000)), customers_mock, products_mock)
