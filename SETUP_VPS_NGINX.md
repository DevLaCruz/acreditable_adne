# 🛠️ CONFIGURACIÓN SIMPLIFICADA - SIN NGINX EN DOCKER

Tu VPS ya tiene Nginx instalado. Aquí está la nueva arquitectura:

```
Internet (80/443)
    ↓
Nginx en VPS (/etc/nginx/sites-available/suarez)
    ↓
Docker (127.0.0.1:8000)
    ↓
Gunicorn → Django → PostgreSQL + Redis
```

## ✅ Cambios Realizados

1. **docker-compose.yml** - Simplificado sin Nginx
   - Django solo corre en `127.0.0.1:8000` (puerto interno)
   - PostgreSQL y Redis sin exponer puertos
   - Solo Gunicorn (sin Supervisor)

2. **Dockerfile** - Más ligero
   - Elimina Nginx, Supervisor, Nginx
   - Solo Python + Gunicorn
   - Tamaño: ~600MB (antes ~1.2GB)

3. **Nuevo:** `nginx.conf.vps`
   - Configuración para tu Nginx del VPS
   - Proxea a `127.0.0.1:8000`
   - SSL/TLS + Rate limiting

## 🚀 Pasos en tu VPS

### 1. Copiar Nginx Config

```bash
# En tu VPS
sudo cp /ruta/del/proyecto/nginx.conf.vps /etc/nginx/sites-available/suarez

# Editar con tu dominio
sudo nano /etc/nginx/sites-available/suarez
# Cambiar:
# - tu-dominio.com → tu dominio real
# - /home/usuario/proyectos/suarez → tu ruta de proyecto
```

### 2. Activar Config de Nginx

```bash
# Crear symlink
sudo ln -s /etc/nginx/sites-available/suarez /etc/nginx/sites-enabled/

# Probar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

### 3. Certificados SSL (Let's Encrypt)

```bash
# Primera vez
sudo certbot certonly --standalone -d tu-dominio.com -d www.tu-dominio.com

# Renovación automática (cron)
(crontab -l 2>/dev/null; echo "0 3 1 * * certbot renew --quiet && systemctl reload nginx") | crontab -
```

### 4. Docker Compose

```bash
cd /home/usuario/proyectos/suarez

# Preparar .env
cp .env.example .env
nano .env  # Editar con tus datos

# Construir primero (instala paquetes)
docker-compose build

# Ejecutar (solo bases de datos + app)
docker-compose up -d

# Verificar que todo está bien
docker-compose ps
docker-compose logs -f web
```

### 5. Verificar que funciona

```bash
# Puerto 8000 abierto en Docker
curl http://127.0.0.1:8000

# A través de Nginx (desde otra máquina)
curl https://tu-dominio.com
```

## 📋 Checklist Producción

- [ ] `.env` configurado (SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS)
- [ ] `nginx.conf.vps` editado con tu dominio
- [ ] Certificados SSL generados (`/etc/letsencrypt/live/tu-dominio.com/`)
- [ ] Nginx recargado (`sudo systemctl reload nginx`)
- [ ] Docker Compose corriendo (`docker-compose ps` muestra 3 servicios)
- [ ] Accedible en https://tu-dominio.com
- [ ] Estáticos funcionan
- [ ] Admin accesible en /admin

## 🧹 Limpiar Docker Antiguo

Si ejecutaste antes con Supervisor/Nginx:

```bash
# Detener antiguos
docker-compose down -v

# Eliminar imagen vieja
docker rmi suarez:latest

# Construir nueva
docker-compose build

# Ejecutar
docker-compose up -d
```

## 📊 Ventajas de esta Configuración

✅ Nginx centralizado en el VPS (más control)
✅ Docker más ligero (solo app)
✅ Múltiples proyectos Django pueden coexistir
✅ Fácil de escalar (agregar más contenedores web)
✅ Certificados SSL manejados por tu VPS
✅ Logs de Nginx centralizados

## 🔧 Troubleshooting

### Port 8000 not reachable

```bash
# Verificar que Docker está escuchando
docker-compose exec web netstat -tlpn | grep 8000

# Si no hay output, Gunicorn no está corriendo
docker-compose logs web
```

### Nginx dice "Connection refused"

```bash
# Verificar que Docker está corriendo
docker-compose ps

# Si dice "Exit", revisar logs
docker-compose logs web
```

### Certificados expirados

```bash
# Renovar manualmente
sudo certbot renew

# Recargar Nginx
sudo systemctl reload nginx
```

### Cambiar puerto de Docker

Si 8000 está en uso, editar `docker-compose.yml`:

```yaml
ports:
  - "127.0.0.1:9000:8000"  # Cambiar 8000 a 9000
```

Y actualizar en nginx.conf:

```nginx
proxy_pass http://127.0.0.1:9000;  # Cambiar aquí también
```

---

**Ahora tu VPS tiene:**
- Nginx manejando HTTPS + proxy
- Docker ejecutando solo la app
- PostgreSQL + Redis aislados en Docker

¡Listo para producción! 🎉
