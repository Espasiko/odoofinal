"""Utilidades para normalizar precios de proveedores antes de enviar a Odoo.

Este módulo centraliza la lógica de conversión de precios brutos
(con IVA y/o Recargo de Equivalencia) a precios netos.
"""
from typing import Optional

# Multiplicadores para convertir precio bruto → neto
#   1.262 = 21 % IVA + 5.2 % Recargo de Equivalencia
#   1.21  = 21 % IVA
PRICE_MULTIPLIERS = {
    "ALMCE": 1.262,
    "NEVIR": 1.262,
    "WORTEN": 1.21,
    "MI ELECTRO": 1.21,
    "JYSK": 1.21,
}

def adjust_price_for_supplier(supplier_name: Optional[str], price: float) -> float:
    """Convierte un precio bruto a neto según el proveedor.

    Args:
        supplier_name: Nombre del proveedor (tal como viene del OCR o Excel).
        price: Precio capturado (posiblemente con impuestos incluidos).

    Returns:
        Precio neto (sin impuestos) redondeado a 2 decimales si correspondía
        aplicar conversión, o el precio original si ya era neto.
    """
    if price is None:
        return 0.0
    if not supplier_name:
        return price
    key = supplier_name.strip().upper()
    for prov, multiplier in PRICE_MULTIPLIERS.items():
        if prov in key:
            return round(price / multiplier, 2)
    return price
