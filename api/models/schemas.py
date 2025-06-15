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
    categ_id: Optional[List[int]] = None  # ID de categoría [id, name] (opcional)
    active: bool = True  # Estado activo/inactivo
    type: Optional[str] = "consu"  # Tipo de producto: consu, service, product
    # Campos calculados para compatibilidad con frontend
    code: Optional[str] = None  # Alias para default_code
    price: Optional[float] = None  # Alias para list_price
    category: Optional[str] = None  # Nombre de categoría para mostrar
    stock: Optional[int] = None  # Stock calculado
    image_url: Optional[str] = None  # URL de imagen

class ProductCreate(BaseModel):
    name: str  # Campo obligatorio
    default_code: Optional[str] = None  # Código del producto
    list_price: Optional[float] = None  # Precio de venta
    categ_id: Optional[int] = None  # ID de categoría
    active: bool = True  # Estado activo
    type: Optional[str] = "consu"  # Tipo de producto
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
    email: Optional[str] = None  # Opcional en Odoo
    phone: Optional[str] = None  # Opcional en Odoo
    street: Optional[str] = None  # Dirección (opcional)
    city: Optional[str] = None  # Ciudad (opcional)
    country_id: Optional[List[int]] = None  # [id, name] del país (opcional)
    customer_rank: int = 0  # Rango de cliente (0 = no es cliente)
    supplier_rank: int = 1  # Rango de proveedor (1 = es proveedor)
    is_company: bool = True  # Por defecto empresa para proveedores
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
    total_products: Optional[int] = 0
    total_sales: Optional[float] = 0.0
    total_customers: Optional[int] = 0
    total_inventory_value: Optional[float] = 0.0
    recent_sales: Optional[List[Sale]] = []
    low_stock_products: Optional[List[Product]] = []

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
