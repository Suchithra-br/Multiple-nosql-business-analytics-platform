# Multi-NoSQL Real-Time Business Analytics Platform
### Superstore Sales Analytics · Polyglot NoSQL Architecture

An enterprise-grade, polyglot NoSQL business analytics platform engineered for retail sales data intelligence. The platform delegates operational, caching, time-series, and graph analytics workloads to four specialized database engines: **MongoDB**, **Redis**, **Apache Cassandra**, and **Neo4j**, driven by a **FastAPI** backend and an interactive **React** analytics dashboard.

---

## 1. Project Overview

Modern enterprise retail systems handle diverse data access patterns simultaneously:
- **Operational Transactions**: Managing nested, semi-structured order documents, product catalogs, and customer profiles.
- **Sub-Millisecond Executive KPIs**: Instant dashboard rendering of core business metrics without repeated expensive aggregation queries.
- **High-Throughput Time-Series Analytics**: Slicing and aggregating multi-year sales records across temporal dimensions (date, month, year) and regional partitions without full table scans.
- **Complex Relationship Discovery**: Traversing entity networks (Customer &rarr; Order &rarr; Product &rarr; Category &rarr; Region) to uncover co-purchasing affinities ("frequently bought together") and geographic rollups.

A single relational or NoSQL database cannot satisfy all four access patterns without significant architectural compromises. This project demonstrates a **Polyglot Persistence Architecture**, routing every query to the database engine engineered specifically for that workload.

---

## 2. Dataset Description

The platform operates on the historical US Superstore retail dataset located at `data/train.csv`:

- **Filename**: `data/train.csv` (Single source of truth)
- **Total Transactions / Line Items**: 9,800
- **Total Orders**: 4,922 unique orders
- **Total Customers**: 793 unique customers
- **Total Products**: 1,861 unique products across 17 sub-categories and 3 main categories
- **Total Recorded Sales**: **$2,261,536.7827**
- **Date Range**: January 3, 2015 to December 30, 2018 (4 calendar years: 2015, 2016, 2017, 2018)
- **Supported Fields**: `Sales`, `Order Date`, `Ship Date`, `Ship Mode`, `Customer ID`, `Customer Name`, `Segment`, `City`, `State`, `Postal Code`, `Region`, `Product ID`, `Category`, `Sub-Category`, `Product Name`.
- **Verified Dataset Scope**: The original dataset does **not** contain `Profit`, `Quantity`, `Discount`, `Cost`, or derived `Profit Margin` fields. All metrics strictly reflect actual transactional data without simulated or fabricated values.

---

## 3. Polyglot Architecture & Roles of the 4 NoSQL Databases

```text
                               ┌────────────────────────────────┐
                               │   data/train.csv (9,800 rows)  │
                               └───────────────┬────────────────┘
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │      Python ETL Pipeline       │
                               │     (Clean / Validate / Norm)  │
                               └───────────────┬────────────────┘
                                               │
        ┌──────────────────────┬───────────────┴───────────────┬──────────────────────┐
        ▼                      ▼                               ▼                      ▼
┌───────────────┐      ┌───────────────┐               ┌───────────────┐      ┌───────────────┐
│     Redis     │      │    MongoDB    │               │   Cassandra   │      │     Neo4j     │
│ In-Memory DB  │      │ Document Store│               │  Wide-Column  │      │Property Graph │
│ • Executive   │      │ • Orders with │               │ • Daily sales │      │ • Co-purchase │
│   KPIs (<5ms) │      │   items       │               │ • Region range│      │ • Customer    │
│ • Leaderboards│      │ • Profiles    │               │ • Category    │      │   journeys    │
│ • Monthly     │      │ • Search      │               │   slices      │      │ • 6-hop geo   │
└───────┬───────┘      └───────┬───────┘               └───────┬───────┘      └───────┬───────┘
        │                      │                               │                      │
        └──────────────────────┼───────────────────────────────┴──────────────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │    FastAPI Backend (/api/v1)  │
               │  (Routers, Services, Repos)   │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │   React Analytics Dashboard   │
               │   (Overview & Query Explorer) │
               └───────────────────────────────┘
```

### 1. Why MongoDB is Used (Document Store)
- **Role**: Master operational document store for orders and customer profiles.
- **Rationale**: Relational databases require expensive multi-table joins to assemble orders, customers, and individual line items. MongoDB's **Embedded Document Pattern** stores each order and its line items inside a single BSON document, enabling single-read atomic retrieval and rapid prefix search autocomplete.
- **Collections**: `orders` (4,922 docs with 9,800 embedded items), `customers` (793 docs), `products` (1,861 docs), `locations` (628 docs).

### 2. Why Redis is Used (In-Memory Cache)
- **Role**: Ultra-fast caching of executive KPIs, pre-calculated totals, and live leaderboards.
- **Rationale**: Scanning thousands of documents on every dashboard page load creates database contention. Redis provides sub-5ms retrieval for executive metrics using hashes (`HSET`) and sorted sets (`ZSET`) for product and customer rankings. Raw transaction rows are never persisted in Redis; it acts strictly as a cache with TTL expiry.

### 3. Why Apache Cassandra is Used (Wide-Column Time-Series Store)
- **Role**: Partition-pruned temporal analytical queries across millions of transactions.
- **Rationale**: Cassandra eliminates table scans by utilizing **query-first data modeling**. Tables are designed around specific query access patterns (`sales_by_date`, `sales_by_region_date`, `sales_by_category_date`). Using composite partition keys and clustering order, time range queries execute as fast, sequential disk reads isolated to a single storage partition.

### 4. Why Neo4j is Used (Property Graph Database)
- **Role**: Complex relationship traversals, product co-purchasing, and geographic hierarchy rollups.
- **Rationale**: Answering "Which products are frequently purchased together?" in SQL requires self-joins that degrade exponentially with scale. Neo4j's **index-free adjacency** traverses `(:Customer)-[:PLACED]->(:Order)-[:CONTAINS]->(:Product)` paths in constant time, powering recommendation algorithms and multi-hop regional traversals.

---

## 4. ETL Flow & Pipeline

The pipeline in `backend/app/etl/` executes deterministic data cleaning, validation, transformation, and normalization:

```text
data/train.csv 
      ↓ [loader.py]
Raw DataFrame (9,800 rows, 18 columns)
      ↓ [cleaner.py]
Trim whitespace, format dates to ISO (YYYY-MM-DD), handle Burlington VT null postal codes safely
      ↓ [validator.py]
Validate 18 schema constraints, zero row duplicates, positive sales values, customer-order consistency
      ↓ [transformer.py]
Add temporal fields (year, month, quarter), normalize entities into:
- orders.csv (4,922 orders)
- order_items.csv (9,800 items)
- customers.csv (793 customers)
- products.csv (1,861 canonical products)
- locations.csv (628 locations)
      ↓ [exporter.py]
Write normalized CSVs to generated_data/ and load to MongoDB, Redis, Cassandra, and Neo4j
```

---

## 5. Backend Architecture & Clean Separation

The backend follows a strict 4-layer unidirectional responsibility flow:

```text
API Router Layer (backend/app/api/v1/)
       ↓ [HTTP parameters, status codes, OpenAPI schemas]
Service Layer (backend/app/services/)
       ↓ [Business logic, cache orchestration, calculations]
Repository Layer (backend/app/repositories/)
       ↓ [Database queries: PyMongo, redis-py, Cassandra CQL, Neo4j Cypher]
Database Connection Layer (backend/app/databases/)
       ↓ [Connection pooling, lifecycle management, ping health checks]
Physical Databases
```

- **Centralized Configuration (`app/core/config.py`)**: Environment variables loaded cleanly with fallback defaults.
- **Centralized Error Handling (`app/core/error_handlers.py`)**: Structured JSON error envelopes protecting internal credentials while preserving diagnostic messages.
- **Structured Logging (`app/core/logging_config.py`)**: Consistent formatting for startup, queries, and failures.

---

## 6. Frontend Architecture

Built with **React + Vite** and Vanilla CSS:

```text
frontend/src/
├── config/environment.js          # API base URL configuration
├── services/api/                  # Modular HTTP client & specialized API services
│   ├── client.js                  # Generic fetch with abort timeout & error parsing
│   ├── dashboardApi.js            # Overview, monthly, regions, categories, segments
│   └── analyticsApi.js            # Leaderboards, MongoDB search, Cassandra, Neo4j
├── hooks/                         # Custom React hooks (useDashboard, useAnalytics)
├── state/appState.js              # Lightweight centralized application context
├── components/                    # Modular component design system
│   ├── common/                    # LoadingState, ErrorState, EmptyState, DataTable
│   ├── layout/                    # Header, Sidebar
│   ├── dashboard/                 # KpiCard, ChartCard
│   └── analytics/                 # QueryResult metadata badge
├── pages/                         # Dashboard (Overview) & Analytics (Query Explorer)
└── utils/                         # formatters.js & csvExport.js
```

---

## 7. API Structure & Versioning

All endpoints are versioned under `/api/v1/`:

| Endpoint | Method | Database | Purpose |
| :--- | :--- | :--- | :--- |
| `/api/v1/health` | `GET` | All 4 DBs | Real-time connectivity probe for all 4 databases |
| `/api/v1/dashboard/overview` | `GET` | Redis / MongoDB | Executive KPI overview ($2.26M sales, 4,922 orders) |
| `/api/v1/dashboard/monthly` | `GET` | Redis / MongoDB | 48-month chronological sales trend (2015–2018) |
| `/api/v1/dashboard/regions` | `GET` | Redis / MongoDB | Regional sales and order breakdown |
| `/api/v1/dashboard/categories` | `GET` | Redis / MongoDB | Product category breakdown |
| `/api/v1/dashboard/segments` | `GET` | Redis / MongoDB | Customer segment distribution |
| `/api/v1/dashboard/shipping` | `GET` | Redis / MongoDB | Shipping logistics volume |
| `/api/v1/dashboard/subcategories` | `GET` | MongoDB | 17 product sub-category revenue aggregates |
| `/api/v1/dashboard/states` | `GET` | MongoDB | State revenue rankings with order counts |
| `/api/v1/analytics/products/top` | `GET` | Redis / MongoDB | Top revenue-generating products |
| `/api/v1/analytics/customers/top` | `GET` | Redis / MongoDB | Highest spending retail customers |
| `/api/v1/analytics/customers/search` | `GET` | MongoDB | Customer name/ID prefix autocomplete |
| `/api/v1/analytics/orders/search` | `GET` | MongoDB | Order ID prefix autocomplete |
| `/api/v1/analytics/orders/{order_id}` | `GET` | MongoDB | Complete order with embedded line items |
| `/api/v1/analytics/customers/{customer_id}` | `GET` | MongoDB | Customer business profile & purchase history |
| `/api/v1/analytics/date` | `GET` | Cassandra | Partition-keyed daily sales line items |
| `/api/v1/analytics/region-date` | `GET` | Cassandra | Regional chronological date range query |
| `/api/v1/analytics/category-date` | `GET` | Cassandra | Category chronological date range query |
| `/api/v1/analytics/graph/customer/{id}/orders` | `GET` | Neo4j | Customer order history graph traversal |
| `/api/v1/analytics/graph/customer/{id}/products` | `GET` | Neo4j | Customer product affinity traversal |
| `/api/v1/analytics/graph/product/{id}/copurchases` | `GET` | Neo4j | Product co-purchasing recommendations ("bought together") |
| `/api/v1/analytics/graph/region/{region}/categories` | `GET` | Neo4j | 6-hop geographic hierarchy category aggregation |

Full request/response examples are available in [docs/api.md](file:///docs/api.md).

---

## 8. Setup & Running Locally

### 1. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 2. Docker Compose (Start Databases)
```bash
docker-compose up -d
```
Starts:
- **MongoDB** on `localhost:27017`
- **Redis** on `localhost:6379`
- **Apache Cassandra** on `localhost:9042`
- **Neo4j** on `localhost:7474` (HTTP) and `localhost:7687` (Bolt)

### 3. Backend Setup & ETL Execution
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\Activate.ps1 on Windows

# Install dependencies
pip install -r backend/requirements.txt

# Run ETL and populate all four databases
python -m backend.app.etl.pipeline
```

### 4. Running the Backend Server
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Swagger UI: `http://localhost:8000/docs`

### 5. Running the Frontend
```bash
cd frontend
npm install
npm run dev
```
- Dashboard URL: `http://localhost:5173`

---

## Production Deployment

The containerized production stack has been verified and deployed:

- **Frontend**: `http://127.0.0.1:4173` (Production preview bundle) / `http://localhost:3000` (Nginx container via `docker-compose.prod.yml`)
- **Backend**: `http://127.0.0.1:8000`
- **Swagger**: `http://127.0.0.1:8000/docs`

For detailed production instructions, see [docs/deployment-guide.md](file:///docs/deployment-guide.md).

---

## 9. Testing & Quality Assurance

### Run Backend Tests (111 tests passing)
```bash
python -m pytest backend/tests -v
```

### Run Frontend Tests (25 tests passing)
```bash
cd frontend
npm test -- --run
```

### Build Frontend Production Bundle
```bash
cd frontend
npm run build
```

---

## 10. Project Limitations

1. **Dataset Scope**: The historical retail dataset covers years 2015–2018 and strictly contains Sales revenue without Profit, Discount, or Cost data.
2. **Single-Node Containers**: Docker Compose runs single-node instances of Cassandra and MongoDB, optimized for development and capstone demonstration rather than multi-datacenter production clustering.
3. **Synthetic Co-Purchases**: Co-purchase recommendations are based on products appearing in the same historical orders; real-time clickstream data is not included in the dataset.

---

## 11. Detailed Documentation

For in-depth architecture diagrams, query schemas, and operational instructions, see:
- [System Architecture](file:///docs/architecture.md)
- [REST API Reference](file:///docs/api.md)
- [Database Design & Schemas](file:///docs/database-design.md)
- [Development & Operations Guide](file:///docs/development-guide.md)
