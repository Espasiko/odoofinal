#!/bin/bash
# Script de prueba para Mistral OCR API
# Uso: ./test_mistral_ocr.sh [archivo_opcional]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
BASE_URL="http://localhost:8000"
USERNAME="admin"
PASSWORD="admin_password_secure"

echo -e "${BLUE}🚀 Iniciando pruebas de Mistral OCR API${NC}"
echo "================================================"

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [archivo_opcional]"
    echo ""
    echo "Opciones:"
    echo "  archivo_opcional    Ruta al archivo a procesar (PDF, PNG, JPG, JPEG, AVIF)"
    echo "  -h, --help         Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0                           # Usar archivo de prueba por defecto"
    echo "  $0 mi_documento.pdf          # Procesar archivo específico"
    echo "  $0 /ruta/completa/imagen.png # Procesar imagen"
}

# Verificar argumentos
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Verificar que el servidor esté ejecutándose
echo -e "${YELLOW}🔍 Verificando que el servidor esté ejecutándose...${NC}"
if ! curl -s "$BASE_URL/docs" > /dev/null; then
    echo -e "${RED}❌ Error: El servidor FastAPI no está ejecutándose en $BASE_URL${NC}"
    echo -e "${YELLOW}💡 Ejecuta: python main_new.py${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Servidor FastAPI está ejecutándose${NC}"

# Paso 1: Obtener token de autenticación
echo -e "\n${YELLOW}🔐 Obteniendo token de autenticación...${NC}"
TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

if [[ $? -ne 0 ]]; then
    echo -e "${RED}❌ Error: No se pudo conectar al endpoint de autenticación${NC}"
    exit 1
fi

# Extraer el access_token
ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [[ -z "$ACCESS_TOKEN" ]]; then
    echo -e "${RED}❌ Error: No se pudo obtener el token de acceso${NC}"
    echo -e "${YELLOW}Respuesta del servidor:${NC}"
    echo "$TOKEN_RESPONSE" | jq . 2>/dev/null || echo "$TOKEN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Token obtenido exitosamente${NC}"
echo -e "${BLUE}Token: ${ACCESS_TOKEN:0:20}...${NC}"

# Paso 2: Preparar archivo de prueba
TEST_FILE="$1"

if [[ -z "$TEST_FILE" ]]; then
    # Crear archivo de prueba por defecto
    TEST_FILE="test_document.txt"
    echo -e "\n${YELLOW}📄 Creando archivo de prueba por defecto...${NC}"
    cat > "$TEST_FILE" << EOF
DOCUMENTO DE PRUEBA PARA OCR
===============================

Este es un documento de prueba para verificar
que el sistema de OCR de Mistral funciona correctamente.

Información de prueba:
- Fecha: $(date)
- Usuario: $USER
- Sistema: $(uname -s)

Texto con números: 12345
Texto con símbolos: @#$%&*

¡Prueba completada!
EOF
    echo -e "${GREEN}✅ Archivo de prueba creado: $TEST_FILE${NC}"
else
    if [[ ! -f "$TEST_FILE" ]]; then
        echo -e "${RED}❌ Error: El archivo '$TEST_FILE' no existe${NC}"
        exit 1
    fi
    echo -e "${BLUE}📄 Usando archivo: $TEST_FILE${NC}"
fi

# Mostrar información del archivo
FILE_SIZE=$(du -h "$TEST_FILE" | cut -f1)
FILE_TYPE=$(file -b "$TEST_FILE")
echo -e "${BLUE}📊 Tamaño: $FILE_SIZE${NC}"
echo -e "${BLUE}📋 Tipo: $FILE_TYPE${NC}"

# Paso 3: Probar endpoint de Mistral OCR
echo -e "\n${YELLOW}🔍 Probando endpoint de Mistral OCR...${NC}"
echo "Endpoint: $BASE_URL/api/v1/mistral-ocr/process-document"

# Crear archivo temporal para la respuesta
RESPONSE_FILE=$(mktemp)

# Realizar la petición
HTTP_STATUS=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/api/v1/mistral-ocr/process-document" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@$TEST_FILE" \
  -F "include_images=true" \
  -o "$RESPONSE_FILE")

# Verificar el resultado
if [[ "$HTTP_STATUS" == "200" ]]; then
    echo -e "${GREEN}✅ Petición exitosa (HTTP $HTTP_STATUS)${NC}"
    
    # Mostrar respuesta formateada
    echo -e "\n${BLUE}📋 Respuesta del servidor:${NC}"
    echo "=========================================="
    
    # Intentar formatear como JSON
    if jq . "$RESPONSE_FILE" 2>/dev/null; then
        echo "=========================================="
        
        # Extraer y mostrar el texto si está disponible
        TEXT_CONTENT=$(jq -r '.data.text // .text // "No se encontró texto"' "$RESPONSE_FILE" 2>/dev/null)
        if [[ "$TEXT_CONTENT" != "null" && "$TEXT_CONTENT" != "No se encontró texto" ]]; then
            echo -e "\n${GREEN}📝 Texto extraído:${NC}"
            echo "------------------"
            echo "$TEXT_CONTENT"
            echo "------------------"
        fi
    else
        # Si no es JSON válido, mostrar contenido raw
        cat "$RESPONSE_FILE"
        echo
    fi
    
elif [[ "$HTTP_STATUS" == "401" ]]; then
    echo -e "${RED}❌ Error de autenticación (HTTP $HTTP_STATUS)${NC}"
    echo -e "${YELLOW}💡 Verifica las credenciales de usuario${NC}"
    
elif [[ "$HTTP_STATUS" == "404" ]]; then
    echo -e "${RED}❌ Endpoint no encontrado (HTTP $HTTP_STATUS)${NC}"
    echo -e "${YELLOW}💡 Verifica que el servidor tenga las rutas de Mistral OCR configuradas${NC}"
    
elif [[ "$HTTP_STATUS" == "400" ]]; then
    echo -e "${RED}❌ Error en la petición (HTTP $HTTP_STATUS)${NC}"
    echo -e "${YELLOW}Respuesta del servidor:${NC}"
    cat "$RESPONSE_FILE"
    echo
    
elif [[ "$HTTP_STATUS" == "500" ]]; then
    echo -e "${RED}❌ Error interno del servidor (HTTP $HTTP_STATUS)${NC}"
    echo -e "${YELLOW}💡 Verifica que la API key de Mistral esté configurada correctamente${NC}"
    echo -e "${YELLOW}Respuesta del servidor:${NC}"
    cat "$RESPONSE_FILE"
    echo
    
else
    echo -e "${RED}❌ Error inesperado (HTTP $HTTP_STATUS)${NC}"
    echo -e "${YELLOW}Respuesta del servidor:${NC}"
    cat "$RESPONSE_FILE"
    echo
fi

# Limpiar archivos temporales
rm -f "$RESPONSE_FILE"
if [[ "$TEST_FILE" == "test_document.txt" ]]; then
    rm -f "$TEST_FILE"
    echo -e "${BLUE}🧹 Archivo de prueba temporal eliminado${NC}"
fi

echo -e "\n${BLUE}🏁 Prueba completada${NC}"
echo "================================================"

# Mostrar información adicional
echo -e "\n${YELLOW}📚 Información adicional:${NC}"
echo "• Documentación interactiva: $BASE_URL/docs"
echo "• Documentación alternativa: $BASE_URL/redoc"
echo "• Guía completa: ./GUIA_MISTRAL_OCR.md"
echo ""
echo -e "${GREEN}¡Gracias por usar Mistral OCR! 🎉${NC}"