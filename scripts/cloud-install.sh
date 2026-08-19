#!/usr/bin/env bash
# Idempotent Cloud Agent install: Python 3.12 venv + project deps.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y python3.12-venv
fi

python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

.venv/bin/python -c "import mcp, fastapi, httpx, cachetools, dotenv"
echo "cloud-install: ok ($(".venv/bin/python" -V))"
