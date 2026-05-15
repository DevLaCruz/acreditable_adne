# Multi-stage build para optimizar el tamaño de la imagen
FROM python:3.13-slim as builder

# Instalar dependencias del sistema necesarias para compilar paquetes Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo para el builder
WORKDIR /build

# Copiar requirements.txt
COPY requirements.txt .

# Crear virtual environment e instalar dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel && \
    pip install -v -r requirements.txt

# Stage final - imagen más pequeña
FROM python:3.13-slim

# Instalar solo las dependencias de runtime necesarias (incluyendo libpq5 para psycopg3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    netcat-openbsd \
    curl \
    ca-certificates \
    libgcc1 \
    libc6 \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser

# Establecer directorio de trabajo
WORKDIR /app

# Copiar virtual environment del builder
COPY --from=builder /opt/venv /opt/venv

# Copiar el código de la aplicación
COPY --chown=appuser:appuser . .

# Configurar variables de entorno
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=TiendaSuarez.settings

# Crear directorios necesarios y fijar permisos
RUN mkdir -p /app/media /app/static && \
    chown -R appuser:appuser /app

# Copiar y hacer ejecutable el script de inicialización
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Recopilar archivos estáticos como appuser
USER appuser
RUN python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Exponer puerto (Gunicorn)
EXPOSE 8000

# Script de inicialización
ENTRYPOINT ["/app/entrypoint.sh"]

