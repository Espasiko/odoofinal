# Ejemplo de Creación de Flujo OCR para Facturas NEVIR con n8n-MCP

## Introducción

Este documento muestra un ejemplo paso a paso de cómo utilizar n8n-MCP con Cascade para crear un flujo de trabajo especializado en el procesamiento OCR de facturas del proveedor NEVIR para Odoo 18. El ejemplo incluye la validación específica de códigos de producto NEVIR (formato NVR-XXXXX) y la implementación del sistema de caché OCR.

## Conversación con Cascade

A continuación se muestra un ejemplo de cómo interactuar con Cascade para crear el flujo de trabajo:

### Usuario:
"Necesito crear un flujo de trabajo en n8n para procesar facturas de NEVIR con OCR. El flujo debe validar que los códigos de producto sigan el formato NVR-XXXXX, implementar el sistema de caché OCR y crear la factura en Odoo 18."

### Cascade:
"Voy a ayudarte a crear un flujo de trabajo especializado para procesar facturas NEVIR con OCR, validación de códigos de producto y sistema de caché. Utilizaré n8n-MCP para esto."

*Cascade utilizará las herramientas MCP para crear el flujo de trabajo*

## Estructura del Flujo de Trabajo

El flujo de trabajo tendrá los siguientes componentes:

1. **Nodo de Entrada HTTP**: Para recibir la factura
2. **Sistema de Caché OCR**: Para evitar reprocesamiento
3. **Procesamiento OCR**: Para extraer texto de la factura
4. **Prompt Específico NEVIR**: Para mejorar la extracción de datos
5. **Validación de Códigos de Producto**: Para verificar el formato NVR-XXXXX
6. **Validación de CIF/NIF**: Para verificar el CIF del proveedor
7. **Integración con Odoo 18**: Para crear la factura

## Implementación Detallada

### 1. Nodo de Entrada HTTP

```json
{
  "name": "Webhook",
  "type": "n8n-nodes-base.webhook",
  "position": [
    250,
    300
  ],
  "parameters": {
    "path": "procesar-factura-nevir",
    "responseMode": "lastNode",
    "options": {}
  }
}
```

### 2. Sistema de Caché OCR

```json
{
  "name": "Function (Verificar Caché)",
  "type": "n8n-nodes-base.function",
  "position": [
    450,
    300
  ],
  "parameters": {
    "functionCode": "// Código para verificar si la factura ya está en caché\nconst md5 = require('md5');\nconst fs = require('fs');\nconst path = require('path');\n\n// Obtener datos de la petición\nconst fileData = $input.item.json.fileData;\nconst fileName = $input.item.json.fileName;\n\n// Calcular hash del archivo\nconst fileHash = md5(fileData);\n\n// Directorio de caché\nconst cacheDir = '/tmp/ocr_cache';\n\n// Crear directorio si no existe\nif (!fs.existsSync(cacheDir)) {\n  fs.mkdirSync(cacheDir, { recursive: true });\n}\n\n// Ruta del archivo de caché\nconst cachePath = path.join(cacheDir, `${fileHash}.json`);\n\n// Verificar si existe en caché\nif (fs.existsSync(cachePath)) {\n  // Leer datos de caché\n  const cacheData = JSON.parse(fs.readFileSync(cachePath, 'utf8'));\n  \n  // Devolver datos de caché\n  return {\n    json: {\n      fromCache: true,\n      cacheData,\n      fileHash\n    }\n  };\n} else {\n  // No está en caché\n  return {\n    json: {\n      fromCache: false,\n      fileHash,\n      cachePath,\n      fileData,\n      fileName\n    }\n  };\n}"
  }
}
```

### 3. Procesamiento OCR (si no está en caché)

```json
{
  "name": "IF (En Caché)",
  "type": "n8n-nodes-base.if",
  "position": [
    650,
    300
  ],
  "parameters": {
    "conditions": {
      "string": [
        {
          "value1": "={{$json[\"fromCache\"]}}",
          "operation": "equal",
          "value2": true
        }
      ]
    }
  }
}
```

```json
{
  "name": "HTTP Request (OCR)",
  "type": "n8n-nodes-base.httpRequest",
  "position": [
    850,
    400
  ],
  "parameters": {
    "url": "={{$env.OCR_API_URL}}",
    "method": "POST",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
    "httpHeaderAuth": {
      "name": "Authorization",
      "value": "Bearer {{$env.OCR_API_KEY}}"
    },
    "sendBody": true,
    "contentType": "multipart-form-data",
    "bodyParameters": {
      "parameters": [
        {
          "name": "file",
          "value": "={{$node[\"Function (Verificar Caché)\"].json[\"fileData\"]}}"
        },
        {
          "name": "provider",
          "value": "NEVIR"
        }
      ]
    }
  }
}
```

### 4. Prompt Específico NEVIR

```json
{
  "name": "Function (Prompt NEVIR)",
  "type": "n8n-nodes-base.function",
  "position": [
    1050,
    400
  ],
  "parameters": {
    "functionCode": "// Aplicar prompt específico para NEVIR\nconst ocrText = $input.item.json.text || '';\n\n// Prompt específico para NEVIR\nconst prompt = `\nAnaliza la siguiente factura de NEVIR y extrae la información en formato JSON:\n\n${ocrText}\n\nExtrae los siguientes campos:\n- Número de factura\n- Fecha de factura (formato DD/MM/YYYY)\n- CIF del proveedor (debe ser B84201219 para NEVIR)\n- Nombre del proveedor (NEVIR)\n- Dirección del proveedor\n- Líneas de factura con:\n  - Código de producto (debe seguir el formato NVR-XXXXX)\n  - Descripción\n  - Cantidad\n  - Precio unitario\n  - Descuento (si aplica)\n  - IVA\n  - Total\n- Base imponible\n- Cuota de IVA (desglosada por tipos)\n- Recargo de equivalencia (si aplica)\n- Total factura\n\nAsegúrate de validar que los códigos de producto sigan el formato NVR-XXXXX.\n`;\n\n// Llamar a LLM con el prompt\nreturn {\n  json: {\n    prompt,\n    ocrText,\n    provider: 'NEVIR'\n  }\n};"
  }
}
```

### 5. Validación de Códigos de Producto

```json
{
  "name": "Function (Validar Códigos)",
  "type": "n8n-nodes-base.function",
  "position": [
    1450,
    400
  ],
  "parameters": {
    "functionCode": "// Validar códigos de producto NEVIR\nconst extractedData = $input.item.json.extractedData || {};\nconst lines = extractedData.lines || [];\n\n// Validar cada línea\nconst validatedLines = lines.map(line => {\n  const productCode = line.productCode || '';\n  \n  // Verificar formato NVR-XXXXX\n  const isValidFormat = /^NVR-\\d{5}$/.test(productCode);\n  \n  return {\n    ...line,\n    isValidProductCode: isValidFormat,\n    validationMessage: isValidFormat ? 'Código válido' : 'Código inválido: debe seguir el formato NVR-XXXXX'\n  };\n});\n\n// Verificar si hay códigos inválidos\nconst invalidCodes = validatedLines.filter(line => !line.isValidProductCode);\n\nreturn {\n  json: {\n    ...extractedData,\n    lines: validatedLines,\n    hasInvalidCodes: invalidCodes.length > 0,\n    invalidCodes\n  }\n};"
  }
}
```

### 6. Validación de CIF/NIF

```json
{
  "name": "Function (Validar CIF)",
  "type": "n8n-nodes-base.function",
  "position": [
    1650,
    400
  ],
  "parameters": {
    "functionCode": "// Validar CIF/NIF español\nconst extractedData = $input.item.json || {};\nconst cif = extractedData.supplierVat || '';\n\n// Función para validar CIF/NIF español\nfunction validateCIF(cif) {\n  if (!cif || typeof cif !== 'string') {\n    return false;\n  }\n  \n  // Eliminar espacios y guiones\n  cif = cif.replace(/[\\s\\-]/g, '').toUpperCase();\n  \n  // Verificar formato básico\n  if (!/^[A-Z0-9]{9}$/.test(cif)) {\n    return false;\n  }\n  \n  // Para NEVIR, el CIF debe ser B84201219\n  if (extractedData.supplierName === 'NEVIR' && cif !== 'B84201219') {\n    return false;\n  }\n  \n  // Aquí iría la validación completa del algoritmo CIF/NIF\n  // Por simplicidad, solo verificamos el formato básico\n  \n  return true;\n}\n\n// Validar CIF\nconst isValidCIF = validateCIF(cif);\n\nreturn {\n  json: {\n    ...extractedData,\n    isValidCIF,\n    cifValidationMessage: isValidCIF ? 'CIF válido' : 'CIF inválido'\n  }\n};"
  }
}
```

### 7. Guardar en Caché

```json
{
  "name": "Function (Guardar Caché)",
  "type": "n8n-nodes-base.function",
  "position": [
    1850,
    400
  ],
  "parameters": {
    "functionCode": "// Guardar resultados en caché\nconst fs = require('fs');\nconst extractedData = $input.item.json || {};\nconst fileHash = $node[\"Function (Verificar Caché)\"].json.fileHash;\nconst cachePath = $node[\"Function (Verificar Caché)\"].json.cachePath;\n\n// Solo guardar en caché si los datos son válidos\nif (extractedData.isValidCIF && !extractedData.hasInvalidCodes) {\n  // Datos a guardar en caché\n  const cacheData = {\n    extractedData,\n    timestamp: new Date().toISOString(),\n    provider: 'NEVIR'\n  };\n  \n  // Guardar en archivo\n  fs.writeFileSync(cachePath, JSON.stringify(cacheData, null, 2));\n  \n  return {\n    json: {\n      ...extractedData,\n      cachedSuccessfully: true,\n      fileHash\n    }\n  };\n} else {\n  return {\n    json: {\n      ...extractedData,\n      cachedSuccessfully: false,\n      reason: !extractedData.isValidCIF ? 'CIF inválido' : 'Códigos de producto inválidos',\n      fileHash\n    }\n  };\n}"
  }
}
```

### 8. Integración con Odoo 18

```json
{
  "name": "HTTP Request (Odoo)",
  "type": "n8n-nodes-base.httpRequest",
  "position": [
    2050,
    400
  ],
  "parameters": {
    "url": "={{$env.ODOO_URL}}/xmlrpc/2/object",
    "method": "POST",
    "authentication": "genericCredentialType",
    "genericAuthType": "basicAuth",
    "username": "={{$env.ODOO_USERNAME}}",
    "password": "={{$env.ODOO_PASSWORD}}",
    "sendBody": true,
    "contentType": "raw",
    "rawContentType": "application/xml",
    "body": "<?xml version=\"1.0\"?>\n<methodCall>\n  <methodName>execute_kw</methodName>\n  <params>\n    <param><value><string>{{$env.ODOO_DB}}</string></value></param>\n    <param><value><int>1</int></value></param>\n    <param><value><string>{{$env.ODOO_PASSWORD}}</string></value></param>\n    <param><value><string>account.move</string></value></param>\n    <param><value><string>create</string></value></param>\n    <param>\n      <value>\n        <array>\n          <data>\n            <value>\n              <struct>\n                <member>\n                  <name>move_type</name>\n                  <value><string>in_invoice</string></value>\n                </member>\n                <member>\n                  <name>ref</name>\n                  <value><string>{{$json[\"invoiceNumber\"]}}</string></value>\n                </member>\n                <member>\n                  <name>invoice_date</name>\n                  <value><string>{{$json[\"invoiceDate\"]}}</string></value>\n                </member>\n                <!-- Más campos de la factura -->\n              </struct>\n            </value>\n          </data>\n        </array>\n      </value>\n    </param>\n  </params>\n</methodCall>"
  }
}
```

### 9. Respuesta Final

```json
{
  "name": "Respuesta Final",
  "type": "n8n-nodes-base.function",
  "position": [
    2250,
    300
  ],
  "parameters": {
    "functionCode": "// Preparar respuesta final\nconst fromCache = $node[\"IF (En Caché)\"].json.fromCache;\nlet response;\n\nif (fromCache) {\n  // Datos obtenidos de caché\n  response = {\n    success: true,\n    message: 'Factura procesada desde caché',\n    data: $node[\"IF (En Caché)\"].json.cacheData,\n    fromCache: true\n  };\n} else {\n  // Datos procesados nuevos\n  response = {\n    success: true,\n    message: 'Factura procesada correctamente',\n    data: $input.item.json,\n    fromCache: false,\n    odooInvoiceId: $node[\"HTTP Request (Odoo)\"].json.result\n  };\n}\n\nreturn {\n  json: response\n};"
  }
}
```

## Conexiones entre Nodos

1. Webhook → Function (Verificar Caché)
2. Function (Verificar Caché) → IF (En Caché)
3. IF (En Caché) → Respuesta Final [Si está en caché]
4. IF (En Caché) → HTTP Request (OCR) [Si no está en caché]
5. HTTP Request (OCR) → Function (Prompt NEVIR)
6. Function (Prompt NEVIR) → LLM Node (no mostrado por brevedad)
7. LLM Node → Function (Validar Códigos)
8. Function (Validar Códigos) → Function (Validar CIF)
9. Function (Validar CIF) → Function (Guardar Caché)
10. Function (Guardar Caché) → HTTP Request (Odoo)
11. HTTP Request (Odoo) → Respuesta Final

## Uso del Flujo de Trabajo

Una vez creado el flujo, puedes ejecutarlo con el siguiente comando desde FastAPI:

```python
import requests
import json

# Datos de la factura
invoice_data = {
    "fileData": "base64_encoded_file_data",
    "fileName": "factura_nevir.pdf"
}

# Ejecutar flujo de trabajo
response = requests.post(
    f"{n8n_config.N8N_API_URL}/workflows/{n8n_config.WORKFLOW_IDS['nevir_ocr']}/execute",
    headers={"Authorization": f"Bearer {n8n_config.N8N_API_KEY}"},
    json={"data": invoice_data}
)

# Procesar respuesta
result = response.json()
print(json.dumps(result, indent=2))
```

## Notas Importantes

1. **Validación de Códigos NEVIR**: El flujo valida específicamente que los códigos de producto sigan el formato NVR-XXXXX.
2. **Sistema de Caché**: Evita reprocesar facturas ya procesadas, mejorando la eficiencia.
3. **Validación de CIF**: Verifica que el CIF del proveedor sea correcto (B84201219 para NEVIR).
4. **Integración con Odoo 18**: Crea la factura directamente en Odoo 18 utilizando la API XMLRPC.

Este flujo de trabajo es un ejemplo de cómo n8n-MCP puede ayudarte a crear flujos complejos y específicos para tu negocio, aprovechando la potencia de n8n y la facilidad de uso de Cascade.

---

Documento creado: 19 de julio de 2025  
Última actualización: 19 de julio de 2025
