#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xmlrpc.client
import json
import re
import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

def extract_product_name(product_name_data: Any) -> str:
    """
    Extrae el nombre del producto de diferentes formatos posibles.
    
    Args:
        product_name_data: Nombre del producto (puede ser string, dict, JSON string)
        
    Returns:
        Nombre del producto como string
    """
    if not product_name_data:
        return ""
        
    # Si es un string normal, devolverlo directamente
    if isinstance(product_name_data, str):
        # Verificar si es un JSON string
        if product_name_data.startswith('{') and product_name_data.endswith('}'):
            try:
                data = json.loads(product_name_data)
                # Intentar obtener el nombre en español o inglés
                if isinstance(data, dict):
                    return data.get('es_ES', '') or data.get('en_US', '')
            except json.JSONDecodeError:
                return product_name_data
        return product_name_data
        
    # Si es un diccionario
    if isinstance(product_name_data, dict):
        return product_name_data.get('es_ES', '') or product_name_data.get('en_US', '')
        
    # Si no podemos procesarlo, convertirlo a string
    return str(product_name_data)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de conexión a Odoo
ODOO_URL = "http://localhost:8069"
ODOO_DB = "manus_odoo-bd"
ODOO_USERNAME = "yo@mail.com"
ODOO_PASSWORD = "admin"

# Mapeo de palabras clave a categorías
# Formato: {"palabra_clave": (id_categoria, nombre_categoria)}
KEYWORD_TO_CATEGORY = {
    # Electrodomésticos de cocina
    "microondas": (39, "Microondas"),
    "horno": (33, "Hornos"),
    "frigorifico": (37, "Frigoríficos"),
    "frigorífico": (37, "Frigoríficos"),
    "frigo": (37, "Frigoríficos"),
    "2pta": (37, "Frigoríficos"),
    "nevera": (37, "Frigoríficos"),
    "combi": (37, "Frigoríficos"),
    "cafetera": (126, "Cafeteras"),
    "café": (126, "Cafeteras"),
    "expresso": (126, "Cafeteras"),
    "batidora": (117, "BATIDORAS MANO"),
    "picadora": (117, "BATIDORAS MANO"),
    "exprimidor": (119, "EXPRIMIDOR"),
    "freidora": (120, "FREIDORAS"),
    "vitro": (103, "Placas de inducción"),
    "induccion": (103, "Placas de inducción"),
    "placa": (103, "Placas de inducción"),
    "encimera": (103, "Placas de inducción"),
    "cocina": (103, "Placas de inducción"),
    "tostador": (135, "OTROS"),
    "tostadora": (135, "OTROS"),
    "envasadora": (135, "OTROS"),
    "campana": (127, "Campanas"),
    
    # Lavado y secado
    "lavadora": (40, "Lavadoras"),
    "secadora": (43, "Secadora"),
    "lavavajillas": (46, "Lavavajillas"),
    
    # Climatización
    "ventilador": (81, "Ventiladores"),
    "aire acondicionado": (115, "A/A"),
    "a/a": (115, "A/A"),
    "inverter": (115, "A/A"),
    "split": (115, "A/A"),
    "calefactor": (20, "CALEFACCIÓN"),
    "calefaccion": (20, "CALEFACCIÓN"),
    "radiador": (20, "CALEFACCIÓN"),
    
    # Congeladores
    "congelador": (38, "CONGELADOR"),
    "congeladores": (38, "CONGELADOR"),
    "arca": (38, "CONGELADOR"),
    "arcon": (38, "CONGELADOR"),
    
    # Cuidado personal
    "secador": (135, "OTROS"),
    "pelo": (135, "OTROS"),
    "cepillo": (135, "OTROS"),
    "dientes": (135, "OTROS"),
    "cortapelo": (135, "OTROS"),
    "afeitadora": (135, "OTROS"),
    
    # Electrónica
    "altavoz": (135, "OTROS"),
    "tv": (135, "OTROS"),
    "televisor": (135, "OTROS"),
    "soporte": (135, "OTROS"),
    
    # Herramientas
    "taladro": (135, "OTROS"),
    "martillo": (135, "OTROS"),
    "alicate": (135, "OTROS"),
    "bateria": (135, "OTROS"),
    "sierra": (135, "OTROS"),
    "amoladora": (135, "OTROS"),
    
    # Otros
    "plancha": (132, "PLANCHAS-ROPA"),
    "jardin": (138, "JARDIN"),
    "lampara": (134, "LUZ"),
    "luz": (134, "LUZ"),
    "led": (134, "LUZ"),
    "guirnalda": (134, "LUZ"),
    "cable": (135, "OTROS"),
    "alargo": (135, "OTROS"),
    "pizzapan": (103, "Placas de inducción"),
}

# Mapeo de proveedores a categorías por defecto
SUPPLIER_TO_DEFAULT_CATEGORY = {
    "ORBEGOZO": (135, "OTROS"),
    "BECKEN": (135, "OTROS"),
    "TEGALUXE": (135, "OTROS"),
    "UFESA": (135, "OTROS"),
}

def infer_category_from_name(product_name: Any) -> Optional[Tuple[int, str]]:
    """
    Infiere la categoría basada en palabras clave en el nombre del producto.
    
    Args:
        product_name: Nombre del producto (puede ser string, dict, JSON string)
        
    Returns:
        Tuple con (id_categoria, nombre_categoria) o None si no se encuentra coincidencia
    """
    # Extraer el nombre del producto como string
    name_str = extract_product_name(product_name)
    
    if not name_str:
        return None
        
    # Convertir a minúsculas para comparación
    name_lower = name_str.lower()
    
    # Buscar palabras clave en el nombre
    for keyword, category in KEYWORD_TO_CATEGORY.items():
        if keyword.lower() in name_lower:
            return category
            
    return None

def get_category_for_product(product_name: Any, supplier_name: Optional[str] = None) -> Optional[int]:
    """
    Determina la categoría más apropiada para un producto basado en su nombre y proveedor.
    
    Args:
        product_name: Nombre del producto
        supplier_name: Nombre del proveedor (opcional)
        
    Returns:
        ID de la categoría o None si no se puede determinar
    """
    # Primero intentar inferir por nombre del producto
    category = infer_category_from_name(product_name)
    
    # Si no se encuentra por nombre y hay proveedor, usar categoría por defecto del proveedor
    if not category and supplier_name:
        supplier_name_upper = supplier_name.upper()
        for supplier_key, default_category in SUPPLIER_TO_DEFAULT_CATEGORY.items():
            if supplier_key in supplier_name_upper:
                category = default_category
                break
    
    # Devolver el ID de categoría si se encontró, o None si no
    return category[0] if category else None

def connect_to_odoo():
    """Establece conexión con Odoo vía XML-RPC"""
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
    
    if not uid:
        raise Exception("Error de autenticación con Odoo")
        
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    return models, uid

def get_category_distribution(models, uid):
    """Obtiene la distribución de productos por categoría"""
    category_counts = defaultdict(int)
    
    # Obtener todas las categorías
    category_ids = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.category', 'search_read',
        [[]], {'fields': ['id', 'name']}
    )
    
    category_map = {cat['id']: cat['name'] for cat in category_ids}
    
    # Contar productos por categoría
    for cat_id, cat_name in category_map.items():
        product_count = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'search_count',
            [[('categ_id', '=', cat_id)]]
        )
        if product_count > 0:
            category_counts[cat_name] = product_count
            
    return category_counts

def get_products_in_all_category(models, uid):
    """Obtiene todos los productos en la categoría 'All'"""
    return models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.template', 'search_read',
        [[('categ_id', '=', 1)]],
        {'fields': ['id', 'name', 'seller_ids']}
    )

def get_supplier_name(models, uid, seller_id):
    """Obtiene el nombre del proveedor a partir del ID de seller_ids"""
    if not seller_id:
        return None
        
    try:
        # Primero obtenemos el partner_id del proveedor
        supplier = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.supplierinfo', 'read',
            [seller_id], {'fields': ['partner_id']}
        )
        
        if supplier and supplier[0]['partner_id']:
            # Luego obtenemos el nombre del partner
            partner = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'res.partner', 'read',
                [supplier[0]['partner_id'][0]], {'fields': ['name']}
            )
            return partner[0]['name'] if partner else None
    except Exception as e:
        logger.error(f"Error al obtener nombre del proveedor: {str(e)}")
    
    return None

def recategorize_products():
    """Recategoriza productos desde 'All' a categorías específicas"""
    models, uid = connect_to_odoo()
    
    # Obtener distribución inicial de categorías
    logger.info("Distribución inicial de productos por categoría:")
    initial_distribution = get_category_distribution(models, uid)
    for cat_name, count in sorted(initial_distribution.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {cat_name}: {count} productos")
    
    # Obtener productos en categoría 'All'
    all_products = get_products_in_all_category(models, uid)
    logger.info(f"Encontrados {len(all_products)} productos en categoría 'All'")
    
    # Estadísticas
    stats = {
        'updated': 0,
        'skipped': 0,
        'errors': 0,
        'no_name': 0,
        'categories': defaultdict(int)
    }
    
    # Procesar cada producto
    for product in all_products:
        product_id = product['id']
        product_name_data = product['name']
        
        # Extraer nombre del producto
        product_name = extract_product_name(product_name_data)
        
        if not product_name or product_name == "Producto sin nombre":
            logger.warning(f"Producto ID {product_id} sin nombre válido: {product_name_data}")
            stats['no_name'] += 1
            continue
            
        # Obtener proveedor si existe
        supplier_name = None
        if product['seller_ids']:
            supplier_name = get_supplier_name(models, uid, product['seller_ids'][0])
            
        # Inferir categoría
        new_category_id = get_category_for_product(product_name, supplier_name)
        
        if new_category_id and new_category_id != 1:  # Si se encontró una categoría diferente de 'All'
            try:
                # Actualizar categoría del producto
                models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'product.template', 'write',
                    [[product_id], {'categ_id': new_category_id}]
                )
                
                # Obtener nombre de la categoría
                category = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'product.category', 'read',
                    [new_category_id], {'fields': ['name']}
                )
                category_name = category[0]['name'] if category else f"ID: {new_category_id}"
                
                logger.info(f"Producto '{product_name}' (ID: {product_id}) recategorizado a '{category_name}'")
                stats['updated'] += 1
                stats['categories'][category_name] += 1
                
            except Exception as e:
                logger.error(f"Error al actualizar producto ID {product_id}: {str(e)}")
                stats['errors'] += 1
        else:
            logger.info(f"Producto '{product_name}' (ID: {product_id}) se mantiene en 'All'")
            stats['skipped'] += 1
    
    # Obtener distribución final de categorías
    logger.info("\nDistribución final de productos por categoría:")
    final_distribution = get_category_distribution(models, uid)
    for cat_name, count in sorted(final_distribution.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {cat_name}: {count} productos")
    
    # Mostrar estadísticas
    logger.info("\nEstadísticas de recategorización:")
    logger.info(f"  Productos actualizados: {stats['updated']}")
    logger.info(f"  Productos sin cambios: {stats['skipped']}")
    logger.info(f"  Productos sin nombre válido: {stats['no_name']}")
    logger.info(f"  Errores: {stats['errors']}")
    
    logger.info("\nCategorías actualizadas:")
    for cat_name, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {cat_name}: +{count} productos")
        
    # Mostrar productos sin nombre para revisión
    logger.info("\nRevisando productos sin nombre:")
    unnamed_products = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'product.template', 'search_read',
        [[('name', 'like', 'Producto sin nombre')]],
        {'fields': ['id', 'name', 'default_code']}
    )
    
    for product in unnamed_products:
        logger.info(f"  ID: {product['id']}, Código: {product.get('default_code', 'N/A')}")
        
    # Mostrar productos en All con nombres que deberían ser categorizados
    logger.info("\nProductos en 'All' que podrían ser categorizados:")
    keywords_to_check = ["frigo", "congelador", "encimera", "cocina", "altavoz", "secador"]
    
    for keyword in keywords_to_check:
        products = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'search_read',
            [['&', ('categ_id', '=', 1), ('name', 'ilike', keyword)]],
            {'fields': ['id', 'name']}
        )
        
        if products:
            logger.info(f"\nProductos con '{keyword}' en el nombre que siguen en 'All':")
            for product in products:
                product_name = extract_product_name(product['name'])
                logger.info(f"  ID: {product['id']}, Nombre: {product_name}")

if __name__ == "__main__":
    try:
        recategorize_products()
    except Exception as e:
        logger.error(f"Error general: {str(e)}")
