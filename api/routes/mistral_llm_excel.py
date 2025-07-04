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
def excel_to_full_text(file_path: str, start_row: int = 0, chunk_size: int = 50, only_first_sheet: bool = True) -> str:
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
    chunk_size: int = Form(50),
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

        prompt = (
            f"Extrae la información de productos del siguiente texto de un archivo Excel. "
            f"El proveedor es {proveedor_nombre}. "
            f"El texto está estructurado en filas y columnas, donde cada fila representa un producto potencial. "
            f"Las columnas contienen datos como código, descripción, precio, etc. "
            f"Devuelve un JSON válido con una clave raíz 'productos' que contenga una lista de objetos. "
            f"Cada objeto debe tener las claves 'codigo', 'nombre', 'precio_venta', 'precio_coste', y opcionalmente 'categoria' si se menciona. "
            f"El campo 'codigo' es OBLIGATORIO y debe contener el código o referencia del producto; si no existe, usa 'SIN_CODIGO'. "
            f"Si no hay precio de venta, asume que es un 30% mayor que el coste. "
            f"Si no hay información de precio, usa 0.0. "
            f"Extrae TODOS los productos válidos con nombre y al menos un precio o código, incluso si hay filas vacías o irrelevantes entre ellos. "
            f"No ignores productos válidos bajo ninguna circunstancia; revisa cada fila con datos. "
            f"Este es el texto extraído del Excel:\n\n{texto_completo}"
        )
        
        from ..utils.mistral_llm_utils import call_llm
        t_before_llm = time.time()
        logger.info("[PERF] Llamando a Groq…")
        try:
            result = await call_llm(prompt, provider="groq")
        except HTTPException as he:
            if he.status_code in (502, 503):
                logger.warning("Groq saturado o error, intentando fallback Mistral…")
                result = await call_llm(prompt, provider="mistral")
            else:
                raise
        t_after_llm = time.time()
        logger.info(f"[PERF] Llamada LLM completada en {t_after_llm - t_before_llm:.2f} s")
        
        productos = parse_mistral_response(result)
        # Asegurarse de que todos los productos tengan 'codigo', asignar 'SIN_CODIGO' si falta
        for prod in productos:
            if 'codigo' not in prod or not prod['codigo']:
                prod['codigo'] = 'SIN_CODIGO'
        logger.info(f"Respuesta parseada con éxito. {len(productos)} productos encontrados.")
        
        if not productos:
            return JSONResponse(content={"message": "No se encontraron productos en la respuesta de la IA.", "raw_response": result})

        logger.info(f"[PERF] Iniciando creación de productos en Odoo...")
        t_before_odoo = time.time()
        creados = []
        fallidos = []
        odoo_product_service = OdooProductService()
        for idx, producto in enumerate(productos):
            try:
                # Construir el diccionario de valores para Odoo usando la utilidad centralizada
                product_vals = odoo_product_service.front_to_odoo_product_dict(producto, proveedor_nombre)

                # Asegurar campos mínimos obligatorios
                if 'name' not in product_vals:
                    product_vals['name'] = producto.get('nombre', 'Producto sin nombre')
                if 'default_code' not in product_vals:
                    product_vals['default_code'] = producto.get('codigo', 'SIN_CODIGO')

                # Valores numéricos seguros en caso de que Groq devuelva cadenas vacías
                product_vals.setdefault('list_price', float(producto.get('precio_venta', 0.0) or 0.0))
                product_vals.setdefault('standard_price', float(producto.get('precio_coste', 0.0) or 0.0))
                
                product_id = odoo_product_service.create_or_update_product(product_vals)
                if product_id:
                    creados.append({
                        'idx': idx,
                        'name': producto.get('nombre'),
                        'id': product_id
                    })
                else:
                    fallidos.append({
                        'idx': idx,
                        'name': producto.get('nombre'),
                        'error': 'No se pudo crear en Odoo'
                    })
            except Exception as e:
                logger.error(f"Error al crear producto {producto.get('nombre')}: {e}")
                fallidos.append({
                    'idx': idx,
                    'name': producto.get('nombre'),
                    'error': str(e)
                })
        t_after_odoo = time.time()
        logger.info(f"[PERF] Creación de productos en Odoo completada en {t_after_odoo - t_before_odoo:.2f} segundos.")
        logger.info(f"[MISTRAL LLM EXCEL] Productos creados: {len(creados)}, fallidos: {len(fallidos)}")

        total_time = time.time() - start_time
        logger.info(f"[PERF] Proceso total completado en {total_time:.2f} segundos.")

        return JSONResponse(content={
            "proveedor": proveedor_nombre,
            "result": result,
            "productos_creados": creados,
            "productos_fallidos": fallidos,
            "total_intentados": len(productos),
            "total_creados": len(creados),
            "total_fallidos": len(fallidos)
        })

    except HTTPException as he:
        # Propagar directamente excepciones HTTP (por ejemplo, 503 de límite LLM)
        raise he
    except Exception as e:
        logger.error(f"[MISTRAL LLM EXCEL] Exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo Excel: {str(e)}")
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass
