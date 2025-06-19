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
                
                # Asegurarse de que default_code sea string
                default_code = p.get('default_code')
                if default_code is False or default_code is None:
                    default_code = ''
                elif not isinstance(default_code, str):
                    default_code = str(default_code)
                
                # Asegurarse de que description_sale sea string
                description_sale = p.get('description_sale')
                if description_sale is False or description_sale is None:
                    description_sale = ''
                elif not isinstance(description_sale, str):
                    description_sale = str(description_sale)
                
                # Asegurarse de que description_purchase sea string
                description_purchase = p.get('description_purchase')
                if description_purchase is False or description_purchase is None:
                    description_purchase = ''
                elif not isinstance(description_purchase, str):
                    description_purchase = str(description_purchase)
                
                # Asegurarse de que barcode sea string o None
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
        try:
            print("Iniciando obtención de proveedores desde Odoo...")
            
            if not self._get_connection():
                print("Error: No se pudo establecer conexión con Odoo")
                return self._get_fallback_providers()
            
            # Buscar partners que sean proveedores
            print("Buscando proveedores en Odoo...")
            provider_ids = self._execute_kw(
                "res.partner", "search",
                [[["supplier_rank", ">", 0]]],
                {"limit": 100}
            )
            
            if not provider_ids:
                print("No se encontraron proveedores en Odoo")
                return self._get_fallback_providers()
            
            print(f"Se encontraron {len(provider_ids)} proveedores en Odoo")
            
            # Obtener datos de los proveedores
            print("Obteniendo detalles de los proveedores...")
            provider_data = self._execute_kw(
                "res.partner", "read",
                [provider_ids],
                {"fields": ["id", "name", "email", "phone", "street", "city", "country_id", "supplier_rank", "is_company", "ref", "vat", "website", "mobile", "zip", "comment"]}
            )
            
            if not provider_data:
                print("No se pudieron obtener los detalles de los proveedores")
                return self._get_fallback_providers()
            
            print("Procesando datos de proveedores...")
            providers = []
            for data in provider_data:
                print(f"Procesando proveedor ID: {data.get('id')}")
                print(f"Datos recibidos de Odoo: {data}")
                country_name = data.get("country_id", [False, ""])[1] if data.get("country_id") else ""
                country_id = data.get('country_id', [False, ''])[0] if data.get('country_id') else 0
                
                # Convertir False a cadenas vacías para todos los campos relevantes
                def safe_str(value, default=""):
                    return str(value) if value is not False else default
                
                email = safe_str(data.get("email", ""))
                phone = safe_str(data.get("phone", ""))
                vat = safe_str(data.get("vat", ""))
                website = safe_str(data.get("website", ""))
                mobile = safe_str(data.get("mobile", ""))
                street = safe_str(data.get("street", ""))
                city = safe_str(data.get("city", ""))
                zip_code = safe_str(data.get("zip", ""))
                comment = safe_str(data.get("comment", ""))
                name = safe_str(data.get("name", ""), "Sin Nombre")
                ref = safe_str(data.get("ref", f"PROV{data.get('id', 'N/A')}"), f"PROV{data.get('id', 'N/A')}")
                
                try:
                    provider = Provider(
                        id=data['id'],
                        name=name,
                        email=email,
                        phone=phone,
                        address=street,
                        city=city,
                        country=country_name,
                        is_company=data.get('is_company', True),
                        supplier_rank=data.get('supplier_rank', 1),
                        external_id=f"provider_{data['id']}",
                        ref=ref,
                        vat=vat,
                        website=website,
                        mobile=mobile,
                        function="",
                        street=street,
                        zip=zip_code,
                        country_id=country_id,
                        customer_rank=0,
                        category_id=[],
                        active=True,
                        lang="es_ES",
                        tz="Europe/Madrid",
                        comment=comment,
                        customer=False,
                        supplier=True
                    )
                    providers.append(provider)
                    print(f"Proveedor {name} (ID: {data['id']}) procesado correctamente")
                except Exception as e:
                    print(f"Error de validación al procesar proveedor ID {data.get('id')}: {str(e)}")
                    print(f"Datos problemáticos: {data}")
                    # Mostrar detalles específicos del error de validación
                    if hasattr(e, 'errors'):
                        for error in e.errors():
                            print(f"Campo: {error['loc'][0]}, Error: {error['msg']}, Tipo: {error['type']}")
        
            print(f"Se procesaron {len(providers)} proveedores correctamente")
            return providers
        except Exception as e:
            print(f"Error al obtener proveedores de Odoo: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_providers()

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
                image_url=f"/web/image/product.template/{p['id']}/image_1920/" if p.get('image_1920') else None,
                is_active=True # Asumimos que si se crea, está activo
            )

        except Exception as e:
            print(f"ODOO_SERVICE: Excepción en create_product: {e}")
            return None
        finally:
            print("ODOO_SERVICE: Finalizando create_product y limpiando conexión")
            self._cleanup_connection()
    
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
