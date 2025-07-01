from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any, Generic, TypeVar, Union
from datetime import datetime

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

# --- Modelos de Producto Refactorizados ---

# Modelo Base con todos los campos opcionales para herencia
class ProductBase(BaseModel):
    name: Optional[str] = None
    default_code: Optional[str] = None
    list_price: Optional[float] = None
    standard_price: Optional[float] = None  # Coste
    categ_id: Optional[int] = None
    barcode: Optional[str] = None
    active: Optional[bool] = True
    type: Optional[str] = "consu"
    external_id: Optional[str] = None
    weight: Optional[float] = None
    sale_ok: Optional[bool] = True
    purchase_ok: Optional[bool] = True
    available_in_pos: Optional[bool] = True
    to_weight: Optional[bool] = False
    is_published: Optional[bool] = True
    website_sequence: Optional[int] = 10
    description_sale: Optional[str] = None
    description_purchase: Optional[str] = None
    sales_description: Optional[str] = None
    public_categ_ids: Optional[List[int]] = []
    seller_ids: Optional[List[Dict[str, Any]]] = []
    taxes_id: Optional[List[int]] = []
    supplier_taxes_id: Optional[List[int]] = []
    property_account_income_id: Optional[int] = None
    property_account_expense_id: Optional[int] = None
    # Campos de compatibilidad para el frontend
    code: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None
    product_name: Optional[str] = None
    location: Optional[str] = None
    last_updated: Optional[str] = None

# Modelo para leer un producto de Odoo (con campos obligatorios de solo lectura)
class Product(ProductBase):
    id: int
    name: str  # El nombre es obligatorio al leer un producto
    template_id: Optional[int] = None
    qty_available: Optional[float] = None
    virtual_available: Optional[float] = None
    incoming_qty: Optional[float] = None
    outgoing_qty: Optional[float] = None
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None
    product_tag_ids: Optional[List[int]] = []
    pos_categ_ids: Optional[List[int]] = []

# Modelo para crear un producto en Odoo
class ProductCreate(ProductBase):
    name: str  # El nombre es obligatorio para crear un producto

# Modelo para actualizar un producto en Odoo (hereda todos los campos opcionales)
class OdooProductUpdate(ProductBase):
    pass

# --- Fin de Modelos de Producto Refactorizados ---

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
    supplier: bool = True  # Calculado desde supplier_rank




class Provider(BaseModel):
    id: int
    name: str
    email: Optional[Union[str, bool, None]] = None
    phone: Optional[Union[str, bool, None]] = None
    is_company: bool = True
    supplier_rank: int = 1
    external_id: Optional[Union[str, bool, None]] = None
    ref: Optional[Union[str, bool, None]] = None
    vat: Optional[Union[str, bool, None]] = None
    website: Optional[Union[str, bool, None]] = None
    mobile: Optional[Union[str, bool, None]] = None
    function: Optional[Union[str, bool, None]] = None
    title: Optional[int] = None
    street: Optional[Union[str, bool, None]] = None
    street2: Optional[Union[str, bool, None]] = None
    city: Optional[Union[str, bool, None]] = None
    zip: Optional[Union[str, bool, None]] = None
    country_id: Optional[int] = None
    state_id: Optional[int] = None
    customer_rank: int = 0
    category_id: Optional[List[int]] = []
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    property_payment_term_id: Optional[int] = None
    property_supplier_payment_term_id: Optional[int] = None
    property_account_payable_id: Optional[int] = None
    property_account_receivable_id: Optional[int] = None
    active: bool = True
    lang: Optional[Union[str, bool, None]] = "es_ES"
    tz: Optional[Union[str, bool, None]] = "Europe/Madrid"
    comment: Optional[Union[str, bool, None]] = None
    country: Optional[Union[str, bool, None]] = None
    customer: bool = False
    supplier: bool = True

    @validator('*', pre=True)
    def false_to_empty(cls, v):
        if v is False or v is None:
            return ""
        return v

class ProviderCreate(BaseModel):
    name: str  # Campo obligatorio
    email: Optional[Union[str, bool, None]] = None
    phone: Optional[Union[str, bool, None]] = None
    street: Optional[Union[str, bool, None]] = None
    city: Optional[Union[str, bool, None]] = None
    country_id: Optional[int] = None
    customer_rank: int = 0  # No es cliente
    supplier_rank: int = 1  # Es proveedor
    is_company: bool = True  # Por defecto empresa
    # Campos de compatibilidad
    country: Optional[Union[str, bool, None]] = None
    customer: bool = False
    supplier: bool = True

    @validator('*', pre=True)
    def false_to_empty(cls, v):
        if v is False or v is None:
            return ""
        return v

class ProviderUpdate(BaseModel):
    name: Optional[Union[str, bool, None]] = None
    tax_calculation_method: Optional[Union[str, bool, None]] = None
    comment: Optional[Union[str, bool, None]] = None
    phone: Optional[Union[str, bool, None]] = None
    email: Optional[Union[str, bool, None]] = None
    street: Optional[Union[str, bool, None]] = None
    city: Optional[Union[str, bool, None]] = None
    country_id: Optional[int] = None
    customer_rank: Optional[int] = None
    supplier_rank: Optional[int] = None
    is_company: Optional[bool] = None
    country: Optional[Union[str, bool, None]] = None
    customer: Optional[bool] = None
    supplier: Optional[bool] = None

    @validator('*', pre=True)
    def false_to_empty(cls, v):
        if v is False or v is None:
            return ""
        return v

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
    limit: int
    pages: int
