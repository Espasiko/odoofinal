# Integración de Mistral OCR

## Descripción

Este documento describe la integración de Mistral OCR en el sistema ManusOdoo para el procesamiento avanzado de documentos con inteligencia artificial.

## Características

### Mistral OCR
- **OCR Avanzado**: Utiliza IA para reconocimiento de texto superior
- **Múltiples Formatos**: Soporta PDF, PNG, JPG, JPEG, AVIF, PPTX, DOCX
- **Comprensión de Documentos**: Entiende layouts complejos y contenido multiidioma
- **Salida Estructurada**: Genera datos en formato JSON estructurado
- **Límite de Archivo**: Hasta 50MB por documento

### Funcionalidades Implementadas

1. **Procesamiento General de Documentos**
   - Extracción de texto completo
   - Detección y extracción de imágenes
   - Análisis de layout y estructura

2. **Procesamiento Específico de Facturas**
   - Extracción automática de datos de factura
   - Identificación de proveedores
   - Creación automática en Odoo (opcional)
   - Análisis de líneas de productos/servicios

3. **Procesamiento desde URL**
   - Procesamiento directo desde enlaces web
   - Sin necesidad de descarga manual

## Endpoints API

### 1. Procesar Documento General

```http
POST /api/v1/mistral-ocr/process-document
Content-Type: multipart/form-data
Authorization: Bearer {token}
```

**Parámetros:**
- `file`: Archivo a procesar (requerido)
- `include_images`: Incluir imágenes extraídas en base64 (opcional, default: true)

**Respuesta:**
```json
{
  "success": true,
  "message": "Documento procesado exitosamente",
  "filename": "documento.pdf",
  "file_type": ".pdf",
  "processed_by": "usuario@email.com",
  "data": {
    "success": true,
    "full_text": "Texto completo extraído...",
    "pages_content": ["Página 1...", "Página 2..."],
    "extracted_images": [],
    "page_count": 2,
    "image_count": 0
  }
}
```

### 2. Procesar Factura

```http
POST /api/v1/mistral-ocr/process-invoice
Content-Type: multipart/form-data
Authorization: Bearer {token}
```

**Parámetros:**
- `file`: Archivo de factura (requerido)
- `create_in_odoo`: Crear factura automáticamente en Odoo (opcional, default: false)

**Respuesta:**
```json
{
  "success": true,
  "message": "Factura procesada exitosamente",
  "filename": "factura.pdf",
  "file_type": ".pdf",
  "processed_by": "usuario@email.com",
  "invoice_data": {
    "extracted_data": {
      "invoice_number": "FAC-2024-001",
      "invoice_date": "15/01/2024",
      "due_date": "15/02/2024",
      "supplier_name": "Proveedor S.L.",
      "supplier_vat": "B12345678",
      "customer_name": "Cliente S.A.",
      "customer_vat": "A87654321",
      "total_amount": 1210.00,
      "tax_amount": 210.00,
      "subtotal": 1000.00,
      "currency": "EUR",
      "payment_terms": "30 días",
      "line_items": [
        {
          "description": "Producto A",
          "quantity": 2,
          "unit_price": 500.00,
          "total_price": 1000.00
        }
      ]
    },
    "confidence": "high"
  },
  "ocr_confidence": "high",
  "odoo_invoice": {
    "created": true,
    "supplier_id": 123,
    "message": "Factura creada exitosamente en Odoo"
  }
}
```

### 3. Procesar desde URL

```http
POST /api/v1/mistral-ocr/process-from-url
Content-Type: application/json
Authorization: Bearer {token}
```

**Cuerpo:**
```json
{
  "document_url": "https://ejemplo.com/documento.pdf",
  "include_images": true
}
```

### 4. Formatos Soportados

```http
GET /api/v1/mistral-ocr/supported-formats
```

**Respuesta:**
```json
{
  "success": true,
  "supported_formats": [".pdf", ".png", ".jpg", ".jpeg", ".avif", ".pptx", ".docx"],
  "max_file_size": "50MB",
  "description": "Formatos de archivo soportados por Mistral OCR"
}
```

## Configuración

### Variables de Entorno

Añadir al archivo `.env`:

```env
# Mistral OCR Configuration
MISTRAL_API_KEY=tu_api_key_de_mistral
```

### Instalación de Dependencias

```bash
# Instalar dependencias de Python
pip install -r requirements.txt

# Para sistemas Linux, instalar Tesseract (si no está instalado)
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev

# Para procesamiento de PDF
sudo apt-get install poppler-utils
```

## Arquitectura

### Servicios

1. **MistralOCRService** (`api/services/mistral_ocr_service.py`)
   - Maneja la comunicación con la API de Mistral OCR
   - Procesa documentos PDF e imágenes
   - Extrae datos estructurados de facturas
   - Valida formatos y tamaños de archivo

2. **Rutas OCR** (`api/routes/mistral_ocr.py`)
   - Endpoints REST para procesamiento de documentos
   - Integración con autenticación JWT
   - Manejo de archivos temporales
   - Integración con servicios de Odoo

### Flujo de Procesamiento

1. **Subida de Archivo**
   - Validación de formato y tamaño
   - Creación de archivo temporal
   - Autenticación de usuario

2. **Procesamiento OCR**
   - Codificación a base64
   - Envío a Mistral OCR API
   - Recepción de datos estructurados

3. **Extracción de Datos**
   - Parsing de respuesta OCR
   - Extracción de información específica
   - Estructuración en formato JSON

4. **Integración con Odoo** (opcional)
   - Búsqueda/creación de proveedores
   - Creación de facturas
   - Asociación de líneas de productos

5. **Limpieza**
   - Eliminación de archivos temporales
   - Logging de operaciones

## Ventajas sobre OCR Tradicional

### Mistral OCR vs Tesseract

| Característica | Mistral OCR | Tesseract |
|---|---|---|
| **Precisión** | Alta (IA avanzada) | Media-Alta |
| **Comprensión de Layout** | Excelente | Básica |
| **Múltiples Idiomas** | Nativo | Requiere configuración |
| **Documentos Complejos** | Excelente | Limitado |
| **Salida Estructurada** | JSON nativo | Requiere post-procesamiento |
| **Configuración** | Mínima | Extensa |
| **Costo** | API de pago | Gratuito |
| **Velocidad** | Rápida (cloud) | Variable (local) |

## Casos de Uso

### 1. Procesamiento de Facturas de Proveedores
- Digitalización automática de facturas en papel
- Extracción de datos para contabilidad
- Creación automática en sistema ERP

### 2. Análisis de Documentos Comerciales
- Contratos y acuerdos
- Órdenes de compra
- Albaranes de entrega

### 3. Digitalización de Archivo
- Conversión de documentos físicos
- Indexación automática
- Búsqueda por contenido

## Seguridad

### Medidas Implementadas

1. **Autenticación JWT**: Todos los endpoints requieren token válido
2. **Validación de Archivos**: Verificación de formato y tamaño
3. **Archivos Temporales**: Eliminación automática después del procesamiento
4. **Logging**: Registro de todas las operaciones
5. **Variables de Entorno**: API keys protegidas

### Recomendaciones

1. **Rotar API Keys**: Cambiar periódicamente las claves de Mistral
2. **Monitoreo**: Supervisar uso y costos de la API
3. **Backup**: Respaldar documentos importantes antes del procesamiento
4. **Límites**: Implementar rate limiting en producción

## Monitoreo y Logs

### Eventos Registrados

- Inicio y fin de procesamiento de documentos
- Errores de API y validación
- Creación de facturas en Odoo
- Uso de recursos y rendimiento

### Métricas Recomendadas

- Documentos procesados por día/mes
- Tiempo promedio de procesamiento
- Tasa de éxito/error
- Costo de API por documento
- Precisión de extracción de datos

## Troubleshooting

### Errores Comunes

1. **"MISTRAL_API_KEY no está configurada"**
   - Verificar variable de entorno
   - Reiniciar aplicación después de configurar

2. **"Formato de archivo no soportado"**
   - Verificar extensión del archivo
   - Consultar endpoint `/supported-formats`

3. **"El archivo excede el límite de 50MB"**
   - Comprimir o dividir el archivo
   - Usar formato más eficiente (PDF vs imágenes)

4. **"Error interno procesando el documento"**
   - Verificar conectividad a internet
   - Comprobar validez de API key
   - Revisar logs para detalles específicos

### Debugging

```python
# Habilitar logging detallado
import logging
logging.basicConfig(level=logging.DEBUG)

# Verificar configuración
from api.utils.config import config
print(f"Mistral API Key configurada: {bool(config.MISTRAL_API_KEY)}")
```

## Roadmap

### Próximas Funcionalidades

1. **Procesamiento por Lotes**: Múltiples documentos simultáneamente
2. **Templates Personalizados**: Configuración específica por tipo de documento
3. **Validación Cruzada**: Verificación con múltiples fuentes
4. **Dashboard de Métricas**: Interfaz para monitoreo
5. **Integración con IA**: Análisis semántico avanzado
6. **Workflow Automático**: Procesamiento basado en reglas

### Mejoras Planificadas

1. **Cache de Resultados**: Evitar reprocesamiento
2. **Optimización de Costos**: Estrategias de uso eficiente
3. **Fallback a Tesseract**: Respaldo en caso de fallo de API
4. **Validación Humana**: Interfaz para revisión manual
5. **Exportación de Datos**: Múltiples formatos de salida

## Conclusión

La integración de Mistral OCR proporciona capacidades avanzadas de procesamiento de documentos que superan significativamente las soluciones tradicionales. La combinación de alta precisión, comprensión de layout y salida estructurada hace que sea ideal para automatizar procesos de digitalización en entornos empresariales.

La arquitectura modular permite fácil extensión y mantenimiento, mientras que la integración con Odoo facilita la automatización completa del flujo de trabajo desde la recepción del documento hasta su registro en el sistema ERP.