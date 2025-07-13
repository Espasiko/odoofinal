from typing import List, Optional, Dict, Any
import logging
from ..models.schemas import Product, ProductCreate, OdooProductUpdate
from fastapi import HTTPException
from .product_transform import prepare_product_vals
from .product_lookup import find_existing_product

"""
Módulo para operaciones CRUD básicas de productos en Odoo.
Este módulo extrae la lógica principal de odoo_product_service.py
para mejorar la modularidad y mantenibilidad.
"""

def get_product_by_id(service, product_id: int) -> Optional[Product]:
    """
    Obtiene un producto por su ID desde Odoo.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_id: ID del producto en Odoo
        
    Returns:
        Optional[Product]: Modelo Pydantic del producto o None si no se encuentra
    """
    try:
        product = service._execute_kw(
            'product.template',
            'read',
            [product_id],
            {'fields': [
                'name', 'list_price', 'standard_price', 'categ_id',
                'default_code', 'barcode', 'weight', 'sale_ok',
                'purchase_ok', 'available_in_pos', 'to_weight',
                'is_published', 'website_sequence', 'description_sale',
                'description_purchase', 'description'
            ]}
        )
        
        if not product:
            logging.warning(f"Producto con ID {product_id} no encontrado")
            return None
            
        product = product[0]
        
        # Obtener nombre de categoría
        category_name = "Sin Categoría"
        if product.get('categ_id'):
            category = service._execute_kw(
                'product.category',
                'read',
                [product['categ_id'][0]],
                {'fields': ['name']}
            )
            if category:
                category_name = category[0]['name']
        
        # Sanitizar campos que pueden venir como booleanos
        barcode = product.get('barcode', '')
        if barcode is False:
            barcode = ''
            
        description_sale = product.get('description_sale', '')
        if description_sale is False:
            description_sale = ''
            
        description_purchase = product.get('description_purchase', '')
        if description_purchase is False:
            description_purchase = ''
            
        description = product.get('description', '')
        if description is False:
            description = ''
        
        # Crear un diccionario con todos los campos necesarios para el modelo Product
        product_dict = {
            'id': product['id'],
            'name': product['name'],
            'list_price': product.get('list_price', 0.0),
            'standard_price': product.get('standard_price', 0.0),
            'category': category_name,
            'default_code': product.get('default_code', ''),
            'barcode': barcode,
            'weight': product.get('weight', 0.0),
            'sale_ok': product.get('sale_ok', True),
            'purchase_ok': product.get('purchase_ok', True),
            'available_in_pos': product.get('available_in_pos', False),
            'to_weight': product.get('to_weight', False),
            'is_published': product.get('is_published', False),
            'website_sequence': product.get('website_sequence', 0),
            'description_sale': description_sale,
            'description': description,
            'description_purchase': description_purchase,
            # Campos obligatorios según el modelo Product
            'template_id': product.get('id'),  # Usamos el mismo ID como template_id
            'qty_available': 0.0,
            'virtual_available': 0.0,
            'incoming_qty': 0.0,
            'outgoing_qty': 0.0,
            'create_date': None,
            'write_date': None,
            'product_tag_ids': [],
            'pos_categ_ids': []
        }
        
        # Crear el objeto Product con los datos
        return Product(**product_dict)
    except Exception as e:
        logging.error(f"Error al obtener producto por ID {product_id}: {str(e)}")
        return None

def get_all_products(service) -> List[Dict[str, Any]]:
    """
    Obtiene todos los productos desde Odoo.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        
    Returns:
        List[Dict[str, Any]]: Lista de productos en formato diccionario
    """
    try:
        product_ids = service._execute_kw(
            'product.template',
            'search',
            [[('active', '=', True)]],
            {'order': 'name'}
        )
        
        if not product_ids:
            return []
            
        products = service._execute_kw(
            'product.template',
            'read',
            [product_ids],
            {'fields': [
                'name', 'list_price', 'standard_price', 'categ_id',
                'default_code', 'barcode', 'weight', 'sale_ok',
                'purchase_ok', 'available_in_pos', 'to_weight',
                'is_published', 'website_sequence'
            ]}
        )
        
        return products
    except Exception as e:
        logging.error(f"Error al obtener todos los productos: {str(e)}")
        return []

def create_product(service, product: ProductCreate) -> Optional[int]:
    """
    Crea un nuevo producto en Odoo.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product: Modelo Pydantic con datos del producto a crear
        
    Returns:
        Optional[int]: ID del producto creado o None en caso de error
    """
    try:
        # Preparar valores para Odoo
        vals = prepare_product_vals(product)
        
        # Asegurar que el tipo sea 'consu' para productos físicos en Odoo 18
        vals['type'] = 'consu'
        
        # Buscar o crear categoría si se especifica
        if product.category and product.category != "Sin Categoría":
            from .product_category_service import find_or_create_category
            category_id = find_or_create_category(service, product.category)
            if category_id:
                vals['categ_id'] = category_id
        
        # Crear producto
        product_id = service._execute_kw('product.template', 'create', [vals])
        logging.info(f"Producto creado con ID: {product_id}")
        return product_id
    except Exception as e:
        logging.error(f"Error al crear producto: {str(e)}")
        return None

def update_product(service, product_id: int, product_update: OdooProductUpdate) -> bool:
    """
    Actualiza un producto existente en Odoo.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_id: ID del producto a actualizar
        product_update: Modelo Pydantic con datos a actualizar
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    try:
        # Verificar que el producto existe
        product_exists = service._execute_kw(
            'product.template',
            'search_count',
            [[('id', '=', product_id)]]
        )
        
        if not product_exists:
            logging.warning(f"Producto con ID {product_id} no encontrado para actualizar")
            return False
        
        # Preparar valores para Odoo
        vals = prepare_product_vals(product_update)
        
        # Buscar o crear categoría si se especifica
        if hasattr(product_update, 'category') and product_update.category:
            from .product_category_service import find_or_create_category
            category_id = find_or_create_category(service, product_update.category)
            if category_id:
                vals['categ_id'] = category_id
        
        # Actualizar producto
        service._execute_kw('product.template', 'write', [[product_id], vals])
        logging.info(f"Producto con ID {product_id} actualizado correctamente")
        return True
    except Exception as e:
        logging.error(f"Error al actualizar producto con ID {product_id}: {str(e)}")
        return False

def delete_product(service, product_id: int) -> bool:
    """
    Elimina un producto de Odoo.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_id: ID del producto a eliminar
        
    Returns:
        bool: True si la eliminación fue exitosa, False en caso contrario
    """
    try:
        # Verificar que el producto existe
        product_exists = service._execute_kw(
            'product.template',
            'search_count',
            [[('id', '=', product_id)]]
        )
        
        if not product_exists:
            logging.warning(f"Producto con ID {product_id} no encontrado para eliminar")
            return False
        
        # Eliminar producto
        service._execute_kw('product.template', 'unlink', [[product_id]])
        logging.info(f"Producto con ID {product_id} eliminado correctamente")
        return True
    except Exception as e:
        logging.error(f"Error al eliminar producto con ID {product_id}: {str(e)}")
        return False

def get_product_by_code(service, code: str) -> Optional[Dict[str, Any]]:
    """
    Busca un producto por su código interno (default_code).
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        code: Código interno del producto
        
    Returns:
        Optional[Dict[str, Any]]: Datos del producto o None si no se encuentra
    """
    try:
        if not code:
            return None
            
        product_ids = service._execute_kw(
            'product.template',
            'search',
            [[('default_code', '=', code)]],
            {'limit': 1}
        )
        
        if not product_ids:
            logging.info(f"No se encontró producto con código: {code}")
            return None
            
        product = service._execute_kw(
            'product.template',
            'read',
            [product_ids[0]],
            {'fields': [
                'id', 'name', 'list_price', 'standard_price', 'categ_id',
                'default_code', 'barcode', 'weight', 'sale_ok',
                'purchase_ok', 'available_in_pos', 'to_weight',
                'is_published', 'website_sequence'
            ]}
        )
        
        return product[0] if product else None
    except Exception as e:
        logging.error(f"Error al buscar producto por código {code}: {str(e)}")
        return None

def archive_product(service, product_id: int) -> bool:
    """
    Archiva un producto en Odoo (lo marca como inactivo).
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_id: ID del producto a archivar
        
    Returns:
        bool: True si el archivado fue exitoso, False en caso contrario
    """
    try:
        # Verificar que el producto existe
        product_exists = service._execute_kw(
            'product.template',
            'search_count',
            [[('id', '=', product_id)]]
        )
        
        if not product_exists:
            logging.warning(f"Producto con ID {product_id} no encontrado para archivar")
            return False
        
        # Archivar producto (marcar como inactivo)
        service._execute_kw('product.template', 'write', [[product_id], {'active': False}])
        logging.info(f"Producto con ID {product_id} archivado correctamente")
        return True
    except Exception as e:
        logging.error(f"Error al archivar producto con ID {product_id}: {str(e)}")
        return False

def get_paginated_products(service, page: int = 1, limit: int = 10, sort_by: str = 'id', 
                          sort_order: str = 'asc', search: Optional[str] = None, 
                          category: Optional[str] = None, include_inactive: bool = False):
    """
    Obtiene productos paginados desde Odoo con opciones de filtrado y ordenación.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        page: Número de página
        limit: Límite de resultados por página
        sort_by: Campo por el que ordenar
        sort_order: Orden (asc o desc)
        search: Texto para buscar en nombre o código
        category: Filtrar por categoría
        include_inactive: Incluir productos inactivos
        
    Returns:
        Dict con productos paginados y metadatos
    """
    try:
        # Calcular offset para paginación
        offset = (page - 1) * limit
        
        # Construir dominio de búsqueda
        domain = []
        
        # Incluir productos activos/inactivos según parámetro
        if not include_inactive:
            domain.append(('active', '=', True))
        
        # Filtrar por texto de búsqueda
        if search:
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('default_code', 'ilike', search))
        
        # Filtrar por categoría
        if category:
            # Buscar ID de la categoría
            category_ids = service._execute_kw(
                'product.category',
                'search',
                [[('name', 'ilike', category)]],
                {'limit': 1}
            )
            if category_ids:
                domain.append(('categ_id', 'child_of', category_ids[0]))
        
        # Construir orden
        order = f"{sort_by} {sort_order}"
        
        # Contar total de productos que coinciden con el dominio
        total_count = service._execute_kw(
            'product.template',
            'search_count',
            [domain]
        )
        
        # Obtener IDs de productos paginados
        product_ids = service._execute_kw(
            'product.template',
            'search',
            [domain],
            {'offset': offset, 'limit': limit, 'order': order}
        )
        
        if not product_ids:
            return {
                'items': [],
                'total': total_count,
                'page': page,
                'limit': limit,
                'pages': (total_count + limit - 1) // limit
            }
        
        # Obtener datos de los productos
        products = service._execute_kw(
            'product.template',
            'read',
            [product_ids],
            {'fields': [
                'name', 'list_price', 'standard_price', 'categ_id',
                'default_code', 'barcode', 'weight', 'sale_ok',
                'purchase_ok', 'available_in_pos', 'to_weight',
                'is_published', 'website_sequence', 'active'
            ]}
        )
        
        # Transformar productos
        transformed_products = service._transform_products(products)
        
        # Construir respuesta paginada
        return {
            'items': transformed_products,
            'total': total_count,
            'page': page,
            'limit': limit,
            'pages': (total_count + limit - 1) // limit
        }
    except Exception as e:
        logging.error(f"Error al obtener productos paginados: {str(e)}")
        return {
            'items': [],
            'total': 0,
            'page': page,
            'limit': limit,
            'pages': 0
        }
