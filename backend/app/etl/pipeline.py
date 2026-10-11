"""
ETL Pipeline Orchestrator.

Main entry point for running the complete Phase 1 Data Cleaning, Validation,
Transformation, and Export workflow.

Usage:
    python -m backend.app.etl.pipeline
"""

import sys
import time
import logging
from pathlib import Path
from typing import Any

from backend.app.etl.loader import load_raw_data
from backend.app.etl.validator import (
    validate_raw_schema,
    validate_dates_and_shipping,
    validate_business_relationships,
    validate_sales_preservation,
    validate_entity_counts,
)
from backend.app.etl.cleaner import clean_dataset
from backend.app.etl.transformer import transform_data, TransformedDatasets
from backend.app.etl.exporter import export_datasets, generate_data_quality_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("etl.pipeline")


def run_etl_pipeline(
    raw_data_path: str | Path | None = None,
    generated_data_dir: str | Path | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Executes the end-to-end ETL pipeline.
    
    Args:
        raw_data_path: Path to the raw CSV file (defaults to data/train.csv).
        generated_data_dir: Path to export directory (defaults to generated_data/).
        report_path: Path to save the data quality report (defaults to docs/data_quality_report.md).
        
    Returns:
        dict[str, Any]: Execution summary, counts, and file paths.
    """
    start_time = time.time()
    logger.info("=" * 70)
    logger.info("STARTING PHASE 1: DATA CLEANING, VALIDATION AND ETL PIPELINE")
    logger.info("=" * 70)

    # Resolve default paths relative to project root
    project_root = Path(__file__).resolve().parents[3]
    raw_path = Path(raw_data_path) if raw_data_path else project_root / "data" / "train.csv"
    gen_dir = Path(generated_data_dir) if generated_data_dir else project_root / "generated_data"
    rep_path = Path(report_path) if report_path else project_root / "docs" / "data_quality_report.md"

    logger.info(f"Project root resolved to: {project_root}")
    logger.info(f"Raw data path:           {raw_path}")
    logger.info(f"Generated data dir:      {gen_dir}")
    logger.info(f"Quality report path:     {rep_path}")

    # Step 1: Load raw data (read-only)
    logger.info("--- Step 1: Loading Raw Data ---")
    raw_df = load_raw_data(raw_path)
    raw_total_sales = float(raw_df["Sales"].sum())

    # Step 2: Validate raw schema and dates
    logger.info("--- Step 2: Validating Raw Schema & Constraints ---")
    raw_report = validate_raw_schema(raw_df)
    if not raw_report.is_valid:
        raise ValueError(f"Raw dataset schema validation failed: {raw_report.errors}")

    date_results = validate_dates_and_shipping(raw_df)
    if not date_results["is_valid"]:
        raise ValueError(f"Date validation failed: {date_results['errors']}")

    # Step 3: Audit business entity relationships
    logger.info("--- Step 3: Auditing Business Relationships ---")
    rel_results = validate_business_relationships(raw_df)

    # Step 4: Clean dataset
    logger.info("--- Step 4: Cleansing Dataset ---")
    cleaned_df = clean_dataset(raw_df)

    # Step 5: Transform and generate entity datasets
    logger.info("--- Step 5: Transforming & Generating Entity Datasets ---")
    datasets = transform_data(cleaned_df)

    # Step 6: Post-transformation validations
    logger.info("--- Step 6: Auditing Financial Totals & Entity Counts ---")
    cleaned_total_sales = float(datasets.cleaned_sales["sales"].sum())
    orders_total_sales = float(datasets.orders["order_total_sales"].sum())
    items_total_sales = float(datasets.order_items["sales"].sum())

    validate_sales_preservation(
        raw_total=raw_total_sales,
        cleaned_total=cleaned_total_sales,
        orders_total=orders_total_sales,
        items_total=items_total_sales,
    )

    entity_counts = validate_entity_counts(
        cleaned_df=datasets.cleaned_sales,
        orders_df=datasets.orders,
        customers_df=datasets.customers,
        products_df=datasets.products,
    )

    # Step 7: Export datasets
    logger.info("--- Step 7: Exporting Generated Datasets ---")
    exported_files = export_datasets(datasets, gen_dir)

    # Step 8: Generate quality report
    logger.info("--- Step 8: Generating Data Quality Report ---")
    report_file = generate_data_quality_report(
        raw_report=raw_report,
        date_results=date_results,
        rel_results=rel_results,
        datasets=datasets,
        output_path=rep_path,
    )

    elapsed_time = time.time() - start_time
    logger.info("=" * 70)
    logger.info(f"ETL PIPELINE COMPLETED SUCCESSFULLY IN {elapsed_time:.2f} SECONDS")
    logger.info(f"Transactions: {entity_counts['transactions']:,}")
    logger.info(f"Orders:       {entity_counts['orders']:,}")
    logger.info(f"Customers:    {entity_counts['customers']:,}")
    logger.info(f"Products:     {entity_counts['products']:,}")
    logger.info(f"Locations:    {len(datasets.locations):,}")
    logger.info(f"Total Sales:  ${cleaned_total_sales:,.4f}")
    logger.info("=" * 70)

    return {
        "status": "SUCCESS",
        "elapsed_seconds": elapsed_time,
        "raw_sales": raw_total_sales,
        "cleaned_sales": cleaned_total_sales,
        "entity_counts": entity_counts,
        "locations_count": len(datasets.locations),
        "exported_files": exported_files,
        "report_file": report_file,
    }


if __name__ == "__main__":
    try:
        run_etl_pipeline()
    except Exception as e:
        logger.exception(f"ETL Pipeline execution failed: {e}")
        sys.exit(1)
