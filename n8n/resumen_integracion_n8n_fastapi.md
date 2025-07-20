# Resumen de Integración n8n-FastAPI

## Mejoras Implementadas

Hemos implementado una integración completa entre n8n y FastAPI para el proyecto Pelotazo ERP, lo que permite una comunicación bidireccional entre ambos sistemas. Las principales mejoras incluyen:

### 1. Configuración de API en n8n

- Habilitación de la API REST de n8n mediante variables de entorno en `docker-compose.yml`:
  ```yaml
  - N8N_API_ENABLED=true
  - N8N_API_AUTH_DISABLED=false
  - N8N_API_AUTH_ACCESS_TOKEN=pelotazo-n8n-api-token-seguro-2025
  ```
- Configuración de autenticación segura mediante token de acceso

### 2. Integración en FastAPI

- Creación de un módulo completo para interactuar con n8n (`api/routes/n8n_integration.py`)
- Implementación de endpoints para:
  - Listar flujos de trabajo disponibles
  - Activar/desactivar flujos de trabajo
  - Ejecutar flujos de trabajo específicos (OCR y LLM-MCP)
  - Monitorizar ejecuciones
  - Verificar estado de conexión con n8n

### 3. Configuración Centralizada

- Creación de un módulo de configuración centralizada (`api/utils/n8n_config.py`)
- Implementación de sistema para detectar y actualizar automáticamente los IDs de flujos de trabajo
- Soporte para variables de entorno personalizables

### 4. Scripts de Automatización

- `actualizar_n8n.sh`: Script para actualizar y reiniciar n8n con la nueva configuración
- `actualizar_env_n8n.sh`: Script para configurar las variables de entorno necesarias para la integración

### 5. Documentación

- `guia_uso_api_n8n.md`: Guía detallada sobre cómo utilizar la API de n8n
- `guia_ocr_mejorado.md`: Documentación sobre el flujo de trabajo OCR mejorado
- `guia_integracion_mcp_llm.md`: Guía sobre la integración del nodo MCP Client con LLM

## Arquitectura de la Integración

La integración funciona de la siguiente manera:

1. **FastAPI → n8n**: 
   - FastAPI puede iniciar flujos de trabajo en n8n mediante llamadas a la API REST
   - Los datos se envían en formato JSON y pueden incluir información del usuario, archivos procesados, etc.
   - Las ejecuciones pueden ser síncronas o asíncronas (en segundo plano)

2. **n8n → FastAPI**:
   - Los flujos de trabajo en n8n pueden enviar datos a FastAPI mediante nodos HTTP Request
   - El servidor MCP en n8n puede exponer herramientas que interactúan con FastAPI

3. **Comunicación bidireccional**:
   - FastAPI puede monitorizar el estado de las ejecuciones en n8n
   - n8n puede utilizar webhooks para notificar a FastAPI sobre eventos importantes

## Flujos de Trabajo Integrados

### 1. Procesamiento OCR Mejorado

- **Endpoint en FastAPI**: `/api/v1/n8n/execute/ocr`
- **Flujo en n8n**: `procesar_factura_ocr_mejorado.json`
- **Funcionalidad**: Procesa facturas con OCR utilizando prompts específicos por proveedor y sistema de caché

### 2. Análisis Inteligente con LLM y MCP

- **Endpoint en FastAPI**: `/api/v1/n8n/execute/llm-mcp`
- **Flujo en n8n**: `llm_mcp_client_factura.json`
- **Funcionalidad**: Analiza facturas con LLM y utiliza herramientas MCP para validaciones avanzadas

## Cómo Utilizar la Integración

### Desde FastAPI

```python
# Ejemplo de uso en otro módulo de FastAPI
from fastapi import APIRouter, Depends, HTTPException
import requests
from api.utils.n8n_config import n8n_config

# Ejecutar flujo OCR
response = requests.post(
    f"{n8n_config.N8N_API_URL}/workflows/{n8n_config.WORKFLOW_IDS['ocr_mejorado']}/execute",
    headers={"Authorization": f"Bearer {n8n_config.N8N_API_KEY}"},
    json={"data": datos_factura}
)
```

### Desde n8n

1. Utilizar el nodo HTTP Request para enviar datos a FastAPI:
   - URL: `http://api:8000/api/v1/...`
   - Método: POST/GET/etc.
   - Headers: Incluir token de autenticación si es necesario
   - Body: Datos en formato JSON

2. Utilizar el servidor MCP para exponer herramientas que interactúan con FastAPI

## Próximos Pasos

1. **Implementar sistema de notificaciones**: Configurar webhooks en n8n para notificar a FastAPI sobre eventos importantes
2. **Mejorar manejo de errores**: Implementar reintentos y recuperación ante fallos
3. **Ampliar herramientas MCP**: Crear más herramientas específicas para el procesamiento de facturas
4. **Implementar monitorización avanzada**: Dashboard para visualizar estado de ejecuciones y estadísticas
5. **Optimizar rendimiento**: Implementar caché de resultados y procesamiento en lotes

---

Documento creado: 19 de julio de 2025  
Última actualización: 19 de julio de 2025
