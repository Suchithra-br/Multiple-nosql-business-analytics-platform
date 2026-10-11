"""
Turnkey Public Demo Launcher for Multi-NoSQL Business Analytics Platform.
Spawns the Cloudflare Quick Tunnel to expose the full production stack
(React frontend, FastAPI backend, MongoDB, Redis, Cassandra, Neo4j)
over a free, globally accessible HTTPS public URL.
"""

import os
import re
import sys
import time
import socket
import subprocess

DOCKER_IMAGE = "cloudflare/cloudflared:latest"
TARGET_PORT = 4173
HOST_TARGET = f"http://host.docker.internal:{TARGET_PORT}"


def check_port(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a local TCP port is listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def main():
    print("=" * 70)
    print("  SUPERSTORE SALES ANALYTICS - ZERO-COST PUBLIC DEMO LAUNCHER")
    print("=" * 70)

    # 1. Check Backend
    if not check_port(8000):
        print("[!] FastAPI backend is not running on port 8000.")
        print("    Starting FastAPI backend in background...")
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)
    else:
        print("[✓] FastAPI backend is active on port 8000.")

    # 2. Check Frontend Preview
    if not check_port(TARGET_PORT):
        print(f"[!] Frontend web server is not running on port {TARGET_PORT}.")
        print("    Starting Vite preview server...")
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
        subprocess.Popen(
            ["npx", "vite", "preview", "--port", str(TARGET_PORT), "--host", "0.0.0.0"],
            cwd=frontend_dir,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)
    else:
        print(f"[✓] Frontend web server is active on port {TARGET_PORT}.")

    # 3. Launch Cloudflare Tunnel
    print("\n[*] Initializing Cloudflare Public Tunnel (₹0, zero signup, secure SSL)...")
    cmd = [
        "docker", "run",
        "--name", "analytics-public-tunnel-launcher",
        "--rm",
        DOCKER_IMAGE,
        "tunnel",
        "--no-autoupdate",
        "--url", HOST_TARGET
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        tunnel_url = None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()

            if not tunnel_url and "trycloudflare.com" in line:
                match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if match:
                    tunnel_url = match.group(0)
                    print("\n" + "=" * 70)
                    print("  🎉 PUBLIC DEMO URL IS READY!")
                    print(f"  Share this link with your evaluators:")
                    print(f"  --> {tunnel_url}")
                    print("=" * 70 + "\n")

    except KeyboardInterrupt:
        print("\n[*] Stopping Cloudflare Tunnel container...")
        subprocess.run(["docker", "stop", "analytics-public-tunnel-launcher"], capture_output=True)
        print("[✓] Tunnel stopped cleanly.")


if __name__ == "__main__":
    main()
