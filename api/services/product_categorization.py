from typing import Optional, Dict, List, Tuple, Any
import re
import logging
import json

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
}

# Mapeo de proveedores a categorías por defecto
# Si no se encuentra palabra clave, usar esta categoría según el proveedor
SUPPLIER_DEFAULT_CATEGORY = {
    "CECOTEC": (135, "OTROS"),
    "JATA": (135, "OTROS"),
    "ORBEGOZO": (135, "OTROS"),
}

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
        
    # Si ya es un string simple
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
        if keyword in name_lower:
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
    # Intentar inferir por nombre primero
    category = infer_category_from_name(product_name)
    if category:
        return category[0]
        
    # Si tenemos proveedor, intentar usar su categoría por defecto
    if supplier_name and supplier_name.upper() in SUPPLIER_DEFAULT_CATEGORY:
        return SUPPLIER_DEFAULT_CATEGORY[supplier_name.upper()][0]
        
    # Si todo falla, devolver la categoría "All"
    return 1

def categorize_existing_products(odoo_service) -> Dict[str, int]:
    """
    Categoriza productos existentes que están en la categoría "All".
    
    Args:
        odoo_service: Instancia de OdooProductService
        
    Returns:
        Diccionario con estadísticas de actualización
    """
    if not odoo_service._models:
        odoo_service._get_connection()
        
    # Obtener productos en categoría "All"
    products = odoo_service._execute_kw(
        'product.template',
        'search_read',
        [[('categ_id', '=', 1)]],
        {'fields': ['id', 'name', 'seller_ids']}
    )
    
    logging.info(f"Encontrados {len(products)} productos en categoría 'All'")
    
    stats = {
        "total": len(products),
        "updated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    for product in products:
        try:
            product_id = product['id']
            product_name = product['name']
            
            # Obtener proveedor si existe
            supplier_name = None
            if product.get('seller_ids'):
                seller_id = product['seller_ids'][0]
                supplier_data = odoo_service._execute_kw(
                    'product.supplierinfo',
                    'read',
                    [seller_id],
                    {'fields': ['partner_id']}
                )
                if supplier_data and supplier_data[0].get('partner_id'):
                    partner_id = supplier_data[0]['partner_id'][0]
                    partner_data = odoo_service._execute_kw(
                        'res.partner',
                        'read',
                        [partner_id],
                        {'fields': ['name']}
                    )
                    if partner_data:
                        supplier_name = partner_data[0]['name']
            
            # Determinar categoría
            category_id = get_category_for_product(product_name, supplier_name)
            
            # Si la categoría es distinta de "All", actualizar
            if category_id != 1:
                odoo_service._execute_kw(
                    'product.template',
                    'write',
                    [[product_id], {'categ_id': category_id}]
                )
                stats["updated"] += 1
                logging.info(f"Producto {product_id} '{product_name}' actualizado a categoría {category_id}")
            else:
                stats["skipped"] += 1
                
        except Exception as e:
            logging.error(f"Error al categorizar producto {product.get('id')}: {e}")
            stats["errors"] += 1
            
    return stats
