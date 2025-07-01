from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
import pandas as pd
import tempfile
import os
import logging
import time
from ..utils.config import config
from ..models.schemas import User
from ..services.auth_service import get_current_active_user
import httpx
from ..services.odoo_service import OdooService
from ..services.odoo_product_service import OdooProductService
from ..utils.mistral_llm_utils import parse_mistral_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/mistral-llm",
    tags=["Mistral LLM Excel"],
    responses={404: {"description": "Not found"}}
)

# Utilidad para convertir Excel a texto plano (todas las hojas)
def excel_to_full_text(file_path: str, start_row: int = 0, chunk_size: int = 25, only_first_sheet: bool = True) -> str:
    xls = pd.ExcelFile(file_path)
    full_text = ""
    sheet_names = [xls.sheet_names[0]] if only_first_sheet else xls.sheet_names
    for sheet_name in sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
        df = df.fillna("")
        # Seleccionar chunk de filas
        df = df.iloc[start_row:start_row+chunk_size]
        sheet_text = df.to_csv(sep=";", index=False, header=True)
        full_text += f"\n--- HOJA: {sheet_name} ---\n"
        full_text += sheet_text
    return full_text

@router.post("/test-minimal")
def test_mistral_minimal(current_user: User = Depends(get_current_active_user)) -> JSONResponse:
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
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            return JSONResponse(content=response.json())
    except httpx.HTTPStatusError as e:
        logger.error(f"Error en la llamada a Mistral: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error inesperado en test-minimal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-excel")
async def process_excel_file(
    file: UploadFile = File(...),
    proveedor_nombre: str = Form(...),
    start_row: int = Form(0),
    chunk_size: int = Form(25),
    only_first_sheet: bool = Form(True),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    start_time = time.time()
    logger.info(f"[PERF] Iniciando procesamiento de archivo a las {start_time}")
    
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            temp_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        logger.info(f"[MISTRAL LLM EXCEL] Procesando archivo: {file.filename}")
        
        t_before_excel = time.time()
        texto_completo = excel_to_full_text(temp_path, start_row, chunk_size, only_first_sheet)
        t_after_excel = time.time()
        logger.info(f"[PERF] Lectura de Excel completada en {t_after_excel - t_before_excel:.2f} segundos.")
        
        api_key = config.MISTRAL_LLM_API_KEY
        if not api_key:
            raise HTTPException(status_code=500, detail="No está configurada la API KEY de Mistral LLM")

        prompt = f"""
        Eres un asistente de extracción de datos para un ERP.
        A partir del siguiente texto extraído de una hoja de cálculo de un proveedor, extrae la lista de productos.
        El proveedor se llama '{proveedor_nombre}'.
        El formato de salida debe ser un objeto JSON con una única clave \"productos\", que contenga una lista de objetos.
        Cada objeto debe representar un producto y tener las siguientes claves en español y minúsculas: \"nombre\", \"referencia_proveedor\", \"precio_coste\", \"categoria\", \"subcategoria\", \"marca\", \"descripcion\".
        Si un campo no está disponible, omítelo o déjalo como null. No inventes datos.
        Asegúrate de que el JSON esté bien formado.

        Texto a procesar:
        ---
        {texto_completo}
        ---
        """
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "model": "mistral-large-latest",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }

        t_before_mistral = time.time()
        logger.info("[PERF] Realizando llamada a la API de Mistral LLM...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60.0
            )
        t_after_mistral = time.time()
        logger.info(f"[PERF] Llamada a Mistral LLM completada en {t_after_mistral - t_before_mistral:.2f} segundos.")
        
        response.raise_for_status()
        result = response.json()
        
        productos = parse_mistral_response(result)
        
        if not productos:
            return JSONResponse(content={"message": "No se encontraron productos en la respuesta de la IA.", "raw_response": result})

        created = []
        failed = []
        
        t_before_odoo = time.time()
        logger.info("[PERF] Iniciando creación de productos en Odoo...")
        odoo_service = OdooService()
        odoo_product_service = OdooProductService()

        for idx, producto in enumerate(productos):
            try:
                odoo_dict = odoo_product_service.front_to_odoo_product_dict(producto, proveedor_nombre)
                created_product_id = odoo_product_service.create_or_update_product(odoo_dict)
                if created_product_id:
                    new_prod = odoo_product_service.get_product_by_id(created_product_id)
                    created.append({"idx": idx, "name": new_prod.name, "id": new_prod.id})
                else:
                    failed.append({"idx": idx, "name": odoo_dict.get("name"), "error": "No se pudo crear en Odoo"})
            except Exception as e:
                failed.append({"idx": idx, "name": producto.get("name") or producto.get("nombre"), "error": str(e)})
        
        t_after_odoo = time.time()
        logger.info(f"[PERF] Creación de productos en Odoo completada en {t_after_odoo - t_before_odoo:.2f} segundos.")
        logger.info(f"[MISTRAL LLM EXCEL] Productos creados: {len(created)}, fallidos: {len(failed)}")

        total_time = time.time() - start_time
        logger.info(f"[PERF] Proceso total completado en {total_time:.2f} segundos.")

        return JSONResponse(content={
            "proveedor": proveedor_nombre,
            "result": result,
            "productos_creados": created,
            "productos_fallidos": failed,
            "total_intentados": len(productos),
            "total_creados": len(created),
            "total_fallidos": len(failed)
        })

    except Exception as e:
        logger.error(f"[MISTRAL LLM EXCEL] Exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error al llamar a la API de Mistral LLM: {str(e)}")
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass
