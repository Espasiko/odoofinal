from typing import Optional, Dict, Any, List, Tuple
import logging
from .product_lookup import find_existing_product
from .product_transform import prepare_product_vals
from .product_category_service import find_or_create_category
from .product_custom_fields import initialize_custom_fields

"""
Módulo para integración avanzada de productos con Odoo y otros sistemas.
Este módulo extrae la lógica de integración de odoo_product_service.py
para mejorar la modularidad y mantenibilidad.
"""

def create_or_update_product(service, product_data: Dict[str, Any]) -> Tuple[int, bool]:
    """
    Crea un nuevo producto o actualiza uno existente en Odoo.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_data: Diccionario con datos del producto
        
    Returns:
        Tuple[int, bool]: (ID del producto, True si es nuevo / False si fue actualizado)
    """
    try:
        # Asegurar que los campos personalizados estén inicializados
        initialize_custom_fields(service)
        
        # Extraer datos relevantes para búsqueda
        default_code = product_data.get('default_code', '')
        barcode = product_data.get('barcode', '')
        supplier_id = product_data.get('supplier_id')
        
        # Buscar producto existente
        existing_product_id = find_existing_product(service, default_code, barcode, supplier_id)
        
        # Preparar valores para Odoo
        vals = prepare_product_vals(product_data)
        
        # Asegurar que el tipo sea 'consu' para productos físicos en Odoo 18
        vals['type'] = 'consu'
        
        # Buscar o crear categoría si se especifica
        if product_data.get('category'):
            category_id = find_or_create_category(service, product_data['category'])
            if category_id:
                vals['categ_id'] = category_id
        
        if existing_product_id:
            # Actualizar producto existente
            service._execute_kw('product.template', 'write', [[existing_product_id], vals])
            logging.info(f"Producto actualizado con ID: {existing_product_id}")
            return existing_product_id, False
        else:
            # Crear nuevo producto
            product_id = service._execute_kw('product.template', 'create', [vals])
            logging.info(f"Nuevo producto creado con ID: {product_id}")
            return product_id, True
    except Exception as e:
        logging.error(f"Error al crear o actualizar producto: {str(e)}")
        raise

def bulk_import_products(service, products_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Importa múltiples productos en lote.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        products_data: Lista de diccionarios con datos de productos
        
    Returns:
        Dict[str, int]: Estadísticas de importación
    """
    stats = {
        "total": len(products_data),
        "created": 0,
        "updated": 0,
        "failed": 0
    }
    
    for product_data in products_data:
        try:
            product_id, is_new = create_or_update_product(service, product_data)
            if is_new:
                stats["created"] += 1
            else:
                stats["updated"] += 1
        except Exception as e:
            logging.error(f"Error al importar producto {product_data.get('name', 'desconocido')}: {str(e)}")
            stats["failed"] += 1
    
    return stats

def update_product_prices(service, product_id: int, list_price: float = None, standard_price: float = None) -> bool:
    """
    Actualiza los precios de un producto.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_id: ID del producto
        list_price: Precio de venta (opcional)
        standard_price: Precio de coste (opcional)
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    if not product_id:
        return False
        
    if list_price is None and standard_price is None:
        return False
        
    try:
        vals = {}
        
        if list_price is not None:
            vals['list_price'] = float(list_price)
            
        if standard_price is not None:
            vals['standard_price'] = float(standard_price)
            
        # Calcular margen si ambos precios están disponibles
        if list_price is not None and standard_price is not None and standard_price > 0:
            margin = ((list_price - standard_price) / standard_price) * 100
            vals['x_margen_calculado'] = margin
            
            # Establecer alerta si el margen es bajo (menor al 15%)
            vals['x_alerta_margen'] = margin < 15
        
        service._execute_kw('product.template', 'write', [[product_id], vals])
        logging.info(f"Precios actualizados para producto ID {product_id}")
        return True
    except Exception as e:
        logging.error(f"Error al actualizar precios del producto {product_id}: {str(e)}")
        return False

def link_product_to_supplier(service, product_id: int, supplier_id: int, supplier_code: str = None, 
                           supplier_price: float = None) -> bool:
    """
    Vincula un producto con un proveedor.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_id: ID del producto
        supplier_id: ID del proveedor
        supplier_code: Código del producto según el proveedor (opcional)
        supplier_price: Precio del proveedor (opcional)
        
    Returns:
        bool: True si la vinculación fue exitosa, False en caso contrario
    """
    try:
        # Verificar si ya existe una relación
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
            # Actualizar relación existente
            service._execute_kw('product.supplierinfo', 'write', [seller_ids[0], vals])
            logging.info(f"Actualizada relación entre producto {product_id} y proveedor {supplier_id}")
        else:
            # Crear nueva relación
            service._execute_kw('product.supplierinfo', 'create', [vals])
            logging.info(f"Creada relación entre producto {product_id} y proveedor {supplier_id}")
        
        return True
    except Exception as e:
        logging.error(f"Error al vincular producto {product_id} con proveedor {supplier_id}: {str(e)}")
        return False

def get_product_suppliers(service, product_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene los proveedores de un producto.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_id: ID del producto
        
    Returns:
        List[Dict[str, Any]]: Lista de proveedores del producto
    """
    try:
        supplier_info_ids = service._execute_kw(
            'product.supplierinfo',
            'search',
            [[('product_tmpl_id', '=', product_id)]],
            {'order': 'sequence, min_qty desc, price'}
        )
        
        if not supplier_info_ids:
            return []
            
        supplier_infos = service._execute_kw(
            'product.supplierinfo',
            'read',
            [supplier_info_ids],
            {'fields': ['partner_id', 'product_code', 'product_name', 'price', 'delay', 'min_qty']}
        )
        
        # Enriquecer con datos del proveedor
        for info in supplier_infos:
            if info.get('partner_id'):
                partner_id = info['partner_id'][0]
                partner = service._execute_kw(
                    'res.partner',
                    'read',
                    [partner_id],
                    {'fields': ['name', 'email', 'phone', 'vat']}
                )
                if partner:
                    info['partner_details'] = partner[0]
        
        return supplier_infos
    except Exception as e:
        logging.error(f"Error al obtener proveedores del producto {product_id}: {str(e)}")
        return []

def calculate_product_margins(service, product_ids: List[int] = None) -> Dict[str, int]:
    """
    Calcula y actualiza los márgenes de beneficio para productos.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        product_ids: Lista de IDs de productos (opcional, si es None se procesan todos)
        
    Returns:
        Dict[str, int]: Estadísticas de actualización
    """
    try:
        # Asegurar que los campos personalizados existen
        initialize_custom_fields(service)
        
        # Si no se especifican IDs, obtener todos los productos activos
        if not product_ids:
            product_ids = service._execute_kw(
                'product.template',
                'search',
                [[('active', '=', True)]]
            )
        
        stats = {"total": len(product_ids), "updated": 0, "failed": 0, "no_cost": 0}
        
        for product_id in product_ids:
            try:
                # Obtener precios actuales
                product = service._execute_kw(
                    'product.template',
                    'read',
                    [product_id],
                    {'fields': ['list_price', 'standard_price']}
                )
                
                if not product:
                    stats["failed"] += 1
                    continue
                    
                product = product[0]
                list_price = product.get('list_price', 0)
                standard_price = product.get('standard_price', 0)
                
                if not standard_price:
                    stats["no_cost"] += 1
                    continue
                
                # Calcular margen
                margin = ((list_price - standard_price) / standard_price) * 100 if standard_price > 0 else 0
                
                # Actualizar campos personalizados
                service._execute_kw(
                    'product.template',
                    'write',
                    [[product_id], {
                        'x_margen_calculado': margin,
                        'x_alerta_margen': margin < 15
                    }]
                )
                
                stats["updated"] += 1
            except Exception as e:
                logging.error(f"Error al calcular margen para producto {product_id}: {str(e)}")
                stats["failed"] += 1
        
        return stats
    except Exception as e:
        logging.error(f"Error general en cálculo de márgenes: {str(e)}")
        return {"total": len(product_ids) if product_ids else 0, "updated": 0, "failed": 0, "no_cost": 0}
