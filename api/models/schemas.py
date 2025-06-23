from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel

T = TypeVar('T')

# Modelos de autenticación
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Modelos de negocio - Basados en campos reales de Odoo 18
class Product(BaseModel):
    id: int
    name: str  # Campo obligatorio en product.template
    default_code: Optional[str] = None  # Código del producto (opcional)
    list_price: Optional[float] = None  # Precio de venta (opcional)
    categ_id: Optional[int] = None  # ID de categoría (opcional)
    active: bool = True  # Estado activo/inactivo
    type: Optional[str] = "consu"  # Tipo de producto: consu, service, product
    
    # NUEVOS CAMPOS OBLIGATORIOS DE ODOO
    external_id: Optional[str] = None  # External ID único
    standard_price: Optional[float] = None  # Cost (precio de coste)
    barcode: Optional[str] = None  # Código de barras EAN-13
    weight: Optional[float] = None  # Peso del producto
    
    # CAMPOS DE CONFIGURACIÓN AVANZADA
    sale_ok: bool = True  # Disponible para venta
    purchase_ok: bool = True  # Disponible para compra
    available_in_pos: bool = True  # Disponible en TPV
    to_weight: bool = False  # Producto a peso
    is_published: bool = True  # Publicado en web
    website_sequence: Optional[int] = 10  # Secuencia en web
    
    # CAMPOS DE DESCRIPCIÓN
    description_sale: Optional[str] = None  # Descripción de venta
    description_purchase: Optional[str] = None  # Descripción de compra
    sales_description: Optional[str] = None  # Descripción para ventas
    
    # CAMPOS DE CATEGORIZACIÓN
    seller_ids: Optional[List[int]] = []  # IDs de proveedores
    product_tag_ids: Optional[List[int]] = []  # Etiquetas del producto
    public_categ_ids: Optional[List[int]] = []  # Categorías públicas
    pos_categ_ids: Optional[List[int]] = []  # Categorías TPV
    
    # CAMPOS DE IMPUESTOS
    taxes_id: Optional[List[int]] = []  # Impuestos de venta
    supplier_taxes_id: Optional[List[int]] = []  # Impuestos de compra
    
    # Campos calculados para compatibilidad con frontend
    qty_available: Optional[float] = None  # Stock disponible de Odoo
    code: Optional[str] = None  # Alias para default_code
    price: Optional[float] = None  # Alias para list_price
    category: Optional[str] = None  # Nombre de categoría para mostrar
    stock: Optional[int] = None  # Stock calculado
    image_url: Optional[str] = None  # URL de imagen
    product_name: Optional[str] = None  # Nombre del producto para frontend
    location: Optional[str] = None  # Ubicación del producto
    last_updated: Optional[str] = None  # Última actualización

class ProductCreate(BaseModel):
    name: str  # Campo obligatorio
    default_code: Optional[str] = None  # Código del producto
    list_price: Optional[float] = None  # Precio de venta
    categ_id: Optional[int] = None  # ID de categoría
    active: bool = True  # Estado activo
    type: Optional[str] = "consu"  # Tipo de producto
    
    # NUEVOS CAMPOS DE ODOO
    external_id: Optional[str] = None  # External ID único
    standard_price: Optional[float] = None  # Cost (precio de coste)
    barcode: Optional[str] = None  # Código de barras EAN-13
    weight: Optional[float] = None  # Peso del producto
    sale_ok: bool = True  # Disponible para venta
    purchase_ok: bool = True  # Disponible para compra
    available_in_pos: bool = True  # Disponible en TPV
    to_weight: bool = False  # Producto a peso
    is_published: bool = True  # Publicado en web
    website_sequence: Optional[int] = 10  # Secuencia en web
    description_sale: Optional[str] = None  # Descripción de venta
    description_purchase: Optional[str] = None  # Descripción de compra
    sales_description: Optional[str] = None  # Descripción para ventas
    
    # Campos de compatibilidad
    code: Optional[str] = None  # Alias para default_code
    price: Optional[float] = None  # Alias para list_price
    category: Optional[str] = None  # Para búsqueda de categoría por nombre

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    default_code: Optional[str] = None
    list_price: Optional[float] = None
    categ_id: Optional[int] = None
    active: Optional[bool] = None
    type: Optional[str] = None
    
    # NUEVOS CAMPOS DE ODOO
    external_id: Optional[str] = None
    standard_price: Optional[float] = None
    barcode: Optional[str] = None
    weight: Optional[float] = None
    sale_ok: Optional[bool] = None
    purchase_ok: Optional[bool] = None
    available_in_pos: Optional[bool] = None
    to_weight: Optional[bool] = None
    is_published: Optional[bool] = None
    website_sequence: Optional[int] = None
    description_sale: Optional[str] = None
    description_purchase: Optional[str] = None
    sales_description: Optional[str] = None
    
    # Campos de compatibilidad
    code: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None

class InventoryItem(BaseModel):
    id: int
    product_id: List[int]  # [id, name] del producto (obligatorio)
    location_id: List[int]  # [id, name] de la ubicación (obligatorio)
    quantity: float  # Cantidad en stock (obligatorio)
    lot_id: Optional[List[int]] = None  # [id, name] del lote (opcional)
    package_id: Optional[List[int]] = None  # [id, name] del paquete (opcional)
    owner_id: Optional[List[int]] = None  # [id, name] del propietario (opcional)
    # Campos de compatibilidad
    product_name: Optional[str] = None  # Nombre del producto
    location: Optional[str] = None  # Nombre de la ubicación
    last_updated: Optional[datetime] = None  # Campo calculado

class InventoryItemCreate(BaseModel):
    product_id: int  # ID del producto (obligatorio)
    location_id: int  # ID de la ubicación (obligatorio)
    quantity: float  # Cantidad (obligatorio)
    lot_id: Optional[int] = None  # ID del lote (opcional)
    package_id: Optional[int] = None  # ID del paquete (opcional)
    owner_id: Optional[int] = None  # ID del propietario (opcional)
    # Campos de compatibilidad
    location: Optional[str] = None  # Para búsqueda por nombre

class Sale(BaseModel):
    id: int
    name: str  # Número de pedido (ej: S00040)
    partner_id: List[int]  # [id, name] del cliente (obligatorio)
    date_order: datetime  # Fecha del pedido
    amount_total: float  # Importe total
    state: str  # Estado: draft, sent, sale, done, cancel
    order_line: Optional[List[int]] = []  # IDs de líneas de pedido
    # Campos de compatibilidad
    customer_id: Optional[int] = None  # ID del cliente
    customer_name: Optional[str] = None  # Nombre del cliente
    product_id: Optional[int] = None  # Para compatibilidad
    product_name: Optional[str] = None  # Para compatibilidad
    quantity: Optional[int] = None  # Para compatibilidad
    unit_price: Optional[float] = None  # Para compatibilidad
    total: Optional[float] = None  # Alias para amount_total
    total_amount: Optional[float] = None  # Alias para amount_total
    date: Optional[datetime] = None  # Alias para date_order
    status: Optional[str] = None  # Alias para state
    reference: Optional[str] = None  # Referencia externa

class SaleCreate(BaseModel):
    partner_id: int  # ID del cliente (obligatorio)
    date_order: Optional[datetime] = None  # Fecha del pedido
    state: Optional[str] = "draft"  # Estado inicial
    order_line: Optional[List[Dict[str, Any]]] = []  # Líneas de pedido
    # Campos de compatibilidad
    customer_id: Optional[int] = None  # Alias para partner_id
    customer_name: Optional[str] = None
    reference: Optional[str] = None
    customer: Optional[str] = None
    date: Optional[datetime] = None
    total: Optional[float] = None
    total_amount: Optional[float] = 0.0
    status: Optional[str] = "draft"

class Customer(BaseModel):
    id: int
    name: str  # Campo obligatorio en res.partner
    email: Optional[str] = None  # Opcional en Odoo
    phone: Optional[str] = None  # Opcional en Odoo
    street: Optional[str] = None  # Dirección (opcional)
    city: Optional[str] = None  # Ciudad (opcional)
    country_id: Optional[List[int]] = None  # [id, name] del país (opcional)
    customer_rank: int = 1  # Rango de cliente (1 = es cliente)
    supplier_rank: int = 0  # Rango de proveedor (0 = no es proveedor)
    is_company: bool = False  # Si es empresa o persona
    # Campos de compatibilidad
    address: Optional[str] = None  # Alias para street
    customer: bool = True  # Calculado desde customer_rank
    supplier: bool = False  # Calculado desde supplier_rank
    total_purchases: Optional[float] = 0.0  # Campo calculado

class CustomerCreate(BaseModel):
    name: str  # Campo obligatorio
    email: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country_id: Optional[int] = None
    customer_rank: int = 1  # Marca como cliente
    supplier_rank: int = 0  # No es proveedor
    is_company: bool = False  # Por defecto persona
    # Campos de compatibilidad
    address: Optional[str] = None  # Se mapea a street
    customer: bool = True
    supplier: bool = False
    status: Optional[str] = "Activo"  # Campo legacy

class Provider(BaseModel):
    id: int
    name: str  # Campo obligatorio en res.partner
    email: Optional[str] = None  # Email del proveedor
    phone: Optional[str] = None  # Teléfono del proveedor
    is_company: bool = True  # Es empresa (True para proveedores)
    supplier_rank: int = 1  # Rango de proveedor (>0 para ser proveedor)
    
    # NUEVOS CAMPOS OBLIGATORIOS DE ODOO
    external_id: Optional[str] = None  # External ID único
    ref: Optional[str] = None  # Referencia interna
    vat: Optional[str] = None  # NIF/CIF
    website: Optional[str] = None  # Sitio web
    
    # CAMPOS DE CONTACTO AMPLIADOS
    mobile: Optional[str] = None  # Teléfono móvil
    function: Optional[str] = None  # Cargo/función
    title: Optional[int] = None  # Título (Sr., Sra., etc.)
    
    # CAMPOS DE DIRECCIÓN COMPLETOS
    street: Optional[str] = None  # Dirección
    street2: Optional[str] = None  # Dirección 2
    city: Optional[str] = None  # Ciudad
    zip: Optional[str] = None  # Código postal
    country_id: Optional[int] = None  # ID del país
    state_id: Optional[int] = None  # ID del estado/provincia
    
    # CAMPOS DE CONFIGURACIÓN COMERCIAL
    customer_rank: int = 0  # Rango de cliente
    category_id: Optional[List[int]] = []  # Categorías de contacto
    user_id: Optional[int] = None  # Comercial asignado
    team_id: Optional[int] = None  # Equipo de ventas
    
    # CAMPOS FINANCIEROS
    property_payment_term_id: Optional[int] = None  # Plazo de pago
    property_supplier_payment_term_id: Optional[int] = None  # Plazo pago proveedor
    property_account_payable_id: Optional[int] = None  # Cuenta por pagar
    property_account_receivable_id: Optional[int] = None  # Cuenta por cobrar
    
    # CAMPOS DE CONFIGURACIÓN
    active: bool = True  # Activo
    lang: Optional[str] = "es_ES"  # Idioma
    tz: Optional[str] = "Europe/Madrid"  # Zona horaria
    comment: Optional[str] = None  # Notas internas
    
    # Campos de compatibilidad
    country: Optional[str] = None  # Nombre del país para mostrar
    customer: bool = False  # Calculado desde customer_rank
    supplier: bool = True  # Calculado desde supplier_rank

class ProviderCreate(BaseModel):
    name: str  # Campo obligatorio
    email: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country_id: Optional[int] = None
    customer_rank: int = 0  # No es cliente
    supplier_rank: int = 1  # Es proveedor
    is_company: bool = True  # Por defecto empresa
    # Campos de compatibilidad
    country: Optional[str] = None
    customer: bool = False
    supplier: bool = True

class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    tax_calculation_method: Optional[str] = None
    discount_type: Optional[str] = None
    payment_term: Optional[str] = None
    incentive_rules: Optional[str] = None
    status: Optional[str] = None

# Modelos de respuesta
class SessionResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class DashboardStats(BaseModel):
    # ESTADÍSTICAS BÁSICAS
    totalProducts: int = 0
    totalSales: float = 0.0
    totalCustomers: int = 0
    totalProviders: int = 0
    
    # ESTADÍSTICAS DE PRODUCTOS
    activeProducts: int = 0  # Productos activos
    inactiveProducts: int = 0  # Productos inactivos
    productsWithStock: int = 0  # Productos con stock
    productsWithoutStock: int = 0  # Productos sin stock
    totalCategories: int = 0  # Total de categorías
    
    # ESTADÍSTICAS DE VENTAS
    salesThisMonth: float = 0.0  # Ventas del mes actual
    salesLastMonth: float = 0.0  # Ventas del mes pasado
    salesGrowth: float = 0.0  # Crecimiento de ventas (%)
    averageOrderValue: float = 0.0  # Valor promedio de pedido
    
    # ESTADÍSTICAS DE STOCK
    totalStockValue: float = 0.0  # Valor total del stock
    lowStockProducts: int = 0  # Productos con stock bajo
    outOfStockProducts: int = 0  # Productos sin stock
    
    # ESTADÍSTICAS DE PROVEEDORES
    activeProviders: int = 0  # Proveedores activos
    providersWithOrders: int = 0  # Proveedores con pedidos
    
    # LISTAS DETALLADAS
    topCategories: List[dict] = []  # Lista de categorías con estadísticas
    recentSales: List[Sale] = []  # Ventas recientes
    low_stock_products: Optional[List[Product]] = []  # Productos con stock bajo
    top_selling_products: Optional[List[dict]] = []  # Productos más vendidos
    recent_customers: Optional[List[Customer]] = []  # Clientes recientes
    recent_providers: Optional[List[Provider]] = []  # Proveedores recientes

# Modelo de categoría de producto - Basado en product.category de Odoo
class ProductCategory(BaseModel):
    id: int
    name: str  # Campo obligatorio
    parent_id: Optional[int] = None  # Categoría padre
    complete_name: Optional[str] = None  # Nombre completo con jerarquía
    
    # NUEVOS CAMPOS DE ODOO
    external_id: Optional[str] = None  # External ID único
    parent_path: Optional[str] = None  # Ruta jerárquica
    child_id: Optional[List[int]] = []  # IDs de categorías hijas
    product_count: Optional[int] = 0  # Número de productos en la categoría
    
    # CAMPOS DE CONFIGURACIÓN
    removal_strategy_id: Optional[int] = None  # Estrategia de eliminación
    packaging_reserve_method: Optional[str] = "by_quantity"  # Método de reserva
    
    # CAMPOS DE CONTABILIDAD
    property_account_income_categ_id: Optional[int] = None  # Cuenta de ingresos
    property_account_expense_categ_id: Optional[int] = None  # Cuenta de gastos
    property_account_creditor_price_difference_categ: Optional[int] = None  # Diferencia de precio
    property_stock_account_input_categ_id: Optional[int] = None  # Cuenta stock entrada
    property_stock_account_output_categ_id: Optional[int] = None  # Cuenta stock salida
    property_stock_valuation_account_id: Optional[int] = None  # Cuenta valoración stock
    
    # CAMPOS DE STOCK
    property_cost_method: Optional[str] = "fifo"  # Método de coste: fifo, lifo, average
    property_valuation: Optional[str] = "manual_periodic"  # Valoración: manual_periodic, real_time

# Modelos de paginación
class PaginationParams(BaseModel):
    page: int = 1
    size: int = 10
    
class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    size: int
    pages: int
