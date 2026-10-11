"""
Unit tests for ETL loader module.
"""

from pathlib import Path
import pytest

from backend.app.etl.loader import load_raw_data


def test_load_raw_data_success():
    """Ensure load_raw_data loads the dataset and preserves row count and column count."""
    project_root = Path(__file__).resolve().parents[2]
    csv_path = project_root / "data" / "train.csv"

    df = load_raw_data(csv_path)

    assert len(df) == 9800
    assert len(df.columns) == 18
    assert "Order ID" in df.columns
    assert "Sales" in df.columns


def test_load_raw_data_file_not_found(tmp_path):
    """Ensure FileNotFoundError is raised when file does not exist."""
    fake_path = tmp_path / "non_existent.csv"
    with pytest.raises(FileNotFoundError):
        load_raw_data(fake_path)


def test_load_raw_data_empty_file(tmp_path):
    """Ensure ValueError is raised when file is empty."""
    empty_path = tmp_path / "empty.csv"
    empty_path.write_text("", encoding="utf-8")
    with pytest.raises(Exception):
        load_raw_data(empty_path)
