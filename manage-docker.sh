#!/bin/bash

# Script auxiliar para gestionar el proyecto con Docker

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar si Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado"
        exit 1
    fi
    
    print_message "Docker y Docker Compose están disponibles"
}

# Mostrar ayuda
show_help() {
    cat << EOF
${GREEN}Gestor de Proyecto Suarez Docker${NC}

Uso: ./manage-docker.sh [COMANDO] [OPCIONES]

Comandos:
  setup                    Configuración inicial del proyecto
  dev                      Iniciar ambiente de desarrollo
  prod                     Iniciar ambiente de producción
  build                    Reconstruir imágenes Docker
  stop                     Detener los servicios
  logs [servicio]          Ver logs (por defecto: web)
  shell [servicio]         Acceder a shell del contenedor
  migrate                  Ejecutar migraciones
  static                   Recolectar archivos estáticos
  createsuperuser          Crear nuevo superuser
  backup                   Crear backup de la base de datos
  restore [archivo]        Restaurar backup
  restart [servicio]       Reiniciar servicio
  clean                    Limpiar volúmenes y contenedores
  ps                       Ver estado de los servicios
  db-shell                 Acceder a PostgreSQL
  help                     Mostrar esta ayuda

Ejemplos:
  ./manage-docker.sh dev              # Iniciar desarrollo
  ./manage-docker.sh logs             # Ver logs de web
  ./manage-docker.sh shell app        # Shell de la app
  ./manage-docker.sh prod             # Iniciar producción
  ./manage-docker.sh backup           # Backup de BD

EOF
}

# Setup inicial
setup() {
    print_message "Configurando proyecto..."
    
    if [ ! -f .env ]; then
        print_message "Creando archivo .env"
        cp .env.example .env
        print_warning "Edita .env con tus valores antes de continuar"
    fi
    
    check_docker
    
    print_message "Construyendo imágenes Docker..."
    docker-compose build
    
    print_message "✓ Setup completado. Ejecuta './manage-docker.sh dev' para iniciar"
}

# Desarrollo
dev() {
    print_message "Iniciando ambiente de desarrollo..."
    check_docker
    docker-compose up -d
    
    print_message "Esperando que los servicios inicien..."
    sleep 5
    
    print_message "✓ Ambiente de desarrollo iniciado"
    print_message "  - Aplicación: http://localhost:80"
    print_message "  - Admin: http://localhost:80/admin"
    print_message "  - Usuario: admin / admin123456"
    print_message ""
    print_message "Ver logs con: ./manage-docker.sh logs"
}

# Producción
prod() {
    print_message "Iniciando ambiente de producción..."
    
    if [ ! -f ssl/cert.pem ]; then
        print_error "Certificados SSL no encontrados en ssl/"
        print_message "Generando certificados autofirmados para testing..."
        mkdir -p ssl
        openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/CN=localhost"
    fi
    
    check_docker
    docker-compose -f docker-compose.prod.yml up -d
    
    print_message "Esperando que los servicios inicien..."
    sleep 10
    
    print_message "✓ Ambiente de producción iniciado"
    print_message "  - Aplicación: https://localhost"
}

# Build
build() {
    print_message "Reconstruyendo imágenes..."
    check_docker
    docker-compose build --no-cache
    print_message "✓ Imágenes reconstruidas"
}

# Stop
stop() {
    print_message "Deteniendo servicios..."
    docker-compose down
    print_message "✓ Servicios detenidos"
}

# Logs
logs() {
    local service="${1:-web}"
    docker-compose logs -f "$service"
}

# Shell
shell() {
    local service="${1:-web}"
    docker-compose exec "$service" bash
}

# Migraciones
migrate() {
    print_message "Ejecutando migraciones..."
    docker-compose exec web python manage.py migrate
    print_message "✓ Migraciones completadas"
}

# Archivos estáticos
static() {
    print_message "Recolectando archivos estáticos..."
    docker-compose exec web python manage.py collectstatic --noinput
    print_message "✓ Archivos estáticos recolectados"
}

# Crear superuser
createsuperuser() {
    print_message "Creando nuevo superuser..."
    docker-compose exec web python manage.py createsuperuser
}

# Backup
backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="backup_${timestamp}.sql"
    
    print_message "Creando backup de la base de datos..."
    docker-compose exec db pg_dump -U suarez_user suarez_db > "$backup_file"
    
    print_message "✓ Backup creado: $backup_file"
}

# Restore
restore() {
    if [ -z "$1" ]; then
        print_error "Especifica el archivo de backup"
        echo "Uso: ./manage-docker.sh restore nombre_backup.sql"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Archivo no encontrado: $1"
        exit 1
    fi
    
    print_warning "Restaurando desde: $1"
    print_warning "Esto sobrescribirá la base de datos actual"
    read -p "¿Continuar? (s/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        print_message "Restaurando..."
        docker-compose exec -T db psql -U suarez_user suarez_db < "$1"
        print_message "✓ Backup restaurado"
    else
        print_message "Operación cancelada"
    fi
}

# Restart
restart() {
    local service="${1:-web}"
    print_message "Reiniciando $service..."
    docker-compose restart "$service"
    print_message "✓ $service reiniciado"
}

# Clean
clean() {
    print_warning "Esto eliminará volúmenes y contenedores"
    read -p "¿Continuar? (s/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        print_message "Limpiando..."
        docker-compose down -v
        print_message "✓ Limpieza completada"
    else
        print_message "Operación cancelada"
    fi
}

# PS
ps() {
    docker-compose ps
}

# DB Shell
db_shell() {
    docker-compose exec db psql -U suarez_user -d suarez_db
}

# Main
main() {
    local cmd="${1:-help}"
    
    case "$cmd" in
        setup)
            setup
            ;;
        dev)
            dev
            ;;
        prod)
            prod
            ;;
        build)
            build
            ;;
        stop)
            stop
            ;;
        logs)
            logs "$2"
            ;;
        shell)
            shell "$2"
            ;;
        migrate)
            migrate
            ;;
        static)
            static
            ;;
        createsuperuser)
            createsuperuser
            ;;
        backup)
            backup
            ;;
        restore)
            restore "$2"
            ;;
        restart)
            restart "$2"
            ;;
        clean)
            clean
            ;;
        ps)
            ps
            ;;
        db-shell)
            db_shell
            ;;
        help)
            show_help
            ;;
        *)
            print_error "Comando desconocido: $cmd"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
