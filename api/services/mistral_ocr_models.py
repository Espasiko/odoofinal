"""
Modelos de datos para OCR con Mistral AI
"""
from typing import Optional, List
from pydantic import BaseModel, Field

class InvoiceLine(BaseModel):
    """Modelo para línea de factura"""
    name: str = Field(description="Descripción del producto o servicio")
    quantity: float = Field(description="Cantidad")
    price_unit: float = Field(description="Precio unitario")
    default_code: Optional[str] = Field(None, description="Código del producto")

class OdooInvoice(BaseModel):
    """Modelo para factura de Odoo"""
    invoice_number: str = Field(description="Número de factura")
    invoice_date: str = Field(description="Fecha de la factura (formato DD/MM/YYYY)")
    due_date: Optional[str] = Field(None, description="Fecha de vencimiento (formato DD/MM/YYYY)")
    
    supplier_name: str = Field(description="Nombre del PROVEEDOR (quien emite la factura)")
    supplier_vat: Optional[str] = Field(None, description="CIF/NIF del proveedor")
    supplier_address: Optional[str] = Field(None, description="Dirección del proveedor")
    supplier_city: Optional[str] = Field(None, description="Ciudad del proveedor")
    supplier_zip: Optional[str] = Field(None, description="Código postal del proveedor")
    supplier_email: Optional[str] = Field(None, description="Email del proveedor")
    supplier_phone: Optional[str] = Field(None, description="Teléfono del proveedor")
    
    customer_name: Optional[str] = Field(None, description="Nombre del CLIENTE (quien recibe la factura)")
    customer_vat: Optional[str] = Field(None, description="CIF/NIF del cliente")
    
    total_amount: float = Field(description="Importe total con impuestos")
    tax_amount: Optional[float] = Field(None, description="Importe de impuestos")
    subtotal: Optional[float] = Field(None, description="Subtotal sin impuestos")
    
    payment_terms: Optional[str] = Field(None, description="Condiciones de pago")
    customer_order_ref: Optional[str] = Field(None, description="Referencia de pedido del cliente")
    
    line_items: list[InvoiceLine] = Field(default_factory=list, description="Líneas de productos/servicios")
