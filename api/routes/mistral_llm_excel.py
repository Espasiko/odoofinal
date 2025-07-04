from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
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
    Endpoint de prueba: llama a la API de LLM con un prompt fijo y clave real, sin procesar archivos.
    """
    import logging
    from ..utils.mistral_llm_utils import GROQ_API_KEY, GROQ_MODEL
    
    logger = logging.getLogger(__name__)
    
    # Usar Groq en lugar de Mistral ya que tenemos una clave válida
    api_key = GROQ_API_KEY
    if not api_key:
        raise HTTPException(status_code=500, detail="No está configurada la API KEY de Groq")
    
    prompt = "Hola, ¿puedes responder con un JSON de ejemplo de productos?"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",  # Modelo actualizado de Groq
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions",  # URL de Groq
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            return JSONResponse(content=response.json())
    except httpx.HTTPStatusError as e:
        logger.error(f"Error en la llamada a Groq: {e.response.status_code} - {e.response.text}")
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
        
        # Usar la variable config importada al inicio del archivo
        from ..utils.config import config
        from ..utils.mistral_llm_utils import MISTRAL_API_KEY, GROQ_API_KEY
        
        # Verificar que al menos un proveedor LLM tiene clave configurada
        if not (MISTRAL_API_KEY or GROQ_API_KEY):
            raise HTTPException(status_code=500, detail="No hay claves API configuradas para ningún proveedor LLM")

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
        # No importar config de nuevo, ya está importado al principio del archivo
        t_before_llm = time.time()
        
        # Usar el proveedor configurado en .env (por defecto "mistral")
        default_provider = config.LLM_PROVIDER.lower() if hasattr(config, 'LLM_PROVIDER') else "mistral"
        logger.info(f"[PERF] Llamando a {default_provider.upper()}...")
        
        try:
            # Intentar con el proveedor principal configurado
            result = await call_llm(prompt, provider=default_provider)
            logger.info(f"[LLM] Respuesta exitosa de {default_provider.upper()}")
        except HTTPException as he:
            # Si falla con códigos 401, 404, 429, 502, 503, intentar con el proveedor alternativo
            if he.status_code in (401, 404, 429, 502, 503):
                fallback_provider = "groq" if default_provider == "mistral" else "mistral"
                logger.warning(f"{default_provider.upper()} error {he.status_code}, intentando fallback con {fallback_provider.upper()}...")
                try:
                    result = await call_llm(prompt, provider=fallback_provider)
                    logger.info(f"[LLM] Respuesta exitosa del fallback {fallback_provider.upper()}")
                except Exception as e2:
                    logger.error(f"Fallback a {fallback_provider} también falló: {e2}")
                    # Intentar con OpenAI como último recurso si está configurado
                    if config.OPENAI_API_KEY:
                        logger.warning(f"Intentando último fallback con OpenAI...")
                        result = await call_llm(prompt, provider="openai")
                    else:
                        raise e2
            else:
                raise
        t_after_llm = time.time()
        logger.info(f"[PERF] Llamada LLM completada en {t_after_llm - t_before_llm:.2f} s")
        
        # Asegurar que result es un string antes de hacer slicing
        result_str = str(result) if result is not None else ""
        logger.info(f"[LLM RAW FULL] Respuesta completa de LLM: {result_str[:500]}...")
        productos = parse_mistral_response(result)
        logger.info(f"Respuesta parseada con éxito. {len(productos)} productos encontrados.")
        
        # Sanitizar y validar productos
        productos_validos = []
        productos_invalidos = []
        
        for idx, prod in enumerate(productos):
            # Validar campos obligatorios
            nombre = prod.get('nombre') or prod.get('name')
            codigo = prod.get('codigo') or prod.get('default_code') or prod.get('referencia_proveedor')
            
            if not nombre:
                logger.warning(f"Producto {idx} sin nombre, se asignará 'Producto sin nombre'")
                prod['nombre'] = 'Producto sin nombre'
                
            if not codigo:
                logger.warning(f"Producto '{nombre}' sin código, se asignará 'SIN_CODIGO_{idx}'")
                prod['codigo'] = f"SIN_CODIGO_{idx}"
            
            # Sanitizar valores numéricos
            precio_keys = ['precio_venta', 'precio_pvp', 'precio_coste', 'coste', 'pvp']
            for key in precio_keys:
                if key in prod:
                    try:
                        # Convertir a float si es posible, o asignar 0.0
                        if prod[key] is None or prod[key] == '':
                            prod[key] = 0.0
                        else:
                            prod[key] = float(str(prod[key]).replace(',', '.').strip())
                    except (ValueError, TypeError):
                        logger.warning(f"Valor no numérico para '{key}' en producto '{nombre}', se asignará 0.0")
                        prod[key] = 0.0
            
            productos_validos.append(prod)
        
        if not productos_validos:
            return JSONResponse(content=jsonable_encoder({
                "message": "No se encontraron productos válidos en la respuesta de la IA.", 
                "raw_response": result,
                "productos_invalidos": productos_invalidos
            }))

        logger.info(f"[PERF] Iniciando creación de productos en Odoo...")
        t_before_odoo = time.time()
        creados = []
        fallidos = []
        odoo_product_service = OdooProductService()
        
        for idx, producto in enumerate(productos_validos):
            try:
                # Log para depuración
                logger.info(f"Procesando producto {idx}: {producto.get('nombre', 'Sin nombre')}")
                
                # Construir el diccionario de valores para Odoo usando la utilidad centralizada
                product_vals = odoo_product_service.front_to_odoo_product_dict(producto, proveedor_nombre)
                
                # Log para depuración
                logger.info(f"Valores preparados para Odoo: {product_vals}")

                # Asegurar campos mínimos obligatorios
                if 'name' not in product_vals or not product_vals['name']:
                    product_vals['name'] = producto.get('nombre', 'Producto sin nombre')
                if 'default_code' not in product_vals or not product_vals['default_code']:
                    product_vals['default_code'] = producto.get('codigo', f"SIN_CODIGO_{idx}")

                # Valores numéricos seguros
                try:
                    product_vals['list_price'] = float(producto.get('precio_venta', 0.0) or 0.0)
                except (ValueError, TypeError):
                    product_vals['list_price'] = 0.0
                    
                try:
                    product_vals['standard_price'] = float(producto.get('precio_coste', 0.0) or 0.0)
                except (ValueError, TypeError):
                    product_vals['standard_price'] = 0.0
                
                # Crear o actualizar producto en Odoo
                product_id = odoo_product_service.create_or_update_product(product_vals)
                
                if product_id:
                    logger.info(f"Producto creado/actualizado con éxito: ID {product_id}")
                    creados.append({
                        'idx': idx,
                        'name': producto.get('nombre', product_vals.get('name', 'Sin nombre')),
                        'id': product_id,
                        'default_code': product_vals.get('default_code', 'Sin código')
                    })
                else:
                    logger.error(f"No se pudo crear/actualizar el producto '{producto.get('nombre')}' en Odoo")
                    fallidos.append({
                        'idx': idx,
                        'name': producto.get('nombre', product_vals.get('name', 'Sin nombre')),
                        'error': 'No se pudo crear en Odoo',
                        'default_code': product_vals.get('default_code', 'Sin código')
                    })
            except Exception as e:
                logger.error(f"Error al crear producto {producto.get('nombre', 'Sin nombre')}: {e}", exc_info=True)
                fallidos.append({
                    'idx': idx,
                    'name': producto.get('nombre', 'Sin nombre'),
                    'error': str(e),
                    'default_code': producto.get('codigo', f"SIN_CODIGO_{idx}")
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
