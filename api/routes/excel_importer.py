from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import shutil
import os
import logging
import json
import time
import httpx
import asyncio
import datetime

# Definición del encoder para serializar objetos datetime a JSON
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)

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
        
        # Verificar si estamos en modo de prueba (solo procesar la primera página)
        test_mode = os.environ.get('EXCEL_IMPORT_TEST_MODE', 'false').lower() == 'true'
        max_products = int(os.environ.get('EXCEL_IMPORT_MAX_PRODUCTS', '50'))
        
        if test_mode:
            logger.info(f"Modo de prueba activado: procesando solo los primeros {max_products} productos")
            raw_data = raw_data[:max_products]
        
        # Verificar si hay productos sin ID y loguear esta información
        products_without_id = [p for p in raw_data if not any(k.lower() in str(k).lower() and v for k, v in p.items() 
                                                           for id_key in ['id', 'ref', 'código', 'codigo', 'referencia'])]
        if products_without_id:
            logger.warning(f"Se encontraron {len(products_without_id)} productos sin ID o referencia")
            
        chunks = [raw_data[i:i + CHUNK_SIZE] for i in range(0, len(raw_data), CHUNK_SIZE)]
        logger.info(f"Datos divididos en {len(chunks)} lotes de ~{CHUNK_SIZE} productos cada uno.")

        business_rules = preprocessed_data.get("business_rules", {})
        prompt_rules = "\n".join([f'- {k}: {v}' for k, v in business_rules.items()])

        async def process_chunk(chunk):
            # Asegurarse de que los datos son serializables antes de enviarlos
            serializable_chunk = json.loads(json.dumps(chunk, cls=DateTimeEncoder))
            
            prompt = f"""
            Eres un asistente experto en la interpretación de datos de productos para Odoo.
            A continuación, te proporciono una lista de productos extraída de un fichero Excel de un proveedor llamado '{proveedor_nombre}'.

            **Reglas de Negocio Específicas (¡Máxima Prioridad!):**
            {prompt_rules if prompt_rules else 'No se han detectado reglas explícitas. Por favor, infiere la lógica comercial a partir de los datos.'}

            **Datos Crudos del Lote (en formato JSON):**
            {json.dumps(serializable_chunk, indent=2)}

            **Instrucciones:**
            1.  Analiza los datos y las reglas de negocio.
            2.  Limpia y normaliza los datos. Ignora filas vacías o sin información relevante.
            3.  Interpreta los nombres de las columnas aunque no sean estándar (ej. 'COD.', 'P.V.P', 'Ref.').
            4.  Extrae la siguiente información para cada producto:
                -   `nombre`: El nombre del producto.
                -   `referencia_proveedor`: El código o referencia único del producto.
                -   `precio_venta`: El precio de venta al público. Si no está, déjalo en 0.
                -   `precio_coste`: El precio de compra o coste. Si no está, déjalo en 0.
                -   `categoria`: La categoría principal del producto.
                -   `subcategoria`: La subcategoría, si existe.
                -   `descripcion`: Una descripción breve si la hay.
            5.  Asegúrate de mantener los valores exactos de precios y categorías tal como aparecen en los datos crudos, a menos que las reglas de negocio indiquen lo contrario.
            6.  Devuelve el resultado como un array de objetos JSON válido contenido dentro de un objeto JSON principal con la clave 'productos'. Ejemplo:
                ```json
                {{
                    "productos": [
                        {{
                            "nombre": "PRODUCTO EJEMPLO 1",
                            "referencia_proveedor": "REF001",
                            "precio_venta": 99.99,
                            "precio_coste": 79.99,
                            "categoria": "CATEGORIA PRINCIPAL",
                            "subcategoria": "SUBCATEGORIA",
                            "descripcion": "Descripción del producto 1."
                        }}
                    ]
                }}
                ```
            """
            # Usar la función call_llm que implementa el fallback a Groq y OpenAI
            from ..utils.mistral_llm_utils import call_llm
            
            try:
                # Llamar a la función que maneja el fallback automáticamente
                logger.info(f"Llamando a LLM para procesar un lote de productos")
                response = await call_llm(prompt)
                if response:
                    logger.info(f"Respuesta exitosa del LLM")
                    return response
                else:
                    logger.error(f"No se recibió respuesta del LLM")
                    return None
            except Exception as e:
                logger.error(f"Error al llamar al LLM: {str(e)}", exc_info=True)
                return None

        # 4. Procesar lotes en paralelo con reintento y espera
        start_time_mistral = time.time()
        
        # Procesamos los chunks con reintento y espera entre lotes para evitar límites de API
        results = []
        max_retries = int(os.environ.get('EXCEL_IMPORT_MAX_RETRIES', '2'))
        max_chunks = int(os.environ.get('EXCEL_IMPORT_MAX_CHUNKS', '10'))
        
        # Limitar el número de chunks a procesar para evitar bucles infinitos
        if len(chunks) > max_chunks:
            logger.warning(f"Limitando procesamiento a los primeros {max_chunks} lotes de un total de {len(chunks)}")
            chunks = chunks[:max_chunks]
        
        for i, chunk in enumerate(chunks):
            retry_count = 0
            chunk_success = False
            
            while not chunk_success and retry_count < max_retries:
                try:
                    logger.info(f"Procesando lote {i+1}/{len(chunks)} (intento {retry_count+1}/{max_retries})")
                    
                    # Verificar si hay productos sin ID en este chunk
                    products_without_id = [p for p in chunk if not any(k.lower() in str(k).lower() and v for k, v in p.items() 
                                                                for id_key in ['id', 'ref', 'código', 'codigo', 'referencia'])]
                    if products_without_id:
                        logger.warning(f"Lote {i+1}: {len(products_without_id)} de {len(chunk)} productos sin ID")
                    
                    result = await process_chunk(chunk)
                    results.append(result)
                    chunk_success = True
                    
                    if i < len(chunks) - 1:
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    retry_count += 1
                    logger.error(f"Error procesando lote {i+1} (intento {retry_count}/{max_retries}): {str(e)}")
                    if retry_count >= max_retries:
                        logger.error(f"Se alcanzó el máximo de intentos para el lote {i+1}. Continuando con el siguiente lote.")
                        results.append(None)
        
        end_time_mistral = time.time()

        all_processed_products = []
        raw_ia_responses = []
        for res in results:
            if res:
                raw_ia_responses.append(res) # Capturamos la respuesta cruda
                products = parse_mistral_response(res)
                all_processed_products.extend(products)
            else:
                logger.warning("Un lote no pudo ser procesado por la IA.")

        try:
            logger.info(f"Respuesta completa de la IA (agregada): {json.dumps(raw_ia_responses, indent=2, cls=DateTimeEncoder)}")
        except Exception as e:
            logger.error(f"Error al serializar respuesta de IA: {str(e)}")



        if not all_processed_products:
            return JSONResponse(content={"message": "La IA no encontró productos para procesar.", "raw_ia_response": None}, status_code=200)

        # --- FASE 3: CARGA EN ODOO --- #
        logger.info("Fase 3: Iniciando carga de productos en Odoo.")
        odoo_service = OdooProductService()
        productos_cargados = 0
        productos_fallidos = 0
        productos_creados = []
        productos_fallidos_lista = []
        
        # Log detallado de los datos recibidos para carga
        logger.info(f"Datos para cargar en Odoo: {all_processed_products}")
        
        for idx, producto in enumerate(all_processed_products):
            try:
                # Log detallado de cada producto antes de cargar
                nombre_producto = producto.get('nombre', producto.get('name', 'Sin nombre'))
                precio_venta = producto.get('precio_venta', producto.get('list_price', 0.0))
                precio_coste = producto.get('precio_coste', producto.get('standard_price', 0.0))
                categoria = producto.get('categoria', producto.get('category', 'Sin categoría'))
                
                # Manejar la categoría correctamente usando find_or_create_category
                if categoria and categoria not in ('Sin categoría', 'Sin categoria'):
                    from api.services.product_category_service import find_or_create_category
                    try:
                        categ_id = find_or_create_category(odoo_service, categoria)
                        if categ_id:
                            producto['categ_id'] = categ_id
                            logger.info(f"Categoría '{categoria}' asignada con ID: {categ_id}")
                    except Exception as cat_error:
                        logger.error(f"Error al procesar categoría '{categoria}': {str(cat_error)}")
                        # Usar categoría por defecto (All - ID 1)
                        producto['categ_id'] = 1
                else:
                    # Usar categoría por defecto (All - ID 1)
                    producto['categ_id'] = 1
                    
                # Eliminar campos de categoría que no son válidos para Odoo
                if 'categoria' in producto:
                    del producto['categoria']
                if 'category' in producto:
                    del producto['category']
                if 'subcategoria' in producto:
                    del producto['subcategoria']
                
                logger.info(f"Cargando producto: {nombre_producto} con precio_venta: {precio_venta}, precio_coste: {precio_coste}, categoria: {categoria}, categ_id: {producto.get('categ_id', 1)}")
                
                
                # Verificar campos obligatorios y referencias
                if not nombre_producto or nombre_producto == 'Sin nombre':
                    raise ValueError("El producto debe tener un nombre válido")
                
                # Verificar si el producto tiene alguna referencia o ID
                tiene_referencia = False
                for key in ['referencia_proveedor', 'default_code', 'barcode', 'ean13', 'codigo', 'ref']:
                    if key in producto and producto[key]:
                        tiene_referencia = True
                        logger.info(f"Producto {nombre_producto} tiene referencia: {key}={producto[key]}")
                        break
                
                if not tiene_referencia:
                    logger.warning(f"Producto {nombre_producto} no tiene ninguna referencia o ID. Esto podría causar duplicados.")
                    # Generar una referencia basada en el nombre para evitar duplicados
                    import hashlib
                    hash_obj = hashlib.md5(nombre_producto.encode())
                    producto['default_code'] = f"AUTO-{hash_obj.hexdigest()[:8]}"
                    logger.info(f"Generada referencia automática: {producto['default_code']}")
                    tiene_referencia = True
                
                # Asegurar que el campo 'name' siempre esté presente
                if 'name' not in producto or not producto['name']:
                    if 'nombre' in producto and producto['nombre']:
                        producto['name'] = producto['nombre']
                        logger.info(f"Campo 'name' asignado desde 'nombre': {producto['name']}")
                    else:
                        producto['name'] = "Producto sin nombre"
                        logger.warning(f"Asignando nombre genérico a producto sin nombre: {producto['name']}")
                
                # Asegurar que type sea 'consu' para productos físicos en Odoo 18
                # En Odoo 18, solo se usa el campo 'type' y no 'detailed_type'
                producto['type'] = 'consu'
                
                # Asegurar que el código de barras siempre sea una cadena de texto
                # Esto evita el error OverflowError: int exceeds XML-RPC limits
                if 'barcode' in producto and producto['barcode'] is not None:
                    producto['barcode'] = str(producto['barcode'])
                    logger.info(f"Código de barras convertido a cadena: {producto['barcode']}")
                    
                # También manejar posibles campos alternativos de códigos de barras
                for barcode_field in ['ean13', 'codigo_barras']:
                    if barcode_field in producto and producto[barcode_field] is not None:
                        producto['barcode'] = str(producto[barcode_field])
                        logger.info(f"Campo {barcode_field} convertido a cadena y asignado a barcode: {producto['barcode']}")
                        break
                
                # Verificar y convertir precios si existen
                if 'precio_venta' in producto and producto['precio_venta']:
                    try:
                        producto['list_price'] = float(producto['precio_venta'])
                        logger.info(f"Precio de venta convertido: {producto['list_price']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error al convertir precio_venta: {e}")
                
                if 'precio_coste' in producto and producto['precio_coste']:
                    try:
                        producto['standard_price'] = float(producto['precio_coste'])
                        logger.info(f"Precio de coste convertido: {producto['standard_price']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error al convertir precio_coste: {e}")
                
                try:
                    # Intentar crear o actualizar el producto en Odoo
                    logger.info(f"Enviando producto a Odoo: {producto}")
                    product_id, is_new = odoo_service.create_or_update_product(producto)
                    
                    if product_id:
                        productos_cargados += 1
                        productos_creados.append({
                            "idx": idx,
                            "name": nombre_producto,
                            "id": product_id,
                            "is_new": is_new
                        })
                        logger.info(f"Producto {nombre_producto} {'creado' if is_new else 'actualizado'} con ID: {product_id}")
                    else:
                        productos_fallidos += 1
                        productos_fallidos_lista.append({"idx": idx, "name": nombre_producto, "error": "ID nulo devuelto"})
                        logger.warning(f"Fallo al cargar producto '{nombre_producto}': ID nulo devuelto")
                except Exception as odoo_error:
                    logger.error(f"Error al crear producto {nombre_producto} en Odoo: {str(odoo_error)}")
                    productos_fallidos += 1
                    productos_fallidos_lista.append({"idx": idx, "name": nombre_producto, "error": f"Error en Odoo: {str(odoo_error)}"})
            except Exception as e:
                nombre_producto = producto.get('nombre', producto.get('name', 'Sin nombre'))
                logger.error(f"Error general al procesar producto {nombre_producto}: {str(e)}")
                productos_fallidos_lista.append({"idx": idx, "name": nombre_producto, "error": f"Error general: {str(e)}"})
                productos_fallidos += 1
        
        logger.info(f"Fase 3: Carga completada. Productos cargados: {productos_cargados}, fallidos: {productos_fallidos}")
        total_time = time.time() - start_time

        try:
            serializable_responses = json.loads(json.dumps(raw_ia_responses, cls=DateTimeEncoder))
            
            return {
                "message": f"Importación completada. {productos_cargados} productos creados o actualizados, {productos_fallidos} fallidos.",
                "total_intentados": len(all_processed_products),
                "total_creados_o_actualizados": productos_cargados,
                "total_fallidos": productos_fallidos,
                "productos_creados_o_actualizados": productos_creados,
                "productos_fallidos": productos_fallidos_lista,
                "tiempo_total_segundos": round(total_time, 2),
                "raw_ia_response": serializable_responses
            }
        except Exception as e:
            logger.error(f"Error al preparar respuesta final: {str(e)}")
            # Devolver respuesta sin raw_ia_response en caso de error
            return {
                "message": f"Importación completada con errores de serialización. {productos_cargados} productos creados o actualizados, {productos_fallidos} fallidos.",
                "total_intentados": len(all_processed_products),
                "total_creados_o_actualizados": productos_cargados,
                "total_fallidos": productos_fallidos,
                "productos_creados_o_actualizados": productos_creados,
                "productos_fallidos": productos_fallidos_lista,
                "tiempo_total_segundos": round(total_time, 2),
                "error_serializacion": str(e)
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