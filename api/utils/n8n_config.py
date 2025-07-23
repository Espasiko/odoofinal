"""
Configuración para la integración con n8n
"""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Cargar variables de entorno desde .env si existe
load_dotenv()

class N8nSettings(BaseSettings):
    """Configuración para la integración con n8n"""
    
    # URL base de la API de n8n
    N8N_API_URL: str = os.getenv("N8N_API_URL", "http://n8n:5678/api/v1")
    
    # Token de autenticación para la API de n8n
    N8N_API_KEY: str = os.getenv("N8N_API_KEY", "pelotazo-n8n-api-token-seguro-2025")
    
    # URL base para webhooks de n8n
    N8N_WEBHOOK_URL: str = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook")
    
    # IDs de flujos de trabajo importantes
    # Estos se actualizarán automáticamente al consultar los flujos disponibles
    WORKFLOW_IDS: dict = {
        "ocr_mejorado": None,
        "llm_mcp_factura": None,
        "servidor_mcp": None
    }
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

# Instancia de configuración para usar en la aplicación
n8n_config = N8nSettings()

# Función para actualizar los IDs de flujos de trabajo
def update_workflow_ids(workflows_data: list) -> dict:
    """
    Actualiza los IDs de flujos de trabajo conocidos basados en sus nombres
    
    Args:
        workflows_data: Lista de flujos de trabajo obtenidos de la API de n8n
        
    Returns:
        Diccionario actualizado con los IDs de flujos de trabajo
    """
    workflow_ids = n8n_config.WORKFLOW_IDS.copy()
    
    for workflow in workflows_data:
        name = workflow.get("name", "").lower()
        
        if "ocr mejorado" in name or "procesar_factura_ocr_mejorado" in name:
            workflow_ids["ocr_mejorado"] = workflow.get("id")
        
        elif ("llm" in name and "mcp" in name and "factura" in name) or "llm_mcp_client_factura" in name:
            workflow_ids["llm_mcp_factura"] = workflow.get("id")
        
        elif "servidor mcp" in name or "servidor_mcp_herramientas" in name:
            workflow_ids["servidor_mcp"] = workflow.get("id")
    
    # Actualizar la configuración
    n8n_config.WORKFLOW_IDS = workflow_ids
    
    return workflow_ids
