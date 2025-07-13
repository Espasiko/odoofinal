from typing import Optional, Dict, Any, List
import logging
from .product_categorization import get_category_for_product, infer_category_from_name

"""
Módulo para gestionar las categorías de productos en Odoo.
Este módulo extrae la lógica de categorías de odoo_product_service.py
para mejorar la modularidad y mantenibilidad.
"""

def find_or_create_category(service, category_name: str) -> Optional[int]:
    """
    Busca una categoría por nombre o la crea si no existe.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        category_name: Nombre de la categoría
        
    Returns:
        Optional[int]: ID de la categoría o None en caso de error
    """
    # Validar entrada
    if not category_name or not isinstance(category_name, str):
        logging.warning(f"Nombre de categoría inválido: {category_name}, usando categoría por defecto")
        return 1  # Categoría 'All' por defecto
    
    # Normalizar el nombre de la categoría
    category_name = category_name.strip()
    if not category_name or category_name.lower() in ["sin categoría", "sin categoria", "none", "default"]:
        return 1  # Categoría 'All' por defecto
        
    try:
        # Buscar categoría existente
        category_ids = service._execute_kw(
            'product.category',
            'search',
            [[('name', '=', category_name)]],
            {'limit': 1}
        )
        
        if category_ids:
            # Verificar que la categoría realmente existe
            try:
                category_data = service._execute_kw(
                    'product.category',
                    'read',
                    [category_ids[0]],
                    {'fields': ['name']}
                )
                if category_data:
                    logging.info(f"Categoría '{category_name}' encontrada con ID: {category_ids[0]}")
                    return category_ids[0]
                else:
                    logging.warning(f"Categoría con ID {category_ids[0]} no existe, usando categoría por defecto")
                    return 1
            except Exception as e:
                logging.error(f"Error al verificar categoría {category_ids[0]}: {str(e)}")
                return 1
            
        # Crear nueva categoría
        try:
            category_id = service._execute_kw(
                'product.category',
                'create',
                [{'name': category_name}]
            )
            
            logging.info(f"Categoría '{category_name}' creada con ID: {category_id}")
            return category_id
        except Exception as e:
            logging.error(f"Error al crear categoría '{category_name}': {str(e)}")
            return 1
    except Exception as e:
        logging.error(f"Error general al buscar o crear categoría '{category_name}': {str(e)}")
        return 1  # Devolver categoría por defecto en caso de error

def get_category_name(service, category_id: int) -> str:
    """
    Obtiene el nombre de una categoría por su ID.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        category_id: ID de la categoría
        
    Returns:
        str: Nombre de la categoría o "Sin Categoría" si no se encuentra
    """
    # Validar entrada
    if not category_id or not isinstance(category_id, int) or category_id <= 0:
        logging.warning(f"ID de categoría inválido: {category_id}, devolviendo 'Sin Categoría'")
        return "Sin Categoría"
    
    # Categoría por defecto
    if category_id == 1:
        return "Sin Categoría"
        
    try:
        # Verificar si la categoría existe
        exists = service._execute_kw(
            'product.category',
            'search_count',
            [[('id', '=', category_id)]]
        )
        
        if not exists:
            logging.warning(f"La categoría con ID {category_id} no existe en la base de datos")
            return "Sin Categoría"
            
        # Obtener el nombre de la categoría
        try:
            category = service._execute_kw(
                'product.category',
                'read',
                [category_id],
                {'fields': ['name']}
            )
            
            if category and 'name' in category[0]:
                return category[0]['name']
            else:
                logging.warning(f"No se pudo obtener el nombre de la categoría con ID {category_id}")
                return "Sin Categoría"
        except Exception as e:
            logging.error(f"Error al leer categoría con ID {category_id}: {str(e)}")
            return "Sin Categoría"
    except Exception as e:
        logging.error(f"Error general al obtener nombre de categoría con ID {category_id}: {str(e)}")
        return "Sin Categoría"

def get_all_categories(service) -> List[Dict[str, Any]]:
    """
    Obtiene todas las categorías de productos.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        
    Returns:
        List[Dict[str, Any]]: Lista de categorías
    """
    try:
        category_ids = service._execute_kw(
            'product.category',
            'search',
            [[]],
            {'order': 'name'}
        )
        
        if not category_ids:
            return []
            
        categories = service._execute_kw(
            'product.category',
            'read',
            [category_ids],
            {'fields': ['name', 'parent_id', 'display_name', 'complete_name']}
        )
        
        return categories
    except Exception as e:
        logging.error(f"Error al obtener todas las categorías: {str(e)}")
        return []

def assign_category_to_product(service, product_id: int, category_id: int) -> bool:
    """
    Asigna una categoría a un producto.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_id: ID del producto
        category_id: ID de la categoría
        
    Returns:
        bool: True si la asignación fue exitosa, False en caso contrario
    """
    try:
        # Verificar que el producto existe
        product_exists = service._execute_kw(
            'product.template',
            'search_count',
            [[('id', '=', product_id)]]
        )
        
        if not product_exists:
            logging.warning(f"Producto con ID {product_id} no encontrado para asignar categoría")
            return False
            
        # Verificar que la categoría existe
        category_exists = service._execute_kw(
            'product.category',
            'search_count',
            [[('id', '=', category_id)]]
        )
        
        if not category_exists:
            logging.warning(f"Categoría con ID {category_id} no encontrada")
            return False
            
        # Asignar categoría al producto
        service._execute_kw(
            'product.template',
            'write',
            [[product_id], {'categ_id': category_id}]
        )
        
        # Obtener nombres para el log de manera segura
        try:
            product_data = service._execute_kw(
                'product.template',
                'read',
                [product_id],
                {'fields': ['name']}
            )
            product_name = product_data[0]['name'] if product_data and 'name' in product_data[0] else f"ID: {product_id}"
            
            category_data = service._execute_kw(
                'product.category',
                'read',
                [category_id],
                {'fields': ['name']}
            )
            category_name = category_data[0]['name'] if category_data and 'name' in category_data[0] else f"ID: {category_id}"
            
            logging.info(f"Categoría '{category_name}' asignada al producto '{product_name}'")
        except Exception as e:
            logging.warning(f"No se pudieron obtener detalles completos para el log: {str(e)}")
            logging.info(f"Categoría ID {category_id} asignada al producto ID {product_id}")
        return True
    except Exception as e:
        logging.error(f"Error al asignar categoría {category_id} al producto {product_id}: {str(e)}")
        return False

def categorize_products_batch(service, product_ids: List[int]) -> Dict[str, Any]:
    """
    Categoriza automáticamente un lote de productos basándose en sus nombres.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_ids: Lista de IDs de productos a categorizar
        
    Returns:
        Dict[str, Any]: Estadísticas de categorización
    """
    if not product_ids:
        return {"total": 0, "categorized": 0, "failed": 0}
        
    stats = {"total": len(product_ids), "categorized": 0, "failed": 0}
    
    try:
        # Obtener datos de los productos
        products = service._execute_kw(
            'product.template',
            'read',
            [product_ids],
            {'fields': ['name', 'categ_id']}
        )
        
        for product in products:
            try:
                # Solo categorizar si está en la categoría por defecto (All / Todos)
                if product['categ_id'][0] == 1:
                    product_name = product['name']
                    category_id = get_category_for_product(product_name)
                    
                    if category_id and category_id != 1:
                        # Asignar nueva categoría
                        service._execute_kw(
                            'product.template',
                            'write',
                            [[product['id']], {'categ_id': category_id}]
                        )
                        stats["categorized"] += 1
                        logging.info(f"Producto '{product_name}' categorizado automáticamente")
                    else:
                        stats["failed"] += 1
            except Exception as e:
                logging.error(f"Error al categorizar producto {product.get('name', 'desconocido')}: {str(e)}")
                stats["failed"] += 1
                
        return stats
    except Exception as e:
        logging.error(f"Error en categorización por lotes: {str(e)}")
        return {"total": len(product_ids), "categorized": 0, "failed": len(product_ids)}
