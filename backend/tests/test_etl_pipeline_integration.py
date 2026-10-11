"""
Integration tests for complete ETL pipeline.
"""

from pathlib import Path
import pandas as pd
import pytest

from backend.app.etl.pipeline import run_etl_pipeline


def test_full_pipeline_execution(tmp_path):
    """
    Executes the full ETL pipeline with custom output directories,
    verifying end-to-end data integrity, file exports, and report creation.
    """
    project_root = Path(__file__).resolve().parents[2]
    raw_csv = project_root / "data" / "train.csv"
    gen_dir = tmp_path / "generated_data"
    report_file = tmp_path / "docs" / "data_quality_report.md"

    summary = run_etl_pipeline(
        raw_data_path=raw_csv,
        generated_data_dir=gen_dir,
        report_path=report_file,
    )

    assert summary["status"] == "SUCCESS"
    assert summary["entity_counts"]["transactions"] == 9800
    assert summary["entity_counts"]["orders"] == 4922
    assert summary["entity_counts"]["customers"] == 793
    assert summary["entity_counts"]["products"] == 1861
    assert summary["locations_count"] == 628

    # Sales preservation
    assert round(summary["raw_sales"], 4) == round(summary["cleaned_sales"], 4)
    assert round(summary["cleaned_sales"], 4) == 2261536.7827

    # Verify all files exist and have content
    expected_files = [
        "cleaned_sales.csv",
        "orders.csv",
        "order_items.csv",
        "customers.csv",
        "products.csv",
        "locations.csv",
    ]
    for fname in expected_files:
        fpath = gen_dir / fname
        assert fpath.is_file(), f"Expected exported file {fname} not found"
        df_read = pd.read_csv(fpath)
        assert len(df_read) > 0, f"Exported file {fname} is empty"

    # Verify report file
    assert report_file.is_file()
    report_content = report_file.read_text(encoding="utf-8")
    assert "Phase 1: Data Quality & Validation Report" in report_content
    assert "$2,261,536.7827" in report_content
    assert "Burlington, Vermont" in report_content
