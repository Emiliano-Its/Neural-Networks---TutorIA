#!/usr/bin/env bash
# Levanta la API (FastAPI, 127.0.0.1:8000) y el frontend (Vite, localhost:5173).
# Uso: ./run_dev.sh        (Ctrl+C detiene ambos)
set -euo pipefail
cd "$(dirname "$0")"

UVICORN=.venv/bin/uvicorn
if [ ! -x "$UVICORN" ]; then
  echo "No encuentro $UVICORN. Crea el entorno e instala dependencias:"
  echo "  python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt"
  exit 1
fi
if ! .venv/bin/python -c "import fastapi" 2>/dev/null; then
  echo "Instalando dependencias de Python (fastapi, uvicorn)..."
  .venv/bin/pip install -r backend/requirements.txt
fi
[ -d frontend/node_modules ] || (cd frontend && npm install)

for puerto in 8000 5173; do
  if ss -ltn 2>/dev/null | grep -q ":$puerto "; then
    echo "El puerto $puerto ya está ocupado (¿otra copia corriendo?). Detenla primero:"
    echo "  ss -ltnp | grep $puerto     # muestra el PID;  luego: kill <PID>"
    exit 1
  fi
done

"$UVICORN" api.main:app --app-dir backend --reload --reload-dir backend --host 127.0.0.1 --port 8000 &
API=$!
trap 'kill $API 2>/dev/null || true' EXIT INT TERM

echo "Esperando a la API..."
for _ in $(seq 1 60); do
  if curl -s http://127.0.0.1:8000/api/salud >/dev/null 2>&1; then break; fi
  if ! kill -0 $API 2>/dev/null; then echo "La API no arrancó; revisa el error de arriba."; exit 1; fi
  sleep 1
done
echo "API arriba en http://127.0.0.1:8000  (entrena los modelos en ~10 s)"
echo "Abre http://localhost:5173  ·  admin: http://localhost:5173/admin"

cd frontend && npm run dev
