#!/bin/bash

# Script para actualizar las variables de entorno para la integración entre FastAPI y n8n
# Autor: Equipo Pelotazo ERP
# Fecha: 19/07/2025

# Colores para mensajes
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
ROJO='\033[0;31m'
AZUL='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
mostrar_mensaje() {
  echo -e "${AZUL}[$(date +"%H:%M:%S")]${NC} $1"
}

# Función para mostrar mensajes de éxito
mostrar_exito() {
  echo -e "${VERDE}[✓] $1${NC}"
}

# Función para mostrar advertencias
mostrar_advertencia() {
  echo -e "${AMARILLO}[!] $1${NC}"
}

# Función para mostrar errores
mostrar_error() {
  echo -e "${ROJO}[✗] $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -d "api" ] || [ ! -d "n8n" ]; then
  mostrar_error "Este script debe ejecutarse desde el directorio raíz del proyecto"
  exit 1
fi

# Mostrar mensaje de inicio
mostrar_mensaje "Configurando variables de entorno para integración FastAPI-n8n..."

# Verificar si existe el archivo .env
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
  mostrar_mensaje "Creando archivo .env..."
  touch "$ENV_FILE"
fi

# Función para actualizar o añadir una variable en .env
actualizar_variable() {
  local nombre=$1
  local valor=$2
  
  if grep -q "^$nombre=" "$ENV_FILE"; then
    # La variable existe, actualizarla
    sed -i "s|^$nombre=.*|$nombre=$valor|" "$ENV_FILE"
    mostrar_mensaje "Variable $nombre actualizada"
  else
    # La variable no existe, añadirla
    echo "$nombre=$valor" >> "$ENV_FILE"
    mostrar_mensaje "Variable $nombre añadida"
  fi
}

# Actualizar variables para n8n
mostrar_mensaje "Configurando variables para n8n..."

# Preguntar por la URL de n8n
read -p "Introduce la URL de la API de n8n [http://n8n:5678/api/v1]: " n8n_api_url
n8n_api_url=${n8n_api_url:-http://n8n:5678/api/v1}

# Preguntar por el token de API
read -p "Introduce el token de API de n8n [pelotazo-n8n-api-token-seguro-2025]: " n8n_api_key
n8n_api_key=${n8n_api_key:-pelotazo-n8n-api-token-seguro-2025}

# Preguntar por la URL de webhook
read -p "Introduce la URL base para webhooks de n8n [http://n8n:5678/webhook]: " n8n_webhook_url
n8n_webhook_url=${n8n_webhook_url:-http://n8n:5678/webhook}

# Actualizar variables en .env
actualizar_variable "N8N_API_URL" "$n8n_api_url"
actualizar_variable "N8N_API_KEY" "$n8n_api_key"
actualizar_variable "N8N_WEBHOOK_URL" "$n8n_webhook_url"

# Mostrar mensaje de finalización
mostrar_exito "Variables de entorno configuradas correctamente"
mostrar_mensaje "Las siguientes variables han sido configuradas:"
echo "N8N_API_URL=$n8n_api_url"
echo "N8N_API_KEY=$n8n_api_key"
echo "N8N_WEBHOOK_URL=$n8n_webhook_url"

# Instrucciones adicionales
echo ""
mostrar_mensaje "Para que FastAPI utilice estas variables, reinicia el servicio:"
echo "docker-compose restart api"

echo ""
mostrar_mensaje "Para verificar la conexión con n8n, accede a:"
echo "http://localhost:8000/api/v1/n8n/status"

exit 0
