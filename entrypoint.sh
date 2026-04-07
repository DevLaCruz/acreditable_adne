#!/bin/bash

set -e

echo "Esperando que la base de datos esté lista..."

# Esperar a que PostgreSQL esté disponible (usando bash en lugar de nc)
while ! timeout 1 bash -c '</dev/tcp/db/5432' 2>/dev/null; do
  echo "PostgreSQL no está disponible, aguardando..."
  sleep 1
done

echo "PostgreSQL está disponible"
echo "Generando migraciones faltantes..."

# Generar migraciones si hay cambios pendientes
python manage.py makemigrations --noinput

echo "Ejecutando migraciones..."

# Ejecutar migraciones
python manage.py migrate --noinput

echo "Creando usuario superadmin si no existe..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123456',
        first_name='Admin',
        last_name='User'
    )
    print(f"Superuser 'admin' creado con éxito")
else:
    print("El superuser 'admin' ya existe")
END

echo "Iniciando Gunicorn..."
exec /opt/venv/bin/gunicorn \
    --workers=4 \
    --worker-class=sync \
    --bind=0.0.0.0:8000 \
    --timeout=120 \
    --access-logfile=/app/logs/gunicorn_access.log \
    --error-logfile=/app/logs/gunicorn_error.log \
    --log-level=info \
    TiendaSuarez.wsgi:application
