#!/usr/bin/env bash
# Levanta la API (FastAPI, puerto 8000) y el frontend (Vite, puerto 5173).
# Uso: ./run_dev.sh        (Ctrl+C detiene ambos)
set -e
cd "$(dirname "$0")"
[ -d .venv ] && source .venv/bin/activate
[ -d frontend/node_modules ] || (cd frontend && npm install)
uvicorn api.main:app --reload --port 8000 &
API=$!
trap 'kill $API 2>/dev/null' EXIT INT TERM
cd frontend && npm run dev
