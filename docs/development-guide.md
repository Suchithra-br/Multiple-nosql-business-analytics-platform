# Development & Operations Guide

## 1. System Requirements & Prerequisites

Ensure the following runtimes and tools are installed on your machine:

- **Python**: Version 3.10 or later (tested up to Python 3.14).
- **Node.js**: Version 18.x or later with `npm` 9+.
- **Docker & Docker Compose**: Docker Desktop with Linux containers enabled.
- **Git**: Version 2.30+.

---

## 2. Initial Setup & Environment Configuration

### Step 2.1 — Clone the Repository
```bash
git clone <repository-url>
cd "Multiple nosql business analytics platform"
```

### Step 2.2 — Configure Environment Variables
Create a local `.env` file from the provided `.env.example`:
```bash
cp .env.example .env
```
Ensure the connection credentials match your local Docker environment defaults:
- MongoDB URI: `mongodb://localhost:27017`
- Redis Host: `localhost`, Port: `6379`
- Cassandra Host: `127.0.0.1`, Port: `9042`, Keyspace: `business_analytics`
- Neo4j URI: `bolt://localhost:7687`, User: `neo4j`, Password: `your_neo4j_password_here`

### Step 2.3 — Install Backend Dependencies
Create and activate a Python virtual environment:
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt
```

### Step 2.4 — Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 3. Launching Database Infrastructure

Start all four NoSQL databases using Docker Compose:

```bash
docker-compose up -d
```

Verify that all containers are healthy and running:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected containers:
- `mongodb` on port `27017`
- `redis` on port `6379`
- `cassandra` on port `9042`
- `neo4j` on ports `7474` (HTTP) and `7687` (Bolt)

> [!NOTE]
> Apache Cassandra takes approximately 30–60 seconds to complete its initial keyspace daemon startup. Allow Cassandra to stabilize before running loaders.

---

## 4. Running the ETL & Database Population

The project includes an automated ETL pipeline that validates the historical dataset `data/train.csv`, isolates clean subsets into `generated_data/`, and populates all four databases.

### Step 4.1 — Execute Full Pipeline
```bash
python -m backend.app.etl.pipeline
```

### Step 4.2 — Execute Individual Database Loaders (if needed)
```bash
# Populate MongoDB document store
python scripts/load_mongodb.py

# Populate Redis in-memory cache and leaderboards
python scripts/refresh_redis.py

# Populate Apache Cassandra wide-column time-series tables
python scripts/load_cassandra.py

# Populate Neo4j property graph
python scripts/load_neo4j.py
```

---

## 5. Running the Application Locally

### Running the FastAPI Backend
Start the Uvicorn development server:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

### Running the React Frontend
In a separate terminal:
```bash
cd frontend
npm run dev
```
- Open your browser at: `http://localhost:5173`

---

## 6. Testing & Quality Assurance

### Run Backend Test Suite (`pytest`)
Executes all 111 unit, integration, and database tests:
```bash
python -m pytest backend/tests -v
```

### Run Frontend Test Suite (`vitest`)
Executes all 25 unit and component tests:
```bash
cd frontend
npm test -- --run
```

### Build Frontend Production Bundle
Validates JSX syntax, Rollup chunking, and asset bundling:
```bash
cd frontend
npm run build
```

---

## 7. Troubleshooting & Common Issues

### Issue 1: Cassandra Connection Timeout
- **Symptom**: `NoHostAvailable: ('Unable to connect to any servers', {'127.0.0.1:9042': ...})`
- **Fix**: Cassandra container is still completing JVM boot. Run `docker logs cassandra` and wait until `Startup complete` appears before rerunning scripts.

### Issue 2: Neo4j Authentication Error
- **Symptom**: `neo4j.exceptions.AuthError: The client is unauthorized due to authentication failure.`
- **Fix**: Verify `NEO4J_PASSWORD` in your `.env` matches the password set in `docker-compose.yml` (`NEO4J_AUTH=neo4j/your_password`).

### Issue 3: Redis Cache Outdated
- **Symptom**: Dashboard shows older metrics after source data modification.
- **Fix**: Run `python scripts/refresh_redis.py` or trigger the refresh button in the dashboard UI.

### Issue 4: Port Already in Use
- **Symptom**: `Bind for 0.0.0.0:8000 failed: port is already allocated`
- **Fix**: Identify the process using `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (Linux) and terminate it.
