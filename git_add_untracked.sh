#!/bin/bash
# Script para verificar el estado de Git y añadir archivos no rastreados

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

# Cambiar a la rama version-consolidada-13-07
print_info "Cambiando a la rama version-consolidada-13-07..."
git checkout version-consolidada-13-07 2>/dev/null

if [ $? -ne 0 ]; then
    print_warning "No se pudo cambiar a la rama version-consolidada-13-07. Creándola..."
    git checkout -b version-consolidada-13-07
fi

# Verificar el estado actual de Git
print_info "Verificando el estado actual de Git..."
git status

# Guardar la lista de archivos no rastreados en un archivo temporal
print_info "Identificando archivos no rastreados..."
git ls-files --others --exclude-standard > /tmp/untracked_files.txt

# Contar cuántos archivos no rastreados hay
UNTRACKED_COUNT=$(wc -l < /tmp/untracked_files.txt)

if [ "$UNTRACKED_COUNT" -eq 0 ]; then
    print_status "No hay archivos nuevos para añadir al control de versiones."
else
    print_status "Se encontraron $UNTRACKED_COUNT archivos no rastreados."
    
    # Mostrar los archivos no rastreados
    echo "Archivos no rastreados:"
    cat /tmp/untracked_files.txt
    
    # Añadir todos los archivos no rastreados al control de versiones
    print_info "Añadiendo archivos no rastreados al control de versiones..."
    # Añadir archivos uno por uno para manejar nombres con espacios
    while IFS= read -r file; do
        git add "$file"
    done < /tmp/untracked_files.txt
    
    if [ $? -eq 0 ]; then
        print_status "✅ Archivos añadidos correctamente"
    else
        print_error "❌ Error al añadir archivos"
        exit 1
    fi
fi

# Verificar si hay cambios para hacer commit
print_info "Verificando cambios para commit..."
git status --porcelain | grep -q "^M"

if [ $? -eq 0 ]; then
    print_status "Hay archivos modificados listos para commit."
    
    # Hacer commit de los cambios
    print_info "Haciendo commit de los cambios..."
    git commit -m "Actualización automática: $(date +%Y-%m-%d) - Consolidación de cambios"
    
    if [ $? -eq 0 ]; then
        print_status "✅ Commit realizado correctamente"
    else
        print_error "❌ Error al hacer commit"
        exit 1
    fi
else
    print_status "No hay cambios modificados para hacer commit."
fi

# Mostrar resumen final
print_info "=== Resumen del estado de Git ==="
git status

print_info "🎉 Proceso completado exitosamente"
echo ""
print_warning "Para subir los cambios a GitHub, ejecuta:"
echo "git push origin version-consolidada-13-07"