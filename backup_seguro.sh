#!/bin/bash
# Script para crear un backup completo del proyecto excluyendo archivos con problemas de permisos

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
    echo -e "${BLUE}[BACKUP]${NC} $1"
}

# Configuración
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/espasiko/mainmanusodoo"
BACKUP_NAME="manusodoo-backup-completo-${DATE}"
BACKUP_TAR="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

print_info "=== Backup Completo ManusOdoo ==="
print_info "Iniciando proceso de backup..."

# Crear backup del proyecto
print_status "Creando backup completo del proyecto..."

# Crear el backup usando tar con exclusiones específicas
tar --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='dist' \
    --exclude='build' \
    --exclude='config/odoo.conf' \
    --exclude='config/odoo1.conf' \
    -czf "$BACKUP_TAR" -C /home/espasiko/mainmanusodoo/manusodoo-roto .

if [ $? -eq 0 ]; then
    print_status "✅ Backup completo creado: $BACKUP_TAR"
    
    # Eliminar backups anteriores
    print_status "Eliminando backups anteriores..."
    find "$BACKUP_DIR" -name "manusodoo-backup-*.tar.gz" -not -name "$(basename $BACKUP_TAR)" -delete
    
    if [ $? -eq 0 ]; then
        print_status "✅ Backups anteriores eliminados"
    else
        print_warning "⚠️ Advertencia al eliminar backups anteriores"
    fi
    
    # Mostrar información del backup
    echo ""
    print_info "=== Información del Backup ==="
    echo "Fecha: $(date)"
    echo "Ubicación: $BACKUP_TAR"
    echo "Tamaño: $(du -h "$BACKUP_TAR" | cut -f1)"
    echo ""
    print_warning "Nota: Se excluyeron archivos de configuración con permisos restringidos."
    print_warning "      Para un backup completo, considere hacer una copia manual de los archivos en config/"
    echo ""
    echo "📋 Para restaurar:"
    echo "   1. Extraer: tar -xzf $BACKUP_TAR -C /ruta/destino"
    echo ""
    
    print_info "🎉 Backup completado exitosamente"
else
    print_error "❌ Error al crear el backup"
    exit 1
fi
