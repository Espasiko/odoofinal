# Guía Completa para Probar Mistral OCR API

## 📋 Configuración Inicial

### 1. Configurar la API Key de Mistral

Ya tienes la API key configurada en `.env.example`. Para usarla:

```bash
# Copia el archivo de ejemplo
cp .env.example .env

# Edita el archivo .env y asegúrate de que la clave esté correcta
echo "MISTRAL_API_KEY=V27eNNH4b7Er1k9WPxYHRaEf9gLsKqmH" >> .env
```

### 2. Verificar que el servidor FastAPI esté ejecutándose

```bash
# Ejecutar el servidor FastAPI
python main_new.py
```

El servidor debería estar disponible en: `http://localhost:8000`

## 🌐 Métodos para Probar la API

### Método 1: Usando la Documentación Interactiva de FastAPI

1. **Accede a la documentación automática:**
   - Abre tu navegador en: `http://localhost:8000/docs`
   - Verás la interfaz Swagger UI con todos los endpoints disponibles

2. **Autenticarse:**
   - Busca el endpoint `/token` en la sección "Authentication"
   - Haz clic en "Try it out"
   - Introduce las credenciales:
     ```
     username: admin
     password: admin_password_secure
     ```
   - Ejecuta la petición y copia el `access_token`

3. **Autorizar en Swagger:**
   - Haz clic en el botón "Authorize" (🔒) en la parte superior
   - Introduce: `Bearer TU_ACCESS_TOKEN_AQUI`
   - Haz clic en "Authorize"

4. **Probar Mistral OCR:**
   - Busca el endpoint `/api/v1/mistral-ocr/process-document`
   - Haz clic en "Try it out"
   - Sube un archivo (PDF, PNG, JPG, JPEG, AVIF)
   - Configura `include_images` según necesites
   - Ejecuta la petición

### Método 2: Usando cURL desde Terminal

#### Paso 1: Obtener Token de Autenticación

```bash
# Obtener token
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin_password_secure"
```

#### Paso 2: Probar el Endpoint de Mistral OCR

```bash
# Reemplaza YOUR_ACCESS_TOKEN con el token obtenido
curl -X POST "http://localhost:8000/api/v1/mistral-ocr/process-document" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/ruta/a/tu/archivo.pdf" \
  -F "include_images=true"
```

### Método 3: Usando la Interfaz Web Existente

**Nota:** La interfaz web actual (`templates/index.html`) está diseñada para mapeo de datos de proveedores, no específicamente para OCR. Sin embargo, puedes:

1. **Acceder a la interfaz:**
   - Abre: `http://localhost:8000` (si tienes configurado el servidor para servir templates)
   - O abre directamente: `file:///ruta/completa/a/templates/index.html`

2. **Modificar para OCR:** Necesitarías adaptar la interfaz para que apunte al endpoint de Mistral OCR.

## 🔧 Script de Prueba Automatizado

Crea un script para probar fácilmente:

```bash
#!/bin/bash
# test_mistral_ocr.sh

echo "🔐 Obteniendo token de autenticación..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin_password_secure")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Error: No se pudo obtener el token de acceso"
    echo "Respuesta: $TOKEN_RESPONSE"
    exit 1
fi

echo "✅ Token obtenido exitosamente"
echo "🔍 Probando endpoint de Mistral OCR..."

# Crear un archivo de prueba si no existe
if [ ! -f "test_document.txt" ]; then
    echo "Este es un documento de prueba para OCR." > test_document.txt
fi

# Probar el endpoint
curl -X POST "http://localhost:8000/api/v1/mistral-ocr/process-document" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@test_document.txt" \
  -F "include_images=true" \
  -v

echo "\n✅ Prueba completada"
```

## 📁 Formatos de Archivo Soportados

Según el código, Mistral OCR soporta:
- **PDF** (.pdf)
- **Imágenes:** PNG (.png), JPG (.jpg), JPEG (.jpeg), AVIF (.avif)
- **Límite de tamaño:** 50MB

## 🔍 Endpoints Disponibles

### Autenticación
- `POST /token` - Obtener token de acceso

### Mistral OCR
- `POST /api/v1/mistral-ocr/process-document` - Procesar documento con OCR

### Otros Endpoints Útiles
- `GET /api/v1/providers/all` - Listar proveedores
- `GET /api/v1/products/all` - Listar productos
- `GET /docs` - Documentación interactiva
- `GET /redoc` - Documentación alternativa

## 🐛 Solución de Problemas

### Error 401 - No autorizado
- Verifica que el token esté correctamente incluido en el header
- Asegúrate de usar `Bearer TOKEN` en el header Authorization

### Error 404 - Endpoint no encontrado
- Verifica que el servidor esté ejecutándose
- Confirma que la URL sea correcta: `/api/v1/mistral-ocr/process-document`

### Error 400 - Formato no soportado
- Verifica que el archivo sea PDF, PNG, JPG, JPEG o AVIF
- Confirma que el archivo no exceda 50MB

### Error 500 - Error del servidor
- Verifica que la API key de Mistral esté configurada correctamente
- Revisa los logs del servidor para más detalles

## 📝 Ejemplo de Respuesta Exitosa

```json
{
  "status": "success",
  "data": {
    "text": "Texto extraído del documento...",
    "images": ["base64_image_data..."],
    "metadata": {
      "pages": 1,
      "format": "pdf",
      "size": "1.2MB"
    }
  }
}
```

## 🚀 Próximos Pasos

1. **Crear una interfaz web específica para OCR** que permita:
   - Subir archivos fácilmente
   - Visualizar resultados del OCR
   - Descargar texto extraído

2. **Integrar con el sistema de proveedores** para:
   - Procesar facturas automáticamente
   - Extraer datos de productos
   - Mapear información a Odoo

3. **Añadir funcionalidades avanzadas:**
   - Procesamiento por lotes
   - Historial de documentos procesados
   - Validación y corrección de datos extraídos

---

**¡La API de Mistral OCR está lista para usar! 🎉**

Puedes empezar probando con la documentación interactiva en `http://localhost:8000/docs` o usando los scripts de ejemplo proporcionados.