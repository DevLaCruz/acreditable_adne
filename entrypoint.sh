#!/bin/bash

set -e

echo "Esperando que la base de datos esté lista..."

# Esperar a que PostgreSQL esté disponible
while ! nc -z db 5432; do
  echo "PostgreSQL no está disponible, aguardando..."
  sleep 1
done

echo "PostgreSQL está disponible"
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
        password='admin123456'
    )
    print(f"Superuser 'admin' creado con éxito")
else:
    print("El superuser 'admin' ya existe")
END

echo "Iniciando Gunicorn..."
exec "$@"
