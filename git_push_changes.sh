#!/bin/bash
# Script para subir los cambios a GitHub

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
    echo -e "${BLUE}[GIT]${NC} $1"
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

# Verificar que estamos en la rama correcta
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "version-consolidada-13-07" ]; then
    print_warning "No estás en la rama version-consolidada-13-07. Cambiando..."
    git checkout version-consolidada-13-07 || { print_error "No se pudo cambiar a la rama version-consolidada-13-07"; exit 1; }
fi

# Verificar si hay cambios para subir
print_info "Verificando si hay cambios para subir..."
git status --porcelain

if [ -z "$(git status --porcelain)" ]; then
    print_status "No hay cambios pendientes para subir."
else
    print_warning "Hay cambios pendientes que no se han hecho commit."
    print_warning "Ejecuta primero el script git_add_untracked.sh para añadir y hacer commit de los cambios."
    exit 1
fi

# Verificar si hay commits para subir
print_info "Verificando si hay commits para subir..."
git log origin/version-consolidada-13-07..HEAD --oneline 2>/dev/null

if [ $? -ne 0 ] || [ -z "$(git log origin/version-consolidada-13-07..HEAD --oneline 2>/dev/null)" ]; then
    # Si la rama remota no existe o no hay commits para subir
    print_info "Subiendo la rama por primera vez o sin nuevos commits..."
    git push -u origin version-consolidada-13-07
else
    # Si hay commits para subir
    print_info "Subiendo commits a GitHub..."
    git push origin version-consolidada-13-07
fi

if [ $? -eq 0 ]; then
    print_status "✅ Cambios subidos correctamente a GitHub"
else
    print_error "❌ Error al subir cambios a GitHub"
    exit 1
fi

print_info "🎉 Proceso completado exitosamente"