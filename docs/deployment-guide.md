# Production Deployment & Hosting Guide

## 1. Deployment Architecture Overview

The **Multi-NoSQL Real-Time Business Analytics Platform** implements a production-grade containerized deployment architecture that isolates and coordinates the frontend, backend, and four distinct NoSQL storage engines:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Production Client Layer                         │
│             React / Vite Single Page Application (Port 4173 / 80)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (/api/v1/)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Production API Gateway Layer                       │
│        FastAPI (Uvicorn Production ASGI / Reverse Proxy, Port 8000)    │
└───────────────┬───────────────────┬───────────────────┬────────────────┘
                │                   │                   │
     ┌──────────┴────────┐ ┌────────┴────────┐ ┌────────┴────────┐
     ▼                   ▼ ▼                 ▼ ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│     Redis     │ │    MongoDB    │ │   Cassandra   │ │     Neo4j     │
│   (Port 6379) │ │  (Port 27017) │ │  (Port 9042)  │ │  (Port 7687)  │
│  In-Memory DB │ │ Document Store│ │  Wide-Column  │ │ Property Graph│
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
```

### Communication Flow:
1. **Frontend to Backend**: The compiled React SPA communicates strictly via HTTP requests to `http://127.0.0.1:8000/api/v1/` using the environment-injected base URL (`VITE_API_BASE_URL`).
2. **Backend to Databases**: FastAPI manages persistent, connection-pooled clients across the isolated network:
   - PyMongo client to `mongodb://localhost:27017`
   - redis-py client to `localhost:6379`
   - cassandra-driver cluster session to `127.0.0.1:9042`
   - neo4j GraphDatabase driver to `bolt://localhost:7687`

---

## 2. Hosting & Infrastructure Selection

### Evaluation of Hosting Strategies for Polyglot Multi-NoSQL:
Hosting four distinct NoSQL engines in a college engineering context presents distinct technical challenges:
- **Serverless/Free Web Tiers** (e.g., Render, Vercel, Railway):
  - Excellent for stateless Web Frontends and FastAPI backends.
  - Incompatible with Apache Cassandra (Cassandra requires 1GB+ dedicated JVM heap and native CQL binary protocol on port 9042, which free container tiers terminate due to Out-Of-Memory (OOM) limits and missing raw TCP port exposure).
  - Incompatible with Neo4j Bolt protocol on free serverless platforms that only proxy standard HTTP/HTTPS traffic.
- **Dedicated Containerized Architecture (Docker Compose / Cloud VM)**:
  - **Chosen Strategy**: Containerized production deployment via Docker Compose and multi-stage Dockerfiles (`backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.prod.yml`).
  - **Suitability**: Provides exact version parity across all 4 databases (`mongo:8`, `redis:7-alpine`, `cassandra:5`, `neo4j:5`), supports healthcheck-gated dependency ordering, preserves persistent disk volumes, and functions identically on a dedicated Linux VPS (e.g., AWS EC2, DigitalOcean Droplet) and local production servers.

---

## 3. Environment Variables

All sensitive values and endpoint configurations are externalized into environment variables.

| Variable | Scope | Description | Production Example |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Frontend | Base URL of the FastAPI gateway | `http://127.0.0.1:8000` |
| `API_ENV` | Backend | Environment flag (`production` / `development`) | `production` |
| `API_HOST` | Backend | Server binding interface | `0.0.0.0` |
| `API_PORT` | Backend | Server HTTP listening port | `8000` |
| `CORS_ORIGINS` | Backend | Comma-separated allowed frontend origins | `http://localhost:3000,http://127.0.0.1:4173` |
| `MONGODB_URI` | Backend | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Backend | Target database name | `business_analytics` |
| `REDIS_URL` | Backend | Optional complete Redis connection URL | `redis://localhost:6379/0` |
| `REDIS_HOST` | Backend | Redis host address | `localhost` |
| `REDIS_PORT` | Backend | Redis listening port | `6379` |
| `REDIS_CACHE_TTL` | Backend | Cache expiration TTL in seconds | `3600` |
| `CASSANDRA_HOST` | Backend | Cassandra contact point host | `127.0.0.1` |
| `CASSANDRA_PORT` | Backend | Cassandra native CQL port | `9042` |
| `CASSANDRA_KEYSPACE`| Backend | Target Cassandra keyspace | `business_analytics` |
| `NEO4J_URI` | Backend | Neo4j Bolt protocol URI | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Backend | Neo4j administrative user | `neo4j` |
| `NEO4J_PASSWORD` | Backend | Neo4j administrative password | *(configured via secret)* |

---

## 4. Database Setup & Initialization Procedure

To deploy and populate the databases from scratch, execute the following verified initialization sequence:

### Step 4.1 — Start Containerized Databases
```bash
docker compose up -d
```
Wait approximately 30–45 seconds for Apache Cassandra and Neo4j to complete JVM initialization and pass their health checks.

### Step 4.2 — Execute Sequential Data Loaders
The loaders must be run in this exact order to respect entity dependencies:

```bash
# 1. Populate master operational documents in MongoDB
python scripts/load_mongodb.py

# 2. Populate partitioned wide-column tables in Cassandra
python scripts/load_cassandra.py

# 3. Populate property graph nodes, relationships, and constraints in Neo4j
python scripts/load_neo4j.py

# 4. Compute and warm executive KPI hashes and leaderboards in Redis
python scripts/refresh_redis.py
```

---

## 5. Backend Production Deployment

The backend runs on **Uvicorn** with production ASGI configuration:

### Direct Production Execution:
```bash
python -m uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  --proxy-headers \
  --forwarded-allow-ips "*"
```

### Containerized Execution (`backend/Dockerfile`):
The provided multi-stage Dockerfile builds a lightweight Python 3.11 image with stripped build dependencies, non-root execution safety, and automated health checks.

---

## 6. Frontend Production Deployment

### Build the Static Bundle:
```bash
cd frontend
npm ci
npm run build
```
This generates optimized static chunks in `frontend/dist/` with gzip compression and cache-busted asset hashing.

### Serving the Production Bundle:
1. **Using Vite Production Server**:
   ```bash
   npx vite preview --port 4173 --host 127.0.0.1
   ```
2. **Using High-Performance Nginx (`frontend/Dockerfile` & `nginx.conf`)**:
   Serves `dist/` with Gzip compression and client-side route fallback to `index.html`.

---

## 7. Cross-Origin Resource Sharing (CORS)

Production CORS is strictly managed in `backend/app/core/config.py`:
- Blind wildcards (`*`) are disallowed.
- Only verified production origins are whitelisted:
  - `http://127.0.0.1:4173`
  - `http://localhost:4173`
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
- Configurable at runtime via the `CORS_ORIGINS` environment variable.

---

## 8. Verified Production Endpoints

The live production deployment is verified and accessible at the following URLs:

- **Frontend Production URL**: [http://127.0.0.1:4173](http://127.0.0.1:4173) (or [http://localhost:3000](http://localhost:3000) via Docker Nginx)
- **Backend API Production URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI Specification**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **Health Diagnostic Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## 9. Health & Diagnostic Verification

The deployment health can be verified at any time using:
```bash
python scripts/verify_deployment.py
```
Expected output:
```text
[PASS] Frontend Production (http://127.0.0.1:4173): Status 200, Latency 40.72ms
[PASS] Swagger UI (http://127.0.0.1:8000/docs): Status 200
[PASS] API Health Check: healthy (Redis: healthy, Mongo: healthy, Cassandra: healthy, Neo4j: healthy)
[PASS] Overview KPIs (Redis): Sales $2,261,536.7827, Orders 4922 - Latency: 5.68ms
[PASS] Filtered Overview (West - MongoDB): Sales $710,219.68 - Latency: 10.24ms
[PASS] MongoDB Order Lookup (CA-2017-152156): Total $993.9, Items 2 - Latency: 6.69ms
[PASS] Cassandra Daily Date (2017-11-08): Items 2, Sales $993.90 - Latency: 55.13ms
[PASS] Cassandra Region-Date (West 2017): Records 787, Sales $182,471.23 - Latency: 52.33ms
[PASS] Neo4j Co-purchases (FUR-BO-10001798): Recommendations 2 - Latency: 19.04ms
[PASS] Neo4j 6-Hop Regional Categories (West): Latency: 21.71ms
[ALL BENCHMARKS VERIFIED ACCURATELY]
```

---

## 10. Troubleshooting Common Deployment Issues

1. **Cassandra Startup Latency**:
   - *Symptom*: Database health probe reports `cassandra: degraded` immediately after container launch.
   - *Remedy*: Cassandra requires 30–60 seconds for JVM warm-up. Wait for the `healthy` status in `docker ps` before starting the backend.
2. **CORS Rejection**:
   - *Symptom*: Browser console error: `Access to XMLHttpRequest has been blocked by CORS policy`.
   - *Remedy*: Ensure the exact frontend hostname and port are included in `CORS_ORIGINS` in `.env`.
3. **Redis Cache Miss / Desynchronization**:
   - *Symptom*: Dashboard metrics return empty or outdated values.
   - *Remedy*: Run `python scripts/refresh_redis.py` to repopulate the in-memory cache hashes and sorted sets.

---

## 11. Honest Deployment Limitations

1. **Resource Requirements**: Operating 4 independent database engines requires a minimum of 4GB RAM (Cassandra and Neo4j alone require 1GB heap each). Low-memory free-tier VPS instances (< 2GB RAM) will experience container termination.
2. **Cold Starts**: When restarting Cassandra or Neo4j containers, initial query latency increases until JVM JIT compilation warms the internal caches.
3. **Single-Node Persistence**: Containers run as single-node instances with local Docker named volumes. In an enterprise multi-region deployment, Cassandra and MongoDB would operate as distributed multi-datacenter clusters with raft/gossip consensus.
