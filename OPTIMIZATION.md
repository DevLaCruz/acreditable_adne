# 🔧 Guía de Optimización y Escalabilidad

## 1. Optimización de Imagen Docker

### Reducir tamaño de la imagen

El Dockerfile ya usa multi-stage build. Para reducir aún más:

```dockerfile
# En Dockerfile, agregar a la sección final:
RUN find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
```

**Tamaño esperado:** ~1.2GB (con todas las dependencias)

### Usar caché agresivo en layers

```bash
# Construir con BuildKit
DOCKER_BUILDKIT=1 docker build -t suarez:latest .
```

## 2. Optimización de Gunicorn

### Ajustar workers según CPU

Edita `supervisord.conf`:

```ini
# Para servidor con 4 cores
command=/opt/venv/bin/gunicorn \
    --workers=9 \
    --worker-class=sync \
    --threads=2 \
    --worker-tmp-dir=/dev/shm
```

**Fórmula:** `workers = (2 × CPU_cores) + 1`

### Usar worker threads

```ini
--worker-class=gthread
--threads=4
--workers=4
```

Ideal para aplicaciones con I/O bound heavy.

## 3. Escalabilidad Horizontal

### Load Balancing con Nginx

```nginx
# Actualizar docker-compose.prod.yml
version: '3.8'

services:
  web1:
    # instancia 1
  web2:
    # instancia 2
  web3:
    # instancia 3
  
  nginx:
    upstream django_web {
        least_conn;  # Distribuir por menos conexiones
        server web1:8000;
        server web2:8000;
        server web3:8000;
    }
```

### Scaling con Docker Compose

```bash
# Ejecutar múltiples instancias
docker-compose up -d --scale web=3
```

Nota: Actualizar nginx.conf con upstream dinámico.

## 4. Caché con Redis

Redis ya está configurado. Para optimizar:

### Usar Redis para sesiones

Edita `TiendaSuarez/settings.py`:

```python
# Session caching
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_KWARGS': {'encoding': 'utf8'},
            'CONNECTION_POOL_KWARGS': {'max_connections': 50, 'retry_on_timeout': True},
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        }
    }
}
```

Instalar dependencia:
```bash
pip install django-redis
```

### Caché de página completa

```python
# settings.py
from django.views.decorators.cache import cache_page

# En urls.py
path('productos/', cache_page(60 * 15)(views.productos), name='productos'),
```

## 5. Base de Datos - Optimización

### Indexar campos búsquedas

```python
# En models.py
class Producto(models.Model):
    nombre = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['categoria', 'precio']),
            models.Index(fields=['slug', 'activo']),
        ]
```

### Connection pooling

Edita `TiendaSuarez/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### Queries optimization

Audit queries en desarrollo:

```bash
docker-compose exec web python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> 
>>> with CaptureQueriesContext(connection) as ctx:
...     # tu código
>>> print(len(ctx), 'queries')
```

Usar `select_related()` y `prefetch_related()`:

```python
# Para ForeignKey y OneToOne
queryset = Producto.objects.select_related('categoria')

# Para ManyToMany y reverse ForeignKey
queryset = Categoria.objects.prefetch_related('productos')
```

## 6. Compresión y Assets

### CDN para archivos estáticos

```python
# settings.py
STATIC_URL = 'https://cdn.tu-dominio.com/static/'
STATIC_ROOT = '/var/www/static/'

# Configurar AWS S3 (opcional)
if os.environ.get('USE_S3'):
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
```

### Minificación automática

```bash
pip install whitenoise django-compressor
```

```python
# settings.py
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Agregar primero
    ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

## 7. Monitoreo y Alertas

### Health checks extendidos

Crear endpoint en `core/views.py`:

```python
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
```

En `TiendaSuarez/urls.py`:

```python
path('health/', core_views.health_check),
```

### Logging estructurado

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

## 8. Seguridad - Producción Ready

### Headers adicionales

```python
# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    "default-src": ("'self'",),
    "script-src": ("'self'", "'unsafe-inline'", "cdn.example.com"),
}
X_FRAME_OPTIONS = 'DENY'
```

### Rate limiting avanzado

```bash
pip install django-ratelimit
```

```python
# views.py
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='100/h')
def api_view(request):
    pass
```

## 9. Celery (Tareas Asincrónicas)

Si necesitas procesos en background:

```bash
pip install celery redis
```

```python
# TiendaSuarez/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TiendaSuarez.settings')

app = Celery('TiendaSuarez')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

```python
# En models o views
from TiendaSuarez.celery import app

@app.task
def enviar_email_async(email):
    # Enviar email sin bloquear request
    pass
```

Descomentar en `docker-compose.prod.yml`:

```yaml
celery:
  build: .
  command: celery -A TiendaSuarez worker -l info
```

## 10. CI/CD con GitHub Actions

Crear `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd ~/proyectos/suarez
            git pull
            docker-compose -f docker-compose.prod.yml build
            docker-compose -f docker-compose.prod.yml up -d
            docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

## 11. Benchmarking

### Prueba de carga local

```bash
pip install locust
```

```python
# locustfile.py
from locust import HttpUser, task

class WebsiteUser(HttpUser):
    @task
    def index(self):
        self.client.get("/")
    
    @task
    def productos(self):
        self.client.get("/tienda/")
```

```bash
locust
# Visitar http://localhost:8089
```

### Apache Bench

```bash
apt-get install apache2-utils

# Test simple
ab -n 100 -c 10 http://localhost/

# Con cookies
ab -n 1000 -c 50 -C "sessionid=..." http://localhost/
```

## 12. Configuración Recomendada por Escala

### Para ~100 usuarios simultáneos
```ini
workers=5
threads=2
```

### Para ~1000 usuarios simultáneos
```ini
workers=9
threads=4
# + Nginx upstream con 2-3 instancias
```

### Para ~10000+ usuarios
```ini
# Distribuido en múltiples servidores
# + PostgreSQL en servidor separado
# + Redis en servidor separado
# + CDN para assets
# + Load balancer de nivel 4
```

---

**Última actualización:** Abril 2024
**Versión:** 1.0
