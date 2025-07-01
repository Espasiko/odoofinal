from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date

class SupplierInfo(BaseModel):
    name: str
    vat: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None

class InvoiceMeta(BaseModel):
    number: str
    date: date
    type: str = Field(..., pattern="^(invoice|delivery_note|credit)$")
    currency: str = "EUR"

class InvoiceLine(BaseModel):
    code: str
    description: str
    qty: float
    price_unit: float
    subtotal: float
    tax_rate: Optional[float] = None

class Totals(BaseModel):
    base: float
    tax_rate: float
    tax_amount: float
    surcharge_rate: Optional[float] = None
    surcharge_amount: Optional[float] = None
    grand_total: float

class CoreInvoice(BaseModel):
    supplier: SupplierInfo
    invoice: InvoiceMeta
    totals: Totals
    lines: List[InvoiceLine]
    payment_terms: Optional[str] = None
