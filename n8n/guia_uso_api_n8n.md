# Guía de Uso de la API de n8n

## Introducción

Esta guía explica cómo utilizar la API REST de n8n para interactuar programáticamente con los flujos de trabajo, ejecuciones y otros recursos de n8n. Esto permite automatizar la gestión de n8n desde FastAPI u otros servicios sin necesidad de usar la interfaz web.

## Configuración

La API de n8n ha sido habilitada con las siguientes configuraciones en `docker-compose.yml`:

```yaml
- N8N_API_ENABLED=true
- N8N_API_AUTH_DISABLED=false
- N8N_API_AUTH_ACCESS_TOKEN=pelotazo-n8n-api-token-seguro-2025
```

### Token de Acceso

Para autenticarte con la API de n8n, debes incluir el token de acceso en tus solicitudes:

```
Authorization: Bearer pelotazo-n8n-api-token-seguro-2025
```

## Endpoints Principales

### 1. Flujos de Trabajo (Workflows)

#### Listar todos los flujos de trabajo

```
GET http://localhost:5678/api/v1/workflows
```

#### Obtener un flujo de trabajo específico

```
GET http://localhost:5678/api/v1/workflows/{id}
```

#### Crear un nuevo flujo de trabajo

```
POST http://localhost:5678/api/v1/workflows
Content-Type: application/json

{
  "name": "Nombre del Flujo",
  "nodes": [...],
  "connections": {...},
  "active": false
}
```

#### Actualizar un flujo de trabajo

```
PUT http://localhost:5678/api/v1/workflows/{id}
Content-Type: application/json

{
  "name": "Nombre Actualizado",
  "nodes": [...],
  "connections": {...}
}
```

#### Activar/Desactivar un flujo de trabajo

```
POST http://localhost:5678/api/v1/workflows/{id}/activate
```

```
POST http://localhost:5678/api/v1/workflows/{id}/deactivate
```

#### Eliminar un flujo de trabajo

```
DELETE http://localhost:5678/api/v1/workflows/{id}
```

### 2. Ejecuciones (Executions)

#### Ejecutar un flujo de trabajo

```
POST http://localhost:5678/api/v1/workflows/{id}/execute
Content-Type: application/json

{
  "data": {
    // Datos para la ejecución (opcional)
  }
}
```

#### Obtener ejecuciones de un flujo de trabajo

```
GET http://localhost:5678/api/v1/executions?workflowId={workflowId}
```

#### Obtener detalles de una ejecución

```
GET http://localhost:5678/api/v1/executions/{id}
```

### 3. Credenciales

#### Listar tipos de credenciales

```
GET http://localhost:5678/api/v1/credential-types
```

#### Listar credenciales

```
GET http://localhost:5678/api/v1/credentials
```

#### Crear nuevas credenciales

```
POST http://localhost:5678/api/v1/credentials
Content-Type: application/json

{
  "name": "Mi Credencial",
  "type": "httpBasicAuth",
  "data": {
    "user": "usuario",
    "password": "contraseña"
  }
}
```

## Ejemplos de Uso con Python

### Configuración Inicial

```python
import requests

N8N_API_URL = "http://localhost:5678/api/v1"
N8N_API_KEY = "pelotazo-n8n-api-token-seguro-2025"

headers = {
    "Authorization": f"Bearer {N8N_API_KEY}",
    "Content-Type": "application/json"
}
```

### Listar Flujos de Trabajo

```python
def listar_flujos():
    response = requests.get(f"{N8N_API_URL}/workflows", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
```

### Ejecutar un Flujo de Trabajo

```python
def ejecutar_flujo(workflow_id, datos=None):
    payload = {}
    if datos:
        payload["data"] = datos
    
    response = requests.post(
        f"{N8N_API_URL}/workflows/{workflow_id}/execute", 
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
```

### Activar un Flujo de Trabajo

```python
def activar_flujo(workflow_id):
    response = requests.post(
        f"{N8N_API_URL}/workflows/{workflow_id}/activate", 
        headers=headers
    )
    
    if response.status_code == 200:
        return True
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return False
```

## Integración con FastAPI

### Ejemplo de Integración en FastAPI

```python
from fastapi import APIRouter, Depends, HTTPException
import requests
from typing import Dict, Any, Optional

router = APIRouter()

N8N_API_URL = "http://localhost:5678/api/v1"
N8N_API_KEY = "pelotazo-n8n-api-token-seguro-2025"

headers = {
    "Authorization": f"Bearer {N8N_API_KEY}",
    "Content-Type": "application/json"
}

@router.post("/ejecutar-flujo-ocr")
async def ejecutar_flujo_ocr(datos: Dict[str, Any]):
    """
    Ejecuta el flujo de OCR en n8n con los datos proporcionados
    """
    # ID del flujo de trabajo de OCR (reemplazar con el ID real)
    workflow_id = "1"  # Obtener el ID real después de importar el flujo
    
    try:
        response = requests.post(
            f"{N8N_API_URL}/workflows/{workflow_id}/execute", 
            headers=headers,
            json={"data": datos}
        )
        
        if response.status_code == 200:
            return {"status": "success", "execution": response.json()}
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al ejecutar flujo en n8n: {response.text}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión con n8n: {str(e)}"
        )

@router.get("/estado-flujos")
async def obtener_estado_flujos():
    """
    Obtiene el estado de todos los flujos de trabajo en n8n
    """
    try:
        response = requests.get(f"{N8N_API_URL}/workflows", headers=headers)
        
        if response.status_code == 200:
            workflows = response.json()
            return {
                "status": "success",
                "total": len(workflows),
                "activos": sum(1 for w in workflows if w.get("active", False)),
                "workflows": [{
                    "id": w.get("id"),
                    "name": w.get("name"),
                    "active": w.get("active", False)
                } for w in workflows]
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al obtener flujos de n8n: {response.text}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión con n8n: {str(e)}"
        )
```

## Obtener IDs de Flujos de Trabajo

Para obtener los IDs de los flujos de trabajo después de importarlos:

1. Accede a n8n en http://localhost:5678
2. Ve a Flujos de trabajo
3. Abre el flujo de trabajo deseado
4. El ID aparece en la URL: `http://localhost:5678/workflow/{ID}`

También puedes obtener los IDs mediante la API:

```bash
curl -X GET "http://localhost:5678/api/v1/workflows" \
  -H "Authorization: Bearer pelotazo-n8n-api-token-seguro-2025"
```

## Webhooks y Ejecuciones Automáticas

Los flujos de trabajo con nodos Webhook se pueden ejecutar directamente mediante una solicitud HTTP a la URL del webhook, sin necesidad de usar la API de n8n.

Por ejemplo, para el flujo de OCR:

```
POST http://localhost:5678/webhook/procesar-factura
```

## Seguridad y Buenas Prácticas

1. **Proteger el token de API**: Almacena el token de API en variables de entorno o en un sistema seguro de gestión de secretos.

2. **Limitar el acceso**: Restringe el acceso a la API de n8n solo a las IPs o redes necesarias.

3. **Monitorizar el uso**: Implementa logging para registrar todas las llamadas a la API de n8n.

4. **Manejar errores**: Implementa un manejo adecuado de errores para las respuestas de la API.

5. **Actualizar regularmente**: Mantén n8n actualizado para beneficiarte de las últimas mejoras de seguridad.

## Solución de Problemas

### Error de Autenticación

Si recibes un error 401 Unauthorized:
- Verifica que estás usando el token correcto
- Comprueba que N8N_API_AUTH_DISABLED está configurado como false
- Asegúrate de que el formato del header de autorización es correcto

### Error de Conexión

Si no puedes conectarte a la API:
- Verifica que n8n está en ejecución
- Comprueba que N8N_API_ENABLED está configurado como true
- Asegúrate de que estás usando la URL correcta

### Error al Ejecutar un Flujo

Si recibes un error al ejecutar un flujo:
- Verifica que el ID del flujo es correcto
- Comprueba que el flujo está activo
- Revisa los logs de n8n para obtener más detalles

---

Documento creado: 19 de julio de 2025  
Última actualización: 19 de julio de 2025
