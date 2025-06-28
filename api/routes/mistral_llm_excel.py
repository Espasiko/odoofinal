from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import pandas as pd
import tempfile
import os
import logging
from ..utils.config import config
from ..models.schemas import User
from ..services.auth_service import get_current_user
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/mistral-llm",
    tags=["Mistral LLM Excel"],
    responses={404: {"description": "Not found"}}
)

# Utilidad para convertir Excel a texto plano (todas las hojas)
def excel_to_full_text(file_path: str, max_rows: int = 12, only_first_sheet: bool = True) -> str:
    xls = pd.ExcelFile(file_path)
    full_text = ""
    sheet_names = [xls.sheet_names[0]] if only_first_sheet else xls.sheet_names
    for sheet_name in sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
        df = df.fillna("")
        # Limitar a las primeras max_rows filas
        df = df.head(max_rows)
        sheet_text = df.to_csv(sep=";", index=False, header=True)
        full_text += f"\n--- HOJA: {sheet_name} ---\n"
        full_text += sheet_text
    return full_text

@router.post("/test-minimal")
def test_mistral_minimal(current_user: User = Depends(get_current_user)) -> JSONResponse:
    """
    Endpoint de prueba: llama a la API de Mistral LLM con un prompt fijo y clave real, sin procesar archivos.
    """
    import logging
    logger = logging.getLogger(__name__)
    api_key = config.MISTRAL_LLM_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="No está configurada la API KEY de Mistral LLM")
    prompt = "Hola, ¿puedes responder con un JSON de ejemplo de productos?"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 256
    }
    try:
        logger.info("[TEST-MISTRAL-MINIMAL] Enviando petición a Mistral LLM...")
        response = requests.post("https://api.mistral.ai/v1/chat/completions", json=data, headers=headers, timeout=30)
        logger.info(f"[TEST-MISTRAL-MINIMAL] Status: {response.status_code}")
        logger.info(f"[TEST-MISTRAL-MINIMAL] Resp: {response.text[:500]}")
        response.raise_for_status()
        return JSONResponse(content=response.json())
    except Exception as e:
        logger.error(f"[TEST-MISTRAL-MINIMAL] Exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error al llamar a la API de Mistral LLM: {str(e)}")

@router.post("/process-excel")
async def process_excel_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Procesa un archivo Excel de proveedor usando Mistral LLM (clave gratuita/desarrollador)
    Devuelve el JSON estructurado generado por Mistral LLM.
    """
    # Validar extensión
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".xlsx", ".xls", ".csv"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado. Solo .xlsx, .xls o .csv"
        )
    # Guardar archivo temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    try:
        # Convertir Excel a texto (máximo 12 filas de la primera hoja)
        excel_text = excel_to_full_text(temp_path, max_rows=12, only_first_sheet=True)
        prompt = f"""
Procesa toda la información contenida en el siguiente archivo Excel de proveedor (solo las primeras 12 filas de la primera hoja para pruebas).\nEl archivo contiene varias hojas (productos, ventas, devoluciones, notas, etc.).\nExtrae y estructura en un JSON toda la información útil para la gestión del negocio, incluyendo pero no limitado a:\n\n- Datos del proveedor (si aparecen)\n- Listado de productos, con todos sus campos (código, nombre, descripción, unidades, precios, márgenes, stock, etc.)\n- Ventas, devoluciones, notas, históricos, totales, etc., asociando cada dato a su producto si es posible\n- Cualquier otra información relevante para compras, inventario, contabilidad o análisis\n\nEl texto de cada hoja empieza con '--- HOJA: <nombre> ---'.\nReconoce el contexto de cada hoja y los campos de cada columna, aunque los encabezados cambien o haya celdas vacías.\n\nDevuélveme el resultado en un JSON estructurado por secciones (ejemplo: 'productos', 'ventas', 'devoluciones', 'notas', 'totales', 'otros').\n\nAquí tienes el contenido del archivo:\n\n""" + excel_text
        # LOG: Mostrar el prompt y tamaño
        logger.info(f"[MISTRAL LLM EXCEL] Prompt length: {len(prompt)}")
        logger.info(f"[MISTRAL LLM EXCEL] Prompt preview: {prompt[:500]}")
        api_key = config.MISTRAL_LLM_API_KEY
        if not api_key:
            raise HTTPException(status_code=500, detail="No está configurada la API KEY de Mistral LLM")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "mistral-large-latest",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 512
        }
        try:
            with httpx.Client(timeout=60) as client:
                response = client.post("https://api.mistral.ai/v1/chat/completions", json=data, headers=headers)
                logger.info(f"[MISTRAL LLM EXCEL] Response status: {response.status_code}")
                logger.info(f"[MISTRAL LLM EXCEL] Response text: {response.text[:500]}")
                response.raise_for_status()
                result = response.json()
                return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"[MISTRAL LLM EXCEL] Exception: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Error al llamar a la API de Mistral LLM: {str(e)}")
    finally:
        # Borrar archivo temporal
        try:
            os.remove(temp_path)
        except Exception:
            pass
