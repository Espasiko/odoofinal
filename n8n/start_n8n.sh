#!/bin/bash

# Script para iniciar n8n en el proyecto Manusodoo-Roto
# Fecha: 19/07/2025

echo "🚀 Iniciando n8n para Manusodoo-Roto..."
echo "========================================"

# Verificar si Docker está en ejecución
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker no está en ejecución. Por favor, inicia Docker primero."
    exit 1
fi

# Verificar si la red de Docker existe
if ! docker network ls | grep -q manusodoo-roto_default; then
    echo "⚠️ La red manusodoo-roto_default no existe. Creándola..."
    docker network create manusodoo-roto_default
fi

# Crear directorio de datos si no existe
mkdir -p ./data

# Iniciar n8n con Docker Compose
echo "🔄 Iniciando contenedor n8n..."
docker-compose up -d

# Verificar si el contenedor se inició correctamente
if [ $? -eq 0 ]; then
    echo "✅ n8n iniciado correctamente"
    echo "📝 Accede a la interfaz web: http://localhost:5678"
    echo "🔑 Usuario por defecto: admin@example.com"
    echo "🔑 Contraseña por defecto: (en blanco, establecer en el primer inicio)"
    echo ""
    echo "📋 Para ver los logs: docker-compose logs -f"
    echo "🛑 Para detener: docker-compose down"
else
    echo "❌ Error al iniciar n8n. Revisa los logs con: docker-compose logs"
fi