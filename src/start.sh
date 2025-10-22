#!/usr/bin/env bash
set -e

echo "⏳ Esperando a que PostgreSQL esté disponible..."
python - <<EOF
from app.wait_db import wait_for_postgres
wait_for_postgres()
EOF

echo "🟢 PostgreSQL está listo. Lanzando Uvicorn..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

echo "⏳ Esperando 5 segundos a que Uvicorn arranque..."
sleep 5

echo "📥 Cargando alertas desde JSON…"
python load_data.py

# Queda a la espera de que Uvicorn termine (para no cerrar el contenedor)
wait
