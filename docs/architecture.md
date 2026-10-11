# System Architecture & Technical Design

## 1. Executive Summary

The **Multi-NoSQL Real-Time Business Analytics Platform** (Superstore Sales Analytics) is an enterprise-grade polyglot persistence analytics platform engineered to process, aggregate, and visualize retail sales data. The platform ingests 9,800 transactional line items across 4,922 orders from the historical US Superstore retail dataset (2015–2018) and distributes the workload across four distinct NoSQL database paradigms:

1. **Redis**: In-Memory Key-Value & Sorted-Set Cache for sub-millisecond executive KPI retrieval.
2. **MongoDB**: Document Database for rich, nested transactional order and customer profiles.
3. **Apache Cassandra**: Distributed Wide-Column Store for partition-optimized temporal time-series queries.
4. **Neo4j**: Labeled Property Graph Database for multi-hop customer journeys and product co-purchase affinities.

---

## 2. High-Level Architecture Diagrams

### 2.1 Simplified Polyglot Architecture Diagram

```mermaid
flowchart TD
    A["Superstore CSV Dataset (data/train.csv)"] --> B["Python ETL Pipeline"]

    B --> C[("MongoDB\n(Document Store)")]
    B --> D[("Redis\n(In-Memory Cache)")]
    B --> E[("Apache Cassandra\n(Wide-Column Store)")]
    B --> F[("Neo4j\n(Property Graph)")]

    C --> G["FastAPI Backend Gateway (/api/v1)"]
    D --> G
    E --> G
    F --> G

    G --> H["React Analytics Frontend"]
    H --> I["Superstore Sales Analytics Dashboard\n(Overview & Query Explorer)"]
```

---

### 2.2 Detailed Polyglot Architecture Diagram

```mermaid
flowchart TD
    subgraph Ingestion ["1. Data Ingestion & Transformation"]
        CSV["Historical Retail Dataset<br/><code>data/train.csv</code><br/>(9,800 records / $2.26M sales)"]
        ETL["Modular Python ETL Pipeline<br/><code>loader</code> ➔ <code>cleaner</code> ➔ <code>validator</code> ➔ <code>transformer</code>"]
        GEN["Normalized Datasets<br/><code>generated_data/*.csv</code>"]
        CSV --> ETL --> GEN
    end

    subgraph Storage ["2. Polyglot NoSQL Storage Layer (Docker)"]
        REDIS[("Redis 7.2<br/><code>In-Memory Cache</code><br/>• Executive KPIs<br/>• Leaderboards<br/>• Monthly Trends")]
        MONGO[("MongoDB 7.0<br/><code>Document Store</code><br/>• Orders (nested items)<br/>• Customer Profiles<br/>• Product Catalog")]
        CASS[("Apache Cassandra 4.1<br/><code>Wide-Column Store</code><br/>• Partitioned Time-Series<br/>• Regional Temporal Slices<br/>• Category Date Ranges")]
        NEO[("Neo4j 5.15<br/><code>Property Graph</code><br/>• Customer ➔ Order ➔ Product<br/>• Co-Purchase Recommendations<br/>• Regional Geographic Hierarchy")]
    end

    GEN --> REDIS
    GEN --> MONGO
    GEN --> CASS
    GEN --> NEO

    subgraph Backend ["3. FastAPI Backend Layer (Python)"]
        ROUTER["API Router (v1)<br/><code>/api/v1/dashboard/*</code><br/><code>/api/v1/analytics/*</code><br/><code>/api/v1/health</code>"]
        SERVICES["Service Layer<br/>• <code>DashboardService</code><br/>• <code>AnalyticsService</code><br/>• <code>GraphService</code>"]
        REPOS["Repository Layer<br/>• <code>MongoDBRepository</code><br/>• <code>RedisRepository</code><br/>• <code>CassandraRepository</code><br/>• <code>Neo4jRepository</code>"]
        DBLAYER["Connection Lifecycle Layer<br/>(Connection pooling, health checks, error trapping)"]

        ROUTER --> SERVICES --> REPOS --> DBLAYER
    end

    DBLAYER -.-> REDIS
    DBLAYER -.-> MONGO
    DBLAYER -.-> CASS
    DBLAYER -.-> NEO

    subgraph Frontend ["4. React Presentation Layer (Vite)"]
        UI["Superstore Analytics Dashboard<br/>(React 19 + Recharts + Vanilla CSS)"]
        HOOKS["Custom React Hooks<br/><code>useDashboard</code> / <code>useAnalytics</code>"]
        API_CLIENT["Modular API Services<br/><code>dashboardApi</code> / <code>analyticsApi</code>"]
        COMPONENTS["Modular UI Components<br/><code>common/*</code> | <code>layout/*</code> | <code>dashboard/*</code> | <code>analytics/*</code>"]

        UI --> HOOKS --> API_CLIENT --> ROUTER
        UI --- COMPONENTS
    end
```

---

## 3. End-to-End Request & Data Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Analyst
    participant React as React UI Page (Dashboard / Analytics)
    participant Hook as Custom Hook (useDashboard / useAnalytics)
    participant Service as Frontend API Service (dashboardApi / analyticsApi)
    participant Client as HTTP Client (client.js)
    participant FastAPIRouter as FastAPI Router (/api/v1/)
    participant AppService as Backend Service Layer
    participant Repo as Repository Layer
    participant DBPool as Database Connection Layer
    participant DB as NoSQL Engine (Redis / Mongo / Cassandra / Neo4j)

    User->>React: Select Filter / Search / View Metric
    React->>Hook: Trigger State Update or Fetch
    Hook->>Service: Call API Method (e.g., getOverview(year, region))
    Service->>Client: get('/api/v1/dashboard/overview', params)
    Client->>FastAPIRouter: HTTP GET /api/v1/dashboard/overview
    FastAPIRouter->>AppService: get_overview(year, region)
    
    alt Filter is None (Default Unfiltered)
        AppService->>Repo: Fetch cached KPIs from Redis
        Repo->>DBPool: Execute Redis HGETALL 'kpi:overview'
        DBPool->>DB: Redis In-Memory Lookup (< 2ms)
        DB-->>AppService: Return Cached KPI Values
    else Filter is Active (Year / Region Applied)
        AppService->>Repo: Execute Dynamic MongoDB Aggregation Pipeline
        Repo->>DBPool: PyMongo aggregate() on 'orders'
        DBPool->>DB: Indexed Scan on 'orders' collection
        DB-->>AppService: Return Aggregated Document Totals
    end

    AppService->>AppService: Compute YoY Growth & AOV Metrics
    AppService-->>FastAPIRouter: Structured Pydantic Response Model
    FastAPIRouter-->>Client: HTTP 200 OK (JSON Payload)
    Client-->>Service: Return Parsed Data
    Service-->>Hook: Update State (overview, loading=false)
    Hook-->>React: Trigger Re-render with Visual Components
    React-->>User: Render KPI Cards, Trends & Charts
```

---

## 4. Database Workload Segregation

No single database engine satisfies all modern analytics access patterns without significant performance compromises. This architecture assigns each database an explicit, mathematically sound role:

| Database Engine | Data Model | Primary Role & Access Pattern | Typical Latency | Key Optimization Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Redis** | In-Memory Key-Value & Sorted Sets | Executive KPI cards, sales aggregates, and top leaderboard rankings. | < 5 ms | Precomputed hashes, Sorted Sets for rank queries, memory eviction safety. |
| **MongoDB** | Document (JSON-like BSON) | Operational drill-downs: order details with embedded line items, customer histories, and text prefix autocomplete. | 10–30 ms | Compound B-tree indexes on `order_id`, `customer_id`, and `product_id`. |
| **Apache Cassandra** | Wide-Column Family | Time-series aggregations, chronological sales queries by date, region-date, and category-date ranges. | 15–40 ms | Query-first data modeling with composite partition keys and clustering order. |
| **Neo4j** | Labeled Property Graph | Multi-hop relationship traversals: co-purchasing ("frequently bought together") and geographic hierarchy. | 25–60 ms | Index-free adjacency, Cypher pattern matching, schema uniqueness constraints. |

---

## 5. Backend Responsibility Separation

The backend follows a strict 4-layer unidirectional responsibility flow:

```text
API Router Layer (FastAPI)
       ↓
Service Layer (Business Logic & Orchestration)
       ↓
Repository Layer (Database Query & Data Retrieval)
       ↓
Database Connection Layer (Connection Pooling & Lifecycle)
       ↓
Physical NoSQL Databases
```

### 1. API Router Layer (`app/api/v1/`)
- Responsible strictly for HTTP protocols, path routing, query parameter parsing, and response status codes.
- Implements versioned routes under `/api/v1/`.
- No database client imports, SQL/CQL queries, or aggregation logic reside here.

### 2. Service Layer (`app/services/`)
- Orchestrates multi-repository workflows (e.g., fallback to MongoDB if Redis cache misses, or calculating Year-over-Year percentage changes).
- Transforms raw database tuples and documents into structured Pydantic response models.
- Contains all domain business rules.

### 3. Repository Layer (`app/repositories/`)
- Encapsulates database-specific query syntax (PyMongo filters, Redis pipelines, Cassandra CQL statements, Neo4j Cypher scripts).
- Handles low-level cursor iteration, schema mapping, and data normalization.
- Does not depend on FastAPI or HTTP concepts.

### 4. Database Connection Layer (`app/databases/`)
- Manages connection creation, persistent connection pools, graceful shutdown hooks, and diagnostic health ping checks.

---

## 6. Frontend Architecture

The frontend is constructed using **React + Vite** with a modular component hierarchy and strict separation of concerns:

```text
React Pages (Dashboard, Analytics)
       ↓
Custom React Hooks (useDashboard, useAnalytics)
       ↓
API Services (dashboardApi, analyticsApi)
       ↓
HTTP Client (client.js with AbortController timeout & error handling)
       ↓
FastAPI Backend Gateway (/api/v1/)
```

- **Environment Config (`src/config/environment.js`)**: Dynamic base URL resolution using `import.meta.env.VITE_API_BASE_URL`.
- **API Client Layer (`src/services/api/`)**: Centralized HTTP client (`client.js`) handling timeout abort controllers and JSON error unpacking, wrapped by specialized service modules (`dashboardApi.js`, `analyticsApi.js`).
- **Custom Hooks (`src/hooks/`)**: `useDashboard` orchestrates multi-panel data loading, filter synchronizations, and loading states; `useAnalytics` tracks query latency and active query sections.
- **Component Design System (`src/components/`)**:
  - `common/`: `LoadingState`, `ErrorState`, `EmptyState`, `DataTable`.
  - `layout/`: `Header`, `Sidebar`.
  - `dashboard/`: `KpiCard`, `ChartCard`.
  - `analytics/`: `QueryResult`.
