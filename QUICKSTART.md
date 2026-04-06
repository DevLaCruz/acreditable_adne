# 🚀 INICIO RÁPIDO - DOCKER SUAREZ (Simplificado)

## Arquitectura

```
Local/Dev: Docker + Nginx interno en puerto 80
VPS:       Tu Nginx (80/443) → Docker (127.0.0.1:8000)
```

## Requisitos
- Docker: https://docs.docker.com/get-docker/
- Docker Compose: https://docs.docker.com/compose/install/

---

## 🏠 DESARROLLO LOCAL

### Paso 1: Preparación (Primera vez)

```bash
chmod +x manage-docker.sh
./manage-docker.sh setup
```

Edita el archivo `.env` con tus datos:
```bash
nano .env
```

### Paso 2: Iniciar

```bash
./manage-docker.sh dev
```

**Acceso:**
- 🌐 Sitio: http://localhost
- 🔧 Admin: http://localhost/admin
- 👤 Usuario: admin
- 🔐 Contraseña: admin123456

### Paso 3: Verificar

```bash
# Ver servicios corriendo
./manage-docker.sh ps

# Ver logs
./manage-docker.sh logs
```

---

## 🖥️ PRODUCCIÓN EN VPS

### Paso 1: En tu VPS (SSH)

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Paso 2: Copiar proyecto

```bash
# En tu VPS
cd /home/usuario/proyectos/
git clone tu-repositorio suarez
cd suarez

# Preparar .env
cp .env.example .env
nano .env  # Editar con tus valores
```

**Valores importantes para .env:**
```env
DEBUG=False
SECRET_KEY=algo-muy-seguro-minimo-50-caracteres
DB_PASSWORD=contraseña-muy-segura
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
EMAIL_HOST_PASSWORD=app-password-de-gmail
```

### Paso 3: Configurar Nginx del VPS

```bash
# Copiar configuración
sudo cp nginx.conf.vps /etc/nginx/sites-available/suarez

# Editar con tu dominio (IMPORTANTE)
sudo nano /etc/nginx/sites-available/suarez
# Buscar y cambiar 3 cosas:
# 1. tu-dominio.com → tu dominio real (línea 9)
# 2. /home/usuario/proyectos/suarez (línea 45 y 49)

# Activar
sudo ln -s /etc/nginx/sites-available/suarez /etc/nginx/sites-enabled/

# Probar
sudo nginx -t

# Recargar
sudo systemctl reload nginx
```

### Paso 4: Certificados SSL

```bash
# Instalar Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx -y

# Generar certificado
sudo certbot certonly --standalone -d tu-dominio.com -d www.tu-dominio.com

# Ver certificados creados
ls /etc/letsencrypt/live/
```

### Paso 5: Ejecutar Docker Compose

```bash
cd /home/usuario/proyectos/suarez

# Construir imagen (la primera vez toma ~5 minutos)
docker-compose -f docker-compose.prod.yml build

# Ejecutar en background
docker-compose -f docker-compose.prod.yml up -d

# Verificar que todo anda
docker-compose -f docker-compose.prod.yml ps
```

### Paso 6: Verificar que funciona

```bash
# Desde tu máquina local
curl https://tu-dominio.com

# Acceder en navegador
# https://tu-dominio.com/admin → admin/admin123456
```

---

## 📋 Comandos Rápidos

**Desarrollo:**
```bash
./manage-docker.sh help              # Ver todos los comandos
./manage-docker.sh dev               # Iniciar
./manage-docker.sh stop              # Detener
./manage-docker.sh logs              # Ver logs
./manage-docker.sh backup            # Backup de BD
```

**Producción (en VPS):**
```bash
# Ver logs
docker-compose -f docker-compose.prod.yml logs -f web

# Backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U suarez_user suarez_db > backup.sql

# Reiniciar app
docker-compose -f docker-compose.prod.yml restart web

# Ejecutar comando Django
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## ✅ Checklist Producción

- [ ] .env configurado (SECRET_KEY, contraseñas, dominios)
- [ ] nginx.conf.vps editado con tu dominio
- [ ] Certificados SSL generados
- [ ] `docker-compose ps` muestra 3 servicios corriendo
- [ ] `https://tu-dominio.com` accesible
- [ ] `/admin` funciona
- [ ] Archivos estáticos cargan (CSS, imágenes)
- [ ] Emails se envían (si configuraste)

---

## 🆘 Solución Rápida de Problemas

| Problema | Solución |
|----------|----------|
| La app no inicia | `docker-compose logs web` |
| Puerto 80/443 en uso | El Nginx del VPS está otra config activa, revisar `/etc/nginx/sites-enabled/` |
| Certificado expirado | `sudo certbot renew` |
| Permisos de archivo | `chmod +x manage-docker.sh entrypoint.sh` |
| Nginx dice "Connection refused" | Revisar que Docker está corriendo: `docker-compose ps` |
| Archivos estáticos no cargan | Revisar ruta en nginx.conf.vps (debe coincidir con tu proyecto real) |

---

## 📚 Documentación Completa

- **README_DOCKER.md** - Guía detallada
- **SETUP_VPS_NGINX.md** - Configuración con tu Nginx
- **OPTIMIZATION.md** - Performance y escalabilidad
- **SECURITY.md** - Hardening para producción

---

**¡Tu aplicación está lista para producción!** 🎉

Última actualización: Abril 2024

