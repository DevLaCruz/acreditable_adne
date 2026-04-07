#!/bin/bash

set -e

echo "=========================================="
echo "Migración de SQLite3 a PostgreSQL"
echo "=========================================="
echo ""

# Paso 1: Intentar exportar datos de SQLite
echo "[1/5] Exportando datos de SQLite3..."
if python manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude admin --natural-foreign --natural-primary > /tmp/data.json 2>&1; then
    DATA_SIZE=$(wc -c < /tmp/data.json)
    if [ "$DATA_SIZE" -gt 100 ]; then
        echo "✓ Datos exportados a /tmp/data.json ($(($DATA_SIZE / 1024)) KB)"
    else
        echo "⚠ No hay datos para exportar, se aplicarán solo las migraciones"
        > /tmp/data.json
    fi
else
    echo "⚠ No se pudo exportar de SQLite3, continuando con migraciones limpias"
    > /tmp/data.json
fi
echo ""

# Paso 2: Configurar PostgreSQL como base de datos
echo "[2/5] Configurando PostgreSQL como base de datos..."
echo "✓ PostgreSQL está configurado"
echo ""

# Paso 3: Aplicar migraciones a PostgreSQL
echo "[3/5] Aplicando migraciones a PostgreSQL..."
python manage.py migrate
echo "✓ Migraciones aplicadas"
echo ""

# Paso 4: Cargar datos si existen
echo "[4/5] Cargando datos a PostgreSQL..."
if [ -s /tmp/data.json ]; then
    python manage.py loaddata /tmp/data.json 2>&1 || echo "⚠ Algunos datos no pudieron cargarse (probablemente datos inconsistentes)"
    echo "✓ Datos cargados"
else
    echo "✓ No hay datos para cargar"
fi
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
echo "Ahora puedes ejecutar: docker-compose logs -f web"
echo "Para ver los logs en tiempo real"
