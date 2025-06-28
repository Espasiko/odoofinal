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

from fastapi import Query

from fastapi import Form

def slugify(value: str) -> str:
    import re
    value = value.lower()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    value = re.sub(r'-+', '-', value)
    value = value.strip('-')
    return value

@router.post("/process-excel")
async def process_excel_file(
    file: UploadFile = File(...),
    start_row: int = Query(0, description="Fila inicial a procesar"),
    chunk_size: int = Query(25, description="Cantidad de filas a procesar"),
    proveedor: str = Form(None),
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
        # Convertir Excel a texto (chunking)
        excel_text = excel_to_full_text(temp_path, start_row=start_row, chunk_size=chunk_size, only_first_sheet=True)
        prompt = f"""
Procesa toda la información contenida en el siguiente archivo Excel de proveedor (bloque de filas {start_row+1} a {start_row+chunk_size} de la primera hoja para chunking).\nEl archivo contiene varias hojas (productos, ventas, devoluciones, notas, etc.).\nExtrae y estructura en un JSON toda la información útil para la gestión del negocio, incluyendo pero no limitado a:\n\n- Datos del proveedor (si aparecen)\n- Listado de productos, con todos sus campos (código, nombre, descripción, unidades, precios, márgenes, stock, etc.)\n- Ventas, devoluciones, notas, históricos, totales, etc., asociando cada dato a su producto si es posible\n- Cualquier otra información relevante para compras, inventario, contabilidad o análisis\n\nEl texto de cada hoja empieza con '--- HOJA: <nombre> ---'.\nReconoce el contexto de cada hoja y los campos de cada columna, aunque los encabezados cambien o haya celdas vacías.\n\nDevuélveme el resultado en un JSON estructurado por secciones (ejemplo: 'productos', 'ventas', 'devoluciones', 'notas', 'totales', 'otros').\n\nAquí tienes el contenido del archivo:\n\n""" + excel_text
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
                # Determinar el nombre del proveedor (preferencia: parámetro, si no, del nombre del archivo)
                proveedor_nombre = proveedor or None
                if not proveedor_nombre:
                    # Extraer del nombre del archivo (antes del primer guion, punto o espacio)
                    base = os.path.basename(file.filename)
                    proveedor_nombre = base.split('-')[0].split('_')[0].split('.')[0].split()[0]
                proveedor_slug = slugify(proveedor_nombre)
                # Guardar el chunk JSON en la carpeta ordenada
                output_dir = '/home/espasiko/mainmanusodoo/manusodoo-roto/static/uploads/'
                os.makedirs(output_dir, exist_ok=True)
                chunk_filename = f"{proveedor_slug}_chunk_{start_row+1}_{start_row+chunk_size}.json"
                chunk_path = os.path.join(output_dir, chunk_filename)
                with open(chunk_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"[MISTRAL LLM EXCEL] Chunk guardado en: {chunk_path}")

                # --- NUEVO: Procesar productos del JSON y crear en Odoo ---
                # Importar aquí para evitar ciclos y errores de importación
                from ..services.odoo_product_service import OdooProductService, odoo_product_service
                
                
                productos = result.get('productos', [])
                created, failed = [], []
                for idx, producto in enumerate(productos):
                    try:
                        # --- RESOLUCIÓN ROBUSTA DE CATEGORÍA Y PROVEEDOR ---
                        from ..services.odoo_service import odoo_service

                        # 1. Resolver categoría (nombre->ID Odoo)
                        categ_name = producto.get('categoria') or producto.get('category')
                        categ_id = None
                        if categ_name:
                            # Buscar por nombre exacto
                            categ_id = odoo_service.product_service._execute_kw(
                                'product.category', 'search', [[('name', '=', categ_name)]])
                            if categ_id and len(categ_id) > 0:
                                categ_id = categ_id[0]
                            else:
                                # Crear la categoría si no existe
                                categ_id = odoo_service.product_service._execute_kw(
                                    'product.category', 'create', [{'name': categ_name}])
                        # 2. Resolver proveedor (nombre->ID Odoo)
                        proveedor_obj = producto.get('proveedor')
                        supplier_id = None
                        if proveedor_obj:
                            proveedor_name = proveedor_obj.get('nombre') or proveedor_obj.get('name') or proveedor_obj.get('Nombre')
                            if proveedor_name:
                                # Buscar proveedor por nombre exacto
                                prov_ids = odoo_service.provider_service._execute_kw(
                                    'res.partner', 'search', [[('name', '=', proveedor_name), ('supplier_rank', '>', 0)]])
                                if prov_ids and len(prov_ids) > 0:
                                    supplier_id = prov_ids[0]
                                else:
                                    # Crear proveedor si no existe (usando todos los datos disponibles)
                                    prov_vals = {
                                        'name': proveedor_name,
                                        'is_company': True,
                                        'supplier_rank': 1,
                                        'vat': proveedor_obj.get('nif') or proveedor_obj.get('vat'),
                                        'email': proveedor_obj.get('email'),
                                        'phone': proveedor_obj.get('telefono') or proveedor_obj.get('phone'),
                                        'street': proveedor_obj.get('direccion') or proveedor_obj.get('street'),
                                        'city': proveedor_obj.get('ciudad') or proveedor_obj.get('city'),
                                        'zip': proveedor_obj.get('cp') or proveedor_obj.get('zip'),
                                        'comment': proveedor_obj.get('comentario') or proveedor_obj.get('comment'),
                                        'active': True
                                    }
                                    # Limpiar valores None
                                    prov_vals = {k:v for k,v in prov_vals.items() if v}
                                    supplier_id = odoo_service.provider_service._execute_kw(
                                        'res.partner', 'create', [prov_vals])
                        # 3. Mapear datos del JSON a formato Odoo
                        odoo_dict = OdooProductService.front_to_odoo_product_dict(producto)
                        # Sobrescribir categ_id y supplier_id si los resolvimos
                        if categ_id:
                            odoo_dict['categ_id'] = categ_id
                        if supplier_id:
                            odoo_dict['supplier_id'] = supplier_id
                        # Crear producto en Odoo
                        prod = odoo_product_service.create_product(odoo_dict)
                        if prod and getattr(prod, 'id', None):
                            created.append({"idx": idx, "name": odoo_dict.get("name"), "id": prod.id})
                        else:
                            failed.append({"idx": idx, "name": odoo_dict.get("name"), "error": "No se pudo crear"})
                    except Exception as e:
                        failed.append({"idx": idx, "name": producto.get("name") or producto.get("nombre"), "error": str(e)})
                logger.info(f"[MISTRAL LLM EXCEL] Productos creados: {len(created)}, fallidos: {len(failed)}")

                # Devolver feedback extendido
                return JSONResponse(content={
                    "proveedor": proveedor_nombre,
                    "chunk_file": chunk_path,
                    "chunk_filename": chunk_filename,
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
        # Borrar archivo temporal
        try:
            os.remove(temp_path)
        except Exception:
            pass
