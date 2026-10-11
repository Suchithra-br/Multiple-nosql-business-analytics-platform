# Multi-NoSQL Business Analytics Platform — React Frontend

Professional, data-focused business analytics dashboard consuming the polyglot FastAPI backend.

---

## 1. Frontend Architecture & Technology

- **Framework**: React 18 with Vite 6
- **Styling**: Vanilla CSS (`src/styles/app.css`) with high-contrast, clean corporate typography and custom CSS tokens.
- **Charts**: Recharts 2.15 (ResponsiveContainer, AreaChart, BarChart, Tooltip)
- **Design Principles**:
  - Genuine business analytics application, NOT a marketing website.
  - Zero purple gradients, no fake/unsupported metrics (no profit, discount, quantity).
  - Clean separation: React connects solely to FastAPI (`http://localhost:8000`), never directly to MongoDB, Redis, Cassandra, or Neo4j.
  - Zero hardcoded database credentials in frontend.

---

## 2. Directory Structure

```text
frontend/
├── package.json
├── vite.config.js
├── index.html
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   │
│   ├── components/
│   │   ├── Header.jsx          # Project title, FastAPI status indicator, refresh trigger
│   │   ├── Sidebar.jsx         # Dashboard and Analytics navigation tabs, polyglot storage list
│   │   ├── KpiCard.jsx         # Executive KPI card with title, value, subtext, and Redis badge
│   │   ├── ChartCard.jsx       # Chart and table card with loading, error, and empty states
│   │   ├── DataTable.jsx       # Tabular data grid with custom column formatters
│   │   └── LoadingState.jsx    # Accessible loading spinner
│   │
│   ├── pages/
│   │   ├── Dashboard.jsx       # Executive overview, monthly trend, regions, categories, leaderboards
│   │   └── Analytics.jsx       # Database roles, MongoDB lookups, Cassandra dates, Neo4j graphs
│   │
│   ├── services/
│   │   └── api.js              # Centralized API service with VITE_API_BASE_URL configuration
│   │
│   ├── utils/
│   │   └── formatters.js       # Consistent currency ($), integer, and date formatters
│   │
│   ├── styles/
│   │   └── app.css             # Professional corporate analytics theme (navy, slate, emerald)
│   │
│   ├── setupTests.js           # Vitest setup with jest-dom matchers & ResizeObserver polyfill
│   └── __tests__/
│       └── App.test.jsx        # 18 unit and integration tests
└── README.md
```

---

## 3. Configuration

The frontend uses a centralized API configuration via Vite environment variables:

```bash
# Default fallback: http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000
```

All 19 API calls originate from `src/services/api.js`. The API URL is never hardcoded across components.

---

## 4. Getting Started

### Installation
```bash
cd frontend
npm install
```

### Running Locally
```bash
npm run dev
```
The dashboard will be available at: **`http://localhost:5173`**

### Running Frontend Tests
```bash
npm test
```
Runs 18 Vitest unit/integration tests covering all dashboard cards, tables, lookups, and error states.

### Production Build
```bash
npm run build
```
Creates an optimized production bundle inside the `dist/` directory.

---

## 5. Available Pages & Major Sections

### Dashboard Page (`/`)
- **Executive KPI Cards**:
  - Total Revenue: `$2,261,536.78` (Redis cache)
  - Total Orders: `4,922` (Redis cache)
  - Average Order Value: `$459.48` (Redis cache)
  - Last Cache Refresh: ISO timestamp
- **Monthly Sales Trend**: Chronological 48-month area chart with year filter (All, 2015, 2016, 2017, 2018).
- **Regional Breakdown**: Bar chart covering West, East, Central, and South.
- **Category Breakdown**: Bar chart covering Technology, Furniture, and Office Supplies.
- **Customer Segments**: Sales breakdown by Consumer, Corporate, and Home Office.
- **Shipping Modes**: Summary table with order volume and percentage of total revenue.
- **Top 10 Products**: Leaderboard ranked via Redis sorted set (`ZREVRANGE`).
- **Top 10 Customers**: Leaderboard ranked by lifetime spend via Redis sorted set.

### Analytics Page (`Analytics Tab`)
- **Database Architecture Indicators**: Highlighting the specific roles of Redis, MongoDB, Cassandra, and Neo4j.
- **MongoDB Operational Search**:
  - Order Document Lookup: Returns nested line items, customer info, shipping addresses, and order total.
  - Customer Profile Lookup: Returns lifetime spend, order count, and primary region.
- **Cassandra Time-Series Slices**:
  - Daily Sales Slice: Point-in-time order retrieval by `order_date` partition key.
  - Regional Date Range: Range scan across region clustering keys.
  - Category Date Range: Range scan across category clustering keys.
- **Neo4j Graph Analytics**:
  - Customer Purchase Network: Graph path traversals for order history and purchased products.
  - Frequently Co-Purchased Products: Collaborative graph queries (`(p1)<-[:CONTAINS]-(:Order)-[:CONTAINS]->(p2)`).
  - Regional Category Taxonomy: 6-hop Cypher traversal linking regions to categories.

---

## 6. System Endpoints

- **Frontend Application**: `http://localhost:5173`
- **FastAPI Backend Gateway**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Backend Health Check**: `http://localhost:8000/api/v1/health`
