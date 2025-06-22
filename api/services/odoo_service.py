import gc
import xmlrpc.client
from typing import List, Optional, Dict, Any
from ..utils.config import config
from ..models.schemas import Product, Provider, Customer, Sale, ProductCreate

class OdooService:
    """Servicio para interactuar con Odoo via XML-RPC"""
    
    def __init__(self):
        self.config = config.get_odoo_config()
        self._common = None
        self._models = None
        self._uid = None
    
    def _get_connection(self):
        """Establece conexión con Odoo"""
        try:
            if not self._common:
                self._common = xmlrpc.client.ServerProxy(f'{self.config["url"]}/xmlrpc/2/common')
            
            if not self._uid:
                self._uid = self._common.authenticate(
                    self.config["db"],
                    self.config["username"],
                    self.config["password"],
                    {}
                )
            
            if not self._models and self._uid:
                self._models = xmlrpc.client.ServerProxy(f'{self.config["url"]}/xmlrpc/2/object')
            
            return self._uid is not None
        except Exception as e:
            print(f"Error conectando con Odoo: {e}")
            return False
    
    def _cleanup_connection(self):
        """Limpia las conexiones y libera memoria"""
        if self._common:
            del self._common
            self._common = None
        if self._models:
            del self._models
            self._models = None
        gc.collect()
    
    def _execute_kw(self, model: str, method: str, args: list, kwargs: dict = None) -> Any:
        """Ejecuta una llamada a Odoo"""
        if not self._get_connection():
            return None
        
        try:
            if kwargs is None:
                kwargs = {}
            return self._models.execute_kw(
                self.config["db"],
                self._uid,
                self.config["password"],
                model,
                method,
                args,
                kwargs
            )
        except Exception as e:
            print(f"Error ejecutando {method} en {model}: {e}")
            return None
    
    def get_products(self) -> List[Product]:
        """Obtiene productos desde Odoo"""
        print("ODOO_SERVICE: Iniciando get_products()")
        try:
            # Buscar productos
            print("ODOO_SERVICE: Buscando productos...")
            product_ids = self._execute_kw('product.template', 'search', [[]])
            print(f"ODOO_SERVICE: Productos encontrados: {len(product_ids) if product_ids else 0}")
            
            if not product_ids:
                print("ODOO_SERVICE: No se encontraron productos, usando fallback")
                return self._get_fallback_products()
            
            # Obtener datos de productos
            print("ODOO_SERVICE: Leyendo datos de productos...")
            odoo_products = self._execute_kw(
                'product.template', 
                'read', 
                [product_ids],
                {'fields': [
                    # Campos básicos obligatorios
                    'id', 'name', 'default_code', 'list_price', 'standard_price', 'type',
                    # Campos básicos opcionales
                    'barcode', 'weight', 'active', 'categ_id', 'qty_available',
                    # Campos avanzados de configuración
                    'sale_ok', 'purchase_ok', 'available_in_pos', 'to_weight', 
                    'is_published', 'website_sequence',
                    # Campos de descripción
                    'description_sale', 'description_purchase',
                    # Campos de categorización
                    'seller_ids', 'product_tag_ids', 'public_categ_ids', 'pos_categ_ids',
                    # Campos de impuestos
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
                    # Campos básicos obligatorios
                    id=p['id'],
                    name=p['name'],
                    default_code=default_code,
                    list_price=p.get('list_price', 0.0),
                    standard_price=p.get('standard_price', 0.0),
                    type=p.get('type', 'product'),
                    
                    # Campos básicos opcionales
                    barcode=barcode,
                    weight=p.get('weight'),
                    active=p.get('active', True),
                    categ_id=categ_id_value,
                    
                    # Campos avanzados de configuración
                    sale_ok=p.get('sale_ok', True),
                    purchase_ok=p.get('purchase_ok', True),
                    available_in_pos=p.get('available_in_pos', True),
                    to_weight=p.get('to_weight', False),
                    is_published=p.get('is_published', True),
                    website_sequence=p.get('website_sequence', 10),
                    
                    # Campos de descripción
                    description_sale=description_sale,
                    description_purchase=description_purchase,
                    
                    # Campos de categorización
                    seller_ids=p.get('seller_ids', []),
                    product_tag_ids=p.get('product_tag_ids', []),
                    public_categ_ids=p.get('public_categ_ids', []),
                    pos_categ_ids=p.get('pos_categ_ids', []),
                    
                    # Campos de impuestos
                    taxes_id=p.get('taxes_id', []),
                    supplier_taxes_id=p.get('supplier_taxes_id', []),
                    
                    # Campos calculados para compatibilidad
                    stock=int(p.get('qty_available') or 0),
                    category=category_name,
                    code=default_code,
                    price=p.get('list_price', 0.0)
                ))
            
            print(f"ODOO_SERVICE: ✓ Devolviendo {len(transformed_products)} productos REALES de Odoo")
            return transformed_products
            
        except Exception as e:
            print(f"ODOO_SERVICE: ✗ Error obteniendo productos: {e}")
            import traceback
            print(f"ODOO_SERVICE: Traceback: {traceback.format_exc()}")
            print("ODOO_SERVICE: Usando datos de fallback")
            return self._get_fallback_products()
        finally:
            print("ODOO_SERVICE: Limpiando conexión")
            self._cleanup_connection()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Obtiene un producto específico por ID"""
        try:
            odoo_product = self._execute_kw(
                'product.template',
                'read',
                [[product_id]],
                {'fields': ['id', 'name', 'default_code', 'categ_id', 'list_price', 'qty_available']}
            )
            
            if not odoo_product:
                return self._get_fallback_product_by_id(product_id)
            
            p = odoo_product[0]
            category_name = self._get_category_name(p.get('categ_id'))

            return Product(
                id=p['id'],
                name=p['name'],
                code=p.get('default_code', '') or f"PROD-{p['id']}",
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
    
    def get_providers(self) -> List[Provider]:
        """Obtiene proveedores desde Odoo"""
        print("ODOO_SERVICE: Iniciando get_providers()")
        try:
            # Buscar proveedores (partners que son suppliers)
            print("ODOO_SERVICE: Buscando proveedores...")
            provider_ids = self._execute_kw(
                'res.partner',
                'search',
                [['&', ('is_company', '=', True), ('supplier_rank', '>', 0)]]
            )
            print(f"ODOO_SERVICE: Proveedores encontrados: {len(provider_ids) if provider_ids else 0}")
            
            if not provider_ids:
                print("ODOO_SERVICE: No se encontraron proveedores, usando fallback")
                return self._get_fallback_providers()
            
            # Obtener datos de proveedores con todos los campos necesarios
            print("ODOO_SERVICE: Leyendo datos de proveedores...")
            odoo_providers = self._execute_kw(
                'res.partner',
                'read',
                [provider_ids],
                {'fields': [
                    # Campos básicos obligatorios
                    'id', 'name', 'email', 'phone', 'is_company', 'supplier_rank',
                    # Campos obligatorios de Odoo
                    'ref', 'vat', 'website',
                    # Campos de contacto ampliados
                    'mobile', 'fax', 'function', 'title',
                    # Campos de dirección completos
                    'street', 'street2', 'city', 'zip', 'country_id', 'state_id',
                    # Campos de configuración comercial
                    'customer_rank', 'category_id', 'user_id', 'team_id',
                    # Campos financieros
                    'property_payment_term_id', 'property_supplier_payment_term_id',
                    'property_account_payable_id', 'property_account_receivable_id',
                    # Campos de configuración
                    'active', 'lang', 'tz', 'comment'
                ]}
            )
            
            if not odoo_providers:
                print("ODOO_SERVICE: No se pudieron leer datos de proveedores, usando fallback")
                return self._get_fallback_providers()
            
            # Transformar a formato esperado
            transformed_providers = []
            for p in odoo_providers:
                # Obtener nombre del país si existe
                country_name = None
                if p.get('country_id'):
                    country_name = p['country_id'][1] if isinstance(p['country_id'], list) else None
                
                transformed_providers.append(Provider(
                    id=p['id'],
                    name=p['name'],
                    email=p.get('email'),
                    phone=p.get('phone'),
                    is_company=p.get('is_company', True),
                    supplier_rank=p.get('supplier_rank', 1),
                    
                    # Campos obligatorios de Odoo
                    external_id=f"provider_{p['id']}",  # Generar external_id
                    ref=p.get('ref'),
                    vat=p.get('vat'),
                    website=p.get('website'),
                    
                    # Campos de contacto ampliados
                    mobile=p.get('mobile'),
                    fax=p.get('fax'),
                    function=p.get('function'),
                    title=p.get('title'),
                    
                    # Campos de dirección completos
                    street=p.get('street'),
                    street2=p.get('street2'),
                    city=p.get('city'),
                    zip=p.get('zip'),
                    country_id=p.get('country_id')[0] if p.get('country_id') and isinstance(p['country_id'], list) else p.get('country_id'),
                    state_id=p.get('state_id')[0] if p.get('state_id') and isinstance(p['state_id'], list) else p.get('state_id'),
                    
                    # Campos de configuración comercial
                    customer_rank=p.get('customer_rank', 0),
                    category_id=p.get('category_id', []),
                    user_id=p.get('user_id')[0] if p.get('user_id') and isinstance(p['user_id'], list) else p.get('user_id'),
                    team_id=p.get('team_id')[0] if p.get('team_id') and isinstance(p['team_id'], list) else p.get('team_id'),
                    
                    # Campos financieros
                    property_payment_term_id=p.get('property_payment_term_id')[0] if p.get('property_payment_term_id') and isinstance(p['property_payment_term_id'], list) else p.get('property_payment_term_id'),
                    property_supplier_payment_term_id=p.get('property_supplier_payment_term_id')[0] if p.get('property_supplier_payment_term_id') and isinstance(p['property_supplier_payment_term_id'], list) else p.get('property_supplier_payment_term_id'),
                    property_account_payable_id=p.get('property_account_payable_id')[0] if p.get('property_account_payable_id') and isinstance(p['property_account_payable_id'], list) else p.get('property_account_payable_id'),
                    property_account_receivable_id=p.get('property_account_receivable_id')[0] if p.get('property_account_receivable_id') and isinstance(p['property_account_receivable_id'], list) else p.get('property_account_receivable_id'),
                    
                    # Campos de configuración
                    active=p.get('active', True),
                    lang=p.get('lang', 'es_ES'),
                    tz=p.get('tz', 'Europe/Madrid'),
                    comment=p.get('comment'),
                    
                    # Campos de compatibilidad
                    country=country_name,
                    customer=p.get('customer_rank', 0) > 0,
                    supplier=p.get('supplier_rank', 0) > 0
                ))
            
            print(f"ODOO_SERVICE: Proveedores transformados: {len(transformed_providers)}")
            return transformed_providers
            
        except Exception as e:
            print(f"Error obteniendo proveedores: {e}")
            return self._get_fallback_providers()
        finally:
            self._cleanup_connection()

    def get_customers(self) -> List[Customer]:
        """Obtiene clientes desde Odoo"""
        try:
            # Buscar clientes (partners que son customers)
            customer_ids = self._execute_kw(
                'res.partner',
                'search',
                [['&', ('is_company', '=', False), ('customer_rank', '>', 0)]]
            )
            
            if not customer_ids:
                return self._get_fallback_customers()
            
            # Obtener datos de clientes
            odoo_customers = self._execute_kw(
                'res.partner',
                'read',
                [customer_ids],
                {'fields': ['id', 'name', 'email', 'phone', 'city', 'country_id']}
            )
            
            if not odoo_customers:
                return self._get_fallback_customers()
            
            # Transformar a formato esperado
            transformed_customers = []
            for c in odoo_customers:
                transformed_customers.append(Customer(
                    id=c['id'],
                    name=c['name'],
                    email=c.get('email', ''),
                    phone=c.get('phone', ''),
                    city=c.get('city', ''),
                    country=c.get('country_id', [None, ''])[1] if c.get('country_id') else ''
                ))
            
            return transformed_customers
            
        except Exception as e:
            print(f"Error obteniendo clientes: {e}")
            return self._get_fallback_customers()
        finally:
            self._cleanup_connection()

    def get_sales(self) -> List[Sale]:
        """Obtiene ventas desde Odoo"""
        try:
            # Buscar órdenes de venta confirmadas
            sale_ids = self._execute_kw(
                'sale.order',
                'search',
                [['state', 'in', ['sale', 'done']]],
                {'limit': 50, 'order': 'date_order desc'}
            )
            
            if not sale_ids:
                return self._get_fallback_sales()
            
            # Obtener datos de ventas
            odoo_sales = self._execute_kw(
                'sale.order',
                'read',
                [sale_ids],
                {'fields': ['id', 'name', 'partner_id', 'date_order', 'amount_total', 'state']}
            )
            
            if not odoo_sales:
                return self._get_fallback_sales()
            
            # Transformar a formato esperado
            transformed_sales = []
            for s in odoo_sales:
                transformed_sales.append(Sale(
                    id=s['id'],
                    name=s['name'],
                    partner_id=s.get('partner_id', [0, 'Cliente desconocido']),
                    date_order=s.get('date_order'),
                    amount_total=s.get('amount_total', 0.0),
                    state=s.get('state', 'draft'),
                    # Campos de compatibilidad
                    customer_name=s.get('partner_id', [None, ''])[1] if s.get('partner_id') else 'Cliente desconocido',
                    date=s.get('date_order'),
                    status=s.get('state', 'draft'),
                    total=s.get('amount_total', 0.0)
                ))
            
            return transformed_sales
            
        except Exception as e:
            print(f"Error obteniendo ventas: {e}")
            return self._get_fallback_sales()
        finally:
            self._cleanup_connection()

    def create_product(self, product_data: ProductCreate) -> Optional[Product]:
        """Crea un nuevo producto en Odoo."""
        try:
            print("ODOO_SERVICE: Iniciando create_product")
            if not self._get_connection():
                print("ODOO_SERVICE: Error de conexión inicial a Odoo")
                return None

            # Buscar o crear la categoría del producto
            category_name = product_data.category
            print(f"ODOO_SERVICE: Buscando categoría '{category_name}'")
            category_ids = self._execute_kw('product.category', 'search', [[('name', '=', category_name)]])
            print(f"ODOO_SERVICE: Resultado búsqueda categoría: {category_ids}")
            if not category_ids:
                # Crear la categoría si no existe
                print(f"ODOO_SERVICE: Categoría '{category_name}' no encontrada, creando...")
                new_category_id = self._execute_kw('product.category', 'create', [{'name': category_name}])
                print(f"ODOO_SERVICE: Resultado creación categoría: {new_category_id}")
                if not new_category_id:
                    print(f"Error creando categoría '{category_name}' en Odoo.")
                    return None
                category_id = new_category_id
            else:
                category_id = category_ids[0]

            # Preparar datos para Odoo
            odoo_product_values = {
                'name': product_data.name,
                'default_code': product_data.code,
                'list_price': product_data.price,
                'standard_price': product_data.price, # Coste, se puede ajustar
                'categ_id': category_id,
                'type': 'product',  # 'consu' para consumible, 'service' para servicio
                'qty_available': product_data.stock, # Esto normalmente se maneja con movimientos de stock
                'sale_ok': True,
                'purchase_ok': True,
                # 'image_1920': product_data.image_url, # Si tienes la imagen en base64
            }

            # Crear el producto en Odoo
            print(f"ODOO_SERVICE: Creando producto en Odoo con valores: {odoo_product_values}")
            product_id = self._execute_kw('product.template', 'create', [odoo_product_values])
            print(f"ODOO_SERVICE: Resultado creación producto (ID): {product_id}")
            if not product_id:
                print(f"Error creando producto '{product_data.name}' en Odoo.")
                return None

            # Leer el producto creado para devolverlo
            print(f"ODOO_SERVICE: Leyendo producto creado con ID: {product_id}")
            created_product_data = self._execute_kw(
                'product.template',
                'read',
                [[product_id]],
                {'fields': ['id', 'name', 'default_code', 'categ_id', 'list_price', 'qty_available']}
            )
            if not created_product_data:
                print(f"ODOO_SERVICE: Error leyendo producto creado con ID: {product_id}")
                return None
            print(f"ODOO_SERVICE: Datos producto leído: {created_product_data}")
            
            p = created_product_data[0]
            # Obtener el nombre de la categoría del producto creado
            created_category_name = self._get_category_name(p.get('categ_id'))

            return Product(
                id=p['id'],
                name=p['name'],
                code=p.get('default_code', '') or f"PROD-{p['id']}",
                category=created_category_name,
                price=p.get('list_price', 0.0),
                stock=int(p.get('qty_available') or 0), # qty_available en product.template puede no ser lo mismo que stock real
                image_url=f"https://example.com/images/product_{p['id']}.jpg",
                is_active=True # Asumimos que si se crea, está activo
            )

        except Exception as e:
            print(f"ODOO_SERVICE: Excepción en create_product: {e}")
            return None
        finally:
            print("ODOO_SERVICE: Finalizando create_product y limpiando conexión")
            self._cleanup_connection()

    def create_invoice(self, supplier_id, invoice_data):
        try:
            invoice_date = invoice_data.get('date', '')
            # Validate and convert date format before passing to Odoo
            if invoice_date:
                import re
                from datetime import datetime
                # Check if date matches expected formats like DD/MM/YYYY, DD-MM-YYYY, etc.
                match = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', invoice_date)
                if match:
                    day, month, year = match.groups()
                    # Handle 2-digit year
                    if len(year) == 2:
                        year = '20' + year  # Assume 20XX for recent dates
                    try:
                        # Convert to YYYY-MM-DD format for Odoo
                        invoice_date = datetime(int(year), int(month), int(day)).strftime('%Y-%m-%d')
                    except ValueError:
                        print(f"Invalid date components: day={day}, month={month}, year={year}")
                        invoice_date = False  # Set to False if date is invalid
                else:
                    print(f"Date format not matched: {invoice_date}")
                    invoice_date = False  # Set to False if not a valid date format
            else:
                invoice_date = False  # Set to False if empty

            invoice_vals = {
                'partner_id': supplier_id,
                'move_type': 'in_invoice',
                'ref': invoice_data.get('number', ''),
                'invoice_date': invoice_date if invoice_date else False,
            }
            invoice_id = self._execute_kw(
                'account.move',
                'create',
                [invoice_vals]
            )
            return invoice_id
        except Exception as e:
            print(f"Error ejecutando create en account.move: {str(e)}")
            return None

    def get_supplier_by_name(self, name):
        try:
            supplier = self._execute_kw(
                'res.partner',
                'search_read',
                [[['name', 'ilike', name]]],
                {'fields': ['id', 'name']}
            )
            return supplier[0] if supplier else None
        except Exception as e:
            print(f"Error searching supplier by name {name}: {str(e)}")
            return None

    def _get_category_name(self, categ_id) -> str:
        """Obtiene el nombre de una categoría"""
        if not categ_id:
            return "Sin categoría"
        
        try:
            category = self._execute_kw(
                'product.category',
                'read',
                [categ_id[0]],
                {'fields': ['name']}
            )
            return category[0]['name'] if category else "Sin categoría"
        except:
            return "Sin categoría"
    
    def _get_fallback_products(self) -> List[Product]:
        """Datos de productos de respaldo"""
        return [
            Product(
                # Campos obligatorios de Odoo
                id=1,
                name="Refrigerador Samsung RT38K5982BS",
                default_code="REF-SAM-001",
                categ_id=1,
                list_price=899.99,
                qty_available=12,
                active=True,
                type="product",
                # Campos opcionales de Odoo 18
                external_id="REF-SAM-001",
                standard_price=750.00,
                barcode="1234567890123",
                weight=45.5,
                sale_ok=True,
                purchase_ok=True,
                available_in_pos=True,
                to_weight=False,
                is_published=True,
                website_sequence=10,
                description_sale="Refrigerador de alta eficiencia energética",
                description_purchase="Refrigerador Samsung con tecnología Twin Cooling Plus",
                sales_description="Ideal para familias grandes",
                # Campos de compatibilidad para frontend
                code="REF-SAM-001",
                category="Refrigeradores",
                price=899.99,
                stock=12,
                image_url="https://example.com/images/refrigerador.jpg",
                product_name="Refrigerador Samsung RT38K5982BS",
                location="Almacén A",
                last_updated="2024-01-15T10:30:00Z"
            ),
            Product(
                # Campos obligatorios de Odoo
                id=2,
                name="Lavadora LG F4WV5012S0W",
                default_code="LAV-LG-002",
                categ_id=2,
                list_price=649.99,
                qty_available=8,
                active=True,
                type="product",
                # Campos opcionales de Odoo 18
                external_id="LAV-LG-002",
                standard_price=520.00,
                barcode="2345678901234",
                weight=65.0,
                sale_ok=True,
                purchase_ok=True,
                available_in_pos=True,
                to_weight=False,
                is_published=True,
                website_sequence=20,
                description_sale="Lavadora de carga frontal con tecnología AI DD",
                description_purchase="Lavadora LG con motor Direct Drive",
                sales_description="Perfecta para el hogar moderno",
                # Campos de compatibilidad para frontend
                code="LAV-LG-002",
                category="Lavadoras",
                price=649.99,
                stock=8,
                image_url="https://example.com/images/lavadora.jpg",
                product_name="Lavadora LG F4WV5012S0W",
                location="Almacén B",
                last_updated="2024-01-15T11:15:00Z"
            ),
            Product(
                # Campos obligatorios de Odoo
                id=3,
                name="Televisor Sony KD-55X80J",
                default_code="TV-SONY-003",
                categ_id=3,
                list_price=799.99,
                qty_available=5,
                active=True,
                type="product",
                # Campos opcionales de Odoo 18
                external_id="TV-SONY-003",
                standard_price=650.00,
                barcode="3456789012345",
                weight=18.5,
                sale_ok=True,
                purchase_ok=True,
                available_in_pos=True,
                to_weight=False,
                is_published=True,
                website_sequence=30,
                description_sale="Smart TV 4K HDR con Google TV",
                description_purchase="Televisor Sony BRAVIA XR con procesador Cognitive Processor XR",
                sales_description="Experiencia cinematográfica en casa",
                # Campos de compatibilidad para frontend
                code="TV-SONY-003",
                category="Televisores",
                price=799.99,
                stock=5,
                image_url="https://example.com/images/televisor.jpg",
                product_name="Televisor Sony KD-55X80J",
                location="Almacén C",
                last_updated="2024-01-15T12:00:00Z"
            )
        ]
    
    def _get_fallback_product_by_id(self, product_id: int) -> Optional[Product]:
        """Producto de respaldo por ID"""
        fallback_products = self._get_fallback_products()
        for product in fallback_products:
            if product.id == product_id:
                return product
        return None
    
    def _get_fallback_providers(self) -> List[Provider]:
        """Datos de proveedores de respaldo"""
        return [
            Provider(
                id=1,
                name="MIELECTRO S.L.",
                email="info@mielectro.es",
                phone="+34 91 123 4567",
                is_company=True,
                supplier_rank=1,
                
                # Campos obligatorios de Odoo
                external_id="provider_1",
                ref="MIEL001",
                vat="B12345678",
                website="https://www.mielectro.es",
                
                # Campos de contacto ampliados
                mobile="+34 600 123 456",
                function="Departamento Comercial",
                
                # Campos de dirección completos
                street="Calle Electrónica, 123",
                city="Madrid",
                zip="28001",
                country_id=68,  # España
                
                # Campos de configuración comercial
                customer_rank=0,
                category_id=[],
                
                # Campos de configuración
                active=True,
                lang="es_ES",
                tz="Europe/Madrid",
                comment="Proveedor principal de componentes electrónicos",
                
                # Campos de compatibilidad
                country="España",
                customer=False,
                supplier=True
            ),
            Provider(
                id=2,
                name="BECKEN ELECTRODOMÉSTICOS S.A.",
                email="ventas@becken.es",
                phone="+34 93 987 6543",
                is_company=True,
                supplier_rank=1,
                
                # Campos obligatorios de Odoo
                external_id="provider_2",
                ref="BECK002",
                vat="A87654321",
                website="https://www.becken.es",
                
                # Campos de contacto ampliados
                mobile="+34 600 987 654",
                function="Departamento de Ventas",
                
                # Campos de dirección completos
                street="Polígono Industrial Becken, Nave 5",
                city="Barcelona",
                zip="08020",
                country_id=68,  # España
                
                # Campos de configuración comercial
                customer_rank=0,
                category_id=[],
                
                # Campos de configuración
                active=True,
                lang="es_ES",
                tz="Europe/Madrid",
                comment="Especialista en electrodomésticos de línea blanca",
                
                # Campos de compatibilidad
                country="España",
                customer=False,
                supplier=True
            ),
            Provider(
                id=3,
                name="TECNOLOGÍA AVANZADA S.L.",
                email="contacto@tecnoavanzada.com",
                phone="+34 96 555 7890",
                is_company=True,
                supplier_rank=1,
                
                # Campos obligatorios de Odoo
                external_id="provider_3",
                ref="TECAV003",
                vat="B98765432",
                website="https://www.tecnoavanzada.com",
                
                # Campos de contacto ampliados
                mobile="+34 600 555 789",
                function="Departamento Técnico",
                
                # Campos de dirección completos
                street="Avenida de la Tecnología, 45",
                city="Valencia",
                zip="46001",
                country_id=68,  # España
                
                # Campos de configuración comercial
                customer_rank=0,
                category_id=[],
                
                # Campos de configuración
                active=True,
                lang="es_ES",
                tz="Europe/Madrid",
                comment="Proveedor de tecnología y equipos informáticos",
                
                # Campos de compatibilidad
                country="España",
                customer=False,
                supplier=True
            )
        ]
    
    def _get_fallback_customers(self) -> List[Customer]:
        """Datos de clientes de respaldo"""
        return [
            Customer(
                id=1,
                name="Juan Pérez",
                email="juan.perez@email.com",
                phone="+34 600 123 456",
                city="Madrid",
                country="España"
            ),
            Customer(
                id=2,
                name="María García",
                email="maria.garcia@email.com",
                phone="+34 600 789 012",
                city="Barcelona",
                country="España"
            ),
            Customer(
                id=3,
                name="Carlos López",
                email="carlos.lopez@email.com",
                phone="+34 600 345 678",
                city="Valencia",
                country="España"
            )
        ]
    
    def _get_fallback_sales(self) -> List[Sale]:
        """Datos de ventas de respaldo"""
        from datetime import datetime, timedelta
        return [
            Sale(
                id=1,
                name="SO001",
                partner_id=[1, "Juan Pérez"],
                date_order=datetime.now() - timedelta(days=1),
                amount_total=1299.99,
                state="sale",
                # Campos de compatibilidad
                customer_name="Juan Pérez",
                date=datetime.now() - timedelta(days=1),
                status="sale",
                total=1299.99
            ),
            Sale(
                id=2,
                name="SO002",
                partner_id=[2, "María García"],
                date_order=datetime.now() - timedelta(days=2),
                amount_total=649.99,
                state="done",
                # Campos de compatibilidad
                customer_name="María García",
                date=datetime.now() - timedelta(days=2),
                status="done",
                total=649.99
            ),
            Sale(
                id=3,
                name="SO003",
                partner_id=[3, "Carlos López"],
                date_order=datetime.now() - timedelta(days=3),
                amount_total=799.99,
                state="sale",
                # Campos de compatibilidad
                customer_name="Carlos López",
                date=datetime.now() - timedelta(days=3),
                status="sale",
                total=799.99
            )
        ]

# Instancia del servicio
odoo_service = OdooService()
