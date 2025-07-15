#!/usr/bin/env python3
"""
Script para probar la importación del Excel de Nevir a Odoo con integración de IA.
Este script:
1. Lee el Excel de Nevir con la estructura mínima
2. Procesa los datos con IA para validar y enriquecer la información
3. Procesa la hoja DATOS_PROVEEDOR para crear/actualizar el proveedor
4. Procesa la hoja PRODUCTOS para crear/actualizar los productos
"""
import asyncio
import logging
import json
import os
import sys
import pandas as pd
from typing import Dict, Any, List, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_nevir_import_ai.log')
    ]
)
logger = logging.getLogger("test_nevir_import_ai")

# Importar las funciones necesarias
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.services.odoo_provider_service import OdooProviderService
from api.services.odoo_product_service import OdooProductService
from api.services.product_category_service import find_or_create_category
from api.services.mistral_llm_odoo_mapper import map_llm_json_to_odoo, merge_chunked_llm_jsons

def read_excel_file(file_path: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Lee el archivo Excel y extrae los datos del proveedor y los productos"""
    logger.info(f"Leyendo archivo Excel: {file_path}")
    
    try:
        # Leer la hoja DATOS_PROVEEDOR
        df_proveedor = pd.read_excel(file_path, sheet_name='DATOS_PROVEEDOR')
        proveedor_data = {}
        
        # Convertir el DataFrame a un diccionario
        for _, row in df_proveedor.iterrows():
            campo = row['campo']
            valor = row['valor']
            if pd.notna(valor):  # Solo incluir valores no nulos
                proveedor_data[campo] = valor
        
        # Leer la hoja PRODUCTOS
        df_productos = pd.read_excel(file_path, sheet_name='PRODUCTOS')
        productos_data = []
        
        # Convertir el DataFrame a una lista de diccionarios
        for _, row in df_productos.iterrows():
            producto = {}
            for column in df_productos.columns:
                if pd.notna(row[column]):  # Solo incluir valores no nulos
                    producto[column.lower()] = row[column]
            if producto:  # Solo incluir productos con datos
                productos_data.append(producto)
        
        logger.info(f"Datos extraídos: 1 proveedor, {len(productos_data)} productos")
        return proveedor_data, productos_data
    
    except Exception as e:
        logger.error(f"Error al leer el archivo Excel: {str(e)}")
        return {}, []

async def process_data_with_ai(provider_data: Dict[str, Any], products_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Procesa los datos con IA para validar y enriquecer la información.
    Simula la llamada a Mistral LLM para procesar los datos.
    """
    logger.info("Procesando datos con IA para validación y enriquecimiento")
    
    # Crear estructura para Mistral LLM
    ai_input = {
        "proveedor": provider_data,
        "productos": []
    }
    
    # Mapear productos al formato esperado por la IA
    for producto in products_data:
        ai_producto = {
            "codigo": producto.get("referencia") or producto.get("default_code"),
            "nombre": producto.get("name") or producto.get("nombre"),
            "descripcion": producto.get("descripcion"),
            "categoria": producto.get("categoria"),
            "precio_coste": float(producto.get("precio_coste") or 0),
            "pvp_final_cliente": float(producto.get("precio_venta") or producto.get("list_price") or 0),
            "barcode": producto.get("barcode") or producto.get("ean13")
        }
        ai_input["productos"].append(ai_producto)
    
    # Simulación de procesamiento con IA
    logger.info("Simulando llamada a Mistral LLM para procesamiento de datos")
    
    # En un caso real, aquí llamaríamos a la API de Mistral
    # Por ahora, simplemente enriquecemos los datos con información adicional
    
    for producto in ai_input["productos"]:
        # Asegurar que todos los productos tengan categoría
        if not producto.get("categoria"):
            # Inferir categoría basada en el nombre o código
            nombre = producto.get("nombre", "").lower()
            codigo = producto.get("codigo", "").lower()
            
            if "tv" in nombre or "tele" in nombre or "televisor" in codigo:
                producto["categoria"] = "Electrónica/Televisores"
            elif "lavadora" in nombre or "lavarropas" in codigo:
                producto["categoria"] = "Electrodomésticos/Lavadoras"
            elif "frigo" in nombre or "refri" in codigo or "nevera" in nombre:
                producto["categoria"] = "Electrodomésticos/Refrigeración"
            elif "horno" in nombre or "cocina" in codigo:
                producto["categoria"] = "Electrodomésticos/Hornos"
            elif "micro" in nombre or "microondas" in codigo:
                producto["categoria"] = "Electrodomésticos/Microondas"
            elif "radio" in nombre or "audio" in codigo or "sonido" in nombre:
                producto["categoria"] = "Electrónica/Audio"
            else:
                producto["categoria"] = "Sin Categoría"
        
        # Calcular margen si no existe
        if not producto.get("margen"):
            pvp = producto.get("pvp_final_cliente", 0)
            coste = producto.get("precio_coste", 0)
            if coste > 0 and pvp > 0:
                margen = (pvp - coste) / pvp * 100
                producto["margen"] = round(margen, 2)
        
        # Generar descripción mejorada si es muy corta
        descripcion = producto.get("descripcion", "")
        if len(descripcion) < 10 and producto.get("nombre"):
            nombre = producto.get("nombre")
            producto["descripcion"] = f"Producto {nombre} de la marca NEVIR. Alta calidad y rendimiento."
    
    # Simular respuesta de Mistral LLM
    ai_output = {
        "proveedor": ai_input["proveedor"],
        "productos": ai_input["productos"]
    }
    
    logger.info(f"IA ha procesado {len(ai_output['productos'])} productos")
    return ai_output

async def create_or_update_supplier(provider_data: Dict[str, Any]) -> int:
    """Crea o actualiza el proveedor en Odoo"""
    logger.info("=== CREANDO/ACTUALIZANDO PROVEEDOR ===")
    logger.info(f"Datos del proveedor: {provider_data}")
    
    try:
        # Inicializar el servicio de proveedores
        provider_service = OdooProviderService()
        
        # Buscar proveedor por nombre
        provider_name = provider_data.get('name')
        if not provider_name:
            logger.error("No se encontró el nombre del proveedor en los datos")
            return None
        
        # Buscar proveedor existente
        existing_providers = await provider_service.search_providers_by_name(provider_name)
        
        if existing_providers:
            provider_id = existing_providers[0]
            logger.info(f"Proveedor encontrado con ID: {provider_id}")
            
            # Actualizar datos del proveedor
            update_data = {}
            for field, value in provider_data.items():
                if field != 'name' and value:  # No actualizar el nombre
                    update_data[field] = value
            
            if update_data:
                await provider_service.update_provider(provider_id, update_data)
                logger.info(f"✅ Proveedor actualizado con ID: {provider_id}")
            else:
                logger.info(f"ℹ️ No hay datos nuevos para actualizar el proveedor")
            
            return provider_id
        else:
            # Crear nuevo proveedor
            provider_id = await provider_service.create_provider(provider_data)
            logger.info(f"✅ Proveedor creado con ID: {provider_id}")
            return provider_id
    
    except Exception as e:
        logger.error(f"Error al crear/actualizar proveedor: {str(e)}")
        return None

async def create_or_update_categories(products: List[Dict[str, Any]]) -> Dict[str, int]:
    """Crea o actualiza las categorías de productos en Odoo"""
    logger.info("=== CREANDO/ACTUALIZANDO CATEGORÍAS ===")
    
    # Extraer categorías únicas de los productos
    categories = {}
    for product in products:
        category = product.get('categoria')
        if category and '/' in category:
            parent, child = category.split('/', 1)
            if parent not in categories:
                categories[parent] = set()
            categories[parent].add(child)
    
    # Crear o actualizar categorías en Odoo
    category_ids = {}
    try:
        for parent, children in categories.items():
            # Crear o buscar categoría padre
            parent_id = await find_or_create_category(parent)
            category_ids[parent] = parent_id
            logger.info(f"Categoría '{parent}' encontrada con ID: {parent_id}")
            
            # Crear o buscar categorías hijas
            for child in children:
                child_id = await find_or_create_category(child, parent_id)
                category_ids[f"{parent}/{child}"] = child_id
                logger.info(f"Categoría '{parent}/{child}' encontrada con ID: {child_id}")
        
        logger.info(f"✅ {len(category_ids)} categorías creadas/actualizadas")
        return category_ids
    
    except Exception as e:
        logger.error(f"Error al crear/actualizar categorías: {str(e)}")
        return {}

async def create_or_update_products(products: List[Dict[str, Any]], provider_id: int, category_ids: Dict[str, int]) -> List[int]:
    """Crea o actualiza los productos en Odoo"""
    logger.info("=== CREANDO/ACTUALIZANDO PRODUCTOS ===")
    
    # Inicializar el servicio de productos
    product_service = OdooProductService()
    
    product_ids = []
    created_count = 0
    updated_count = 0
    failed_count = 0
    
    for producto in products:
        try:
            # Preparar datos del producto para Odoo
            product_data = {
                "name": producto.get("nombre") or producto.get("descripcion"),
                "default_code": producto.get("codigo"),
                "type": "product",  # Almacenable
                "detailed_type": "product",  # Almacenable
                "barcode": str(producto.get("barcode") or ""),
                "standard_price": float(producto.get("precio_coste") or 0),
                "list_price": float(producto.get("pvp_final_cliente") or 0)
            }
            
            # Asignar categoría
            category = producto.get("categoria")
            if category and category in category_ids:
                product_data["categ_id"] = category_ids[category]
            
            logger.info(f"Enviando producto a Odoo: {json.dumps(product_data)}")
            
            # Buscar producto existente
            existing_product = await product_service.find_product_by_code(product_data["default_code"])
            
            if existing_product:
                # Actualizar producto existente
                product_id = existing_product["id"]
                await product_service.update_product(product_id, product_data)
                logger.info(f"✅ Producto actualizado con ID: {product_id}")
                
                # Vincular producto con proveedor
                success = await link_product_supplier(
                    product_service,
                    product_id,
                    provider_id,
                    product_data["default_code"],
                    product_data["standard_price"]
                )
                
                if success:
                    logger.info(f"✅ Actualizada vinculación del producto con el proveedor, ID: {product_id}")
                else:
                    logger.error(f"❌ Error al vincular producto con proveedor, ID: {product_id}")
                
                product_ids.append(product_id)
                updated_count += 1
            else:
                # Crear nuevo producto
                product_id = await product_service.create_product(product_data)
                logger.info(f"✅ Producto creado con ID: {product_id}")
                
                # Vincular producto con proveedor
                success = await link_product_supplier(
                    product_service,
                    product_id,
                    provider_id,
                    product_data["default_code"],
                    product_data["standard_price"]
                )
                
                if success:
                    logger.info(f"✅ Creada vinculación del producto con el proveedor, ID: {product_id}")
                else:
                    logger.error(f"❌ Error al vincular producto con proveedor, ID: {product_id}")
                
                product_ids.append(product_id)
                created_count += 1
        
        except Exception as e:
            logger.error(f"Error al crear/actualizar producto: {str(e)}")
            failed_count += 1
    
    logger.info(f"Resumen: {created_count} creados, {updated_count} actualizados, {failed_count} fallidos")
    return product_ids

async def link_product_supplier(service, product_id, supplier_id, supplier_code=None, supplier_price=None) -> bool:
    """Vincula un producto con un proveedor en Odoo"""
    try:
        seller_ids = service._execute_kw(
            'product.supplierinfo',
            'search',
            [[('product_tmpl_id', '=', product_id), ('partner_id', '=', supplier_id)]],
            {'limit': 1}
        )
        vals = {
            'product_tmpl_id': product_id,
            'partner_id': supplier_id,
        }
        if supplier_code:
            vals['product_code'] = supplier_code
        if supplier_price:
            vals['price'] = float(supplier_price)
        if seller_ids:
            service._execute_kw('product.supplierinfo', 'write', [seller_ids[0], vals])
        else:
            service._execute_kw('product.supplierinfo', 'create', [vals])
        return True
    except Exception as e:
        logging.error(f"Error al vincular producto {product_id} con proveedor {supplier_id}: {str(e)}")
        return False

async def main():
    """Función principal que ejecuta todas las pruebas"""
    logger.info("Iniciando importación de Excel de Nevir con IA")
    
    # Configurar la URL de Odoo para pruebas locales
    from api.utils.config import config
    config.set_odoo_config({
        "url": "http://localhost:8069",
        "db": "fresh_odoo_db",
        "username": "admin",
        "password": "admin"
    })
    logger.info(f"Configuración de Odoo establecida: URL=http://localhost:8069")
    
    # Ruta al archivo Excel
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
        logger.info(f"Usando archivo Excel proporcionado: {excel_file}")
    else:
        excel_file = "/home/espasiko/mainmanusodoo/manusodoo-roto/NEVIR_IMPORT.xlsx"
        logger.info(f"Usando archivo Excel por defecto: {excel_file}")
    
    try:
        # Leer el archivo Excel
        provider_data, products_data = read_excel_file(excel_file)
        
        # Procesar datos con IA
        ai_processed_data = await process_data_with_ai(provider_data, products_data)
        
        # Extraer datos procesados
        provider_data = ai_processed_data["proveedor"]
        products_data = ai_processed_data["productos"]
        
        # Crear o actualizar el proveedor
        provider_id = await create_or_update_supplier(provider_data)
        
        if provider_id:
            # Crear o actualizar las categorías
            category_ids = await create_or_update_categories(products_data)
            
            # Crear o actualizar los productos
            product_ids = await create_or_update_products(products_data, provider_id, category_ids)
            
            logger.info(f"Importación completada: {len(product_ids)} productos procesados")
        else:
            logger.error("No se pudo crear/actualizar el proveedor, abortando importación")
    
    except Exception as e:
        logger.error(f"Error en la importación: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
