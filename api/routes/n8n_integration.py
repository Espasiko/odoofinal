from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List
import requests
import os
import logging
from ..models.user import User
from ..dependencies import get_current_user
from ..utils.n8n_config import n8n_config, update_workflow_ids

# Configuración de logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/n8n",
    tags=["n8n"],
    responses={404: {"description": "No encontrado"}},
)

# Usar configuración centralizada de n8n
N8N_API_URL = n8n_config.N8N_API_URL
N8N_API_KEY = n8n_config.N8N_API_KEY
WORKFLOW_IDS = n8n_config.WORKFLOW_IDS

def get_n8n_headers():
    """Obtiene los headers para las solicitudes a la API de n8n"""
    return {
        "Authorization": f"Bearer {N8N_API_KEY}",
        "Content-Type": "application/json"
    }

@router.get("/workflows", response_model=Dict[str, Any])
async def get_workflows(current_user: User = Depends(get_current_user)):
    """
    Obtiene todos los flujos de trabajo disponibles en n8n
    """
    try:
        response = requests.get(
            f"{N8N_API_URL}/workflows",
            headers=get_n8n_headers()
        )
        
        if response.status_code == 200:
            workflows = response.json()
            
            # Actualizar los IDs de flujos conocidos usando la función centralizada
            update_workflow_ids(workflows)
            
            # Formatear la respuesta
            result = {
                "total": len(workflows),
                "activos": sum(1 for w in workflows if w.get("active", False)),
                "workflows": [{
                    "id": w.get("id"),
                    "name": w.get("name"),
                    "active": w.get("active", False),
                    "createdAt": w.get("createdAt"),
                    "updatedAt": w.get("updatedAt")
                } for w in workflows]
            }
            
            return result
        else:
            logger.error(f"Error al obtener flujos de n8n: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al obtener flujos de n8n: {response.text}"
            )
    except Exception as e:
        logger.error(f"Error de conexión con n8n: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión con n8n: {str(e)}"
        )

@router.post("/workflows/{workflow_id}/activate")
async def activate_workflow(workflow_id: str, current_user: User = Depends(get_current_user)):
    """
    Activa un flujo de trabajo específico
    """
    try:
        response = requests.post(
            f"{N8N_API_URL}/workflows/{workflow_id}/activate",
            headers=get_n8n_headers()
        )
        
        if response.status_code == 200:
            return {"status": "success", "message": f"Flujo de trabajo {workflow_id} activado correctamente"}
        else:
            logger.error(f"Error al activar flujo {workflow_id}: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al activar flujo de trabajo: {response.text}"
            )
    except Exception as e:
        logger.error(f"Error de conexión con n8n: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión con n8n: {str(e)}"
        )

@router.post("/workflows/{workflow_id}/deactivate")
async def deactivate_workflow(workflow_id: str, current_user: User = Depends(get_current_user)):
    """
    Desactiva un flujo de trabajo específico
    """
    try:
        response = requests.post(
            f"{N8N_API_URL}/workflows/{workflow_id}/deactivate",
            headers=get_n8n_headers()
        )
        
        if response.status_code == 200:
            return {"status": "success", "message": f"Flujo de trabajo {workflow_id} desactivado correctamente"}
        else:
            logger.error(f"Error al desactivar flujo {workflow_id}: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al desactivar flujo de trabajo: {response.text}"
            )
    except Exception as e:
        logger.error(f"Error de conexión con n8n: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión con n8n: {str(e)}"
        )

@router.post("/execute/ocr", response_model=Dict[str, Any])
async def execute_ocr_workflow(
    datos: Dict[str, Any], 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Ejecuta el flujo de trabajo de OCR mejorado
    """
    workflow_id = WORKFLOW_IDS.get("ocr_mejorado")
    
    # Si no tenemos el ID, intentamos obtenerlo
    if not workflow_id:
        await get_workflows(current_user)
        workflow_id = WORKFLOW_IDS.get("ocr_mejorado")
        
        if not workflow_id:
            raise HTTPException(
                status_code=404,
                detail="No se encontró el flujo de trabajo de OCR mejorado en n8n"
            )
    
    try:
        # Añadir información del usuario que ejecuta
        datos["user_info"] = {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name
        }
        
        # Ejecutar el flujo en segundo plano para no bloquear la respuesta
        background_tasks.add_task(
            execute_workflow_background,
            workflow_id,
            datos
        )
        
        return {
            "status": "success", 
            "message": "Procesamiento OCR iniciado en segundo plano",
            "workflow_id": workflow_id
        }
    except Exception as e:
        logger.error(f"Error al ejecutar flujo OCR: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al ejecutar flujo OCR: {str(e)}"
        )

@router.post("/execute/llm-mcp", response_model=Dict[str, Any])
async def execute_llm_mcp_workflow(
    datos: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Ejecuta el flujo de trabajo de LLM con MCP para análisis inteligente de facturas
    """
    workflow_id = WORKFLOW_IDS.get("llm_mcp_factura")
    
    # Si no tenemos el ID, intentamos obtenerlo
    if not workflow_id:
        await get_workflows(current_user)
        workflow_id = WORKFLOW_IDS.get("llm_mcp_factura")
        
        if not workflow_id:
            raise HTTPException(
                status_code=404,
                detail="No se encontró el flujo de trabajo de LLM con MCP en n8n"
            )
    
    try:
        # Añadir información del usuario que ejecuta
        datos["user_info"] = {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name
        }
        
        # Ejecutar el flujo en segundo plano para no bloquear la respuesta
        background_tasks.add_task(
            execute_workflow_background,
            workflow_id,
            datos
        )
        
        return {
            "status": "success", 
            "message": "Análisis inteligente de factura iniciado en segundo plano",
            "workflow_id": workflow_id
        }
    except Exception as e:
        logger.error(f"Error al ejecutar flujo LLM-MCP: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al ejecutar flujo LLM-MCP: {str(e)}"
        )

@router.get("/executions", response_model=Dict[str, Any])
async def get_executions(
    workflow_id: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene las ejecuciones de flujos de trabajo
    """
    try:
        url = f"{N8N_API_URL}/executions"
        params = {"limit": limit}
        
        if workflow_id:
            params["workflowId"] = workflow_id
        
        response = requests.get(
            url,
            headers=get_n8n_headers(),
            params=params
        )
        
        if response.status_code == 200:
            executions = response.json()
            
            # Formatear la respuesta
            result = {
                "total": len(executions),
                "executions": [{
                    "id": e.get("id"),
                    "workflowId": e.get("workflowId"),
                    "status": e.get("status"),
                    "startedAt": e.get("startedAt"),
                    "stoppedAt": e.get("stoppedAt"),
                    "mode": e.get("mode")
                } for e in executions]
            }
            
            return result
        else:
            logger.error(f"Error al obtener ejecuciones: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al obtener ejecuciones: {response.text}"
            )
    except Exception as e:
        logger.error(f"Error de conexión con n8n: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión con n8n: {str(e)}"
        )

@router.get("/executions/{execution_id}", response_model=Dict[str, Any])
async def get_execution_details(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los detalles de una ejecución específica
    """
    try:
        response = requests.get(
            f"{N8N_API_URL}/executions/{execution_id}",
            headers=get_n8n_headers()
        )
        
        if response.status_code == 200:
            execution = response.json()
            return execution
        else:
            logger.error(f"Error al obtener detalles de ejecución: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error al obtener detalles de ejecución: {response.text}"
            )
    except Exception as e:
        logger.error(f"Error de conexión con n8n: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión con n8n: {str(e)}"
        )

@router.get("/status", response_model=Dict[str, Any])
async def get_n8n_status(current_user: User = Depends(get_current_user)):
    """
    Verifica el estado de conexión con n8n
    """
    try:
        # Intentamos obtener la lista de flujos como prueba de conexión
        response = requests.get(
            f"{N8N_API_URL}/workflows",
            headers=get_n8n_headers()
        )
        
        if response.status_code == 200:
            workflows = response.json()
            return {
                "status": "connected",
                "message": "Conexión exitosa con n8n",
                "workflows_count": len(workflows),
                "active_workflows": sum(1 for w in workflows if w.get("active", False))
            }
        else:
            logger.error(f"Error de conexión con n8n: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"Error de conexión con n8n: {response.status_code} - {response.text}"
            }
    except Exception as e:
        logger.error(f"Error de conexión con n8n: {str(e)}")
        return {
            "status": "error",
            "message": f"Error de conexión con n8n: {str(e)}"
        }

# Función auxiliar para ejecutar flujos en segundo plano
async def execute_workflow_background(workflow_id: str, datos: Dict[str, Any]):
    """
    Ejecuta un flujo de trabajo en segundo plano
    """
    try:
        response = requests.post(
            f"{N8N_API_URL}/workflows/{workflow_id}/execute",
            headers=get_n8n_headers(),
            json={"data": datos}
        )
        
        if response.status_code != 200:
            logger.error(f"Error al ejecutar flujo {workflow_id}: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error al ejecutar flujo {workflow_id} en segundo plano: {str(e)}")
