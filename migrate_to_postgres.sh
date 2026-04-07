#!/bin/bash

set -e

echo "=========================================="
echo "Migración de SQLite3 a PostgreSQL"
echo "=========================================="
echo ""

# Paso 1: Exportar datos de SQLite
echo "[1/5] Exportando datos de SQLite3..."
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > data.json
echo "✓ Datos exportados a data.json"
echo ""

# Paso 2: Crear archivo de configuración temporal para PostgreSQL
echo "[2/5] Configurando PostgreSQL como base de datos..."
# Los datos están en .env, así que Django ya usa PostgreSQL
echo "✓ PostgreSQL está configurado como base de datos"
echo ""

# Paso 3: Aplicar migraciones a PostgreSQL
echo "[3/5] Aplicando migraciones a PostgreSQL..."
python manage.py migrate
echo "✓ Migraciones aplicadas"
echo ""

# Paso 4: Cargar datos de vuelta
echo "[4/5] Cargando datos a PostgreSQL..."
python manage.py loaddata data.json
echo "✓ Datos cargados"
echo ""

# Paso 5: Crear superuser
echo "[5/5] Creando superuser (si no existe)..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123456',
        first_name='Admin',
        last_name='User'
    )
    print("✓ Superuser 'admin' creado")
else:
    print("✓ Superuser 'admin' ya existe")
END
echo ""

echo "=========================================="
echo "✓ Migración completada exitosamente"
echo "=========================================="
echo ""
echo "Datafile guardado como: data.json"
echo "Puedes mantenerlo como backup o borrarlo después."
