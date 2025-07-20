#!/bin/bash

# Script para detener n8n en el proyecto Manusodoo-Roto
# Fecha: 19/07/2025

echo "🛑 Deteniendo n8n para Manusodoo-Roto..."
echo "========================================"

# Verificar si Docker está en ejecución
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker no está en ejecución. Por favor, inicia Docker primero."
    exit 1
fi

# Detener n8n con Docker Compose
echo "🔄 Deteniendo contenedor n8n..."
docker-compose down

# Verificar si el contenedor se detuvo correctamente
if [ $? -eq 0 ]; then
    echo "✅ n8n detenido correctamente"
else
    echo "❌ Error al detener n8n. Revisa los logs con: docker-compose logs"
fi
