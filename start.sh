#!/bin/bash
# start.sh - Script de arranque del sistema ManusOdoo

echo "=== Iniciando ManusOdoo ==="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[SYSTEM]${NC} $1"
}

# Verificar que Docker esté instalado
if ! which docker > /dev/null 2>&1; then
    print_error "Docker no está instalado. Ejecute ./install.sh primero"
    exit 1
fi

# Verificar que Docker esté ejecutándose
if ! docker info &> /dev/null; then
    print_error "Docker no está ejecutándose. Iniciando Docker..."
    sudo systemctl start docker
    sleep 3
    if ! docker info &> /dev/null; then
        print_error "No se pudo iniciar Docker. Verifique la instalación"
        exit 1
    fi
fi

# Verificar si los contenedores ya están ejecutándose
if docker ps | grep -q "odoo\|db\|adminer\|fastapi"; then
    print_warning "Algunos contenedores ya están ejecutándose"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAMES|odoo|db|adminer|fastapi"
else
    print_status "Algunos contenedores ya están ejecutándose. Verificando estado..."
fi

# Detener contenedores existentes para evitar conflictos
print_status "Deteniendo contenedores existentes..."
docker-compose down 2>/dev/null || true

# Iniciar los contenedores con Docker Compose
print_status "Iniciando contenedores con Docker Compose..."
docker-compose up -d db
sleep 5  # Esperar a que la base de datos esté lista
docker-compose up -d odoo adminer fastapi

if [ $? -ne 0 ]; then
    print_error "Error al iniciar los contenedores con docker-compose"
    print_error "Verificando logs de docker-compose..."
    docker-compose logs --tail 20
    exit 1
fi

print_status "✅ Contenedores iniciados correctamente"

# Esperar a que PostgreSQL esté listo
print_status "Esperando a que PostgreSQL esté disponible..."
retries=0
max_retries=30

# Obtener el nombre real del contenedor de la base de datos
DB_CONTAINER=$(docker-compose ps -q db)
if [ -z "$DB_CONTAINER" ]; then
    print_error "No se pudo encontrar el contenedor de la base de datos"
    exit 1
fi

while ! docker exec $DB_CONTAINER pg_isready -U odoo &> /dev/null; do
    echo -n "."
    sleep 2
    retries=$((retries + 1))
    if [ $retries -ge $max_retries ]; then
        print_error "Timeout esperando a PostgreSQL. Verificando logs..."
        docker logs --tail 20 $DB_CONTAINER
        exit 1
    fi
done
echo ""
print_status "✅ PostgreSQL está listo"

# Esperar a que Odoo esté listo
print_status "Esperando a que Odoo esté disponible..."
retries=0
max_retries=30

# Obtener el nombre real del contenedor de Odoo
ODOO_CONTAINER=$(docker-compose ps -q odoo)
if [ -z "$ODOO_CONTAINER" ]; then
    print_error "No se pudo encontrar el contenedor de Odoo"
    exit 1
fi

while ! curl -s http://localhost:8069 > /dev/null; do
    echo -n "."
    sleep 5
    retries=$((retries + 1))
    if [ $retries -ge $max_retries ]; then
        print_error "Timeout esperando a Odoo. Verificando logs..."
        docker logs --tail 20 $ODOO_CONTAINER
        exit 1
    fi
done
echo ""
print_status "✅ Odoo está ejecutándose"

# Esperar a que FastAPI esté listo
print_status "Esperando a que FastAPI esté disponible..."
retries=0
max_retries=15

# Obtener el nombre real del contenedor de FastAPI
FASTAPI_CONTAINER=$(docker-compose ps -q fastapi)
if [ -z "$FASTAPI_CONTAINER" ]; then
    print_error "No se pudo encontrar el contenedor de FastAPI"
    exit 1
fi

while ! curl -s http://localhost:8000/docs > /dev/null; do
    echo -n "."
    sleep 3
    retries=$((retries + 1))
    if [ $retries -ge $max_retries ]; then
        print_error "Timeout esperando a FastAPI. Verificando logs..."
        docker logs --tail 20 $FASTAPI_CONTAINER
        exit 1
    fi
done
echo ""
print_status "✅ FastAPI está ejecutándose"

# Configurar entorno Python para middleware (si es necesario)
if [ -f "requirements.txt" ]; then
    if [ ! -d "venv" ]; then
        print_status "Creando entorno virtual Python..."
        python3 -m venv venv
    fi
    
    print_status "Activando entorno virtual y actualizando dependencias..."
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
    print_status "✅ Entorno Python configurado"
fi

# Verificar dependencias Node.js
if [ -f "package.json" ]; then
    if [ ! -d "node_modules" ]; then
        print_status "Instalando dependencias Node.js..."
        npm install
    else
        print_status "✅ Dependencias Node.js ya instaladas"
    fi
fi

# FastAPI ahora se inicia automáticamente como contenedor Docker (servicio fastapi en docker-compose.yml)

# Iniciar frontend en modo desarrollo si se especifica
if [ "$1" = "--with-frontend" ]; then
    print_status "Iniciando frontend en puerto 3001..."
    if pgrep -f "vite.*3001" > /dev/null; then
        print_warning "El frontend ya está en ejecución"
    else
        nohup npm run dev > frontend.log 2>&1 &
        sleep 5
        if pgrep -f "vite.*3001" > /dev/null; then
            print_status "✅ Frontend iniciado en http://localhost:3001"
        else
            print_error "❌ Error al iniciar el frontend. Revise frontend.log"
        fi
    fi
fi

# Mostrar estado del sistema
echo ""
print_info "=== Estado del Sistema ==="
echo "Contenedores en ejecución:"
docker-compose ps

echo ""
print_status "🎉 Sistema iniciado correctamente"
echo ""
echo "📋 Servicios disponibles:"
echo "   🏢 Odoo ERP: http://localhost:8069"
echo "   🗄️  PostgreSQL: localhost:5432"
echo "   🔌 API FastAPI: http://localhost:8000 (contenedor Docker)"
echo "   🛠️  Adminer: http://localhost:8080"
if [ "$1" = "--with-frontend" ]; then
    echo "   🖥️  Frontend: http://localhost:3001"
else
    echo "   📊 Dashboard: Ejecute './dev-dashboard.sh' para iniciar"
fi
echo ""
echo "🔧 Comandos útiles:"
echo "   ./start.sh --with-frontend  - Iniciar todo el sistema incluyendo frontend"
echo "   ./dev-dashboard.sh         - Iniciar dashboard en modo desarrollo"
echo "   ./stop.sh                  - Detener todos los servicios"
echo "   ./backup.sh                - Crear backup del sistema"
echo "   docker-compose logs odoo   - Ver logs de Odoo"
echo "   docker-compose logs db     - Ver logs de PostgreSQL"
echo "   docker-compose logs fastapi - Ver logs de FastAPI"
echo "   docker-compose ps          - Ver estado de contenedores"
echo ""