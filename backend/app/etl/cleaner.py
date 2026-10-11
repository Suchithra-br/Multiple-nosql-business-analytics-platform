"""
ETL Cleaner Module.

Performs data cleansing, column name standardization, robust date parsing,
and precise postal code formatting without imputing missing values.
"""

import logging
from typing import Any
import pandas as pd
import numpy as np

logger = logging.getLogger("etl.cleaner")

COLUMN_RENAME_MAP = {
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Customer Name": "customer_name",
    "Segment": "segment",
    "Country": "country",
    "City": "city",
    "State": "state",
    "Postal Code": "postal_code",
    "Region": "region",
    "Product ID": "product_id",
    "Category": "category",
    "Sub-Category": "sub_category",
    "Product Name": "product_name",
    "Sales": "sales",
}


def clean_postal_code(val: Any) -> str | None:
    """
    Safely cleans a postal code value.
    
    Rules:
    - If null/NaN/None: returns None. Does NOT invent postal codes.
    - If valid: converts float/int to 5-digit zero-padded string (e.g. 6824.0 -> '06824').
    """
    if pd.isna(val) or val is None or str(val).strip() in ("", "nan", "NaN", "None"):
        return None
    try:
        numeric_val = int(float(val))
        return f"{numeric_val:05d}"
    except (ValueError, TypeError):
        cleaned = str(val).strip()
        return cleaned if cleaned else None


def clean_dataset(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the raw dataset:
    - Creates an isolated deep copy to ensure the raw DataFrame is never modified.
    - Standardizes column names to snake_case.
    - Parses 'order_date' and 'ship_date' with format %d/%m/%Y.
    - Formats 'postal_code' safely (preserving None for the 11 missing Burlington, VT rows).
    - Trims whitespace from text fields.
    - Casts numeric fields to canonical types.
    
    Args:
        raw_df: Raw pandas DataFrame.
        
    Returns:
        pd.DataFrame: Cleaned DataFrame.
    """
    logger.info("Starting dataset cleaning...")
    df = raw_df.copy(deep=True)

    # 1. Standardize column names
    df = df.rename(columns=COLUMN_RENAME_MAP)
    logger.info(f"Standardized {len(df.columns)} column names to snake_case.")

    # 2. Text stripping for string columns
    str_cols = [
        "order_id",
        "ship_mode",
        "customer_id",
        "customer_name",
        "segment",
        "country",
        "city",
        "state",
        "region",
        "product_id",
        "category",
        "sub_category",
        "product_name",
    ]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 3. Date parsing (%d/%m/%Y)
    logger.info("Parsing dates with format %d/%m/%Y...")
    df["order_date"] = pd.to_datetime(df["order_date"], format="%d/%m/%Y")
    df["ship_date"] = pd.to_datetime(df["ship_date"], format="%d/%m/%Y")

    # 4. Postal Code handling
    logger.info("Formatting postal codes safely...")
    df["postal_code"] = df["postal_code"].apply(clean_postal_code)
    missing_pc_count = df["postal_code"].isna().sum()
    logger.info(f"Postal code formatting complete. Null postal codes preserved: {missing_pc_count} (Burlington, VT).")

    # 5. Row ID and Sales types
    df["row_id"] = df["row_id"].astype(int)
    df["sales"] = df["sales"].astype(float)

    # Ensure sorting for determinism
    df = df.sort_values(by="row_id").reset_index(drop=True)

    logger.info(f"Cleaning complete. Output shape: {df.shape[0]} rows, {df.shape[1]} columns.")
    return df
