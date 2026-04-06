# Guía de Despliegue con Docker

## Descripción General

Este proyecto Django está configurado para desplegarse fácilmente usando Docker, con soporte para PostgreSQL, Redis, Nginx y Gunicorn.

## Requisitos Previos

- Docker >= 20.10
- Docker Compose >= 1.29
- 2GB de RAM mínimo

## Estructura de Archivos

```
.
├── Dockerfile              # Imagen Docker multietapa optimizada
├── docker-compose.yml      # Desarrollo local
├── docker-compose.prod.yml # Producción
├── nginx.conf             # Configuración Nginx básica
├── nginx.prod.conf        # Configuración Nginx con SSL
├── supervisord.conf       # Supervisor para procesos
├── entrypoint.sh          # Script de inicialización
├── .env.example           # Ejemplo de variables de entorno
└── .dockerignore          # Archivos a ignorar en la imagen
```

## Inicio Rápido

### 1. Preparar Variables de Entorno

```bash
cp .env.example .env
```

Editar `.env` con tus valores reales:

```env
DEBUG=False
SECRET_KEY=tu-clave-secreta-muy-segura
DB_PASSWORD=tu-contraseña-postgres-segura
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
```

### 2. Desarrollo Local

```bash
# Construir la imagen
docker-compose build

# Iniciar los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Acceder a la aplicación
# http://localhost:80
```

**Primera vez:**
- El script `entrypoint.sh` ejecutará:
  - Migraciones de BD
  - Recolección de archivos estáticos
  - Creación de superuser (admin / admin123456)

### 3. Comandos Útiles de Desarrollo

```bash
# Ver estado
docker-compose ps

# Ver logs
docker-compose logs -f web

# Ejecutar comando Django
docker-compose exec web python manage.py createsuperuser

# Acceder a la shell Django
docker-compose exec web python manage.py shell

# Ver base de datos
docker-compose exec db psql -U suarez_user -d suarez_db

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes (cuidado: elimina datos)
docker-compose down -v
```

## Despliegue en Producción

### 1. Preparar el Servidor VPS

```bash
# Actualizar el sistema
sudo apt-get update && sudo apt-get upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Crear usuario para Docker (opcional)
sudo usermod -aG docker $USER
```

### 2. Copiar el Proyecto

```bash
# Clonar o copiar el proyecto a /home/usuario/proyectos/suarez
cd /home/usuario/proyectos/suarez

cp .env.example .env

# Editar variables de entorno
nano .env
```

### 3. Generar Certificados SSL (Obligatorio en Producción)

```bash
# Crear directorio para SSL
mkdir -p ssl

# Opción A: Usar Let's Encrypt con Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Generar certificado
sudo certbot certonly --standalone -d tu-dominio.com -d www.tu-dominio.com

# Copiar certificados
sudo cp /etc/letsencrypt/live/tu-dominio.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/tu-dominio.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*

# Opción B: Autofirmado (solo para testing)
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
```

### 4. Configurar DNS

En tu registrador de dominios, apunta tu dominio a la IP del VPS:

```
A record: tu-dominio.com -> IP_DEL_VPS
A record: www.tu-dominio.com -> IP_DEL_VPS
```

### 5. Levantar en Producción

```bash
# Usar compose de producción
docker-compose -f docker-compose.prod.yml build

docker-compose -f docker-compose.prod.yml up -d

# Verificar servicios
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f web
```

### 6. Renovación Automática de Certificados SSL

```bash
# Crear script de renovación
cat << 'EOF' > renew-ssl.sh
#!/bin/bash

# Renovar certificado
sudo certbot renew --quiet

# Copiar nuevos certificados
sudo cp /etc/letsencrypt/live/tu-dominio.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/tu-dominio.com/privkey.pem ssl/key.pem
sudo chown $USER:$USER ssl/*

# Recargar nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
EOF

chmod +x renew-ssl.sh

# Agregar a crontab para ejecutar cada 3 meses
(crontab -l 2>/dev/null; echo "0 0 1 */3 * /home/usuario/proyectos/suarez/renew-ssl.sh") | crontab -
```

## Monitoreo y Mantenimiento

### Logs

```bash
# Ver todos los logs
docker-compose -f docker-compose.prod.yml logs

# Solo de la aplicación
docker-compose -f docker-compose.prod.yml logs web

# Nginx
docker-compose -f docker-compose.prod.yml logs nginx

# Base de datos
docker-compose -f docker-compose.prod.yml logs db
```

### Backup de Base de Datos

```bash
# Crear backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U suarez_user suarez_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U suarez_user suarez_db < backup_20240101_000000.sql
```

### Actualizar Aplicación

```bash
# Descargar cambios
git pull

# Reconstruir imagen
docker-compose -f docker-compose.prod.yml build

# Actualizar servicios
docker-compose -f docker-compose.prod.yml up -d

# Ejecutar migraciones
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Recolectar estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Optimizaciones de Producción

### 1. Configuración de Gunicorn

En `supervisord.conf`, ajusta según tu servidor:

```
--workers=N  # CPU_CORES * 2 + 1
--max-requests=1000
--max-requests-jitter=100
```

### 2. Escalabilidad

Para escalar horizontalmente:

```bash
# Crear múltiples instancias de web
docker-compose -f docker-compose.prod.yml up -d --scale web=3 nginx
```

Actualizar `docker-compose.prod.yml` para usar load balancing en Nginx.

### 3. Almacenamiento de Media

Para archivos grandes, considerar AWS S3:

```python
# En settings.py, agregar:
if os.environ.get('AWS_STORAGE_BUCKET_NAME'):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

## Troubleshooting

### La aplicación no se inicia

```bash
# Ver logs de error
docker-compose logs web

# Verificar que la BD está lista
docker-compose exec db pg_isready -U suarez_user
```

### Puerto 80 o 443 en uso

```bash
# Cambiar puertos en docker-compose
# Buscar "ports:" y cambiar 80: o 443:
```

### Base de datos con permisos incorrectos

```bash
# Recrear volumen
docker volume rm suarez_postgres_data
docker-compose -f docker-compose.prod.yml up -d db
```

### Sitio seguro (HTTPS) no responde

```bash
# Verificar certificados
ls -la ssl/

# Verificar configuración de Nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

## Variables de Entorno Importantes

```
DEBUG                  # False en producción
SECRET_KEY            # Clave única y segura (mínimo 50 caracteres)
ALLOWED_HOSTS         # Dominios permitidos
DB_PASSWORD           # Contraseña de PostgreSQL
REDIS_PASSWORD        # Contraseña de Redis (opcional)
EMAIL_HOST_PASSWORD   # Contraseña de email
```

## Seguridad

✅ Multi-stage Dockerfile para minimizar tamaño
✅ Usuario no-root en la aplicación
✅ SSL/TLS obligatorio en producción
✅ Headers de seguridad configurados
✅ Rate limiting en Nginx
✅ Gzip compression habilitado
✅ Variables de entorno para secretos
✅ Health checks implementados

## Soporte

Para problemas, revisar:
1. Los logs: `docker-compose logs`
2. La configuración de `.env`
3. El estado de los servicios: `docker-compose ps`
4. Puertos disponibles en el servidor

---

**Última actualización:** 2024
**Versión Docker Compose:** 3.8
