"""
Utilidades de validación para facturas y datos OCR
"""
import logging
from typing import Dict, Tuple, Any, List, Optional

logger = logging.getLogger(__name__)

def validate_invoice_totals(extracted_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Valida que los totales extraídos sean coherentes con los subtotales y los impuestos.
    
    Args:
        extracted_data: Datos extraídos de la factura
        
    Returns:
        Tuple[bool, Dict]: (es_válido, detalles_validación)
    """
    if not extracted_data or not extracted_data.get("line_items"):
        return False, {"error": "No hay datos de factura o líneas para validar"}
    
    # Obtener totales declarados
    declared_subtotal = float(extracted_data.get("subtotal", 0) or 0)
    declared_tax_amount = float(extracted_data.get("tax_amount", 0) or 0)
    declared_recargo = float(extracted_data.get("recargo_equivalencia", 0) or 0)
    declared_total = float(extracted_data.get("total_amount", 0) or 0)
    
    # Calcular totales basados en líneas
    calculated_subtotal = 0
    calculated_tax = 0
    calculated_recargo = 0
    
    for line in extracted_data.get("line_items", []):
        price = float(line.get("price_unit", 0) or 0)
        qty = float(line.get("quantity", 1) or 1)
        discount = float(line.get("discount", 0) or 0)
        
        # Aplicar descuento
        line_subtotal = price * qty * (1 - discount/100)
        calculated_subtotal += line_subtotal
        
        # Calcular impuestos
        tax_rate = float(line.get("tax_rate", 0) or 0)
        recargo_rate = float(line.get("recargo_rate", 0) or 0)
        
        calculated_tax += line_subtotal * tax_rate / 100
        calculated_recargo += line_subtotal * recargo_rate / 100
    
    # Calcular total
    calculated_total = calculated_subtotal + calculated_tax + calculated_recargo
    
    # Verificar diferencias (con margen de tolerancia de 1€)
    subtotal_diff = abs(declared_subtotal - calculated_subtotal)
    tax_diff = abs(declared_tax_amount - calculated_tax)
    recargo_diff = abs(declared_recargo - calculated_recargo)
    total_diff = abs(declared_total - calculated_total)
    
    # Tolerancias
    subtotal_tolerance = 1.0  # 1€
    tax_tolerance = 1.0  # 1€
    recargo_tolerance = 0.5  # 50 céntimos
    total_tolerance = 1.0  # 1€
    
    # Verificar si las diferencias están dentro de las tolerancias
    subtotal_valid = subtotal_diff <= subtotal_tolerance
    tax_valid = tax_diff <= tax_tolerance
    recargo_valid = recargo_diff <= recargo_tolerance
    total_valid = total_diff <= total_tolerance
    
    # Resultado global
    is_valid = subtotal_valid and tax_valid and recargo_valid and total_valid
    
    validation_details = {
        "subtotal": {
            "declared": declared_subtotal,
            "calculated": round(calculated_subtotal, 2),
            "difference": round(subtotal_diff, 2),
            "valid": subtotal_valid
        },
        "tax_amount": {
            "declared": declared_tax_amount,
            "calculated": round(calculated_tax, 2),
            "difference": round(tax_diff, 2),
            "valid": tax_valid
        },
        "recargo_equivalencia": {
            "declared": declared_recargo,
            "calculated": round(calculated_recargo, 2),
            "difference": round(recargo_diff, 2),
            "valid": recargo_valid
        },
        "total_amount": {
            "declared": declared_total,
            "calculated": round(calculated_total, 2),
            "difference": round(total_diff, 2),
            "valid": total_valid
        },
        "is_valid": is_valid
    }
    
    if not is_valid:
        logger.warning(f"Validación de totales fallida: {validation_details}")
    
    return is_valid, validation_details

def validate_supplier_vat(vat: str) -> bool:
    """
    Valida un NIF/CIF español según las reglas oficiales
    
    Args:
        vat: NIF/CIF a validar
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not vat or len(vat) < 8:
        return False
    
    # Eliminar espacios y convertir a mayúsculas
    vat = vat.replace(" ", "").upper()
    
    # Validación básica de formato
    if len(vat) < 8 or len(vat) > 9:
        return False
    
    # TODO: Implementar validación completa del dígito de control
    # Por ahora hacemos una validación básica
    
    # Para NIFs (personas físicas)
    if vat[0].isalpha() and vat[0] in "KLMXYZ":
        return len(vat) == 9 and vat[1:8].isdigit() and vat[8].isalpha()
    
    # Para CIFs (empresas)
    if vat[0].isalpha() and vat[0] in "ABCDEFGHJNPQRSUVW":
        return len(vat) == 9 and vat[1:8].isdigit() and (vat[8].isdigit() or vat[8].isalpha())
    
    # Para NIFs estándar
    if vat[0].isdigit():
        return len(vat) == 9 and vat[0:8].isdigit() and vat[8].isalpha()
    
    return False

def validate_product_code(code: str, provider: str) -> bool:
    """
    Valida el formato del código de producto según el proveedor
    
    Args:
        code: Código de producto
        provider: Nombre del proveedor
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not code or not provider:
        return False
    
    provider_upper = provider.upper()
    
    # Validación para NEVIR
    if "NEVIR" in provider_upper:
        return code.startswith("NVR-")
    
    # Validación para FABRILAMP
    if "FABRILAMP" in provider_upper:
        # Códigos numéricos o con formato específico
        return code.isdigit() or code.startswith("CANON/")
    
    # Validación para ABRILÁ
    if "ABRILA" in provider_upper or "ABRILÁ" in provider_upper:
        # Formato específico para ABRILÁ
        return True  # TODO: Implementar validación específica
    
    # Por defecto, aceptamos cualquier formato
    return True
