from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

# Modelo para lista de precios de proveedores - Basado en product.supplierinfo de Odoo
class SupplierPriceList(BaseModel):
    id: int
    partner_id: int  # ID del proveedor (res.partner)
    product_tmpl_id: Optional[int] = None  # ID del template del producto
    product_id: Optional[int] = None  # ID específico del producto
    
    # CAMPOS OBLIGATORIOS DE ODOO
    external_id: Optional[str] = None  # External ID único
    product_name: Optional[str] = None  # Nombre del producto del proveedor
    product_code: Optional[str] = None  # Código del producto del proveedor
    
    # CAMPOS DE PRECIO Y CANTIDAD
    price: float  # Precio del proveedor
    min_qty: float = 1.0  # Cantidad mínima
    currency_id: Optional[int] = None  # ID de la moneda
    
    # CAMPOS DE FECHAS
    date_start: Optional[datetime] = None  # Fecha de inicio de validez
    date_end: Optional[datetime] = None  # Fecha de fin de validez
    
    # CAMPOS DE CONFIGURACIÓN
    sequence: int = 1  # Secuencia (prioridad)
    delay: int = 1  # Días de entrega
    company_id: Optional[int] = None  # ID de la empresa
    
    # CAMPOS CALCULADOS
    partner_name: Optional[str] = None  # Nombre del proveedor
    product_name_display: Optional[str] = None  # Nombre completo para mostrar
    is_active: bool = True  # Si está activo según fechas

class SupplierPriceListCreate(BaseModel):
    partner_id: int  # ID del proveedor (obligatorio)
    product_tmpl_id: Optional[int] = None
    product_id: Optional[int] = None
    external_id: Optional[str] = None
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    price: float  # Precio (obligatorio)
    min_qty: float = 1.0
    currency_id: Optional[int] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    sequence: int = 1
    delay: int = 1
    company_id: Optional[int] = None

class SupplierPriceListUpdate(BaseModel):
    partner_id: Optional[int] = None
    product_tmpl_id: Optional[int] = None
    product_id: Optional[int] = None
    external_id: Optional[str] = None
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    price: Optional[float] = None
    min_qty: Optional[float] = None
    currency_id: Optional[int] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    sequence: Optional[int] = None
    delay: Optional[int] = None
    company_id: Optional[int] = None