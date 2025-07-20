#!/bin/bash

# Script para actualizar y reiniciar n8n con la nueva configuración
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
if [ ! -f "docker-compose.yml" ]; then
  mostrar_error "Este script debe ejecutarse desde el directorio n8n que contiene docker-compose.yml"
  exit 1
fi

# Verificar que Docker está en ejecución
if ! docker info > /dev/null 2>&1; then
  mostrar_error "Docker no está en ejecución. Por favor, inicia Docker y vuelve a intentarlo."
  exit 1
fi

# Mostrar mensaje de inicio
mostrar_mensaje "Iniciando actualización de n8n..."

# Detener n8n si está en ejecución
if docker ps | grep -q n8n_n8n; then
  mostrar_mensaje "Deteniendo n8n..."
  docker-compose down
  if [ $? -ne 0 ]; then
    mostrar_error "Error al detener n8n. Abortando."
    exit 1
  fi
  mostrar_exito "n8n detenido correctamente"
else
  mostrar_advertencia "n8n no está en ejecución actualmente"
fi

# Solicitar las claves API si no están configuradas
if grep -q "MISTRAL_API_KEY=" docker-compose.yml && grep -q "OPENAI_API_KEY=" docker-compose.yml; then
  mostrar_advertencia "Las claves API de Mistral y OpenAI no están configuradas en docker-compose.yml"
  
  read -p "¿Deseas configurar las claves API ahora? (s/n): " configurar_claves
  if [[ $configurar_claves == "s" || $configurar_claves == "S" ]]; then
    read -p "Introduce la clave API de Mistral (deja en blanco para omitir): " mistral_key
    read -p "Introduce la clave API de OpenAI (deja en blanco para omitir): " openai_key
    
    if [ ! -z "$mistral_key" ]; then
      sed -i "s/MISTRAL_API_KEY=/MISTRAL_API_KEY=$mistral_key/" docker-compose.yml
      mostrar_exito "Clave API de Mistral configurada"
    fi
    
    if [ ! -z "$openai_key" ]; then
      sed -i "s/OPENAI_API_KEY=/OPENAI_API_KEY=$openai_key/" docker-compose.yml
      mostrar_exito "Clave API de OpenAI configurada"
    fi
  else
    mostrar_advertencia "Las claves API no han sido configuradas. Algunas funcionalidades pueden no estar disponibles."
  fi
fi

# Crear directorios para los flujos si no existen
if [ ! -d "flujos" ]; then
  mostrar_mensaje "Creando directorio para flujos..."
  mkdir -p flujos
  mostrar_exito "Directorio de flujos creado"
fi

# Iniciar n8n con la nueva configuración
mostrar_mensaje "Iniciando n8n con la nueva configuración..."
docker-compose up -d

# Verificar si n8n se inició correctamente
if [ $? -eq 0 ]; then
  mostrar_exito "n8n iniciado correctamente"
  mostrar_mensaje "n8n está disponible en: http://localhost:5678"
  mostrar_mensaje "Servidor MCP disponible en: http://localhost:3000/v1/mcp"
  
  # Mostrar instrucciones adicionales
  echo ""
  mostrar_mensaje "Instrucciones para importar los flujos de trabajo:"
  echo "1. Accede a n8n en http://localhost:5678"
  echo "2. Ve a Flujos de trabajo > Importar"
  echo "3. Selecciona los archivos JSON de la carpeta 'flujos'"
  echo ""
  mostrar_mensaje "Flujos de trabajo disponibles:"
  echo "- procesar_factura_ocr_mejorado.json: Flujo mejorado para procesamiento OCR de facturas"
  echo "- llm_mcp_client_factura.json: Flujo para procesamiento inteligente con LLM y MCP"
  echo "- servidor_mcp_herramientas.json: Servidor MCP con herramientas para procesamiento de facturas"
  echo ""
  mostrar_advertencia "Recuerda configurar las credenciales necesarias en cada flujo de trabajo"
else
  mostrar_error "Error al iniciar n8n. Revisa los logs con: docker-compose logs"
fi

# Mostrar cómo ver los logs
echo ""
mostrar_mensaje "Para ver los logs de n8n, ejecuta:"
echo "docker-compose logs -f"

# Mostrar cómo detener n8n
echo ""
mostrar_mensaje "Para detener n8n, ejecuta:"
echo "./stop_n8n.sh"

exit 0
