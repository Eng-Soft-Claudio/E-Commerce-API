#!/bin/sh
set -e

echo "--- [ENTRYPOINT] Inicializando o banco de dados..."
python /app/create_db.py

echo "--- [ENTRYPOINT] Iniciando o servidor Uvicorn..."
exec "$@"