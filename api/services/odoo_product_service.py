from typing import List, Optional, Dict, Union, Any
from .odoo_base_service import OdooBaseService
import logging
from ..models.schemas import Product, ProductCreate, OdooProductUpdate
from fastapi import HTTPException
import logging

class OdooProductService(OdooBaseService):
    """Servicio para gestión de productos en Odoo"""

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
                        'description_sale', 'description_purchase', 'seller_ids',
                        'product_tag_ids', 'public_categ_ids', 'pos_categ_ids',
                        'taxes_id', 'supplier_taxes_id'
                    ]
                }
            )
            
            if not product_data:
                return None
            
            transformed_data = self._transform_products(product_data)
            # Odoo's search_read returns a list, even for one result
            return Product(**transformed_data[0])

        except Exception as e:
            logging.error(f"Error fetching product {product_id}: {str(e)}")
            return None

    def _prepare_product_data_for_odoo(self, product_data: Union[ProductCreate, OdooProductUpdate]) -> Dict:
        """
        Prepara el diccionario de datos para Odoo, filtrando campos no existentes
        y manejando mapeos de nombres si es necesario.
        """
        data_dict = product_data.model_dump(exclude_unset=True)
        
        allowed_fields = {
            'name', 'default_code', 'list_price', 'standard_price', 'categ_id',
            'barcode', 'active', 'type', 'weight', 'sale_ok', 'purchase_ok',
            'available_in_pos', 'to_weight', 'is_published', 'website_sequence',
            'description_sale', 'description_purchase', 'public_categ_ids',
            'seller_ids', 'taxes_id', 'supplier_taxes_id',
            'property_account_income_id', 'property_account_expense_id'
        }

        field_mappings = {
            'price': 'list_price',
            'cost': 'standard_price',
            'code': 'default_code'
        }

        vals = {}
        for key, value in data_dict.items():
            odoo_key = field_mappings.get(key, key)
            if odoo_key in allowed_fields:
                vals[odoo_key] = value

        return vals

    def create_product(self, product_data: ProductCreate) -> Dict:
        """
        Crea un nuevo producto en Odoo.
        """
        vals = self._prepare_product_data_for_odoo(product_data)
        if not vals:
            raise HTTPException(status_code=400, detail="No se proporcionaron datos válidos para crear el producto.")
        
        try:
            if not self._models:
                self._get_connection()

            product_id = self._execute_kw(
                'product.template', 'create', [vals]
            )
            
            if product_id:
                created_product = self.get_product_by_id(product_id)
                if created_product:
                    return created_product.model_dump()
                else:
                    raise HTTPException(status_code=404, detail=f"Producto creado con ID {product_id} pero no se pudo recuperar.")
            else:
                raise HTTPException(status_code=500, detail="No se pudo crear el producto en Odoo, no se devolvió ID.")
                
        except Exception as e:
            logging.error(f"Error al crear producto en Odoo: {e}")
            raise HTTPException(status_code=500, detail=f"Ocurrió un error al comunicarse con Odoo: {str(e)}")

    def update_product(self, product_id: int, update_data: OdooProductUpdate) -> Optional[Product]:
        """
        Actualiza un producto existente en Odoo usando write().
        """
        vals = self._prepare_product_data_for_odoo(update_data)

        if not vals:
            logging.warning(f"No se proporcionaron campos válidos para actualizar el producto {product_id}. No se realizará ninguna acción.")
            return self.get_product_by_id(product_id)

        try:
            if not self._models:
                self._get_connection()

            success = self._execute_kw('product.template', 'write', [[product_id], vals])
            
            if success:
                logging.info(f"Producto {product_id} actualizado exitosamente en Odoo.")
            else:
                logging.warning(f"El método 'write' de Odoo para el producto {product_id} no devolvió un error, pero tampoco éxito explícito.")
            
            return self.get_product_by_id(product_id)
        except Exception as e:
            logging.error(f"Error al actualizar el producto {product_id} en Odoo: {str(e)}")
            return None

    def archive_product(self, product_id: int) -> bool:
        """
        Archiva (desactiva) un producto en Odoo (active=False).
        """
        import logging
        logger = logging.getLogger("odoo_product_archive")
        try:
            if not self._models:
                self._get_connection()
            # Se elimina la comprobación de existencia previa para evitar condiciones de carrera.
            # El método 'write' de Odoo devolverá False si el ID no existe, lo que es más eficiente.
            res = self._execute_kw('product.template', 'write', [[product_id], {'active': False}])
            
            if not res:
                logger.error(f"Fallo al archivar producto {product_id} en Odoo. Puede que no exista o ya esté archivado.")
                return False
            logger.info(f"Producto {product_id} archivado correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error archivando producto {product_id}: {str(e)}")
            return False

    def resolve_supplier(self, supplier_name: str) -> Optional[int]:
        """Busca un proveedor por nombre y lo crea si no existe."""
        if not supplier_name:
            return None
        try:
            if not self._models:
                self._get_connection()
            supplier_ids = self._execute_kw('res.partner', 'search', [[('name', 'ilike', supplier_name), ('is_company', '=', True)]], {'limit': 1})
            if supplier_ids:
                return supplier_ids[0]
            else:
                new_supplier_id = self._execute_kw('res.partner', 'create', [{'name': supplier_name, 'is_company': True}])
                logging.info(f"Nuevo proveedor '{supplier_name}' creado con ID: {new_supplier_id}")
                return new_supplier_id
        except Exception as e:
            logging.error(f"Error resolviendo proveedor '{supplier_name}': {e}")
            return None

    def resolve_category(self, category_name: str, subcategory_name: Optional[str] = None) -> Optional[int]:
        """Busca una categoría y subcategoría, creándolas si no existen."""
        if not category_name:
            return None
        try:
            if not self._models:
                self._get_connection()
            # Busca la categoría padre
            parent_cat_ids = self._execute_kw('product.category', 'search', [[('name', 'ilike', category_name)]], {'limit': 1})
            if parent_cat_ids:
                parent_id = parent_cat_ids[0]
            else:
                parent_id = self._execute_kw('product.category', 'create', [{'name': category_name}])
                logging.info(f"Nueva categoría '{category_name}' creada con ID: {parent_id}")

            if not subcategory_name:
                return parent_id

            # Busca la subcategoría
            sub_cat_ids = self._execute_kw('product.category', 'search', [[('name', 'ilike', subcategory_name), ('parent_id', '=', parent_id)]], {'limit': 1})
            if sub_cat_ids:
                return sub_cat_ids[0]
            else:
                sub_id = self._execute_kw('product.category', 'create', [{'name': subcategory_name, 'parent_id': parent_id}])
                logging.info(f"Nueva subcategoría '{subcategory_name}' creada con ID: {sub_id} bajo '{category_name}'")
                return sub_id
        except Exception as e:
            logging.error(f"Error resolviendo categoría '{category_name}': {e}")
            return None

    def front_to_odoo_product_dict(self, product_data: Dict[str, Any], supplier_name: str) -> Dict[str, Any]:
        """Convierte un dict de la IA a un dict para Odoo, incluyendo seller_ids."""
        vals = {}
        if product_data.get('nombre'):
            vals['name'] = product_data['nombre']
        if product_data.get('referencia_proveedor'):
            vals['default_code'] = str(product_data['referencia_proveedor'])
        # Cost price
        if product_data.get('precio_coste') is not None:
            try:
                vals['standard_price'] = float(product_data['precio_coste'])
            except (ValueError, TypeError):
                logging.warning(f"No se pudo convertir 'precio_coste' a float para {product_data.get('nombre')}")

        # Sale price (PVP)
        posible_pvp_keys = [
            'precio_venta', 'precio_pvp', 'precio_publico', 'pvp', 'precio_venta_publico',
            'precio_final', 'precio_final_cliente', 'precio_venta_cliente', 'pvp_final', 'precio', 'precio_proveedor'
        ]
        for key in posible_pvp_keys:
            if product_data.get(key) is not None:
                try:
                    vals['list_price'] = float(product_data[key])
                except (ValueError, TypeError):
                    logging.warning(f"No se pudo convertir '{key}' a float para {product_data.get('nombre')}")
                break
        if product_data.get('descripcion'):
            vals['description_sale'] = product_data['descripcion']
        
        category_id = self.resolve_category(product_data.get('categoria'), product_data.get('subcategoria'))
        if category_id:
            vals['categ_id'] = category_id

        supplier_id = self.resolve_supplier(supplier_name)
        if supplier_id and 'standard_price' in vals:
            vals['seller_ids'] = [(0, 0, {
                'partner_id': supplier_id,
                'price': vals['standard_price'],
                'product_code': product_data.get('referencia_proveedor')
            })]
        
        return vals

    def create_or_update_product(self, product_vals: Dict[str, Any]) -> Optional[int]:
        """
        Busca un producto por 'default_code'. Si existe, lo actualiza. Si no, lo crea.
        """
        try:
            if not self._models:
                self._get_connection()

            ref_code = product_vals.get('default_code', 'SIN_CODIGO')
            if not ref_code:
                logging.warning(f"Producto sin 'default_code' no puede ser procesado: {product_vals.get('name')}")
                return None
            # Buscar por default_code
            product_ids = self._execute_kw('product.template', 'search', [[('default_code', '=', ref_code)]], {'limit': 1})
            
            if product_ids:
                # --- LÓGICA DE ACTUALIZACIÓN ---
                product_id = product_ids[0]
                
                # Actualiza los campos básicos del producto si hay alguno.
                if product_vals:
                    self._execute_kw('product.template', 'write', [[product_id], product_vals])
                logging.info(f"Producto '{product_vals.get('name', ref_code)}' (ID: {product_id}) actualizado.")

                return product_id
            else:
                # --- LÓGICA DE CREACIÓN ---
                # Volvemos a añadir los datos del proveedor para la creación.
                new_product_id = self._execute_kw('product.template', 'create', [product_vals])
                logging.info(f"Producto '{product_vals.get('name')}' creado con ID: {new_product_id}.")
                return new_product_id

        except Exception as e:
            logging.error(f"Error en create_or_update para producto '{ref_code}': {e}", exc_info=True)
            return None





    
    def get_paginated_products(self, page: int = 1, limit: int = 10, sort_by: str = 'id', sort_order: str = 'asc', search: Optional[str] = None, category: Optional[str] = None, include_inactive: bool = False):
        """Obtiene productos paginados, ordenados y filtrados desde Odoo."""
        logger = logging.getLogger("odoo_product_service.get_paginated")
        logger.info(f"--- Iniciando get_paginated_products con page={page}, limit={limit}, include_inactive={include_inactive} ---")

        offset = (page - 1) * limit
        order = f'{sort_by} {sort_order.upper()}'

        domain = []
        if not include_inactive:
            domain.append(('active', '=', True))
        if search:
            domain.extend(['|', ('name', 'ilike', search), ('default_code', 'ilike', search)])
        if category:
            category_id = self._execute_kw('product.category', 'search', [[('name', 'ilike', category)]], {'limit': 1})
            if category_id:
                domain.append(('categ_id', '=', category_id[0]))

        logger.info(f"Dominio de búsqueda para Odoo: {domain}")

        try:
            total = self._execute_kw('product.template', 'search_count', [domain])
            logger.info(f"Total de productos encontrados por search_count: {total}")

            if total == 0:
                logger.warning("search_count devolvió 0. Finalizando búsqueda.")
                return [], 0

            odoo_products = self._execute_kw(
                'product.template',
                'search_read',
                [domain],
                {
                    'offset': offset,
                    'limit': limit,
                    'order': order,
                    'fields': ['id', 'name', 'default_code', 'active', 'is_published']
                }
            )
            
            logger.info(f"Respuesta de search_read (primeros 5): {odoo_products[:5]}")

            if not odoo_products:
                logger.warning("search_read devolvió una lista vacía, pero search_count encontró resultados.")
                return [], total

            products = [Product(**p) for p in self._transform_products(odoo_products)]
            logger.info(f"Transformación a Pydantic exitosa. Devolviendo {len(products)} productos.")
            return products, total
        except Exception as e:
            logger.error(f"EXCEPCIÓN CRÍTICA en get_paginated_products: {e}", exc_info=True)
            return [], 0

    def _transform_products(self, odoo_products: List[Dict]) -> List[Dict]:
        transformed = []
        for p in odoo_products:
            data = p.copy()
            if data.get('categ_id') and isinstance(data['categ_id'], list):
                data['categ_id'] = data['categ_id'][0]
            for key in ['default_code', 'description_sale', 'description_purchase', 'barcode']:
                if data.get(key) is False:
                    data[key] = '' if key != 'barcode' else None
            transformed.append(data)
        return transformed

    def get_products(self, offset=0, limit=100):
        """Obtiene productos desde Odoo"""
        try:
            if not self._models:
                self._get_connection()

            print(f"ODOO_SERVICE: Obteniendo productos de Odoo con offset {offset} y límite {limit}...")
            odoo_products = self._execute_kw(
                'product.product',
                'search_read',
                [[]],
                {'offset': offset, 'limit': limit, 'fields': [
                    'id', 'name', 'default_code', 'list_price', 'categ_id', 'active',
                    'type', 'standard_price', 'barcode', 'weight',
                    'sale_ok', 'purchase_ok', 'available_in_pos', 'to_weight',
                    'is_published', 'website_sequence', 'description_sale',
                    'description_purchase', 'seller_ids',
                    'product_tag_ids', 'public_categ_ids', 'pos_categ_ids',
                    'taxes_id', 'supplier_taxes_id'
                ]}
            )
            print(f"ODOO_SERVICE: Datos obtenidos: {len(odoo_products) if odoo_products else 0} productos")
        
            if not odoo_products:
                print("ODOO_SERVICE: No se pudieron leer datos, usando fallback")
                return self._get_fallback_products()
        
            # Transformar a formato esperado
            print("ODOO_SERVICE: Transformando datos...")
            transformed_products = []
            for p in odoo_products:
                category_name = self._get_category_name(p.get('categ_id'))
                # Extraer solo el ID de la categoría si viene como [id, name]
                categ_id_value = None
                if p.get('categ_id'):
                    if isinstance(p['categ_id'], list) and len(p['categ_id']) > 0:
                        categ_id_value = p['categ_id'][0]  # Solo el ID
                    elif isinstance(p['categ_id'], int):
                        categ_id_value = p['categ_id']
            
                # Asegurar que default_code sea string
                default_code = p.get('default_code')
                if default_code is False or default_code is None:
                    default_code = ''
                elif not isinstance(default_code, str):
                    default_code = str(default_code)
            
                # Asegurar que description_sale sea string
                description_sale = p.get('description_sale')
                if description_sale is False or description_sale is None:
                    description_sale = ''
                elif not isinstance(description_sale, str):
                    description_sale = str(description_sale)
            
                # Asegurar que description_purchase sea string
                description_purchase = p.get('description_purchase')
                if description_purchase is False or description_purchase is None:
                    description_purchase = ''
                elif not isinstance(description_purchase, str):
                    description_purchase = str(description_purchase)
            
                # Asegurar que barcode sea string o None
                barcode = p.get('barcode')
                if barcode is False:
                    barcode = None
                elif barcode is not None and not isinstance(barcode, str):
                    barcode = str(barcode)
            
                transformed_products.append(Product(
                    id=p.get('id'),
                    name=p.get('name', ''),
                    default_code=default_code,
                    list_price=p.get('list_price', 0.0),
                    categ_id=categ_id_value,
                    active=p.get('active', True),
                    type=p.get('type', 'product'),
                    standard_price=p.get('standard_price', 0.0),
                    barcode=barcode,
                    weight=p.get('weight', 0.0),
                    sale_ok=p.get('sale_ok', True),
                    purchase_ok=p.get('purchase_ok', True),
                    available_in_pos=p.get('available_in_pos', True),
                    to_weight=p.get('to_weight', False),
                    is_published=p.get('is_published', True),
                    website_sequence=p.get('website_sequence', 1),
                    description_sale=description_sale,
                    description_purchase=description_purchase,
                    seller_ids=p.get('seller_ids', []),
                    product_tag_ids=p.get('product_tag_ids', []),
                    public_categ_ids=p.get('public_categ_ids', []),
                    pos_categ_ids=p.get('pos_categ_ids', []),
                    taxes_id=p.get('taxes_id', []),
                    supplier_taxes_id=p.get('supplier_taxes_id', []),
                    qty_available=None,
                    code=default_code,
                    price=p.get('list_price', 0.0),
                    category=category_name if category_name else 'Sin categoría',
                    stock=0,
                    image_url=None,
                    product_name=None,
                    location=None,
                    last_updated=None
                ))
        
            print(f"ODOO_SERVICE: Productos transformados: {len(transformed_products)}")
            return transformed_products
        except Exception as e:
            print(f"ODOO_SERVICE: Error obteniendo productos: {str(e)}")
            # Forzar conexión a Odoo en caso de error
            self._get_connection()
            print("ODOO_SERVICE: Intentando obtener productos nuevamente después de reconectar...")
            try:
                odoo_products = self._execute_kw(
                    'product.product',
                    'search_read',
                    [[]],
                    {'offset': offset, 'limit': limit, 'fields': [
                        'id', 'name', 'default_code', 'list_price', 'categ_id', 'active',
                        'type', 'standard_price', 'barcode', 'weight',
                        'sale_ok', 'purchase_ok', 'available_in_pos', 'to_weight',
                        'is_published', 'website_sequence', 'description_sale',
                        'description_purchase', 'seller_ids',
                        'product_tag_ids', 'public_categ_ids', 'pos_categ_ids',
                        'taxes_id', 'supplier_taxes_id'
                    ]}
                )
                print(f"ODOO_SERVICE: Datos obtenidos en segundo intento: {len(odoo_products) if odoo_products else 0} productos")
            
                if not odoo_products:
                    print("ODOO_SERVICE: No se pudieron leer datos en segundo intento, usando fallback")
                    return self._get_fallback_products()
                
                # Repetir transformación para segundo intento
                transformed_products = []
                for p in odoo_products:
                    category_name = self._get_category_name(p.get('categ_id'))
                    categ_id_value = None
                    if p.get('categ_id'):
                        if isinstance(p['categ_id'], list) and len(p['categ_id']) > 0:
                            categ_id_value = p['categ_id'][0]
                        elif isinstance(p['categ_id'], int):
                            categ_id_value = p['categ_id']
                    
                    default_code = p.get('default_code')
                    if default_code is False or default_code is None:
                        default_code = ''
                    elif not isinstance(default_code, str):
                        default_code = str(default_code)
                    
                    description_sale = p.get('description_sale')
                    if description_sale is False or description_sale is None:
                        description_sale = ''
                    elif not isinstance(description_sale, str):
                        description_sale = str(description_sale)
                    
                    description_purchase = p.get('description_purchase')
                    if description_purchase is False or description_purchase is None:
                        description_purchase = ''
                    elif not isinstance(description_purchase, str):
                        description_purchase = str(description_purchase)
                    
                    barcode = p.get('barcode')
                    if barcode is False:
                        barcode = None
                    elif barcode is not None and not isinstance(barcode, str):
                        barcode = str(barcode)
                    
                    transformed_products.append(Product(
                        id=p['id'],
                        name=p['name'],
                        default_code=default_code,
                        list_price=p.get('list_price', 0.0),
                        categ_id=categ_id_value,
                        active=p.get('active', True),
                        type=p.get('type', 'product'),
                        standard_price=p.get('standard_price', 0.0),
                        barcode=barcode,
                        weight=p.get('weight', 0.0),
                        sale_ok=p.get('sale_ok', True),
                        purchase_ok=p.get('purchase_ok', True),
                        available_in_pos=p.get('available_in_pos', True),
                        to_weight=p.get('to_weight', False),
                        is_published=p.get('is_published', True),
                        website_sequence=p.get('website_sequence', 1),
                        description_sale=description_sale,
                        description_purchase=description_purchase,
                        seller_ids=p.get('seller_ids', []),
                        product_tag_ids=p.get('product_tag_ids', []),
                        public_categ_ids=p.get('public_categ_ids', []),
                        pos_categ_ids=p.get('pos_categ_ids', []),
                        taxes_id=p.get('taxes_id', []),
                        supplier_taxes_id=p.get('supplier_taxes_id', []),
                        qty_available=None,
                        code=default_code,
                        price=p.get('list_price', 0.0),
                        category=category_name if category_name else 'Sin categoría',
                        stock=0,
                        image_url=None,
                        product_name=None,
                        location=None,
                        last_updated=None
                    ))
                
                print(f"ODOO_SERVICE: Productos transformados en segundo intento: {len(transformed_products)}")
                return transformed_products
            except Exception as e2:
                print(f"ODOO_SERVICE: Error en segundo intento: {str(e2)}")
                return self._get_fallback_products()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Obtiene un producto específico por ID (inteligente: busca en template y product, y suma stock real)."""
        try:
            # 1. Intentar leer como product.template (es lo más robusto para updates y frontend)
            p = self._execute_kw(
                'product.template',
                'read',
                [[product_id]],
                {'fields': ['id', 'name', 'default_code', 'categ_id', 'list_price']}
            )
            if p and isinstance(p, list) and len(p) > 0:
                p = p[0]
                category_name = self._get_category_name(p.get('categ_id'))
                # 2. Buscar el stock REAL sumando stock_quant
                stock = 0
                try:
                    # Buscar todos los product.product con este template
                    variants = self._execute_kw(
                        'product.product',
                        'search_read',
                        [[('product_tmpl_id', '=', product_id)]],
                        {'fields': ['id']}
                    )
                    variant_ids = [v['id'] for v in variants]
                    if variant_ids:
                        # Buscar stock en stock.quant
                        stock_quants = self._execute_kw(
                            'stock.quant',
                            'search_read',
                            [[('product_id', 'in', variant_ids)]],
                            {'fields': ['quantity']}
                        )
                        stock = sum(float(q['quantity']) for q in stock_quants if 'quantity' in q)
                except Exception as e:
                    print(f"Error calculando stock real para template {product_id}: {e}")
                return Product(
                    id=p['id'],
                    name=p['name'],
                    code=p.get('default_code', ''),
                    category=category_name,
                    price=p.get('list_price', 0.0),
                    stock=stock,
                    image_url=f"https://example.com/images/product_{p['id']}.jpg"
                )
            # 3. Si no existe como template, intentar como product.product (legacy)
            p = self._execute_kw(
                'product.product',
                'read',
                [product_id],
                {'fields': ['id', 'name', 'default_code', 'list_price', 'categ_id']}
            )
            if p and isinstance(p, list) and len(p) > 0:
                p = p[0]
                category_name = self._get_category_name(p.get('categ_id'))
                return Product(
                    id=p['id'],
                    name=p['name'],
                    code=p.get('default_code', ''),
                    category=category_name,
                    price=p.get('list_price', 0.0),
                    stock=0,
                    image_url=f"https://example.com/images/product_{p['id']}.jpg"
                )
            return self._get_fallback_product_by_id(product_id)
        except Exception as e:
            print(f"Error obteniendo producto {product_id}: {e}")
            return self._get_fallback_product_by_id(product_id)
        finally:
            self._cleanup_connection()
    
    def create_product(self, product_data: ProductCreate) -> Optional[Product]:
        """Crea un nuevo producto en Odoo"""
        try:
            # Preparar datos del producto
            vals = {
                'name': product_data.name,
                'default_code': product_data.default_code or '',
                'list_price': product_data.list_price or 0.0,
                'standard_price': product_data.standard_price or 0.0,
                'type': product_data.type or 'product',
                'categ_id': product_data.categ_id or 1,  # Categoría por defecto
                'sale_ok': product_data.sale_ok if product_data.sale_ok is not None else True,
                'purchase_ok': product_data.purchase_ok if product_data.purchase_ok is not None else True,
                'active': product_data.active if product_data.active is not None else True,
                'barcode': product_data.barcode or False,
                'weight': product_data.weight or 0.0,
                'description_sale': product_data.description_sale or '',
                'description_purchase': product_data.description_purchase or ''
            }
            
            # Crear producto
            product_id = self._execute_kw(
                'product.product',
                'create',
                [vals]
            )
            
            if product_id:
                # Obtener el producto creado
                product = self.get_product_by_id(product_id)
                # Obtener el template_id real desde product.product
                template_id = None
                try:
                    product_data = self._execute_kw(
                        'product.product',
                        'read',
                        [product_id],
                        {'fields': ['product_tmpl_id']}
                    )
                    if product_data and 'product_tmpl_id' in product_data[0]:
                        template_id = product_data[0]['product_tmpl_id'][0]
                except Exception as e:
                    print(f"Error obteniendo template_id para product_id {product_id}: {e}")
                # Adjunta el template_id como atributo extra (hack rápido)
                if product:
                    product.template_id = template_id
                return product
            else:
                print("Error: No se pudo crear el producto")
                return None
                
        except Exception as e:
            print(f"Error creando producto: {e}")
            return None
    
    def get_product_count(self):
        """Obtiene el número total de productos"""
        try:
            count = self._execute_kw(
                'product.product',
                'search_count',
                [[]]
            )
            return count if count is not None else 0
        except Exception as e:
            print(f"Error obteniendo conteo de productos: {e}")
            return 0
    
    def _get_fallback_products(self) -> List[Product]:
        """Datos de productos de respaldo"""
        return [
            Product(
                id=1,
                name="Producto de Ejemplo 1",
                default_code="PROD001",
                list_price=29.99,
                categ_id=1,
                active=True,
                type="product",
                standard_price=20.00,
                barcode="1234567890123",
                weight=1.5,
                sale_ok=True,
                purchase_ok=True,
                available_in_pos=True,
                to_weight=False,
                is_published=True,
                website_sequence=1,
                description_sale="Descripción de venta del producto 1",
                description_purchase="Descripción de compra del producto 1",
                seller_ids=[],
                product_tag_ids=[],
                public_categ_ids=[],
                pos_categ_ids=[],
                taxes_id=[],
                supplier_taxes_id=[],
                qty_available=100,
                code="PROD001",
                price=29.99,
                category="Electrónicos",
                stock=100,
                image_url="https://example.com/images/product_1.jpg",
                product_name="Producto de Ejemplo 1",
                location="Almacén A",
                last_updated="2024-01-15"
            ),
            Product(
                id=2,
                name="Producto de Ejemplo 2",
                default_code="PROD002",
                list_price=49.99,
                categ_id=2,
                active=True,
                type="product",
                standard_price=35.00,
                barcode="2345678901234",
                weight=2.0,
                sale_ok=True,
                purchase_ok=True,
                available_in_pos=True,
                to_weight=False,
                is_published=True,
                website_sequence=2,
                description_sale="Descripción de venta del producto 2",
                description_purchase="Descripción de compra del producto 2",
                seller_ids=[],
                product_tag_ids=[],
                public_categ_ids=[],
                pos_categ_ids=[],
                taxes_id=[],
                supplier_taxes_id=[],
                qty_available=50,
                code="PROD002",
                price=49.99,
                category="Hogar",
                stock=50,
                image_url="https://example.com/images/product_2.jpg",
                product_name="Producto de Ejemplo 2",
                location="Almacén B",
                last_updated="2024-01-16"
            )
        ]
    
    def _get_fallback_product_by_id(self, product_id: int) -> Optional[Product]:
        """Producto de respaldo por ID"""
        fallback_products = self._get_fallback_products()
        for product in fallback_products:
            if product.id == product_id:
                return product
        return None

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

# Instancia global para evitar errores de importación circular
odoo_product_service = OdooProductService()