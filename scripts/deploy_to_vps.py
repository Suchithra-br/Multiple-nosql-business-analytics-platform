"""
Production VPS Deployment Automation Script.
Deploys the Multi-NoSQL Analytics Platform directly to a Linux VPS via SSH/SCP without GitHub.
"""

import os
import sys
import tarfile
import subprocess
import argparse
import time

EXCLUDE_PATTERNS = {
    'node_modules',
    '__pycache__',
    '.pytest_cache',
    '.git',
    'dist',
    '.venv',
    'venv',
}

def should_exclude(tarinfo):
    name = tarinfo.name
    for pattern in EXCLUDE_PATTERNS:
        if f"/{pattern}/" in f"/{name}/" or name.endswith(f"/{pattern}") or name == pattern:
            return None
    return tarinfo

def create_bundle(output_tar="deploy_bundle.tar.gz"):
    print(f"[*] Packaging project files into {output_tar} (excluding node_modules, pycache)...")
    with tarfile.open(output_tar, "w:gz") as tar:
        for item in ["backend", "frontend", "data", "generated_data", "scripts", "docs", "docker-compose.prod.yml", ".env.example", "README.md"]:
            if os.path.exists(item):
                tar.add(item, filter=should_exclude)
    size_mb = os.path.getsize(output_tar) / (1024 * 1024)
    print(f"[+] Bundle created successfully ({size_mb:.2f} MB)")
    return output_tar

REMOTE_SETUP_SCRIPT = """#!/bin/bash
set -e

echo "=== [1/6] Installing Docker & Docker Compose if missing ==="
if ! command -v docker &> /dev/null; then
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg lsb-release
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

echo "=== [2/6] Unpacking Project Bundle ==="
DEPLOY_DIR="/opt/multi-nosql-analytics"
mkdir -p $DEPLOY_DIR
tar -xzf /tmp/deploy_bundle.tar.gz -C $DEPLOY_DIR
cd $DEPLOY_DIR

echo "=== [3/6] Starting Production Docker Stack ==="
docker compose -f docker-compose.prod.yml up -d --build

echo "=== [4/6] Waiting for Databases to be Healthy ==="
for service in mongodb redis cassandra neo4j; do
    echo "Checking health for $service..."
    while true; do
        STATUS=$(docker inspect --format='{{json .State.Health.Status}}' "prod-analytics-$service" 2>/dev/null || echo '"starting"')
        if [ "$STATUS" = '"healthy"' ]; then
            echo "$service is healthy!"
            break
        fi
        echo "Waiting for $service ($STATUS)..."
        sleep 5
    done
done

echo "=== [5/6] Checking if Data Population is Needed ==="
# Check if MongoDB has orders
ORDER_COUNT=$(docker exec prod-analytics-mongodb mongosh business_analytics --quiet --eval "db.orders.countDocuments()")
if [ "$ORDER_COUNT" -eq "0" ] || [ -z "$ORDER_COUNT" ]; then
    echo "Populating production databases..."
    docker exec prod-analytics-backend python scripts/load_mongodb.py
    docker exec prod-analytics-backend python scripts/load_cassandra.py
    docker exec prod-analytics-backend python scripts/load_neo4j.py
    docker exec prod-analytics-backend python scripts/refresh_redis.py
else
    echo "Databases already initialized with $ORDER_COUNT orders. Skipping duplicate reload."
fi

echo "=== [6/6] Production Stack is Ready ==="
docker ps
"""

def main():
    parser = argparse.ArgumentParser(description="Deploy to Linux Cloud VPS")
    parser.add_argument("--host", required=True, help="VPS Public IP address")
    parser.add_argument("--user", default="root", help="SSH username (default: root)")
    parser.add_argument("--key", help="Path to SSH private key file")
    parser.add_argument("--port", default="22", help="SSH port (default: 22)")
    args = parser.parse_args()

    bundle_path = create_bundle()

    # Write remote setup shell script
    with open("remote_setup.sh", "w", newline="\n") as f:
        f.write(REMOTE_SETUP_SCRIPT)

    ssh_opts = ["-p", args.port, "-o", "StrictHostKeyChecking=no"]
    if args.key:
        ssh_opts += ["-i", args.key]

    target = f"{args.user}@{args.host}"

    print(f"[*] Uploading deployment bundle and setup script to {target}...")
    scp_cmd = ["scp", "-P", args.port]
    if args.key:
        scp_cmd += ["-i", args.key]
    scp_cmd += ["-o", "StrictHostKeyChecking=no", bundle_path, "remote_setup.sh", f"{target}:/tmp/"]
    
    subprocess.run(scp_cmd, check=True)

    print(f"[*] Executing remote provisioning on {target}...")
    ssh_cmd = ["ssh"] + ssh_opts + [target, "bash /tmp/remote_setup.sh"]
    subprocess.run(ssh_cmd, check=True)

    print(f"\n[+] DEPLOYMENT COMPLETED ON PUBLIC HOST: http://{args.host}:3000")
    print(f"[+] BACKEND API: http://{args.host}:8000")
    print(f"[+] SWAGGER DOCS: http://{args.host}:8000/docs")

if __name__ == "__main__":
    main()
