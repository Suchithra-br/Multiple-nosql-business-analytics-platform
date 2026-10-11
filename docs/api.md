# REST API Documentation (v1)

Base URL: `http://localhost:8000/api/v1`  
Interactive Swagger UI: `http://localhost:8000/docs`  
OpenAPI Specification: `http://localhost:8000/openapi.json`

---

## 1. Health

### `GET /api/v1/health`
Checks the live connectivity status of all 4 NoSQL database backends.

- **Method**: `GET`
- **Database Used**: Redis, MongoDB, Cassandra, Neo4j
- **Parameters**: None
- **Response Purpose**: Returns individual engine health status for system monitoring and automated readiness probes.
- **Success Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-10-11T12:00:00Z",
    "databases": {
      "redis": "healthy",
      "mongodb": "healthy",
      "cassandra": "healthy",
      "neo4j": "healthy"
    }
  }
  ```
- **Possible Errors**: 
  - `503 Service Unavailable`: Critical database connection failure.
  - Returns `200 OK` with `"status": "degraded"` if individual non-critical pools time out.

---

## 2. Dashboard

### `GET /api/v1/dashboard/overview`
Retrieves executive KPI cards including total revenue, order count, unique customer count, product count, and average order value.

- **Method**: `GET`
- **Database Used**: Redis (in-memory cached default) / MongoDB (aggregation pipeline when filtered)
- **Parameters**:
  - `year` (query, integer, optional): Filter by fiscal year (2015, 2016, 2017, 2018).
  - `region` (query, string, optional): Filter by geographic region (`West`, `East`, `Central`, `South`).
- **Response Purpose**: Populates top-level KPI metric cards and Year-over-Year (YoY) comparison badges.
- **Success Response (200 OK)**:
  ```json
  {
    "total_sales": 2261536.7827,
    "total_orders": 4922,
    "average_order_value": 459.4752,
    "last_refreshed_at": "2026-10-11T12:09:22Z",
    "average_shipping_days": 4.0,
    "yoy_sales_growth": 20.3,
    "yoy_orders_growth": 28.3,
    "yoy_aov_growth": -6.2,
    "comparison_label": "2018 vs 2017"
  }
  ```
- **Possible Errors**: `422 Unprocessable Entity` for invalid year or region format.

### `GET /api/v1/dashboard/monthly`
Returns chronological monthly sales volume across all recorded years.

- **Method**: `GET`
- **Database Used**: Redis / MongoDB
- **Parameters**:
  - `year` (query, integer, optional)
  - `region` (query, string, optional)
- **Response Purpose**: Drives the interactive sales trendline chart and monthly seasonality breakdown.
- **Success Response (200 OK)**:
  ```json
  [
    { "month": "2015-01", "sales": 14236.89, "orders": 31 },
    { "month": "2015-02", "sales": 4519.89, "orders": 19 }
  ]
  ```

### `GET /api/v1/dashboard/regions`
Provides sales distribution and order volumes across the four sales regions.

- **Method**: `GET`
- **Database Used**: Redis / MongoDB
- **Parameters**:
  - `year` (query, integer, optional)
- **Response Purpose**: Populates regional distribution charts and market share summaries.
- **Success Response (200 OK)**:
  ```json
  [
    { "region": "West", "sales": 710219.68, "orders": 1543 },
    { "region": "East", "sales": 669518.73, "orders": 1435 },
    { "region": "Central", "sales": 492646.91, "orders": 1085 },
    { "region": "South", "sales": 389151.46, "orders": 859 }
  ]
  ```

### `GET /api/v1/dashboard/categories`
Provides product category breakdown (Technology, Furniture, Office Supplies).

- **Method**: `GET`
- **Database Used**: Redis / MongoDB
- **Parameters**:
  - `year` (query, integer, optional)
  - `region` (query, string, optional)
- **Response Purpose**: Renders category revenue distribution charts.
- **Success Response (200 OK)**:
  ```json
  [
    { "category": "Technology", "sales": 827455.87, "orders": 1812 },
    { "category": "Furniture", "sales": 728658.58, "orders": 1720 },
    { "category": "Office Supplies", "sales": 705422.33, "orders": 2963 }
  ]
  ```

### `GET /api/v1/dashboard/segments`
Retrieves customer segment breakdown (Consumer, Corporate, Home Office).

- **Method**: `GET`
- **Database Used**: Redis / MongoDB
- **Parameters**:
  - `year` (query, integer, optional)
  - `region` (query, string, optional)
- **Response Purpose**: Visualizes customer segment share across retail channels.
- **Success Response (200 OK)**:
  ```json
  [
    { "segment": "Consumer", "sales": 1148060.53, "orders": 2548 },
    { "segment": "Corporate", "sales": 688494.07, "orders": 1477 },
    { "segment": "Home Office", "sales": 424982.18, "orders": 897 }
  ]
  ```

### `GET /api/v1/dashboard/shipping`
Returns distribution of orders and revenue across delivery shipping modes.

- **Method**: `GET`
- **Database Used**: Redis / MongoDB
- **Parameters**:
  - `year` (query, integer, optional)
  - `region` (query, string, optional)
- **Response Purpose**: Provides logistics breakdown (Standard Class, Second Class, First Class, Same Day).
- **Success Response (200 OK)**:
  ```json
  [
    { "ship_mode": "Standard Class", "sales": 1340831.31, "orders": 2899 },
    { "ship_mode": "Second Class", "sales": 449914.18, "orders": 943 },
    { "ship_mode": "First Class", "sales": 345572.26, "orders": 772 },
    { "ship_mode": "Same Day", "sales": 125219.03, "orders": 308 }
  ]
  ```

### `GET /api/v1/dashboard/subcategories`
Provides sales breakdown across 17 granular merchandise sub-categories.

- **Method**: `GET`
- **Database Used**: MongoDB (Aggregation Pipeline)
- **Parameters**:
  - `year` (query, integer, optional)
  - `region` (query, string, optional)
- **Response Purpose**: Renders sub-category bar charts and inventory ranking cards.
- **Success Response (200 OK)**:
  ```json
  [
    { "sub_category": "Phones", "sales": 327782.45, "orders": 876 },
    { "sub_category": "Chairs", "sales": 322822.73, "orders": 607 }
  ]
  ```

### `GET /api/v1/dashboard/states`
Returns state revenue rankings with order frequency.

- **Method**: `GET`
- **Database Used**: MongoDB
- **Parameters**:
  - `year` (query, integer, optional)
  - `region` (query, string, optional)
  - `limit` (query, integer, default: 10, min: 1, max: 50)
- **Response Purpose**: Supplies state-level revenue leaderboards.
- **Success Response (200 OK)**:
  ```json
  [
    { "state": "California", "sales": 446306.46, "orders": 981 },
    { "state": "New York", "sales": 306361.15, "orders": 551 }
  ]
  ```

---

## 3. Analytics

### `GET /api/v1/analytics/products/top`
Retrieves top revenue-generating products using high-speed Redis sorted sets.

- **Method**: `GET`
- **Database Used**: Redis (Sorted Sets) / MongoDB (when filtered)
- **Parameters**:
  - `limit` (query, integer, default: 10, min: 1, max: 100)
  - `year` (query, integer, optional)
  - `region` (query, string, optional)
- **Response Purpose**: Renders product leaderboards and exportable data tables.
- **Success Response (200 OK)**:
  ```json
  [
    { "product_id": "TEC-CO-10004722", "product_name": "Canon imageCLASS 2200 Advanced Copier", "total_sales": 61599.82 }
  ]
  ```

### `GET /api/v1/analytics/customers/top`
Retrieves highest spending retail customers.

- **Method**: `GET`
- **Database Used**: Redis (Sorted Sets) / MongoDB (when filtered)
- **Parameters**:
  - `limit` (query, integer, default: 10, min: 1, max: 100)
  - `year` (query, integer, optional)
  - `region` (query, string, optional)
- **Response Purpose**: Renders top VIP customer tables with total expenditure and order counts.
- **Success Response (200 OK)**:
  ```json
  [
    { "customer_id": "SM-20320", "customer_name": "Sean Miller", "total_spend": 25043.05, "order_count": 5 }
  ]
  ```

### `GET /api/v1/analytics/date`
Queries exact single-day sales volume via Cassandra partition lookup (`partition_key: order_date`).

- **Method**: `GET`
- **Database Used**: Apache Cassandra (`sales_by_date`)
- **Parameters**:
  - `date` (query, string, required): Format `YYYY-MM-DD` (e.g., `2017-11-08`)
- **Response Purpose**: Demonstrates Cassandra partition-pruned single-day time-series retrieval.
- **Success Response (200 OK)**:
  ```json
  {
    "date": "2017-11-08",
    "total_sales": 1345.92,
    "line_items_count": 8,
    "items": [...]
  }
  ```

### `GET /api/v1/analytics/region-date`
Queries chronological sales range within a specific geographical partition (`partition_key: region`, `clustering_key: order_date`).

- **Method**: `GET`
- **Database Used**: Apache Cassandra (`sales_by_region_date`)
- **Parameters**:
  - `region` (query, string, required): `West`, `East`, `Central`, `South`
  - `start_date` (query, string, required): `YYYY-MM-DD`
  - `end_date` (query, string, required): `YYYY-MM-DD`
- **Response Purpose**: Demonstrates Cassandra partition-bounded clustering column date range scanning.
- **Success Response (200 OK)**:
  ```json
  {
    "region": "West",
    "start_date": "2017-01-01",
    "end_date": "2017-06-30",
    "total_sales": 74320.15,
    "record_count": 240,
    "records": [...]
  }
  ```
- **Possible Errors**: `400 Bad Request` if `start_date > end_date`.

### `GET /api/v1/analytics/category-date`
Queries chronological sales range within a specific category partition (`partition_key: category`, `clustering_key: order_date`).

- **Method**: `GET`
- **Database Used**: Apache Cassandra (`sales_by_category_date`)
- **Parameters**:
  - `category` (query, string, required): `Technology`, `Furniture`, `Office Supplies`
  - `start_date` (query, string, required): `YYYY-MM-DD`
  - `end_date` (query, string, required): `YYYY-MM-DD`
- **Response Purpose**: Demonstrates Cassandra category partition range scans.
- **Success Response (200 OK)**:
  ```json
  {
    "category": "Technology",
    "start_date": "2017-01-01",
    "end_date": "2017-12-31",
    "total_sales": 226153.67,
    "record_count": 482,
    "records": [...]
  }
  ```

---

## 4. Graph

### `GET /api/v1/analytics/graph/customer/{customer_id}/orders`
Traverses the `(:Customer)-[:PLACED]->(:Order)` path to retrieve purchase history.

- **Method**: `GET`
- **Database Used**: Neo4j
- **Parameters**:
  - `customer_id` (path, string, required): e.g., `CG-12520`
- **Response Purpose**: Demonstrates 1-hop customer order history path traversal.
- **Success Response (200 OK)**:
  ```json
  {
    "customer_id": "CG-12520",
    "customer_name": "Claire Gute",
    "orders": [
      { "order_id": "CA-2017-152156", "order_date": "2017-11-08", "sales": 993.9 }
    ]
  }
  ```
- **Possible Errors**: `404 Not Found` if customer does not exist.

### `GET /api/v1/analytics/graph/customer/{customer_id}/products`
Traverses 2 hops: `(:Customer)-[:PLACED]->(:Order)-[:CONTAINS]->(:Product)`.

- **Method**: `GET`
- **Database Used**: Neo4j
- **Parameters**:
  - `customer_id` (path, string, required): e.g., `CG-12520`
- **Response Purpose**: Demonstrates multi-hop customer product affinity discovery.
- **Success Response (200 OK)**:
  ```json
  {
    "customer_id": "CG-12520",
    "products_purchased": 5,
    "products": [
      { "product_id": "FUR-BO-10001798", "product_name": "Bush Somerset Collection Bookcase", "category": "Furniture" }
    ]
  }
  ```

### `GET /api/v1/analytics/graph/product/{product_id}/copurchases`
Executes collaborative recommendation algorithm finding products that share orders with the target product: `(:Product {product_id: $id})<-[:CONTAINS]-(:Order)-[:CONTAINS]->(other:Product)`.

- **Method**: `GET`
- **Database Used**: Neo4j
- **Parameters**:
  - `product_id` (path, string, required): e.g., `FUR-BO-10001798`
  - `limit` (query, integer, default: 10)
- **Response Purpose**: Generates collaborative "Frequently Bought Together" product recommendations.
- **Success Response (200 OK)**:
  ```json
  [
    {
      "product_id": "FUR-CH-10000454",
      "product_name": "Hon Deluxe Stacking Chairs",
      "copurchase_count": 3
    }
  ]
  ```

### `GET /api/v1/analytics/graph/region/{region}/categories`
Traverses 6 hops from `Region` through geographic hierarchy and orders to product `Category`: `(:Region {name: $region})<-[:PART_OF]-(:State)<-[:LOCATED_IN]-(:City)<-[:SHIPPED_TO]-(:Order)-[:CONTAINS]->(:Product)-[:BELONGS_TO]->(:Category)`.

- **Method**: `GET`
- **Database Used**: Neo4j
- **Parameters**:
  - `region` (path, string, required): `West`, `East`, `Central`, `South`
- **Response Purpose**: Demonstrates deep multi-hop relationship rollup across spatial and merchandise hierarchies.
- **Success Response (200 OK)**:
  ```json
  [
    { "category": "Technology", "sales": 251991.61 },
    { "category": "Furniture", "sales": 252612.74 },
    { "category": "Office Supplies", "sales": 220808.33 }
  ]
  ```

---

## 5. Search

### `GET /api/v1/analytics/customers/search`
Live text prefix lookup for customer autocomplete.

- **Method**: `GET`
- **Database Used**: MongoDB
- **Parameters**:
  - `q` (query, string, required): Partial query text.
  - `limit` (query, integer, default: 10)
- **Response Purpose**: Powers instant search suggestions for customer names and IDs.
- **Success Response (200 OK)**:
  ```json
  [
    { "customer_id": "CG-12520", "customer_name": "Claire Gute", "segment": "Consumer" }
  ]
  ```

### `GET /api/v1/analytics/orders/search`
Live order identifier prefix lookup for search autocomplete.

- **Method**: `GET`
- **Database Used**: MongoDB
- **Parameters**:
  - `q` (query, string, required): Partial order identifier.
  - `limit` (query, integer, default: 10)
- **Response Purpose**: Powers instant search suggestions for order IDs.
- **Success Response (200 OK)**:
  ```json
  [
    { "order_id": "CA-2017-152156", "customer_name": "Claire Gute", "order_date": "2017-11-08" }
  ]
  ```

### `GET /api/v1/analytics/orders/{order_id}`
Retrieves a complete order document with embedded purchased items.

- **Method**: `GET`
- **Database Used**: MongoDB
- **Parameters**:
  - `order_id` (path, string, required): e.g., `CA-2017-152156`
- **Response Purpose**: Displays full operational receipt with customer info, delivery address, and line items.
- **Success Response (200 OK)**:
  ```json
  {
    "order_id": "CA-2017-152156",
    "order_date": "2017-11-08",
    "ship_date": "2017-11-11",
    "ship_mode": "Second Class",
    "customer": { "customer_id": "CG-12520", "customer_name": "Claire Gute" },
    "items": [
      { "product_id": "FUR-BO-10001798", "product_name": "Bush Somerset Collection Bookcase", "sales": 261.96 }
    ],
    "total_sales": 993.9
  }
  ```
- **Possible Errors**: `404 Not Found` if order does not exist.

### `GET /api/v1/analytics/customers/{customer_id}`
Retrieves complete customer profile with order history and total lifetime spending.

- **Method**: `GET`
- **Database Used**: MongoDB
- **Parameters**:
  - `customer_id` (path, string, required): e.g., `CG-12520`
- **Response Purpose**: Displays customer profile card with order history, first order date, and last order date.
- **Success Response (200 OK)**:
  ```json
  {
    "customer_id": "CG-12520",
    "customer_name": "Claire Gute",
    "segment": "Consumer",
    "total_orders": 3,
    "total_spent": 1148.40,
    "orders": [
      { "order_id": "CA-2017-152156", "order_date": "2017-11-08", "sales": 993.9 }
    ]
  }
  ```
- **Possible Errors**: `404 Not Found` if customer does not exist.
