from typing import List, Optional, Dict, Union, Any, Tuple
from .odoo_base_service import OdooBaseService
import logging
from ..models.schemas import Product, ProductCreate, OdooProductUpdate
from fastapi import HTTPException

# Importar funciones de los módulos refactorizados
from .product_core_service import (
    get_product_by_id as core_get_product_by_id,
    get_all_products as core_get_all_products,
    create_product as core_create_product,
    update_product as core_update_product,
    delete_product as core_delete_product,
    get_product_by_code as core_get_product_by_code,
    get_paginated_products as core_get_paginated_products,
    archive_product as core_archive_product
)

from .product_custom_fields import (
    initialize_custom_fields as init_custom_fields,
    ensure_custom_field,
    check_available_fields
)

from .product_category_service import (
    find_or_create_category,
    get_category_name,
    get_all_categories,
    assign_category_to_product,
    categorize_products_batch
)

from .product_integration_service import (
    create_or_update_product as integration_create_or_update_product,
    bulk_import_products,
    update_product_prices,
    link_product_to_supplier,
    get_product_suppliers,
    calculate_product_margins
)

from .product_transform import prepare_product_vals

from .product_lookup import find_existing_product

class OdooProductService(OdooBaseService):
    """
    Servicio para gestión de productos en Odoo.
    
    Esta clase actúa como fachada para mantener compatibilidad con el código existente,
    delegando la implementación real a módulos especializados.
    """
    
    def initialize_custom_fields(self) -> bool:
        """Inicializa los campos personalizados necesarios en Odoo"""
        return init_custom_fields(self)

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Obtiene un producto por su ID de la base de datos de Odoo.
        """
        return core_get_product_by_id(self, product_id)
            
    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos activos de la base de datos de Odoo.
        """
        return core_get_all_products(self)
            
    def create_product(self, product: ProductCreate) -> Optional[int]:
        """
        Crea un nuevo producto en la base de datos de Odoo.
        """
        return core_create_product(self, product)
            
    def update_product(self, product_id: int, product_update: OdooProductUpdate) -> bool:
        """
        Actualiza un producto existente en la base de datos de Odoo.
        """
        return core_update_product(self, product_id, product_update)
            
    def delete_product(self, product_id: int) -> bool:
        """
        Elimina un producto de la base de datos de Odoo (marcándolo como inactivo).
        """
        return core_delete_product(self, product_id)
            
    def get_product_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Busca un producto por su código (default_code) en Odoo.
        """
        return core_get_product_by_code(self, code)
    
    def get_paginated_products(self, page: int = 1, limit: int = 10, sort_by: str = 'id', 
                              sort_order: str = 'asc', search: Optional[str] = None, 
                              category: Optional[str] = None, include_inactive: bool = False):
        """Obtiene productos paginados, ordenados y filtrados desde Odoo."""
        try:
            # Asegurar conexión
            if not self._models:
                self._get_connection()
                
            # Verificar qué campos existen en el modelo product.template
            available_fields = check_available_fields(self, 'product.template')
            
            # Construir dominio de búsqueda
            domain = []
            
            # Filtro de activos/inactivos
            if not include_inactive:
                domain.append(('active', '=', True))
                
            # Filtro de búsqueda por nombre o código
            if search:
                domain.append('|')
                domain.append(('name', 'ilike', search))
                domain.append(('default_code', 'ilike', search))
                
            # Filtro por categoría
            if category:
                category_ids = self._execute_kw(
                    'product.category',
                    'search',
                    [[('name', 'ilike', category)]]
                )
                if category_ids:
                    domain.append(('categ_id', 'in', category_ids))
            
            # Obtener total de registros para paginación
            total = self._execute_kw(
                'product.template',
                'search_count',
                [domain]
            )
            
            # Si no hay resultados, devolver lista vacía
            if total == 0:
                return {
                    'items': [],
                    'total': 0,
                    'page': page,
                    'limit': limit,
                    'pages': 0
                }
                
            # Calcular offset para paginación
            offset = (page - 1) * limit
            
            # Ordenación
            order = f"{sort_by} {sort_order}"
            
            # Obtener productos paginados
            odoo_products = self._execute_kw(
                'product.template',
                'search_read',
                [domain],
                {
                    'offset': offset,
                    'limit': limit,
                    'order': order,
                    'fields': [
                        'id', 'name', 'default_code', 'active', 'is_published',
                        'list_price', 'standard_price', 'categ_id', 'seller_ids',
                        'product_variant_ids', 'barcode', 'description_sale',
                        'description_purchase', 'description', 'weight',
                        'sale_ok', 'purchase_ok', 'available_in_pos', 'to_weight',
                        'website_sequence'
                    ]
                }
            )
            
            # Transformar productos
            transformed_products = self._transform_products(odoo_products)
            
            # Calcular total de páginas
            total_pages = (total + limit - 1) // limit
            
            # Construir respuesta paginada
            return {
                'items': transformed_products,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': total_pages
            }
            
        except Exception as e:
            logging.error(f"Error en get_paginated_products: {str(e)}")
            return {
                'items': [],
                'total': 0,
                'page': page,
                'limit': limit,
                'pages': 0
            }
    
    def _transform_products(self, odoo_products):
        """Transforma productos de Odoo al formato de API"""
        transformed_products = []
        
        for p in odoo_products:
            try:
                # Obtener categoría
                category_name = "Sin Categoría"
                if p.get('categ_id'):
                    category_id = p['categ_id'][0] if isinstance(p['categ_id'], list) else p['categ_id']
                    category_name = get_category_name(self, category_id)
                
                # Sanitizar campos de texto que podrían venir como booleanos
                default_code = p.get('default_code', '')
                if default_code is False:
                    default_code = ''
                    
                barcode = p.get('barcode', '')
                if barcode is False:
                    barcode = ''
                    
                description_sale = p.get('description_sale', '')
                if description_sale is False:
                    description_sale = ''
                    
                description_purchase = p.get('description_purchase', '')
                if description_purchase is False:
                    description_purchase = ''
                    
                description = p.get('description', '')
                if description is False:
                    description = ''
                
                # Construir diccionario de producto transformado
                product_dict = {
                    'id': p['id'],
                    'name': p['name'],
                    'default_code': default_code,
                    'barcode': barcode,
                    'list_price': p.get('list_price', 0.0),
                    'standard_price': p.get('standard_price', 0.0),
                    'categ_id': p['categ_id'][0] if isinstance(p['categ_id'], list) else p.get('categ_id', 1),
                    'category': category_name,
                    'active': p.get('active', True),
                    'weight': p.get('weight', 0.0),
                    'sale_ok': p.get('sale_ok', True),
                    'purchase_ok': p.get('purchase_ok', True),
                    'available_in_pos': p.get('available_in_pos', False),
                    'to_weight': p.get('to_weight', False),
                    'is_published': p.get('is_published', False),
                    'website_sequence': p.get('website_sequence', 0),
                    'description_sale': description_sale,
                    'description': description,
                    'description_purchase': description_purchase
                }
                
                # Añadir campos personalizados si existen
                if 'x_margen_calculado' in p:
                    product_dict['margen_calculado'] = p.get('x_margen_calculado', 0.0)
                    
                if 'x_alerta_margen' in p:
                    product_dict['alerta_margen'] = p.get('x_alerta_margen', False)
                
                transformed_products.append(product_dict)
                
            except Exception as e:
                logging.error(f"Error transformando producto {p.get('id', 'desconocido')}: {str(e)}")
                # Continuar con el siguiente producto
                continue
                
        return transformed_products
    
    def _ensure_custom_field(self, model_name: str, field_name: str, field_type: str, field_label: str) -> bool:
        """
        Asegura que un campo personalizado existe en un modelo de Odoo.
        Si no existe, lo crea.
        """
        return ensure_custom_field(self, model_name, field_name, field_type, field_label)
    
    def _check_available_fields(self, model_name: str) -> Dict[str, Any]:
        """Verifica qué campos están disponibles en un modelo de Odoo"""
        return check_available_fields(self, model_name)
    
    def find_or_create_category(self, category_name: str) -> Optional[int]:
        """
        Busca una categoría por nombre y la crea si no existe.
        """
        return find_or_create_category(self, category_name)
    
    def create_or_update_product(self, product_data: Dict[str, Any]) -> Optional[int]:
        """
        Crea o actualiza un producto en Odoo.
        """
        try:
            product_id, is_new = integration_create_or_update_product(self, product_data)
            return product_id
        except Exception as e:
            logging.error(f"Error en create_or_update_product: {str(e)}")
            return None
    
    def archive_product(self, product_id: int) -> bool:
        """
        Archiva (desactiva) un producto en Odoo.
        """
        return core_archive_product(self, product_id)
    
    def front_to_odoo_product_dict(self, producto: Dict[str, Any], proveedor_nombre: Optional[str] = None) -> Dict[str, Any]:
        """
        Convierte un producto del formato frontend/Excel al formato Odoo para crear o actualizar.
        """
        try:
            # Usar prepare_product_vals para transformar los datos al formato de Odoo
            product_vals = prepare_product_vals(producto, proveedor_nombre)
            
            # Asegurar que el tipo sea 'consu' para productos físicos en Odoo 18
            product_vals['type'] = 'consu'
            
            # Buscar o crear proveedor si se especifica
            if proveedor_nombre:
                from .odoo_provider_service import odoo_provider_service
                supplier_id = odoo_provider_service.find_or_create_provider(proveedor_nombre)
                if supplier_id:
                    product_vals['supplier_id'] = supplier_id
            
            # Buscar o crear categoría si se especifica
            if 'category' in producto and producto['category']:
                category_id = self.find_or_create_category(producto['category'])
                if category_id:
                    product_vals['categ_id'] = category_id
            
            return product_vals
            
        except Exception as e:
            logging.error(f"Error en front_to_odoo_product_dict: {str(e)}")
            return {}
    
    # Métodos adicionales delegados a los módulos especializados
    
    def update_product_prices(self, product_id: int, list_price: float = None, standard_price: float = None) -> bool:
        """Actualiza los precios de un producto."""
        return update_product_prices(self, product_id, list_price, standard_price)
    
    def link_product_to_supplier(self, product_id: int, supplier_id: int, supplier_code: str = None, 
                               supplier_price: float = None) -> bool:
        """Vincula un producto con un proveedor."""
        return link_product_to_supplier(self, product_id, supplier_id, supplier_code, supplier_price)
    
    def get_product_suppliers(self, product_id: int) -> List[Dict[str, Any]]:
        """Obtiene los proveedores de un producto."""
        return get_product_suppliers(self, product_id)
    
    def calculate_product_margins(self, product_ids: List[int] = None) -> Dict[str, int]:
        """Calcula y actualiza los márgenes de beneficio para productos."""
        return calculate_product_margins(self, product_ids)
    
    def bulk_import_products(self, products_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Importa múltiples productos en lote."""
        return bulk_import_products(self, products_data)

# Instancia global para evitar errores de importación circular
odoo_product_service = OdooProductService()
