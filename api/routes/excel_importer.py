from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import shutil
import os
import logging
import json
import time
import httpx
import asyncio

from ..services.excel_preprocessor import ExcelPreprocessor
from ..models.schemas import User
from ..services.auth_service import get_current_active_user
from ..utils.config import config
from ..services.odoo_service import OdooService
from ..services.odoo_product_service import OdooProductService
from ..utils.mistral_llm_utils import parse_mistral_response

router = APIRouter(prefix="/api/v1/importer", tags=["Excel Importer"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMP_DIR = "/tmp/uploads"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

CHUNK_SIZE = 25  # Procesar en lotes de 50 productos

@router.post("/", response_model=dict)
async def process_and_load_excel(
    file: UploadFile = File(...),
    proveedor_nombre: str = Form(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Orquesta el proceso completo de importación de Excel:
    1.  Fase 1: Pre-procesa el archivo para obtener un JSON limpio.
    2.  Fase 2: Envía el JSON a Mistral AI para interpretación de negocio.
    3.  Fase 3: Carga los productos resultantes en Odoo.
    """
    start_time = time.time()
    temp_file_path = os.path.join(TEMP_DIR, file.filename)

    try:
        # --- FASE 1: PRE-PROCESAMIENTO --- #
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Fase 1: Archivo '{file.filename}' guardado en '{temp_file_path}'")

        preprocessor = ExcelPreprocessor(temp_file_path)
        preprocessed_data = preprocessor.process_file()
        logger.info("Fase 1: Pre-procesamiento completado.")

        # --- FASE 2: INTERPRETACIÓN CON IA --- #
        logger.info("Fase 2: Iniciando interpretación con IA.")
        raw_data = preprocessed_data.get('raw_data', [])
        chunks = [raw_data[i:i + CHUNK_SIZE] for i in range(0, len(raw_data), CHUNK_SIZE)]
        logger.info(f"Datos divididos en {len(chunks)} lotes de ~{CHUNK_SIZE} productos cada uno.")

        business_rules = preprocessed_data.get("business_rules", {})
        prompt_rules = "\n".join([f'- {k}: {v}' for k, v in business_rules.items()])

        async def process_chunk(chunk):
            prompt = f"""
            Eres un asistente experto en la interpretación de datos de productos para Odoo.
            A continuación, te proporciono una lista de productos extraída de un fichero Excel de un proveedor llamado '{proveedor_nombre}'.

            **Reglas de Negocio Específicas (¡Máxima Prioridad!):**
            {prompt_rules if prompt_rules else 'No se han detectado reglas explícitas. Por favor, infiere la lógica comercial a partir de los datos.'}

            **Datos Crudos del Lote (en formato JSON):**
            {json.dumps(chunk, indent=2)}

            **Instrucciones:**
            1.  Analiza los datos y las reglas de negocio.
            2.  Limpia y normaliza los datos. Ignora filas vacías o sin información relevante.
            3.  Interpreta los nombres de las columnas aunque no sean estándar (ej. 'COD.', 'P.V.P', 'Ref.').
            4.  Extrae la siguiente información para cada producto:
                -   `nombre`: El nombre del producto.
                -   `referencia_proveedor`: El código o referencia único del producto.
                -   `precio_coste`: El precio de compra o coste. Si no está, déjalo en 0.
                -   `categoria`: La categoría principal del producto.
                -   `subcategoria`: La subcategoría, si existe.
                -   `descripcion`: Una descripción breve si la hay.
            5.  Devuelve el resultado como un array de objetos JSON válido contenido dentro de un objeto JSON principal con la clave 'productos'. Ejemplo:
                ```json
                {{
                    "productos": [
                        {{
                            "nombre": "PRODUCTO EJEMPLO 1",
                            "referencia_proveedor": "REF001",
                            "precio_coste": 99.99,
                            "categoria": "CATEGORIA PRINCIPAL",
                            "subcategoria": "SUBCATEGORIA",
                            "descripcion": "Descripción del producto 1."
                        }}
                    ]
                }}
                """
            async with httpx.AsyncClient(timeout=180.0) as client:
                try:
                    response = await client.post(
                        "https://api.mistral.ai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {config.MISTRAL_LLM_API_KEY}"},
                        json={"model": "mistral-large-latest", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError as e:
                    logger.error(f"Error en la API de Mistral para un lote: {e.response.text}")
                    return None # Devolver None para identificar fallos
                except Exception as e:
                    logger.error(f"Error inesperado procesando un lote: {e}", exc_info=True)
                    return None

        # 4. Procesar lotes en paralelo
        start_time_mistral = time.time()
        tasks = [process_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)
        end_time_mistral = time.time()

        all_processed_products = []
        for res in results:
            if res:
                products = parse_mistral_response(res)
                all_processed_products.extend(products)
            else:
                logger.warning("Un lote no pudo ser procesado por la IA.")

        if not all_processed_products:
            return JSONResponse(content={"message": "La IA no encontró productos para procesar.", "raw_ia_response": None}, status_code=200)

        # --- FASE 3: CARGA EN ODOO --- #
        logger.info("Fase 3: Iniciando carga de productos en Odoo.")
        created, failed = [], []
        odoo_product_service = OdooProductService()

        for idx, producto in enumerate(all_processed_products):
            try:
                odoo_dict = odoo_product_service.front_to_odoo_product_dict(producto, proveedor_nombre)
                created_product_id = odoo_product_service.create_or_update_product(odoo_dict)
                if created_product_id:
                    created.append({"idx": idx, "name": odoo_dict.get("name"), "odoo_id": created_product_id})
                else:
                    failed.append({"idx": idx, "name": odoo_dict.get("name"), "error": "No se pudo crear o actualizar en Odoo."})
            except Exception as e:
                logger.error(f"Error procesando producto en Odoo: {producto.get('nombre')}, error: {e}")
                failed.append({"idx": idx, "name": producto.get('nombre'), "error": str(e)})

        logger.info(f"Fase 3: Carga en Odoo completada.")
        total_time = time.time() - start_time

        return {
            "message": "Proceso completado.",
            "proveedor": proveedor_nombre,
            "total_intentados": len(all_processed_products),
            "total_creados_o_actualizados": len(created),
            "total_fallidos": len(failed),
            "productos_creados_o_actualizados": created,
            "productos_fallidos": failed,
            "tiempo_total_segundos": round(total_time, 2),
            "raw_ia_response": None
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"Error en la llamada a Mistral: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Error de la API de Mistral: {e.response.text}")
    except Exception as e:
        logger.error(f"Error en el proceso de importación: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"Archivo temporal '{temp_file_path}' eliminado.")