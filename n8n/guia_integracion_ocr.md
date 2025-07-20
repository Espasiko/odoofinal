# Guía de Integración de n8n con OCR de Facturas

## Introducción

Esta guía detalla cómo configurar n8n para automatizar el procesamiento OCR de facturas en el proyecto Pelotazo ERP. La integración permite automatizar el flujo completo desde la recepción de la factura hasta su creación en Odoo, utilizando el servicio OCR de Mistral implementado en FastAPI.

## Requisitos previos

- n8n instalado y funcionando (ver README.md)
- FastAPI backend en ejecución
- Odoo 18 configurado
- Acceso a credenciales de autenticación

## Flujo de trabajo básico

El flujo de trabajo "Procesar Factura OCR" automatiza las siguientes tareas:

1. Recibir una factura a través de un webhook
2. Enviar la factura al servicio OCR de FastAPI
3. Validar los datos extraídos
4. Crear la factura en Odoo
5. Notificar el resultado del proceso

## Configuración paso a paso

### 1. Importar el flujo de trabajo

1. Accede a n8n en http://localhost:5678
2. Ve a "Flujos de trabajo"
3. Haz clic en "Importar" y selecciona el archivo `/home/espasiko/mainmanusodoo/manusodoo-roto/n8n/flujos/procesar_factura_ocr.json`

### 2. Configurar credenciales

1. En el nodo "Set Variables", configura:
   - `apiUrl`: URL del endpoint OCR de FastAPI
   - `authToken`: Token de autenticación para FastAPI
   - `odooUid`: ID de usuario de Odoo
   - `odooPassword`: Contraseña de Odoo

### 3. Personalizar el flujo de trabajo

#### Webhook de entrada

El webhook está configurado para recibir facturas en formato multipart/form-data. Los parámetros esperados son:

- `file`: Archivo de factura (PDF, PNG, JPG)
- `token`: Token de autenticación
- `supplier_name` (opcional): Nombre del proveedor
- `supplier_vat` (opcional): NIF/CIF del proveedor

#### Procesamiento OCR

El nodo "Procesar OCR en FastAPI" envía la factura al endpoint `/api/v1/mistral-free-ocr/process-invoice` con los siguientes parámetros:

- `file`: Archivo de factura
- `create_in_odoo`: Booleano para crear automáticamente en Odoo
- `supplier_name`: Nombre del proveedor (si se proporcionó)
- `supplier_vat`: NIF/CIF del proveedor (si se proporcionó)

#### Verificación en Odoo

Si el OCR es exitoso, el flujo verifica que la factura se haya creado correctamente en Odoo consultando la API de Odoo.

## Mejoras y personalizaciones

### Caché OCR

Para mejorar el rendimiento, puedes habilitar el caché OCR modificando el código en `api/routes/mistral_free_ocr.py`. Busca las líneas comentadas relacionadas con el caché y descoméntalas.

### Prompts específicos por proveedor

Para mejorar la precisión del OCR, puedes implementar prompts específicos por proveedor:

1. Crea un nuevo nodo "Switch" después del webhook para identificar el proveedor
2. Para cada proveedor, configura un nodo HTTP Request con un prompt específico
3. Conecta cada salida del Switch al nodo correspondiente

### Validación avanzada

Para mejorar la validación de los datos extraídos:

1. Añade un nodo "Function" después del procesamiento OCR
2. Implementa validaciones específicas para:
   - Validar CIF/NIF español (dígito de control)
   - Validar códigos de producto según patrones conocidos
   - Verificar cálculos de impuestos y totales

## Ejemplos de uso

### Ejemplo 1: Procesamiento de factura desde email

1. Configura un trigger de email en n8n
2. Extrae los adjuntos del email
3. Envía cada adjunto al flujo de procesamiento OCR
4. Notifica al remitente del email sobre el resultado

### Ejemplo 2: Procesamiento por lotes

1. Configura un trigger de carpeta vigilada
2. Procesa todas las facturas nuevas en la carpeta
3. Mueve las facturas procesadas a una carpeta de "completados"
4. Genera un informe de procesamiento

## Solución de problemas

### Error: "No se pudo procesar la factura"

- Verifica que el formato de archivo sea compatible
- Comprueba que el tamaño del archivo no exceda los 50MB
- Revisa los logs de FastAPI para más detalles

### Error: "Proveedor no encontrado"

- Asegúrate de proporcionar información correcta del proveedor
- Verifica que el proveedor exista en Odoo o que se permita su creación automática

### Error: "Fallo en la validación de totales"

- Revisa la calidad de la imagen/PDF
- Verifica que los cálculos en la factura sean correctos
- Ajusta los umbrales de validación en OCRValidator

## Recursos adicionales

- [Documentación de n8n](https://docs.n8n.io/)
- [API de FastAPI para OCR](/api/v1/mistral-free-ocr/docs)
- [Documentación de Odoo 18](https://www.odoo.com/documentation/18.0/)
