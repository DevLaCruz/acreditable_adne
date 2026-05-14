#!/bin/bash

set -e

echo "=========================================="
echo "Migración de SQLite3 a PostgreSQL"
echo "=========================================="
echo ""

SQLITE_FILE="suarez_db.sqlite3"

# Verificar que el archivo SQLite exista
if [ ! -f "$SQLITE_FILE" ]; then
    echo "✗ No se encontró $SQLITE_FILE en el directorio actual."
    echo "  Ejecuta este script desde /app dentro del contenedor:"
    echo "  podman-compose exec web bash migrate_to_postgres.sh"
    exit 1
fi

# Paso 1: Exportar datos de SQLite (forzando DB_ENGINE=sqlite3 para este paso)
echo "[1/4] Exportando datos de SQLite3..."
# IMPORTANTE: Se sobrescribe DB_ENGINE=sqlite3 solo para este comando.
# Sin esto, Django leería de PostgreSQL (que ya está activo en el contenedor).
# La opción -o escribe directo al archivo, evitando mezclar warnings de stderr con el JSON.
if DB_ENGINE=sqlite3 python manage.py dumpdata \
    --exclude auth.permission \
    --exclude contenttypes \
    --exclude admin \
    --indent 2 \
    -o /tmp/data.json; then

    DATA_SIZE=$(wc -c < /tmp/data.json)
    if [ "$DATA_SIZE" -gt 100 ]; then
        echo "✓ Datos exportados a /tmp/data.json ($(($DATA_SIZE / 1024)) KB)"
    else
        echo "⚠ No hay datos para exportar"
        > /tmp/data.json
    fi
else
    echo "✗ Error al exportar datos de SQLite3"
    exit 1
fi
echo ""

# Paso 2: Limpiar PostgreSQL para evitar conflictos de PKs y unique constraints
echo "[2/4] Limpiando PostgreSQL y reaplicando migraciones..."
python manage.py makemigrations
python manage.py flush --no-input
python manage.py migrate
echo "✓ PostgreSQL limpio y migraciones aplicadas"
echo ""

# Paso 3: Cargar los datos del SQLite en PostgreSQL
echo "[3/4] Cargando datos a PostgreSQL..."
if [ -s /tmp/data.json ]; then
    python manage.py loaddata /tmp/data.json
    echo "✓ Datos cargados correctamente"
else
    echo "⚠ No hay datos para cargar, la base de datos queda vacía"
fi
echo ""

# Paso 4: Verificar que existan superusuarios (cargados desde SQLite)
# No se crea uno nuevo a ciegas: los superusuarios originales ya vienen del dump.
echo "[4/4] Verificando superusuarios..."
python manage.py shell << 'END'
from django.contrib.auth import get_user_model
User = get_user_model()
admins = User.objects.filter(is_superadmin=True)
if admins.exists():
    usernames = ', '.join(admins.values_list('username', flat=True))
    print(f"✓ Superusuario(s) encontrados: {usernames}")
else:
    print("⚠ No hay superusuarios. Creando uno de emergencia...")
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123456',
        first_name='Admin',
        last_name='User'
    )
    print("✓ Superusuario 'admin' creado (cambia la contraseña luego)")
END
echo ""

echo "=========================================="
echo "✓ Migración completada exitosamente"
echo "=========================================="
echo ""
echo "Ejecuta los logs con: podman-compose logs -f web"
