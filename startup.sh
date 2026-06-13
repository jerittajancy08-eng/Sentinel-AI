#!/usr/bin/env bash
# ─────────────────────────────────────────────
# Sentinel AI — Backend Startup Command (Azure App Service, code deploy)
#
# If deploying via ZIP/code push instead of a container (App Service ->
# Configuration -> General Settings -> Startup Command), set the startup
# command to:
#
#   bash startup.sh
#
# Or directly:
#
#   uvicorn api.main:app --host 0.0.0.0 --port 8000
#
# App Service injects $PORT automatically; this script respects it.
# ─────────────────────────────────────────────
set -e

pip install -r requirements.txt --quiet
uvicorn api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
