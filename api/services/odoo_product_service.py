from typing import List, Optional
from .odoo_base_service import OdooBaseService
from ..models.schemas import Product, ProductCreate

class OdooProductService(OdooBaseService):
    """Servicio para gestión de productos en Odoo"""
    
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
                
                print(f"ODOO_SERVICE: Productos transformados en segundo intento: {len(transformed_products)}")
                return transformed_products
            except Exception as e2:
                print(f"ODOO_SERVICE: Error en segundo intento: {str(e2)}")
                return self._get_fallback_products()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Obtiene un producto específico por ID"""
        try:
            p = self._execute_kw(
                'product.product',
                'read',
                [product_id],
                {'fields': ['id', 'name', 'default_code', 'list_price', 'categ_id', 'qty_available']}
            )
            
            if not p:
                return self._get_fallback_product_by_id(product_id)
            
            p = p[0]  # read devuelve una lista
            category_name = self._get_category_name(p.get('categ_id'))
            
            return Product(
                id=p['id'],
                name=p['name'],
                code=p.get('default_code', ''),
                category=category_name,
                price=p.get('list_price', 0.0),
                stock=int(p.get('qty_available') or 0),
                image_url=f"https://example.com/images/product_{p['id']}.jpg"
            )
            
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
                return self.get_product_by_id(product_id)
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