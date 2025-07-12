from typing import List, Optional, Dict, Union, Any
from .odoo_base_service import OdooBaseService
import logging
from ..models.schemas import Product, ProductCreate, OdooProductUpdate
from fastapi import HTTPException
import logging
from .product_transform import prepare_product_vals
from .product_lookup import find_existing_product

class OdooProductService(OdooBaseService):
    """Servicio para gestión de productos en Odoo"""
    
    def initialize_custom_fields(self):
        """Inicializa los campos personalizados necesarios en Odoo"""
        try:
            if not self._models:
                self._get_connection()
                
            # Crear campos personalizados para márgenes y alertas si no existen
            self._ensure_custom_field('product.template', 'x_margen_calculado', 'float', 'Margen Calculado (%)')
            self._ensure_custom_field('product.template', 'x_alerta_margen', 'boolean', 'Alerta de Margen')
            logging.info("Campos personalizados para márgenes y alertas verificados/creados correctamente")
            return True
        except Exception as e:
            logging.error(f"Error al inicializar campos personalizados: {str(e)}")
            return False

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Obtiene un producto por su ID de la base de datos de Odoo.
        """
        try:
            if not self._models:
                self._get_connection()
            
            product_data = self._execute_kw(
                'product.template', 
                'search_read', 
                [[['id', '=', product_id]]], 
                {
                    'limit': 1,
                    'fields': [
                        'id', 'name', 'default_code', 'list_price', 'categ_id', 'active',
                        'type', 'standard_price', 'barcode', 'weight', 'sale_ok', 'purchase_ok',
                        'available_in_pos', 'to_weight', 'is_published', 'website_sequence',
                        'description_sale', 'description', 'description_purchase'
                    ]
                }
            )
            
            if not product_data:
                return None
                
            product = product_data[0]
            
            # Extraer categoría si existe
            category_name = None
            if product.get('categ_id'):
                category_id = product['categ_id'][0] if isinstance(product['categ_id'], list) else product['categ_id']
                category_data = self._execute_kw(
                    'product.category',
                    'read',
                    [category_id],
                    {'fields': ['name']}
                )
                if category_data:
                    category_name = category_data[0]['name']
            
            # Asegurar que los campos de texto sean strings y no booleanos
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
            
            # Construir objeto Product
            return Product(
                id=product['id'],
                name=product['name'],
                default_code=product.get('default_code', ''),
                list_price=product.get('list_price', 0.0),
                standard_price=product.get('standard_price', 0.0),
                categ_id=product['categ_id'][0] if isinstance(product['categ_id'], list) else product.get('categ_id'),
                category=category_name,
                active=product.get('active', True),
                type=product.get('type', 'product'),
                barcode=barcode,
                weight=product.get('weight', 0.0),
                sale_ok=product.get('sale_ok', True),
                purchase_ok=product.get('purchase_ok', True),
                available_in_pos=product.get('available_in_pos', False),
                to_weight=product.get('to_weight', False),
                is_published=product.get('is_published', False),
                website_sequence=product.get('website_sequence', 0),
                description_sale=description_sale,
                description=description,
                description_purchase=description_purchase
            )
            
        except Exception as e:
            logging.error(f"Error obteniendo producto por ID {product_id}: {e}")
            return None
            
    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos activos de la base de datos de Odoo.
        """
        try:
            if not self._models:
                self._get_connection()
                
            # Obtener productos activos
            products = self._execute_kw(
                'product.template',
                'search_read',
                [[['active', '=', True]]],
                {
                    'fields': [
                        'id', 'name', 'default_code', 'list_price', 'standard_price',
                        'categ_id', 'active', 'type', 'barcode'
                    ]
                }
            )
            
            if not products:
                return []
                
            # Transformar productos
            transformed_products = []
            for product in products:
                # Extraer categoría
                category_name = None
                if product.get('categ_id'):
                    category_id = product['categ_id'][0] if isinstance(product['categ_id'], list) else product['categ_id']
                    category_data = self._execute_kw(
                        'product.category',
                        'read',
                        [category_id],
                        {'fields': ['name']}
                    )
                    if category_data:
                        category_name = category_data[0]['name']
                
                # Construir diccionario de producto
                transformed_product = {
                    'id': product['id'],
                    'name': product['name'],
                    'default_code': product.get('default_code', ''),
                    'list_price': product.get('list_price', 0.0),
                    'standard_price': product.get('standard_price', 0.0),
                    'categ_id': product['categ_id'][0] if isinstance(product['categ_id'], list) else product.get('categ_id'),
                    'category': category_name,
                    'active': product.get('active', True),
                    'type': product.get('type', 'product'),
                    'barcode': product.get('barcode', '')
                }
                transformed_products.append(transformed_product)
                
            return transformed_products
            
        except Exception as e:
            logging.error(f"Error obteniendo todos los productos: {e}")
            return []
            
    def create_product(self, product: ProductCreate) -> Optional[int]:
        """
        Crea un nuevo producto en la base de datos de Odoo.
        """
        try:
            if not self._models:
                self._get_connection()
                
            # Preparar valores para el producto
            product_vals = {
                'name': product.name,
                'default_code': product.default_code,
                'list_price': product.list_price,
                'standard_price': product.standard_price,
                'type': 'product',  # Producto almacenable por defecto
                'active': True
            }
            
            # Asignar categoría si se proporciona
            if product.category:
                category_id = self.find_or_create_category(product.category)
                if category_id:
                    product_vals['categ_id'] = category_id
            
            # Crear producto
            new_product_id = self._execute_kw(
                'product.template',
                'create',
                [product_vals]
            )
            
            if new_product_id:
                logging.info(f"Producto '{product.name}' creado con ID: {new_product_id}")
                return new_product_id
            else:
                logging.error(f"No se pudo crear el producto '{product.name}'")
                return None
                
        except Exception as e:
            logging.error(f"Error creando producto '{product.name}': {e}")
            return None
            
    def update_product(self, product_id: int, product_update: OdooProductUpdate) -> bool:
        """
        Actualiza un producto existente en la base de datos de Odoo.
        """
        try:
            if not self._models:
                self._get_connection()
                
            # Verificar que el producto existe
            product_exists = self._execute_kw(
                'product.template',
                'search_count',
                [[['id', '=', product_id]]]
            )
            
            if not product_exists:
                logging.error(f"Producto con ID {product_id} no encontrado")
                return False
                
            # Preparar valores para actualizar
            update_vals = {}
            
            if product_update.name is not None:
                update_vals['name'] = product_update.name
                
            if product_update.default_code is not None:
                update_vals['default_code'] = product_update.default_code
                
            if product_update.list_price is not None:
                update_vals['list_price'] = product_update.list_price
                
            if product_update.standard_price is not None:
                update_vals['standard_price'] = product_update.standard_price
                
            if product_update.active is not None:
                update_vals['active'] = product_update.active
                
            if product_update.category:
                category_id = self.find_or_create_category(product_update.category)
                if category_id:
                    update_vals['categ_id'] = category_id
            
            # Si no hay nada que actualizar
            if not update_vals:
                logging.warning(f"No se proporcionaron campos para actualizar el producto {product_id}")
                return True
                
            # Actualizar producto
            result = self._execute_kw(
                'product.template',
                'write',
                [[product_id], update_vals]
            )
            
            if result:
                logging.info(f"Producto {product_id} actualizado correctamente")
                return True
            else:
                logging.error(f"Error al actualizar producto {product_id}")
                return False
                
        except Exception as e:
            logging.error(f"Error actualizando producto {product_id}: {e}")
            return False
            
    def delete_product(self, product_id: int) -> bool:
        """
        Elimina un producto de la base de datos de Odoo (marcándolo como inactivo).
        """
        try:
            if not self._models:
                self._get_connection()
                
            # Verificar que el producto existe
            product_exists = self._execute_kw(
                'product.template',
                'search_count',
                [[['id', '=', product_id]]]
            )
            
            if not product_exists:
                logging.error(f"Producto con ID {product_id} no encontrado")
                return False
                
            # En lugar de eliminar, marcar como inactivo
            result = self._execute_kw(
                'product.template',
                'write',
                [[product_id], {'active': False}]
            )
            
            if result:
                logging.info(f"Producto {product_id} marcado como inactivo")
                return True
            else:
                logging.error(f"Error al marcar como inactivo el producto {product_id}")
                return False
                
        except Exception as e:
            logging.error(f"Error eliminando producto {product_id}: {e}")
            return False
            
    def get_product_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Busca un producto por su código (default_code) en Odoo.
        """
        try:
            if not self._models:
                self._get_connection()
                
            # Buscar producto por código
            products = self._execute_kw(
                'product.template',
                'search_read',
                [[['default_code', '=', code]]],
                {
                    'limit': 1,
                    'fields': [
                        'id', 'name', 'default_code', 'list_price', 'standard_price',
                        'categ_id', 'active', 'type', 'barcode'
                    ]
                }
            )
            
            if not products:
                return None
                
            product = products[0]
            
            # Extraer categoría
            category_name = None
            if product.get('categ_id'):
                category_id = product['categ_id'][0] if isinstance(product['categ_id'], list) else product['categ_id']
                category_data = self._execute_kw(
                    'product.category',
                    'read',
                    [category_id],
                    {'fields': ['name']}
                )
                if category_data:
                    category_name = category_data[0]['name']
            
            # Construir diccionario de producto
            return {
                'id': product['id'],
                'name': product['name'],
                'default_code': product.get('default_code', ''),
                'list_price': product.get('list_price', 0.0),
                'standard_price': product.get('standard_price', 0.0),
                'categ_id': product['categ_id'][0] if isinstance(product['categ_id'], list) else product.get('categ_id'),
                'category': category_name,
                'active': product.get('active', True),
                'type': product.get('type', 'product'),
                'barcode': product.get('barcode', '')
            }
            
        except Exception as e:
            logging.error(f"Error buscando producto por código '{code}': {e}")
            return None
            
    # NOTA: La implementación original de create_or_update_product que recibía ref_code y product_data
    # ha sido eliminada para evitar duplicidad. Se mantiene la implementación más robusta
    # que se encuentra más abajo en este archivo (línea ~906).
    # Esta implementación incluye manejo de categorías, proveedores y validación de campos.
    
    
    def get_paginated_products(self, page: int = 1, limit: int = 10, sort_by: str = 'id', sort_order: str = 'asc', search: Optional[str] = None, category: Optional[str] = None, include_inactive: bool = False):
        """Obtiene productos paginados, ordenados y filtrados desde Odoo."""
        import logging
        logger = logging.getLogger("odoo_product_service.get_paginated")
        
        try:
            # Asegurar conexión
            if not self._models:
                self._get_connection()
            
            # Verificar qué campos existen en el modelo product.template
            available_fields = self._check_available_fields('product.template')
            logger.info(f"Campos disponibles en product.template: {available_fields[:10]}...")
            
            # Lista base de campos a solicitar
            fields = [
                'id', 'name', 'default_code', 'active', 'is_published',
                'list_price', 'standard_price', 'categ_id', 'seller_ids',
                'product_variant_ids'  # Para obtener variantes del producto
            ]
            
            # Añadir campos personalizados solo si existen
            if 'x_margen_calculado' in available_fields:
                fields.append('x_margen_calculado')
                logger.info("Campo x_margen_calculado encontrado y añadido")
            else:
                logger.warning("Campo x_margen_calculado no encontrado en el modelo")
                
            if 'x_alerta_margen' in available_fields:
                fields.append('x_alerta_margen')
                logger.info("Campo x_alerta_margen encontrado y añadido")
            else:
                logger.warning("Campo x_alerta_margen no encontrado en el modelo")
                
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
            
            logger.info(f"Total productos encontrados: {total}")
            
            # Si no hay resultados, devolver lista vacía
            if total == 0:
                return [], 0
                
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
                    'fields': fields
                }
            )
            
            if odoo_products is None:
                logger.error("search_read devolvió None. Posible problema de conexión con Odoo.")
                return [], 0
                
            logger.info(f"Respuesta de search_read (primeros 5): {odoo_products[:5] if odoo_products else []}")

            if not odoo_products:
                logger.warning("search_read devolvió una lista vacía, pero search_count encontró resultados.")
                return [], total
                
            # Transformar productos a formato de API
            products = self._transform_products(odoo_products)
            
            return products, total
            
        except Exception as e:
            logger.error(f"Error obteniendo productos paginados: {e}", exc_info=True)
            return [], 0
            
    def _transform_products(self, odoo_products):
        """Transforma productos de Odoo al formato de API"""
        import logging
        logger = logging.getLogger("odoo_product_service.transform")
        
        transformed = []
        for p in odoo_products:
            try:
                # Obtener nombre de categoría
                categ_name = None
                categ_id = None
                
                if p.get('categ_id'):
                    if isinstance(p['categ_id'], list) and len(p['categ_id']) > 0:
                        categ_id = p['categ_id'][0]
                        categ_name = p['categ_id'][1] if len(p['categ_id']) > 1 else self._get_category_name(categ_id)
                    elif isinstance(p['categ_id'], int):
                        categ_id = p['categ_id']
                        categ_name = self._get_category_name(categ_id)
                
                # Obtener información del proveedor si existe
                supplier_name = None
                supplier_id = None
                
                if p.get('seller_ids') and len(p.get('seller_ids', [])) > 0:
                    try:
                        # Obtener todos los proveedores del producto
                        seller_ids = p['seller_ids']
                        logger.info(f"Producto {p.get('id')} tiene {len(seller_ids)} proveedores: {seller_ids}")
                        
                        if seller_ids:
                            # Obtener información detallada de los proveedores
                            # En Odoo 18, el campo 'name' se ha cambiado a 'partner_id' en product.supplierinfo
                            seller_info = self._execute_kw(
                                'product.supplierinfo',
                                'search_read',
                                [[('id', 'in', seller_ids)]],
                                {'fields': ['partner_id', 'price', 'delay', 'min_qty', 'product_name', 'product_code']}
                            )
                            
                            logger.info(f"Información de proveedores para producto {p.get('id')}: {seller_info}")
                            
                            if seller_info and len(seller_info) > 0:
                                # Tomar el primer proveedor
                                first_seller = seller_info[0]
                                partner_id_data = first_seller.get('partner_id')
                                
                                if partner_id_data:
                                    # En Odoo, los campos many2one vienen como [id, display_name]
                                    if isinstance(partner_id_data, list) and len(partner_id_data) > 1:
                                        supplier_id = partner_id_data[0]
                                        supplier_name = partner_id_data[1]
                                        logger.info(f"Proveedor encontrado: {supplier_name} (ID: {supplier_id})")
                                    else:
                                        # Si solo tenemos el ID, buscar el nombre en res.partner
                                        if isinstance(partner_id_data, list):
                                            supplier_id = partner_id_data[0]
                                        else:
                                            supplier_id = partner_id_data
                                        
                                        if supplier_id:
                                            partner_info = self._execute_kw(
                                                'res.partner',
                                                'read',
                                                [supplier_id],
                                                {'fields': ['name', 'email', 'phone']}
                                            )
                                            
                                            if partner_info and len(partner_info) > 0:
                                                supplier_name = partner_info[0].get('name')
                                                logger.info(f"Nombre de proveedor obtenido de res.partner: {supplier_name}")
                    except Exception as e:
                        logger.warning(f"Error obteniendo proveedor para producto {p.get('id')}: {e}", exc_info=True)
                
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
                
                # Crear diccionario de producto con valores por defecto
                product_dict = {
                    'id': p.get('id', 0),
                    'name': p.get('name', ''),
                    'default_code': default_code,
                    'list_price': p.get('list_price', 0.0),
                    'standard_price': p.get('standard_price', 0.0),
                    'categ_id': categ_id,
                    'categ_name': categ_name,  # Campo adicional para compatibilidad con frontend
                    'category': categ_name,
                    'active': p.get('active', True),
                    'is_published': p.get('is_published', False),
                    'x_margen_calculado': 0.0,  # Valor por defecto
                    'x_alerta_margen': False,   # Valor por defecto
                    # Campos adicionales para compatibilidad con frontend
                    'code': default_code,
                    'price': p.get('list_price', 0.0),
                    'stock': 0,  # Placeholder, se podría obtener de stock.quant
                    'supplier_name': supplier_name,
                    'supplier_id': supplier_id,
                    'barcode': barcode,
                    'description_sale': description_sale,
                    'description_purchase': description_purchase,
                    'description': description
                }
                
                # Añadir campos personalizados si existen en la respuesta de Odoo
                if 'x_margen_calculado' in p:
                    product_dict['x_margen_calculado'] = p.get('x_margen_calculado', 0.0)
                    
                if 'x_alerta_margen' in p:
                    product_dict['x_alerta_margen'] = p.get('x_alerta_margen', False)
                
                # Calcular margen si no existe el campo personalizado pero tenemos precio de venta y coste
                if product_dict['x_margen_calculado'] == 0.0 and product_dict['standard_price'] > 0:
                    try:
                        margen = ((product_dict['list_price'] - product_dict['standard_price']) / product_dict['standard_price']) * 100
                        product_dict['x_margen_calculado'] = round(margen, 2)
                    except (ZeroDivisionError, TypeError):
                        product_dict['x_margen_calculado'] = 0.0
                
                transformed.append(product_dict)
            except Exception as e:
                logger.error(f"Error transformando producto {p.get('id', 'unknown')}: {e}")
                # Continuar con el siguiente producto
                continue
                
        logger.info(f"Transformados {len(transformed)} productos de {len(odoo_products)} recibidos")
        return transformed
        
    def _get_category_name(self, category_id):
        """Obtiene el nombre de una categoría por su ID"""
        if not category_id:
            return None
            
        try:
            category_data = self._execute_kw(
                'product.category',
                'read',
                [category_id],
                {'fields': ['name']}
            )
            
            if category_data and len(category_data) > 0:
                return category_data[0]['name']
            return None
        except Exception as e:
            logging.error(f"Error obteniendo nombre de categoría {category_id}: {e}")
            return None
            
    def _ensure_custom_field(self, model_name, field_name, field_type, field_label):
        """
        Asegura que un campo personalizado existe en un modelo de Odoo.
        Si no existe, lo crea.
        
        Args:
            model_name: Nombre del modelo (ej: 'product.template')
            field_name: Nombre del campo (debe empezar con 'x_')
            field_type: Tipo de campo ('char', 'text', 'integer', 'float', 'boolean', etc.)
            field_label: Etiqueta visible del campo
            
        Returns:
            bool: True si el campo ya existía o se creó correctamente, False en caso de error
        """
        try:
            if not self._models:
                self._get_connection()
                
            # Verificar si el campo ya existe
            ir_model_fields = self._models.execute_kw(
                'ir.model.fields', 
                'search_read', 
                [[['model', '=', model_name], ['name', '=', field_name]]], 
                {'fields': ['id']}
            )
            
            if ir_model_fields:
                logging.info(f"Campo personalizado {field_name} ya existe en {model_name}")
                return True
                
            # Obtener el ID del modelo
            model_id = self._models.execute_kw(
                'ir.model', 
                'search', 
                [[['model', '=', model_name]]]
            )
            
            if not model_id:
                logging.error(f"No se encontró el modelo {model_name}")
                return False
                
            # Crear el campo personalizado
            field_vals = {
                'name': field_name,
                'field_description': field_label,
                'model_id': model_id[0],
                'ttype': field_type,
                'state': 'manual',
                'store': True,
            }
            
            field_id = self._models.execute_kw('ir.model.fields', 'create', [field_vals])
            logging.info(f"Campo personalizado {field_name} creado en {model_name} con ID {field_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error al crear campo personalizado {field_name} en {model_name}: {str(e)}")
            return False
    
    def _check_available_fields(self, model_name):
        """Verifica qué campos están disponibles en un modelo de Odoo"""
        try:
            if not self._models:
                self._get_connection()
                
            # Obtener todos los campos del modelo
            fields_data = self._execute_kw(
                'ir.model.fields',
                'search_read',
                [[('model', '=', model_name)]],
                {'fields': ['name', 'field_description']}
            )
            
            if not fields_data:
                return []
                
            # Extraer solo los nombres de los campos
            field_names = [field['name'] for field in fields_data]
            return field_names
            
        except Exception as e:
            logging.error(f"Error al verificar campos disponibles en {model_name}: {e}")
            return []

    def find_or_create_category(self, category_name: str) -> int:
        """
        Busca una categoría por nombre y la crea si no existe.
        
        Args:
            category_name: Nombre de la categoría a buscar o crear
            
        Returns:
            ID de la categoría encontrada o creada, o 1 (categoría por defecto) en caso de error
        """
        import logging
        logger = logging.getLogger("odoo_product_service.category")
        
        if not category_name or not isinstance(category_name, str):
            category_name = "Sin Categoría"

        try:
            if not self._models:
                self._get_connection()

            # Primero intentamos buscar la categoría por nombre exacto
            domain = [('name', '=', category_name)]
            category_ids = self._execute_kw('product.category', 'search', [domain], {'limit': 1})

            if category_ids:
                category_id = category_ids[0]
                logger.info(f"Categoría encontrada: '{category_name}' con ID: {category_id}")
                return category_id
            else:
                # Si no existe, intentamos crearla
                logger.info(f"Categoría '{category_name}' no encontrada. Creando...")
                new_category_vals = {'name': category_name}
                new_category_id = self._execute_kw('product.category', 'create', [new_category_vals])
                
                if new_category_id:
                    logger.info(f"Categoría '{category_name}' creada con ID: {new_category_id}")
                    return new_category_id
                else:
                    logger.error(f"No se pudo crear la categoría '{category_name}'. Usando categoría por defecto.")
                    return 1  # ID de la categoría 'All' por defecto en Odoo

        except Exception as e:
            logger.error(f"Error en find_or_create_category para '{category_name}': {e}")
            # En caso de error, devolvemos la categoría por defecto (ID 1) en lugar de lanzar una excepción
            return 1  # ID de la categoría 'All' por defecto en Odoo
            
    # NOTA: Se ha eliminado código duplicado e incorrecto que estaba entre el método find_or_create_category y create_or_update_product

    def create_or_update_product(self, product_data):
        """
        Crea o actualiza un producto en Odoo.
        
        Args:
            product_data: Diccionario con datos del producto
            
        Returns:
            ID del producto creado o actualizado, None en caso de error
        """
        import logging
        logger = logging.getLogger("odoo_product_service.create_update")
        logger.info(f"[TEST-LOG] Recibido product_data: {product_data}")
        
        try:
            if not self._models:
                self._get_connection()
                
            # Validar campos obligatorios
            if 'nombre' not in product_data or not product_data['nombre']:
                logger.error("Error: El campo 'nombre' es obligatorio para crear/actualizar un producto")
                return None
                
            if 'default_code' not in product_data or not product_data['default_code']:
                logger.error("Error: El campo 'default_code' es obligatorio para crear/actualizar un producto")
                return None
            
            # Extraer datos principales
            nombre_producto = product_data['nombre']
            referencia = product_data['default_code']
            precio_venta = float(product_data.get('precio_venta', 0.0))
            precio_coste = float(product_data.get('precio_coste', 0.0))
            categoria = product_data.get('categoria', 'Sin Categoría')
            descripcion = product_data.get('descripcion', '')
            
            logger.info(f"Procesando producto: {nombre_producto} (Ref: {referencia})")
            
            # Buscar si ya existe el producto por referencia
            existing = self._execute_kw(
                'product.template', 
                'search_read', 
                [[('default_code', '=', referencia)]], 
                {'fields': ['id'], 'limit': 1}
            )
            
            # Buscar o crear categoría (con manejo de errores mejorado)
            try:
                categoria_id = self.find_or_create_category(categoria)
                logger.info(f"Categoría asignada: {categoria} (ID: {categoria_id})")
            except Exception as e:
                logger.error(f"Error al buscar/crear categoría '{categoria}': {e}. Usando categoría por defecto.")
                categoria_id = 1  # Usar categoría por defecto 'All'
            
            # Preparar valores del producto
            product_vals = {
                'name': nombre_producto,
                'default_code': referencia,
                'list_price': precio_venta,
                'standard_price': precio_coste,
                'categ_id': categoria_id,
                'type': 'consu',  # En Odoo 18 se usa 'consu' para productos consumibles
                'sale_ok': True,
                'purchase_ok': True,
                'active': True,
                'description': descripcion
            }
            
            # Eliminar campos problemáticos
            if 'detailed_type' in product_vals:
                logger.warning(f"Eliminando campo detailed_type no compatible con Odoo 18")
                del product_vals['detailed_type']
                
            # Asegurar que type está presente y es válido
            if 'type' not in product_vals:
                logger.warning(f"Añadiendo campo type='consu' que faltaba")
                product_vals['type'] = 'consu'
                
            # Log detallado de los valores finales
            logger.info(f"Valores finales para Odoo: {product_vals}")
                
            # Crear o actualizar producto con manejo de errores mejorado
            product_id = None
            try:
                if existing:
                    # Actualizar
                    product_id = existing[0]['id']
                    self._execute_kw('product.template', 'write', [[product_id], product_vals])
                    logger.info(f"Producto '{nombre_producto}' actualizado (ID: {product_id})")
                else:
                    # Crear
                    product_id = self._execute_kw('product.template', 'create', [product_vals])
                    logger.info(f"Producto '{nombre_producto}' creado (ID: {product_id})")
            except Exception as e:
                logger.error(f"Error al crear/actualizar producto '{nombre_producto}': {e}")
                return None

            # Si no se pudo crear/actualizar el producto, salir
            if not product_id:
                logger.error(f"No se pudo crear/actualizar el producto '{nombre_producto}'")
                return None

            # Asociar proveedor si hay datos
            supplier_id = None
            if 'proveedor_id' in product_data:
                supplier_id = product_data['proveedor_id']
            elif 'supplier_id' in product_data:
                supplier_id = product_data['supplier_id']
            
            if supplier_id:
                try:
                    # Relación producto-proveedor
                    supplier_domain = [
                        ('product_tmpl_id', '=', product_id),
                        ('partner_id', '=', supplier_id)
                    ]
                    existing_supplier = self._execute_kw(
                        'product.supplierinfo', 'search_read', [supplier_domain], {'fields': ['id'], 'limit': 1}
                    )
                    supplier_data = {
                        'product_tmpl_id': product_id,
                        'partner_id': supplier_id,
                        'product_code': referencia,
                        'price': precio_coste,
                        'min_qty': 1.0,
                        'delay': 1
                    }
                    if existing_supplier:
                        supplier_info_id = existing_supplier[0]['id']
                        self._execute_kw('product.supplierinfo', 'write', [[supplier_info_id], supplier_data])
                        logger.info(f"Proveedor actualizado para producto {product_id} y proveedor {supplier_id}")
                    else:
                        supplier_info_id = self._execute_kw('product.supplierinfo', 'create', [supplier_data])
                        logger.info(f"Proveedor asociado a producto {product_id} (supplierinfo {supplier_info_id})")
                except Exception as e:
                    # Si falla la asociación con el proveedor, no fallamos todo el proceso
                    logger.error(f"Error al asociar proveedor {supplier_id} al producto {product_id}: {e}")
            
            return product_id
        except Exception as e:
            logger.error(f"Error general en create_or_update_product: {e}", exc_info=True)
            return None

    def archive_product(self, product_id):
        """
        Archiva (desactiva) un producto en Odoo.
        
        Args:
            product_id: ID del producto a archivar
            
        Returns:
            bool: True si se archivó correctamente, False en caso contrario
        """
        import logging
        logger = logging.getLogger("odoo_product_service.archive")
        
        try:
            if not self._models:
                self._get_connection()
            
            # Verificar que el producto existe
            product = self._execute_kw(
                'product.template',
                'search_read',
                [[('id', '=', product_id)]],
                {'fields': ['id', 'active'], 'limit': 1}
            )
            
            if not product:
                logger.warning(f"No se encontró el producto con ID {product_id} para archivar")
                return False
            
            # Si ya está archivado (inactivo), no hacer nada
            if product[0].get('active') is False:
                logger.info(f"El producto con ID {product_id} ya está archivado")
                return True
            
            # Archivar el producto (establecer active=False)
            result = self._execute_kw(
                'product.template',
                'write',
                [[product_id], {'active': False}]
            )
            
            logger.info(f"Producto con ID {product_id} archivado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al archivar producto con ID {product_id}: {e}", exc_info=True)
            return False


    def front_to_odoo_product_dict(self, producto, proveedor_nombre):
        """
        Convierte un producto del formato frontend/Excel al formato Odoo para crear o actualizar.
        
        Args:
            producto: Diccionario con datos del producto desde el frontend o Excel
            proveedor_nombre: Nombre del proveedor para asociar al producto
            
        Returns:
            Diccionario con formato compatible con Odoo para crear/actualizar producto
        """
        import logging
        logger = logging.getLogger("odoo_product_service.transform")
        
        try:
            # Buscar o crear proveedor
            proveedor_id = None
            if proveedor_nombre:
                try:
                    # Buscar proveedor por nombre
                    proveedor = self._execute_kw(
                        'res.partner',
                        'search_read',
                        [[('name', '=', proveedor_nombre)]],
                        {'fields': ['id'], 'limit': 1}
                    )
                    
                    if proveedor:
                        proveedor_id = proveedor[0]['id']
                        logger.info(f"Proveedor '{proveedor_nombre}' encontrado con ID: {proveedor_id}")
                    else:
                        # Crear proveedor si no existe
                        try:
                            nuevo_proveedor = {
                                'name': proveedor_nombre,
                                'supplier_rank': 1,  # Lo marcamos como proveedor
                                'company_type': 'company'
                            }
                            logger.info(f"Datos para crear proveedor: {nuevo_proveedor}")
                            proveedor_id = self._execute_kw('res.partner', 'create', [nuevo_proveedor])
                            logger.info(f"Nuevo proveedor '{proveedor_nombre}' creado con ID: {proveedor_id}")
                        except Exception as e:
                            logger.error(f"Error al crear el proveedor '{proveedor_nombre}': {str(e)}")
                except Exception as e:
                    logger.error(f"Error general al procesar proveedor '{proveedor_nombre}': {str(e)}")
                    # Continuamos sin proveedor si hay error
            
            # Transformar datos del formato frontend/Excel al formato de Odoo
            nombre = producto.get('nombre') or producto.get('name', '')
            codigo = producto.get('codigo') or producto.get('referencia_proveedor') or producto.get('default_code', '')
            
            # Manejo mejorado de precios
            precio_venta = 0.0
            if 'precio_venta' in producto and producto['precio_venta']:
                try:
                    precio_venta = float(producto['precio_venta'])
                except (ValueError, TypeError):
                    if isinstance(producto['precio_venta'], str):
                        # Limpiar formato de precio (quitar €, espacios, etc.)
                        precio_str = producto['precio_venta'].replace('€', '').replace(',', '.').strip()
                        try:
                            precio_venta = float(precio_str)
                        except (ValueError, TypeError):
                            logger.warning(f"No se pudo convertir precio_venta: {producto['precio_venta']}")
            
            # Si no hay precio_venta, intentar con list_price
            if precio_venta == 0.0 and 'list_price' in producto and producto['list_price']:
                try:
                    precio_venta = float(producto['list_price'])
                except (ValueError, TypeError):
                    if isinstance(producto['list_price'], str):
                        precio_str = producto['list_price'].replace('€', '').replace(',', '.').strip()
                        try:
                            precio_venta = float(precio_str)
                        except (ValueError, TypeError):
                            logger.warning(f"No se pudo convertir list_price: {producto['list_price']}")
            
            # Manejo similar para precio_coste
            precio_coste = 0.0
            if 'precio_coste' in producto and producto['precio_coste']:
                try:
                    precio_coste = float(producto['precio_coste'])
                except (ValueError, TypeError):
                    if isinstance(producto['precio_coste'], str):
                        precio_str = producto['precio_coste'].replace('€', '').replace(',', '.').strip()
                        try:
                            precio_coste = float(precio_str)
                        except (ValueError, TypeError):
                            logger.warning(f"No se pudo convertir precio_coste: {producto['precio_coste']}")
            
            # Si no hay precio_coste, intentar con standard_price
            if precio_coste == 0.0 and 'standard_price' in producto and producto['standard_price']:
                try:
                    precio_coste = float(producto['standard_price'])
                except (ValueError, TypeError):
                    if isinstance(producto['standard_price'], str):
                        precio_str = producto['standard_price'].replace('€', '').replace(',', '.').strip()
                        try:
                            precio_coste = float(precio_str)
                        except (ValueError, TypeError):
                            logger.warning(f"No se pudo convertir standard_price: {producto['standard_price']}")
            
            # Buscar precio en campos específicos del Excel de NEVIR
            if precio_venta == 0.0 and 'P.V.P FINAL CLIENTE' in producto:
                try:
                    pvp = producto['P.V.P FINAL CLIENTE']
                    if isinstance(pvp, str):
                        pvp = pvp.replace('€', '').replace(',', '.').strip()
                    precio_venta = float(pvp)
                except (ValueError, TypeError):
                    logger.warning(f"No se pudo convertir P.V.P FINAL CLIENTE: {producto.get('P.V.P FINAL CLIENTE')}")
            
            if precio_coste == 0.0 and 'IMPORTE BRUTO' in producto:
                try:
                    importe = producto['IMPORTE BRUTO']
                    if isinstance(importe, str):
                        importe = importe.replace('€', '').replace(',', '.').strip()
                    precio_coste = float(importe)
                except (ValueError, TypeError):
                    logger.warning(f"No se pudo convertir IMPORTE BRUTO: {producto.get('IMPORTE BRUTO')}")
            
            # Registrar los precios encontrados
            logger.info(f"Precios para {nombre}: venta={precio_venta}, coste={precio_coste}")
            
            categoria = producto.get('categoria') or producto.get('category', 'Sin Categoría')
            descripcion = producto.get('descripcion') or producto.get('description', '')
            
            # Construir diccionario para Odoo
            odoo_dict = {
                'nombre': nombre,
                'default_code': codigo,
                'precio_venta': precio_venta,
                'precio_coste': precio_coste,
                'categoria': categoria,
                'descripcion': descripcion,
                'type': 'consu'  # Valor por defecto para productos físicos en Odoo 18
            }
            
            # Añadir ID del proveedor si se encontró
            if proveedor_id:
                odoo_dict['proveedor_id'] = proveedor_id
            
            logger.info(f"Producto transformado: {nombre} (Ref: {codigo})")
            return odoo_dict
        except Exception as e:
            logger.error(f"Error transformando producto para Odoo: {e}", exc_info=True)
            # Devolver un diccionario básico para evitar errores en cascada
            return {
                'nombre': producto.get('nombre', 'Producto sin nombre'),
                'default_code': producto.get('codigo', 'SIN_CODIGO'),
                'precio_venta': 0.0,
                'precio_coste': 0.0,
                'categoria': 'Sin Categoría',
                'type': 'consu'  # Valor por defecto para productos físicos en Odoo 18
            }

# Instancia global para evitar errores de importación circular
odoo_product_service = OdooProductService()