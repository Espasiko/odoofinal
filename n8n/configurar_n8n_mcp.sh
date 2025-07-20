#!/bin/bash
# Script para configurar n8n-MCP para Windsurf/Cascade
# Autor: Equipo Pelotazo ERP
# Fecha: 19/07/2025

# Colores para terminal
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
ROJO='\033[0;31m'
AZUL='\033[0;34m'
NC='\033[0m' # Sin Color

echo -e "${AZUL}=== Configuración de n8n-MCP para Windsurf/Cascade ===${NC}"
echo -e "${AZUL}Este script configurará n8n-MCP para que puedas usar n8n directamente desde Windsurf/Cascade${NC}"

# Verificar si npm está instalado
if ! command -v npm &> /dev/null; then
    echo -e "${ROJO}Error: npm no está instalado. Por favor, instala Node.js y npm primero.${NC}"
    exit 1
fi

# Instalar n8n-mcp globalmente
echo -e "${AMARILLO}Instalando n8n-mcp globalmente...${NC}"
npm install -g n8n-mcp

# Crear directorio de configuración de Windsurf si no existe
WINDSURF_CONFIG_DIR="$HOME/.codeium/windsurf"
if [ ! -d "$WINDSURF_CONFIG_DIR" ]; then
    echo -e "${AMARILLO}Creando directorio de configuración de Windsurf...${NC}"
    mkdir -p "$WINDSURF_CONFIG_DIR"
fi

# Obtener variables de entorno
source .env
N8N_API_URL=${N8N_API_URL:-"http://n8n:5678/api/v1"}
N8N_API_KEY=${N8N_API_KEY:-"pelotazo-n8n-api-token-seguro-2025"}

# Crear o actualizar archivo de configuración MCP
MCP_CONFIG_FILE="$WINDSURF_CONFIG_DIR/mcp_config.json"
echo -e "${AMARILLO}Creando archivo de configuración MCP en $MCP_CONFIG_FILE...${NC}"

# Verificar si el archivo existe y hacer backup
if [ -f "$MCP_CONFIG_FILE" ]; then
    echo -e "${AMARILLO}Se encontró una configuración existente. Haciendo backup...${NC}"
    cp "$MCP_CONFIG_FILE" "$MCP_CONFIG_FILE.bak"
    
    # Verificar si ya existe la configuración de n8n-mcp
    if grep -q "n8n-mcp" "$MCP_CONFIG_FILE"; then
        echo -e "${AMARILLO}La configuración de n8n-mcp ya existe. Actualizando...${NC}"
        # Aquí podríamos usar jq para actualizar el archivo JSON, pero para simplificar
        # vamos a crear un nuevo archivo de configuración
    fi
fi

# Crear archivo de configuración MCP
cat > "$MCP_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "N8N_API_URL": "$N8N_API_URL",
        "N8N_API_KEY": "$N8N_API_KEY"
      }
    }
  }
}
EOF

echo -e "${VERDE}Configuración de n8n-MCP creada correctamente en $MCP_CONFIG_FILE${NC}"

# Crear archivo .windsurfrules
WINDSURF_RULES_FILE="$(pwd)/.windsurfrules"
echo -e "${AMARILLO}Creando archivo de reglas de Windsurf en $WINDSURF_RULES_FILE...${NC}"

cat > "$WINDSURF_RULES_FILE" << EOF
# Reglas de proyecto para n8n-MCP

## Contexto del proyecto
Este proyecto utiliza n8n para automatizar flujos de trabajo de procesamiento OCR de facturas y validación con LLM.
La integración con FastAPI permite controlar n8n programáticamente.

## Instrucciones para n8n-MCP
Cuando trabajes con n8n, utiliza las herramientas MCP para:
1. Crear nuevos flujos de trabajo
2. Modificar flujos existentes
3. Ejecutar flujos de trabajo
4. Obtener información sobre los nodos disponibles
5. Gestionar credenciales y variables

## Flujos de trabajo principales
- OCR Mejorado: Procesa facturas con OCR utilizando prompts específicos por proveedor
- LLM-MCP: Analiza facturas con LLM y utiliza herramientas MCP para validaciones avanzadas
- Servidor MCP: Expone herramientas especializadas para procesamiento de facturas

## Estructura del proyecto
- /n8n: Configuración y flujos de trabajo de n8n
- /api/routes/n8n_integration.py: Integración de FastAPI con n8n
- /api/utils/n8n_config.py: Configuración centralizada para n8n

## Variables de entorno
- N8N_API_URL: URL de la API de n8n
- N8N_API_KEY: Token de autenticación para la API de n8n
- N8N_WEBHOOK_URL: URL de webhooks de n8n
EOF

echo -e "${VERDE}Archivo de reglas de Windsurf creado correctamente en $WINDSURF_RULES_FILE${NC}"

# Instrucciones finales
echo -e "${AZUL}=== Configuración completada ===${NC}"
echo -e "${VERDE}n8n-MCP ha sido configurado correctamente para su uso con Windsurf/Cascade.${NC}"
echo -e "${AMARILLO}Para usar n8n-MCP en Windsurf/Cascade:${NC}"
echo -e "1. Reinicia Windsurf/Cascade"
echo -e "2. Cuando uses Cascade, menciona que quieres usar n8n-MCP para trabajar con flujos de trabajo"
echo -e "3. Cascade podrá crear, modificar y ejecutar flujos de trabajo directamente"
echo -e "${AZUL}¡Disfruta de la integración!${NC}"
