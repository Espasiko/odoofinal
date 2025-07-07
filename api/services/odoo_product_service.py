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
                barcode=product.get('barcode'),
                weight=product.get('weight', 0.0),
                sale_ok=product.get('sale_ok', True),
                purchase_ok=product.get('purchase_ok', True),
                available_in_pos=product.get('available_in_pos', False),
                to_weight=product.get('to_weight', False),
                is_published=product.get('is_published', False),
                website_sequence=product.get('website_sequence', 0),
                description_sale=product.get('description_sale', ''),
                description=product.get('description', ''),
                description_purchase=product.get('description_purchase', '')
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
            
    def create_or_update_product(self, ref_code: str, product_data: Dict[str, Any]) -> Optional[int]:
        """
        Crea o actualiza un producto en Odoo basado en su código de referencia.
        
        Args:
            ref_code: Código de referencia del producto (default_code)
            product_data: Diccionario con los datos del producto
            
        Returns:
            ID del producto creado o actualizado, None en caso de error
        """
        try:
            if not self._models:
                self._get_connection()
                
            # Buscar si el producto ya existe
            existing_product = find_existing_product(self, ref_code)
            
            # Preparar valores para el producto
            product_vals = prepare_product_vals(product_data, ref_code)
            
            # Si existe el producto, actualizarlo
            if existing_product:
                product_id = existing_product['id']
                logging.info(f"Actualizando producto existente '{ref_code}' con ID: {product_id}")
                
                result = self._execute_kw(
                    'product.template',
                    'write',
                    [[product_id], product_vals]
                )
                
                if result:
                    logging.info(f"Producto '{ref_code}' actualizado correctamente.")
                    return product_id
                else:
                    logging.error(f"Error al actualizar producto '{ref_code}'")
                    return None
            
            # Si no existe, crear nuevo producto
            logging.info(f"Creando nuevo producto '{ref_code}'")
            new_product_id = self._execute_kw(
                'product.template',
                'create',
                [product_vals]
            )
            
            if new_product_id:
                logging.info(f"Producto '{product_vals.get('name')}' creado con ID: {new_product_id}")
                return new_product_id
            else:
                logging.error(f"Error al crear producto '{product_vals.get('name')}'")
                return None

        except Exception as e:
            logging.error(f"Error en create_or_update para producto '{ref_code}': {e}", exc_info=True)
            return None
    
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
                
                # Crear diccionario de producto con valores por defecto
                product_dict = {
                    'id': p.get('id', 0),
                    'name': p.get('name', ''),
                    'default_code': p.get('default_code', ''),
                    'list_price': p.get('list_price', 0.0),
                    'standard_price': p.get('standard_price', 0.0),
                    'categ_id': categ_id,
                    'category': categ_name,
                    'active': p.get('active', True),
                    'is_published': p.get('is_published', False),
                    'x_margen_calculado': 0.0,  # Valor por defecto
                    'x_alerta_margen': False,   # Valor por defecto
                    # Campos adicionales para compatibilidad con frontend
                    'code': p.get('default_code', ''),
                    'price': p.get('list_price', 0.0),
                    'stock': 0,  # Placeholder, se podría obtener de stock.quant
                    'supplier_name': supplier_name,
                    'supplier_id': supplier_id
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
        Busca una categoría de producto por nombre. Si no existe, la crea.
        Devuelve el ID de la categoría.
        """
        if not category_name or not isinstance(category_name, str):
            category_name = "Sin Categoría"

        try:
            if not self._models:
                self._get_connection()

            domain = [('name', '=', category_name)]
            category_ids = self._execute_kw('product.category', 'search', [domain], {'limit': 1})

            if category_ids:
                category_id = category_ids[0]
                logging.info(f"Categoría encontrada: '{category_name}' con ID: {category_id}")
                return category_id
            else:
                logging.info(f"Categoría '{category_name}' no encontrada. Creando...")
                new_category_vals = {'name': category_name}
                new_category_id = self._execute_kw('product.category', 'create', [new_category_vals])
                
                if new_category_id:
                    logging.info(f"Categoría '{category_name}' creada con ID: {new_category_id}")
                    return new_category_id
                else:
                    logging.error(f"No se pudo crear la categoría '{category_name}'")
                    raise Exception(f"Fallo al crear la categoría '{category_name}' en Odoo.")

        except Exception as e:
            logging.error(f"Error en find_or_create_category para '{category_name}': {e}")
            raise

# Instancia global para evitar errores de importación circular
odoo_product_service = OdooProductService()