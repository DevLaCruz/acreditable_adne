# Multi-stage build para optimizar el tamaño de la imagen
FROM python:3.13-slim as builder

# Instalar dependencias del sistema necesarias para compilar paquetes Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo para el builder
WORKDIR /build

# Copiar requirements.txt
COPY requirements.txt .

# Crear virtual environment e instalar dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage final - imagen más pequeña
FROM python:3.13-slim

# Instalar solo las dependencias de runtime necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    netcat-openbsd \
    curl \
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

# Crear directorios necesarios
RUN mkdir -p /app/logs /app/media /app/static && \
    chown -R appuser:appuser /app

# Recopilar archivos estáticos (sin interacción)
RUN python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Cambiar a usuario no-root
USER appuser

# Exponer puerto (Gunicorn)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Script de inicialización
COPY entrypoint.sh /app/entrypoint.sh
USER root
RUN chmod +x /app/entrypoint.sh
USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]

