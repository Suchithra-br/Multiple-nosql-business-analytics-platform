FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for network tools and diagnostics
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application and dataset assets
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY generated_data/ /app/generated_data/
COPY scripts/ /app/scripts/

ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV API_ENV=production

EXPOSE 8000

# Run with production ASGI configuration
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
