#!/bin/bash
# Script para verificar que los cambios se han subido correctamente a GitHub

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
    echo -e "${BLUE}[GITHUB]${NC} $1"
}

# Directorio del proyecto
PROJECT_DIR="/home/espasiko/mainmanusodoo/manusodoo-roto"

# Cambiar al directorio del proyecto
cd "$PROJECT_DIR" || { print_error "No se pudo acceder al directorio del proyecto"; exit 1; }

# Verificar si estamos en un repositorio Git
if [ ! -d ".git" ]; then
    print_error "No se encontró un repositorio Git en $PROJECT_DIR"
    exit 1
fi

# Obtener información del repositorio
REPO_URL=$(git config --get remote.origin.url)
if [[ "$REPO_URL" =~ github\.com[:/]([^/]+)/([^/.]+) ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    print_info "Repositorio: $OWNER/$REPO"
else
    print_error "No se pudo determinar el propietario y nombre del repositorio"
    exit 1
fi

# Obtener la rama actual
BRANCH=$(git branch --show-current)
print_info "Rama actual: $BRANCH"

# Verificar si hay cambios locales no subidos
print_info "Verificando cambios locales no subidos..."
LOCAL_COMMITS=$(git log origin/$BRANCH..$BRANCH --oneline 2>/dev/null | wc -l)

if [ "$LOCAL_COMMITS" -gt 0 ]; then
    print_warning "Hay $LOCAL_COMMITS commits locales que no se han subido a GitHub."
    git log origin/$BRANCH..$BRANCH --oneline
else
    print_status "No hay commits locales pendientes de subir."
fi

# Verificar archivos importantes
print_info "Verificando archivos importantes en el repositorio local..."

# Lista de directorios y archivos importantes a verificar
IMPORTANT_DIRS=(
    "odoo"
    "fastapi"
    "frontend"
    "n8n"
    "docker-compose.yml"
    "README.md"
)

for item in "${IMPORTANT_DIRS[@]}"; do
    if [ -e "$item" ]; then
        if [ -d "$item" ]; then
            FILES_COUNT=$(find "$item" -type f | wc -l)
            print_status "✅ $item (directorio con $FILES_COUNT archivos)"
        else
            print_status "✅ $item (archivo)"
        fi
    else
        print_warning "⚠️ $item no encontrado en el repositorio local"
    fi
done

print_info "=== Resumen de verificación ==="
print_info "Repositorio: $OWNER/$REPO"
print_info "Rama: $BRANCH"

if [ "$LOCAL_COMMITS" -eq 0 ]; then
    print_status "✅ Todos los cambios están subidos a GitHub"
else
    print_warning "⚠️ Hay cambios locales que no se han subido a GitHub"
fi

print_info "🎉 Verificación completada"
echo ""
print_warning "Para una verificación completa, ejecuta los siguientes comandos:"
echo "1. git fetch origin"
echo "2. git diff origin/$BRANCH"