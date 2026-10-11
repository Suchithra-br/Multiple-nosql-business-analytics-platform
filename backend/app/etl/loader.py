"""
ETL Loader Module.

Safely loads the raw CSV dataset from disk without altering the original file.
"""

import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger("etl.loader")

EXPECTED_RAW_COLUMNS = [
    "Row ID",
    "Order ID",
    "Order Date",
    "Ship Date",
    "Ship Mode",
    "Customer ID",
    "Customer Name",
    "Segment",
    "Country",
    "City",
    "State",
    "Postal Code",
    "Region",
    "Product ID",
    "Category",
    "Sub-Category",
    "Product Name",
    "Sales",
]


def load_raw_data(filepath: str | Path) -> pd.DataFrame:
    """
    Loads raw CSV data from the specified path in read-only mode.
    
    Args:
        filepath: Path to the raw CSV file.
        
    Returns:
        pd.DataFrame containing the raw dataset.
        
    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the file is empty or cannot be read.
    """
    path = Path(filepath).resolve()
    logger.info(f"Loading raw dataset from: {path}")

    if not path.is_file():
        raise FileNotFoundError(f"Raw dataset file not found at: {path}")

    file_size_mb = path.stat().st_size / (1024 * 1024)
    logger.info(f"Dataset file size: {file_size_mb:.2f} MB")

    try:
        # Read with default types, preserving raw values
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        logger.warning("UTF-8 decoding failed, falling back to latin1 encoding.")
        df = pd.read_csv(path, encoding="latin1")

    if df.empty:
        raise ValueError(f"Loaded dataset from {path} is empty.")

    logger.info(f"Successfully loaded raw dataset: {len(df)} rows, {len(df.columns)} columns.")
    return df
