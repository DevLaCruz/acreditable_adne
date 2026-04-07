#!/bin/bash

set -e

# Esperar a que PostgreSQL esté disponible
echo "Esperando PostgreSQL..."
while ! timeout 1 bash -c '</dev/tcp/db/5432' 2>/dev/null; do
  sleep 1
done

echo "PostgreSQL listo. Iniciando Gunicorn..."

# Ejecutar Gunicorn directamente
exec gunicorn \
    --bind=0.0.0.0:8000 \
    --workers=4 \
    --timeout=120 \
    TiendaSuarez.wsgi:application
