#!/usr/bin/env python3
"""
Script para probar la importación del Excel de Nevir a Odoo.
Este script:
1. Lee el Excel de Nevir con la estructura mínima
2. Procesa la hoja DATOS_PROVEEDOR para crear/actualizar el proveedor
3. Procesa la hoja PRODUCTOS para crear/actualizar los productos
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
        logging.FileHandler('test_nevir_import.log')
    ]
)
logger = logging.getLogger("test_nevir_import")

# Importar las funciones necesarias
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.services.odoo_provider_service import OdooProviderService
from api.services.odoo_product_service import OdooProductService
from api.services.product_category_service import find_or_create_category

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
            productos_data.append(producto)
        
        logger.info(f"Datos extraídos: 1 proveedor, {len(productos_data)} productos")
        return proveedor_data, productos_data
    
    except Exception as e:
        logger.error(f"Error al leer el archivo Excel: {str(e)}")
        raise

async def create_or_update_supplier(provider_data: Dict[str, Any]) -> int:
    """Crea o actualiza el proveedor en Odoo"""
    logger.info("=== CREANDO/ACTUALIZANDO PROVEEDOR ===")
    
    try:
        # Inicializar el servicio de proveedores
        provider_service = OdooProviderService()
        
        # Mostrar los datos del proveedor
        logger.info(f"Datos del proveedor: {json.dumps(provider_data, ensure_ascii=False)}")
        
        # Convertir tipos de datos si es necesario
        if 'is_company' in provider_data and isinstance(provider_data['is_company'], str):
            provider_data['is_company'] = provider_data['is_company'].lower() == 'true'
        
        if 'supplier_rank' in provider_data and isinstance(provider_data['supplier_rank'], str):
            provider_data['supplier_rank'] = int(provider_data['supplier_rank'])
        
        if 'customer_rank' in provider_data and isinstance(provider_data['customer_rank'], str):
            provider_data['customer_rank'] = int(provider_data['customer_rank'])
        
        # Buscar si existe el proveedor por VAT (NIF)
        vat = provider_data.get('vat')
        provider_id = None
        
        if vat:
            # Buscar por VAT
            existing_ids = provider_service._execute_kw(
                'res.partner',
                'search',
                [[['vat', '=', vat], ['is_company', '=', True], ['supplier_rank', '>', 0]]],
                {'limit': 1}
            )
            if existing_ids:
                provider_id = existing_ids[0]
                logger.info(f"Proveedor encontrado por VAT con ID: {provider_id}")
        
        # Si no se encontró por VAT, buscar por nombre
        if not provider_id and provider_data.get('name'):
            existing_ids = provider_service._execute_kw(
                'res.partner',
                'search',
                [[['name', '=', provider_data['name']], ['is_company', '=', True], ['supplier_rank', '>', 0]]],
                {'limit': 1}
            )
            if existing_ids:
                provider_id = existing_ids[0]
                logger.info(f"Proveedor encontrado por nombre con ID: {provider_id}")
        
        # Crear o actualizar según corresponda
        if provider_id:
            # Actualizar proveedor existente
            result = provider_service.update_provider(provider_id, provider_data)
            logger.info(f"✅ Proveedor actualizado con ID: {provider_id}")
            return provider_id
        else:
            # Crear nuevo proveedor
            result = provider_service.create_supplier(provider_data)
            if not result:
                logger.error("❌ No se pudo crear el proveedor")
                return None
            
            logger.info(f"✅ Proveedor creado con ID: {result.id}")
            return result.id
    
    except Exception as e:
        logger.error(f"❌ Error al procesar proveedor: {str(e)}")
        return None

async def create_or_update_categories(products: List[Dict[str, Any]]) -> Dict[str, int]:
    """Crea o actualiza las categorías de productos en Odoo"""
    logger.info("=== CREANDO/ACTUALIZANDO CATEGORÍAS ===")
    
    try:
        # Inicializar el servicio de productos (lo usaremos para acceder a Odoo)
        odoo_service = OdooProductService()
        
        # Extraer categorías únicas de los productos
        categories = set()
        for product in products:
            if 'categoria' in product and product['categoria']:
                categories.add(product['categoria'])
        
        # Crear un diccionario para mapear nombres de categorías a IDs
        category_ids = {}
        
        # Procesar cada categoría
        for category_path in categories:
            try:
                # Dividir la ruta de categoría si contiene '/'
                if '/' in category_path:
                    category_parts = category_path.split('/')
                    parent_path = None
                    parent_id = None
                    
                    # Crear cada nivel de categoría
                    for i, part in enumerate(category_parts):
                        current_path = part if i == 0 else f"{parent_path}/{part}"
                        
                        # Crear o actualizar la categoría
                        if parent_id:
                            # Si tiene padre, primero buscamos si ya existe
                            category_ids_search = odoo_service._execute_kw(
                                'product.category',
                                'search',
                                [[('name', '=', part.strip()), ('parent_id', '=', parent_id)]],
                                {'limit': 1}
                            )
                            
                            if category_ids_search:
                                category_id = category_ids_search[0]
                            else:
                                # Crear categoría con padre
                                category_id = odoo_service._execute_kw(
                                    'product.category',
                                    'create',
                                    [{
                                        'name': part.strip(),
                                        'parent_id': parent_id
                                    }]
                                )
                        else:
                            # Categoría de primer nivel
                            category_id = find_or_create_category(odoo_service, part.strip())
                        
                        category_ids[current_path] = category_id
                        parent_id = category_id
                        parent_path = current_path
                else:
                    # Categoría simple sin jerarquía
                    category_id = find_or_create_category(odoo_service, category_path.strip())
                    category_ids[category_path] = category_id
            
            except Exception as e:
                logger.error(f"❌ Error al procesar categoría '{category_path}': {str(e)}")
        
        logger.info(f"✅ {len(category_ids)} categorías creadas/actualizadas")
        return category_ids
    
    except Exception as e:
        logger.error(f"❌ Error al procesar categorías: {str(e)}")
        return {}

async def create_or_update_products(products: List[Dict[str, Any]], provider_id: int, category_ids: Dict[str, int]) -> List[int]:
    """Crea o actualiza los productos en Odoo"""
    logger.info("=== CREANDO/ACTUALIZANDO PRODUCTOS ===")
    
    if not products:
        logger.error("❌ No hay productos para crear")
        return []
    
    odoo_service = OdooProductService()
    productos_creados = 0
    productos_actualizados = 0
    productos_fallidos = 0
    product_ids = []
    
    for producto in products:
        try:
            # Mapear campos del Excel a los campos de Odoo
            odoo_product = {
                'name': producto.get('nombre', ''),
                'default_code': producto.get('referencia_proveedor', ''),
                'type': 'product',  # 'product' para productos almacenables en Odoo 18
                'detailed_type': 'product',
                'barcode': str(producto.get('barcode', '')) if producto.get('barcode') else ''
            }
            
            # Asignar precios
            if 'precio_coste' in producto:
                odoo_product['standard_price'] = float(producto['precio_coste'])
            
            if 'precio_venta' in producto:
                odoo_product['list_price'] = float(producto['precio_venta'])
            
            # Asignar categoría
            if 'categoria' in producto and producto['categoria'] in category_ids:
                odoo_product['categ_id'] = category_ids[producto['categoria']]
            
            # Crear o actualizar el producto
            logger.info(f"Enviando producto a Odoo: {json.dumps(odoo_product, ensure_ascii=False)}")
            product_id, is_new = odoo_service.create_or_update_product(odoo_product)
            
            if product_id:
                product_ids.append(product_id)
                
                # Vincular el producto con el proveedor
                if provider_id:
                    try:
                        # Buscar si ya existe una relación entre este producto y proveedor
                        existing_supplier_info = odoo_service._execute_kw(
                            'product.supplierinfo',
                            'search_read',
                            [[('product_tmpl_id', '=', product_id), ('partner_id', '=', provider_id)]],
                            {'fields': ['id'], 'limit': 1}
                        )
                        
                        supplier_info = {
                            'partner_id': provider_id,  # ID del proveedor (en Odoo 18 se usa partner_id en lugar de name)
                            'product_tmpl_id': product_id,  # ID del producto
                            'product_code': producto.get('referencia_proveedor', ''),  # Código del proveedor para este producto
                            'price': float(producto.get('precio_coste', 0)) if producto.get('precio_coste') else 0.0  # Precio de compra
                        }
                        
                        if existing_supplier_info:
                            # Actualizar la información del proveedor existente
                            supplier_info_id = existing_supplier_info[0]['id']
                            odoo_service._execute_kw('product.supplierinfo', 'write', [[supplier_info_id], supplier_info])
                            logger.info(f"✅ Actualizada vinculación del producto con el proveedor, ID: {supplier_info_id}")
                        else:
                            # Crear nueva información de proveedor
                            supplier_info_id = odoo_service._execute_kw('product.supplierinfo', 'create', [supplier_info])
                            logger.info(f"✅ Producto vinculado al proveedor con ID: {supplier_info_id}")
                    except Exception as e:
                        logger.error(f"❌ Error al vincular producto con proveedor: {str(e)}")
                        # Continuar con el siguiente producto, no es un error crítico
                
                if is_new:
                    productos_creados += 1
                    logger.info(f"✅ Producto creado con ID: {product_id}")
                else:
                    productos_actualizados += 1
                    logger.info(f"✅ Producto actualizado con ID: {product_id}")
            else:
                productos_fallidos += 1
                logger.error(f"❌ Fallo al crear/actualizar producto: {producto.get('nombre', 'Sin nombre')}")
        
        except Exception as e:
            productos_fallidos += 1
            logger.error(f"❌ Error al procesar producto: {str(e)}")
    
    logger.info(f"Resumen: {productos_creados} creados, {productos_actualizados} actualizados, {productos_fallidos} fallidos")
    return product_ids

async def main():
    """Función principal que ejecuta todas las pruebas"""
    logger.info("Iniciando importación de Excel de Nevir")
    
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
        excel_file = "/tmp/nevir_test/NEVIR_TEST.xlsx"
        logger.info(f"Usando archivo Excel por defecto: {excel_file}")
    
    try:
        # Leer el archivo Excel
        provider_data, products_data = read_excel_file(excel_file)
        
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
