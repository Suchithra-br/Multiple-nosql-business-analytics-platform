"""
Unit tests for ETL cleaner module.
"""

import pandas as pd
import numpy as np
import pytest

from backend.app.etl.cleaner import clean_postal_code, clean_dataset


def test_clean_postal_code_null_handling():
    """Ensure null/missing postal codes are safely returned as None without inventing data."""
    assert clean_postal_code(None) is None
    assert clean_postal_code(np.nan) is None
    assert clean_postal_code("") is None
    assert clean_postal_code("   ") is None
    assert clean_postal_code("nan") is None
    assert clean_postal_code("NaN") is None


def test_clean_postal_code_formatting():
    """Ensure numeric postal codes are zero-padded to 5 digits and do not contain decimal points."""
    assert clean_postal_code(42420.0) == "42420"
    assert clean_postal_code("42420") == "42420"
    # Leading zeros in US zip codes (e.g. New England)
    assert clean_postal_code(6824.0) == "06824"
    assert clean_postal_code(1040.0) == "01040"
    assert clean_postal_code("7090") == "07090"


def test_clean_dataset_isolation_and_transformation():
    """Ensure clean_dataset does not mutate original input and standardizes columns and types."""
    sample_raw = pd.DataFrame([
        {
            "Row ID": 1,
            "Order ID": "CA-2017-1000",
            "Order Date": "08/11/2017",
            "Ship Date": "11/11/2017",
            "Ship Mode": "Second Class",
            "Customer ID": "CG-12520",
            "Customer Name": " Claire Gute ",
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
            "Order Date": "15/04/2018",
            "Ship Date": "20/04/2018",
            "Ship Mode": "Standard Class",
            "Customer ID": "AA-10480",
            "Customer Name": "Andrew Allen",
            "Segment": "Consumer",
            "Country": "United States",
            "City": "Burlington",
            "State": "Vermont",
            "Postal Code": np.nan,  # Missing postal code
            "Region": "East",
            "Product ID": "OFF-PA-10002365",
            "Category": "Office Supplies",
            "Sub-Category": "Paper",
            "Product Name": "Xerox 1967",
            "Sales": 15.552,
        },
    ])

    raw_copy = sample_raw.copy(deep=True)
    cleaned = clean_dataset(sample_raw)

    # 1. Original dataframe is not modified
    pd.testing.assert_frame_equal(sample_raw, raw_copy)

    # 2. Columns are snake_case
    assert "row_id" in cleaned.columns
    assert "order_id" in cleaned.columns
    assert "Row ID" not in cleaned.columns

    # 3. Dates are parsed as timestamps
    assert pd.api.types.is_datetime64_any_dtype(cleaned["order_date"])
    assert pd.api.types.is_datetime64_any_dtype(cleaned["ship_date"])
    assert cleaned.loc[0, "order_date"] == pd.Timestamp("2017-11-08")

    # 4. Postal codes formatted properly
    assert cleaned.loc[0, "postal_code"] == "42420"
    assert cleaned.loc[1, "postal_code"] is None

    # 5. Text whitespace stripped
    assert cleaned.loc[0, "customer_name"] == "Claire Gute"
