# Phase 1: Data Quality & Validation Report

**Generated Date**: 2026-10-11  
**Project**: Multi-NoSQL Real-Time Business Analytics Platform  
**Target Dataset**: `data/train.csv` (Unaltered, Read-Only)  
**ETL Pipeline Status**: `PASSED` (100% Validated)

---

## 1. Executive Summary

The Phase 1 ETL pipeline loaded, verified, cleansed, and transformed the raw Superstore retail dataset without modifying the original `data/train.csv` file. All financial totals and record counts were preserved with zero discrepancy across all operational and analytical entity tables.

| Metric | Raw Dataset | Transformed Dataset | Status |
| :--- | :--- | :--- | :---: |
| **Total Transactions** | 9,800 | 9,800 | `MATCH` |
| **Total Orders** | 4,922 | 4,922 | `MATCH` |
| **Total Customers** | 793 | 793 | `MATCH` |
| **Total Products** | 1,861 | 1,861 | `MATCH` |
| **Unique Locations** | 628 | 628 | `MATCH` |
| **Total Sales Volume** | $2,261,536.7827 | $2,261,536.7827 | `EXACT (diff = 0.00)` |
| **Duplicate Rows** | 0 | 0 | `CLEAN` |
| **Duplicate Row IDs** | 0 | 0 | `CLEAN` |

---

## 2. Dataset Schema & Column Validation

All 18 expected columns were identified and matched against expected domain types:

- **Missing Required Columns**: None (`0`)
- **Unexpected Columns**: None (`0`)
- **Date Format**: `DD/MM/YYYY` parsed successfully for 100% of rows (0 errors).
- **Date Range**:
  - `Order Date`: `2015-01-03` to `2018-12-30` (4 full years: 2015–2018)
  - `Ship Date`: `2015-01-07` to `2019-01-05`
  - `Shipping Days Range`: `0` to `7` days (Negative shipping days: `0`)

---

## 3. Missing Value Audit

| Column Name | Missing Count | % of Dataset | Handling Strategy & Rationale |
| :--- | :---: | :---: | :--- |
| `Postal Code` | **11** | 0.11% | **Preserved as `null` / `None`**. All 11 records belong to **Burlington, Vermont** (East Region). As per project specifications, postal codes were NOT invented or imputed. |
| All other 17 columns | **0** | 0.00% | 100% complete data integrity. |

---

## 4. Business Relationship Consistency

The ETL pipeline audited relational consistency across core business entities:

1. **Customer ID &rarr; Customer Name**: Strictly **1:1** (`793` distinct customers, 0 naming conflicts).
2. **Customer ID &rarr; Segment**: Strictly **1:1** (0 segment conflicts).
3. **Product ID &rarr; Category / Sub-Category**: Strictly **1:1** (0 taxonomy conflicts).
4. **Order ID Consistency**:
   - `Order ID` &rarr; `Order Date`: 100% consistent (0 discrepancies).
   - `Order ID` &rarr; `Ship Date`: 100% consistent (0 discrepancies).
   - `Order ID` &rarr; `Ship Mode`: 100% consistent (0 discrepancies).
   - `Order ID` &rarr; `Customer ID`: 100% consistent (0 discrepancies).
   - `Order ID` &rarr; Destination Location: 100% consistent (0 discrepancies).
5. **Product ID &rarr; Product Name (Documented Anomaly)**:
   - Found **32 Product IDs** with multiple Product Names (e.g., variant naming differences).
   - **Resolution**:
     - Preserved verbatim in `order_items.csv` and `cleaned_sales.csv`.
     - In `products.csv`, the canonical name is assigned to the most frequent name, with `variant_names_count` tracked.

---

## 5. Financial Sales Reconciliation Audit

Total sales were audited across all transformed entities to guarantee financial integrity:

- **Raw CSV Sales Sum**: `$2,261,536.7827`
- **Cleaned Transactions Sales Sum**: `$2,261,536.7827`
- **Orders Entity Sales Sum**: `$2,261,536.7827`
- **Order Items Entity Sales Sum**: `$2,261,536.7827`
- **Reconciliation Variance**: `0.00000000` (Epsilon tolerance `<= 1e-4`)

---

## 6. Derived Features Policy Verification

Strict compliance with the project constraint regarding derived business metrics:
- **Allowed Derived Fields Created**:
  - `shipping_days`: Calculated as `ship_date - order_date` (range: 0 to 7 days).
  - `order_year`: Extracted integer year (`2015`, `2016`, `2017`, `2018`).
  - `order_month`: Extracted integer month (`1` to `12`).
  - `order_month_name`: Month string (`January` through `December`).
  - `order_quarter`: Quarter string (`Q1`, `Q2`, `Q3`, `Q4`).
  - `order_year_month`: Format `YYYY-MM`.
- **Prohibited Business Metrics**:
  - `Profit`: **NOT CREATED** (Confirmed absent).
  - `Discount`: **NOT CREATED** (Confirmed absent).
  - `Quantity`: **NOT CREATED** (Confirmed absent).
  - `Cost / Margin`: **NOT CREATED** (Confirmed absent).

---

## 7. Generated Datasets Summary

| Entity File | Row Count | Column Count | Primary Key | Purpose in Polyglot Platform |
| :--- | :---: | :---: | :--- | :--- |
| `cleaned_sales.csv` | 9,800 | 23 | `row_id` | Unified cleaned transaction store with temporal features |
| `orders.csv` | 4,922 | 17 | `order_id` | Document ingestion for MongoDB & Cassandra |
| `order_items.csv` | 9,800 | 7 | `row_id` | Line item array embedding in MongoDB & Cassandra |
| `customers.csv` | 793 | 7 | `customer_id` | Customer master dimension & Neo4j Customer nodes |
| `products.csv` | 1,861 | 6 | `product_id` | Product catalog dimension & Neo4j Product nodes |
| `locations.csv` | 628 | 7 | `location_id` | Geographic hierarchy dimension for Neo4j & Cassandra |

---
*Report automatically generated by `backend.app.etl.pipeline`*
