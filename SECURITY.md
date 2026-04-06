# 🔐 Guía de Seguridad para Producción

## Checklist de Seguridad - ANTES de lanzar

- [ ] `DEBUG = False` en .env
- [ ] `SECRET_KEY` es único y muy largo (50+ caracteres)
- [ ] `ALLOWED_HOSTS` solo contiene tus dominios reales
- [ ] SSL/TLS configurado y válido
- [ ] Base de datos con contraseña fuerte
- [ ] Usuario `admin` cambió su contraseña default
- [ ] Archivos estáticos recolectados
- [ ] Backups automatizados configurados
- [ ] Logs centralizados
- [ ] Firewall configurado

## 1. Django Settings - Seguridad

### Mínimo requerido

```python
# settings.py

# OBLIGATORIO en producción
DEBUG = False
ALLOWED_HOSTS = ['tu-dominio.com', 'www.tu-dominio.com']

# CSRF y Cookies
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_TRUSTED_ORIGINS = ['https://tu-dominio.com']

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 3600  # 1 hora

# HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "cdn.jsdelivr.net"],
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", 'data:', 'https:'],
    'font-src': ["'self'", 'fonts.googleapis.com'],
}

X_CONTENT_TYPE_OPTIONS = 'nosniff'
X_FRAME_OPTIONS = 'DENY'
REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Archivos
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
```

## 2. Dockerfile - Seguridad

El Dockerfile incluye:

✅ Usuario no-root (`appuser`)
✅ Multi-stage build (menos vulnerabilidades)
✅ Sin acceso al histórico de comandos
✅ Permisos restrictivos en archivos

Para mejorar aún más:

```dockerfile
# Versión más segura
FROM python:3.11-slim

# Crear usuario restringido
RUN useradd -m -u 1000 -s /sbin/nologin appuser

# Instalar solo lo necesario
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Permisos restrictivos
COPY --chown=appuser:appuser . /app

# Limpiar archivos temporales
RUN chmod 644 /app/* && \
    find /app -name "*.pyc" -delete && \
    find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

USER appuser

# No correr como root
ENTRYPOINT ["/bin/sh", "-c"]
```

## 3. Nginx - Seguridad

El nginx.prod.conf incluye headers de seguridad. Adicionales:

```nginx
# En nginx.conf / nginx.prod.conf

# Protección contra clickjacking
add_header X-Frame-Options "DENY" always;

# Protección XSS
add_header X-XSS-Protection "1; mode=block" always;

# MIME type sniffing
add_header X-Content-Type-Options "nosniff" always;

# HSTS (HTTP Strict Transport Security)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# CSP (Content Security Policy)
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'" always;

# Permissions Policy
add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=()" always;

# Limitar métodos HTTP
limit_except GET HEAD POST PUT DELETE {
    deny all;
}

# Protección contra DDoS - Rate Limiting
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req zone=general burst=50 nodelay;

# Timeouts para prevenir DoS
client_body_timeout 12s;
client_header_timeout 12s;
keepalive_timeout 15s;
send_timeout 10s;
```

## 4. PostgreSQL - Seguridad

```bash
# En el contenedor PostgreSQL, crear usuario limitado

# Conectar y ejecutar
docker-compose exec db psql -U postgres

# Crear usuario con permisos limitados
CREATE USER app_user WITH PASSWORD 'strong_password_here';

# Crear BD
CREATE DATABASE app_db OWNER app_user;

# Permisos específicos (NO dar SUPERUSER)
GRANT CONNECT ON DATABASE app_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT CREATE ON SCHEMA public TO app_user;

# Revocar permisos de sistema
REVOKE ALL ON DATABASE postgres FROM PUBLIC;
```

## 5. Firewall - Configuración Básica

### UFW (Uncomplicated Firewall)

```bash
sudo ufw enable

# Permitir SSH (MUY IMPORTANTE - no te cierres)
sudo ufw allow 22/tcp

# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Bloquear todo lo demás
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Ver status
sudo ufw status numbered
```

### Iptables avanzado

```bash
# Limitar conexiones SSH
sudo iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set
sudo iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 4 -j DROP

# Protección contra port scanning
sudo iptables -N port-scanning
sudo iptables -A port-scanning -p tcp --tcp-flags SYN,ACK,FIN,RST RST -m limit --limit 1/s --limit-burst 2 -j ACCEPT
sudo iptables -A port-scanning -j DROP
```

## 6. SSH - Seguridad Mejorada

```bash
# Editar /etc/ssh/sshd_config

# Puerto no estándar (OPCIONAL - documentation best practice)
Port 2222

# Desabilitar login de root
PermitRootLogin no

# Desabilitar password auth (usar keys)
PubkeyAuthentication yes
PasswordAuthentication no

# Desabilitar X11 forwarding
X11Forwarding no

# Conexiones simultáneas limitadas
MaxAuthTries 3
MaxSessions 5

# Timeout de inactividad
ClientAliveInterval 300
ClientAliveCountMax 2

# Reiniciar SSH
sudo systemctl restart sshd
```

## 7. Variables de Entorno - Best Practices

### Nunca en .env production

```env
# ❌ NUNCA HAGAS ESTO
DATABASE_PASSWORD=password123
SECRET_KEY=secret-key-visible-en-github
AWS_KEY=AKIAIOSFODNN7EXAMPLE

# ✅ CORRECTO
# Usar AWS Secrets Manager, HashiCorp Vault, etc.
```

### Usar Secrets Manager

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id suarez/prod > /tmp/secrets.json
export $(cat /tmp/secrets.json | jq -r '.SecretString' | jq -r 'to_entries | .[] | "\(.key)=\(.value)"')
```

## 8. HTTPS/SSL - Certificados

### Let's Encrypt - Renovación Automática

```bash
# Crear script
cat << 'EOF' > /home/usuario/renew_ssl.sh
#!/bin/bash

# Renovar certificados
certbot renew --quiet --agree-tos

# Copiar a volumen de Docker
sudo cp /etc/letsencrypt/live/tu-dominio/fullchain.pem /home/usuario/proyectos/suarez/ssl/cert.pem
sudo cp /etc/letsencrypt/live/tu-dominio/privkey.pem /home/usuario/proyectos/suarez/ssl/key.pem
sudo chown usuario:usuario /home/usuario/proyectos/suarez/ssl/*

# Recargar nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
EOF

chmod +x /home/usuario/renew_ssl.sh

# Agregar a cron (ejecutar cada mes)
(crontab -l 2>/dev/null; echo "0 2 1 * * /home/usuario/renew_ssl.sh") | crontab -
```

### Verificar Certificado

```bash
# Verificar validez
openssl x509 -in ssl/cert.pem -text -noout

# Validar con SSL Labs
# https://www.ssllabs.com/ssltest/analyze.html?d=tu-dominio.com
```

## 9. Backups - Automatizados

### Script de Backup Cifrado

```bash
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/suarez"

# Crear backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U suarez_user suarez_db > "${BACKUP_DIR}/db_${DATE}.sql"

# Comprimir
gzip "${BACKUP_DIR}/db_${DATE}.sql"

# Cifrar (opcional)
openssl enc -aes-256-cbc -salt -in "${BACKUP_DIR}/db_${DATE}.sql.gz" -out "${BACKUP_DIR}/db_${DATE}.sql.gz.enc" -pass pass:"$BACKUP_PASSWORD"

# Eliminar original no cifrado
rm "${BACKUP_DIR}/db_${DATE}.sql.gz"

# Sincronizar a AWS S3
aws s3 sync "${BACKUP_DIR}" "s3://tu-bucket-backups/" --delete

# Mantener solo últimos 30 días
find "${BACKUP_DIR}" -name "*.enc" -mtime +30 -delete

echo "Backup completado: db_${DATE}.sql.gz.enc"
```

Agregar a cron:

```bash
# Diario a las 3 AM
0 3 * * * /home/usuario/backup.sh >> /var/log/backups.log 2>&1
```

## 10. Monitoreo y Logging

### Logging Centralizado

```bash
pip install python-json-logger
```

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

### Monitoreo con Prometheus

```bash
pip install django-prometheus
```

```python
# settings.py
INSTALLED_APPS = [
    'django_prometheus',
    ...
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
```

## 11. Auditoría y Logs

### Log de cambios sensibles

```python
# En models.py
import logging

logger = logging.getLogger('audit')

class Pedido(models.Model):
    def save(self, *args, **kwargs):
        if self.pk:
            logger.warning(f'Pedido {self.pk} modificado por {user}')
        super().save(*args, **kwargs)
```

### Webhook de seguridad

```python
# Agregar a settings.py
SECURITY_WEBHOOK = 'https://tu-servicio-alertas.com/webhook'
```

## 12. Pruebas de Seguridad

### Check list antes de producción

```bash
# Scan de vulnerabilidades conocidas
pip install safety
safety check

# Análisis estático (SAST)
pip install bandit
bandit -r . -ll

# Escanear dependencias
pip install pip-audit
pip-audit

# Mozilla Security Guidelines
# https://infosec.mozilla.org/guidelines/

# OWASP Top 10
# https://owasp.org/www-project-top-ten/
```

## 13. Respuesta ante Incidentes

### En caso de compromiso

```bash
# 1. Aislar el servidor
sudo iptables -P INPUT DROP
sudo iptables -P OUTPUT DROP

# 2. Crear snapshot del sistema para forense
# En cloud: tomar snapshot del volumen

# 3. Restorar desde backup limpio
docker-compose -f docker-compose.prod.yml down -v
# Restaurar backup seguro
./manage-docker.sh restore backup_limpio.sql.enc

# 4. Cambiar todas las contraseñas
# 5. Rotar keys de API
# 6. Auditar logs de acceso
```

## 14. Cumplimiento Regulatorio

### Si manejas datos personales

- **GDPR** (Europa): Cumplir con derechos de datos
- **CCPA** (California): Transparencia de datos
- **PCI-DSS** (Pagos): Si procesas tarjetas
- **HIPAA** (Salud): Si datos médicos

```python
# Agregar en settings.py para GDPR
GDPR_COMPLIANT = True
DATA_RETENTION_DAYS = 365

# Logging de acceso a datos sensibles
logger.info(f'PII accessed for user {user_id}')
```

---

**Recuerda:** 🔒 Seguridad es un proceso continuo, no un destino.

Última actualización: Abril 2024
