# Guía de Uso del Flujo OCR Mejorado en n8n

## Introducción

Esta guía explica cómo utilizar el flujo de trabajo mejorado para el procesamiento OCR de facturas en n8n. Este flujo ha sido optimizado basándose en ejemplos oficiales de n8n para operaciones con documentos y en las mejores prácticas de procesamiento OCR.

## Mejoras Implementadas

El flujo de trabajo mejorado incluye las siguientes características:

1. **Prompts específicos por proveedor**: Detecta automáticamente el proveedor y utiliza un prompt especializado para mejorar la precisión del OCR.
2. **Sistema de caché OCR**: Evita el reprocesamiento de facturas ya analizadas (implementación simulada, lista para conectar con un sistema real).
3. **Validación avanzada**: Incluye validación de CIF/NIF, totales y formato de datos.
4. **Integración con FastAPI y Odoo**: Procesa los datos extraídos y los envía a Odoo para crear facturas.
5. **Manejo de errores mejorado**: Proporciona información detallada sobre posibles problemas.

## Requisitos Previos

- n8n instalado y configurado según las instrucciones en `README.md`
- Acceso a la API de Mistral (para OCR)
- FastAPI y Odoo funcionando correctamente

## Configuración del Flujo

### 1. Importar el Flujo

1. Accede a n8n en http://localhost:5678
2. Ve a Flujos de trabajo > Importar
3. Selecciona el archivo `flujos/procesar_factura_ocr_mejorado.json`
4. Haz clic en "Importar"

### 2. Configurar Credenciales

1. Abre el flujo importado
2. Configura las credenciales para los siguientes nodos:
   - **Procesar con Mistral OCR**: Añade tu clave API de Mistral
   - **Procesar OCR en FastAPI**: Configura la autenticación para tu API

### 3. Personalizar Prompts por Proveedor

El nodo "Preparar Datos" contiene lógica para detectar proveedores y asignar prompts específicos. Puedes personalizar estos prompts según tus necesidades:

```javascript
// Ejemplo de personalización de prompts
if (supplierName.toUpperCase().includes('NEVIR')) {
  proveedorDetectado = 'NEVIR';
  promptEspecifico = 'Extrae de esta factura de NEVIR: número de factura (en formato NVR-XXXXX), fecha, CIF (B84201219), totales con IVA desglosado y recargo de equivalencia, y líneas de productos con códigos que siguen el patrón NVR-XXXXX.';
}
```

### 4. Configurar Sistema de Caché

El flujo incluye una implementación simulada del sistema de caché. Para implementar un sistema real:

1. Modifica el nodo "Preparar Datos" para verificar si la factura está en caché
2. Actualiza el nodo "Obtener de Caché" para recuperar datos reales de tu sistema de caché
3. Añade lógica para guardar resultados en caché después del procesamiento

## Uso del Flujo

### Enviar una Factura para Procesamiento

1. Utiliza una herramienta como Postman o curl para enviar una solicitud POST al webhook:

```bash
curl -X POST http://localhost:5678/webhook/procesar-factura \
  -F "file=@ruta/a/tu/factura.pdf" \
  -F "supplier_name=NEVIR" \
  -F "supplier_vat=B84201219"
```

2. Parámetros disponibles:
   - `file`: Archivo de factura (PDF, JPG, PNG)
   - `supplier_name`: Nombre del proveedor (opcional)
   - `supplier_vat`: CIF/NIF del proveedor (opcional)
   - `create_in_odoo`: "true" para crear la factura en Odoo, "false" para solo procesar (opcional)

### Interpretar la Respuesta

La respuesta incluirá:

1. Datos extraídos de la factura:
   - Número de factura
   - Fecha
   - Proveedor
   - CIF/NIF
   - Base imponible, IVA y total
   - Líneas de productos

2. Estado de validación:
   - Indicación de si los datos son válidos
   - Lista de errores detectados (si los hay)

3. Información adicional:
   - Si los datos se recuperaron de caché
   - Resultado de la creación en Odoo (si se solicitó)

## Flujo de Trabajo Detallado

### 1. Recepción de la Factura

El nodo "Webhook" recibe la factura y la pasa al siguiente nodo.

### 2. Preparación de Datos

El nodo "Preparar Datos" extrae información del archivo y detecta el proveedor para seleccionar el prompt adecuado.

### 3. Verificación de Caché

El nodo "¿Está en Caché?" verifica si la factura ya ha sido procesada anteriormente.

### 4. Procesamiento OCR

Si la factura no está en caché, se procesa con Mistral OCR utilizando el prompt específico para el proveedor.

### 5. Procesamiento de la Respuesta

El nodo "Procesar Respuesta Mistral" extrae datos estructurados del texto OCR.

### 6. Validación de Datos

El nodo "Validar Datos OCR" verifica que los datos extraídos sean válidos y completos.

### 7. Creación en Odoo

Si se solicita, el nodo "Crear Factura en Odoo" envía los datos a FastAPI para crear la factura en Odoo.

### 8. Respuesta al Cliente

El nodo "Respuesta HTTP" devuelve los resultados del procesamiento.

## Personalización Avanzada

### Añadir Nuevos Proveedores

Para añadir soporte para un nuevo proveedor:

1. Modifica el nodo "Preparar Datos" para detectar el nuevo proveedor
2. Añade un prompt específico para ese proveedor
3. Si es necesario, añade lógica de extracción específica en "Procesar Respuesta Mistral"

### Mejorar la Extracción de Datos

Para mejorar la precisión de la extracción:

1. Refina los prompts específicos por proveedor
2. Mejora las expresiones regulares en "Procesar Respuesta Mistral"
3. Añade validaciones adicionales en "Validar Datos OCR"

### Integración con Sistemas Externos

El flujo puede integrarse con sistemas externos adicionales:

1. Añade nodos HTTP Request para conectar con otras APIs
2. Utiliza nodos Function para transformar datos según sea necesario
3. Configura webhooks adicionales para notificaciones

## Solución de Problemas

### Error en el Procesamiento OCR

- Verifica que la clave API de Mistral sea válida
- Comprueba que el formato del archivo sea compatible
- Revisa los logs para ver errores específicos

### Datos Incorrectos o Incompletos

- Refina el prompt específico para el proveedor
- Mejora las expresiones regulares de extracción
- Añade validaciones adicionales

### Error al Crear en Odoo

- Verifica la conexión con FastAPI
- Comprueba las credenciales de autenticación
- Revisa los logs de FastAPI y Odoo para errores específicos

## Próximas Mejoras

1. Implementación completa del sistema de caché OCR
2. Mejora de la detección automática de proveedores
3. Integración con un sistema de aprendizaje continuo para mejorar la precisión
4. Soporte para facturas rectificativas
5. Validación avanzada de productos y precios

---

Documento creado: 19 de julio de 2025  
Última actualización: 19 de julio de 2025
