"""Utilidades para normalizar precios de proveedores antes de enviar a Odoo.

Este módulo centraliza la lógica de conversión de precios brutos
(con IVA y/o Recargo de Equivalencia) a precios netos.
"""
from typing import Optional, Union, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Configuración de proveedores con información detallada para mejorar la extracción OCR
# Incluye multiplicadores para convertir precio bruto → neto:
#   1.262 = 21 % IVA + 5.2 % Recargo de Equivalencia (IVA + RE)
#   1.21  = 21 % IVA
#   1.10  = 10 % IVA
#   1.052 = 4 % IVA + 1.2 % Recargo de Equivalencia
#   1.04  = 4 % IVA
PROVIDER_CONFIG: Dict[str, Dict[str, Any]] = {
    # Mayoristas con RE
    "ALMCE": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "tax_rate": 21.0,
        "recargo_rate": 5.2,
        "patron_descuento": r"\d+\s*%",
        "formato_factura": r"\d{4}/\d{4}",
        "prompt_addition": """
        Para facturas de ALMCE:
        - Busca la columna "R.E." junto a "IVA" (siempre aplica 5.2%)
        - Los descuentos aparecen como porcentajes en cada línea
        """
    },
    "FABRILAMP": {
        "price_multiplier": 1.21,
        "aplica_recargo": False,
        "tax_rate": 21.0,
        "recargo_rate": 0.0,
        "patron_descuento": r"\d+\s*%",
        "formato_factura": r"\d{8}",
        "prompt_addition": """
        Para facturas de FABRILAMP ILUMINACIÓN S.L.:
        - El cliente está en la parte superior derecha de la factura
        - El IVA es siempre 21% sin recargo de equivalencia
        - Los descuentos aparecen como porcentajes (10%) en cada línea
        - Los códigos de producto son numéricos (ej: 142591403)
        """
    },
    "NEVIR": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "tax_rate": 21.0,
        "recargo_rate": 5.2,
        "patron_descuento": r"\d+\s*%",
        "formato_factura": r"\d{6,8}"
    },
    "DISTRIBUCIONES": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "tax_rate": 21.0,
        "recargo_rate": 5.2
    },
    "MAYORISTA": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "tax_rate": 21.0,
        "recargo_rate": 5.2
    },
    "ALMACEN": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "tax_rate": 21.0,
        "recargo_rate": 5.2
    },
    "ALMACÉN": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "tax_rate": 21.0,
        "recargo_rate": 5.2
    },
    "COMERCIAL": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "tax_rate": 21.0,
        "recargo_rate": 5.2
    },
    "ABRILÁ": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "tax_rate": 21.0,
        "recargo_rate": 5.2,
        "patron_descuento": r"\d+\s*%",
        "formato_factura": r"\d{4}/\d{4}",
        "prompt_addition": """
        Para facturas de ABRILÁ ILUMINACIÓN:
        - Busca la columna "R.E." junto a "IVA" (siempre aplica 5.2%)
        - Los descuentos aparecen como porcentajes en cada línea
        - El formato de factura es YYYY/NNNN
        """
    },
    "FABRILAMP": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "tax_rate": 21.0,
        "recargo_rate": 5.2,
        "patron_descuento": r"\d+\s*%",
        "formato_factura": r"\d{8}",
        "prompt_addition": """
        Para facturas de FABRILAMP ILUMINACIÓN:
        - Siempre aplica recargo de equivalencia (5.2%)
        - Los descuentos aparecen como "XX%" en columna separada
        """
    },
    "ILUMINACIÓN": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "tax_rate": 21.0,
        "recargo_rate": 5.2
    },
    
    # Tiendas con IVA 21%
    "WORTEN": {
        "price_multiplier": 1.21,
        "aplica_recargo": False,
        "tax_rate": 21.0,
        "recargo_rate": 0.0
    },
    "MI ELECTRO": {
        "price_multiplier": 1.21,
        "aplica_recargo": False,
        "tax_rate": 21.0,
        "recargo_rate": 0.0
    },
    "JYSK": {
        "price_multiplier": 1.21,
        "aplica_recargo": False,
        "tax_rate": 21.0,
        "recargo_rate": 0.0
    },
    "MEDIA MARKT": {
        "price_multiplier": 1.21,
        "aplica_recargo": False,
        "tax_rate": 21.0,
        "recargo_rate": 0.0
    },
    "CARREFOUR": {
        "price_multiplier": 1.21,
        "aplica_recargo": False,
        "tax_rate": 21.0,
        "recargo_rate": 0.0
    },
    "ALCAMPO": {
        "price_multiplier": 1.21,
        "aplica_recargo": False,
        "tax_rate": 21.0,
        "recargo_rate": 0.0
    },
    "LEROY MERLIN": {
        "price_multiplier": 1.21,
        "aplica_recargo": False,
        "tax_rate": 21.0,
        "recargo_rate": 0.0
    },
    "IKEA": {
        "price_multiplier": 1.21,
        "aplica_recargo": False,
        "tax_rate": 21.0,
        "recargo_rate": 0.0
    },
    
    # Alimentación con IVA 10%
    "MERCADONA": {
        "price_multiplier": 1.10,
        "aplica_recargo": False,
        "tax_rate": 10.0,
        "recargo_rate": 0.0
    },
    "DIA": {
        "price_multiplier": 1.10,
        "aplica_recargo": False,
        "tax_rate": 10.0,
        "recargo_rate": 0.0
    },
    "LIDL": {
        "price_multiplier": 1.10,
        "aplica_recargo": False,
        "tax_rate": 10.0,
        "recargo_rate": 0.0
    },
    "ALDI": {
        "price_multiplier": 1.10,
        "aplica_recargo": False,
        "tax_rate": 10.0,
        "recargo_rate": 0.0
    },
    
    # Productos con IVA 4% + RE
    "FARMACIA": {
        "price_multiplier": 1.052,
        "aplica_recargo": True,
        "tax_rate": 4.0,
        "recargo_rate": 1.2
    },
    "PARAFARMACIA": {
        "price_multiplier": 1.052,
        "aplica_recargo": True,
        "tax_rate": 4.0,
        "recargo_rate": 1.2
    },
    
    # Productos con IVA 4%
    "LIBRERÍA": {
        "price_multiplier": 1.04,
        "aplica_recargo": False,
        "tax_rate": 4.0,
        "recargo_rate": 0.0
    },
    "LIBRERIA": {
        "price_multiplier": 1.04,
        "aplica_recargo": False,
        "tax_rate": 4.0,
        "recargo_rate": 0.0
    },
    "PAPELERÍA": {
        "price_multiplier": 1.04,
        "aplica_recargo": False,
        "tax_rate": 4.0,
        "recargo_rate": 0.0
    },
    "PAPELERIA": {
        "price_multiplier": 1.04,
        "aplica_recargo": False,
        "tax_rate": 4.0,
        "recargo_rate": 0.0
    }
}

PRICE_MULTIPLIERS: Dict[str, float] = {
    key: config["price_multiplier"] for key, config in PROVIDER_CONFIG.items()
}

def adjust_price_for_supplier(supplier_name: Optional[str], price: Union[float, int, str, None]) -> Dict[str, Any]:
    """Convierte un precio bruto a neto según el proveedor y devuelve información detallada.

    Args:
        supplier_name: Nombre del proveedor (tal como viene del OCR o Excel).
        price: Precio capturado (posiblemente con impuestos incluidos).

    Returns:
        Diccionario con información detallada:
        - price_net: Precio neto (sin impuestos) redondeado a 2 decimales
        - price_original: Precio original de entrada
        - provider_matched: Proveedor coincidente en la configuración (o None)
        - tax_rate: Tasa de IVA detectada (21.0, 10.0, 4.0)
        - recargo_rate: Tasa de recargo de equivalencia (5.2, 1.4, 0.5, 0.0)
        - aplica_recargo: Booleano indicando si se aplica recargo
    """
    # Inicializar resultado con valores por defecto
    result = {
        "price_net": 0.0,
        "price_original": price,
        "provider_matched": None,
        "tax_rate": 21.0,  # IVA por defecto
        "recargo_rate": 0.0,
        "aplica_recargo": False
    }
    
    # Manejar valores nulos o no numéricos
    if price is None:
        logger.warning("Se recibió un precio None, devolviendo 0.0")
        return result
    
    # Intentar convertir a float si es string
    if isinstance(price, str):
        try:
            # Verificar si el string está vacío
            if not price.strip():
                logger.warning("Se recibió un precio como string vacío, devolviendo 0.0")
                return result
                
            # Limpiar el string de caracteres no numéricos excepto punto decimal
            clean_price = ''.join(c for c in price if c.isdigit() or c == '.')
            if not clean_price:
                logger.warning(f"No se encontraron dígitos en el precio '{price}', devolviendo 0.0")
                return result
                
            price = float(clean_price)
        except (ValueError, TypeError) as e:
            logger.warning(f"No se pudo convertir el precio '{price}' a float: {str(e)}, devolviendo 0.0")
            return result
    
    # Convertir a float si es entero
    if isinstance(price, int):
        price = float(price)
    
    # Verificar que el precio sea un número válido
    if not isinstance(price, float):
        logger.warning(f"Precio no es float después de conversión: {type(price)}, valor: {price}, devolviendo 0.0")
        return result
        
    if price < 0:
        logger.warning(f"Precio negativo: {price}, devolviendo 0.0")
        return result
    
    result["price_original"] = price
    
    # Si no hay nombre de proveedor, devolver el precio tal cual
    if not supplier_name:
        result["price_net"] = round(price, 2)
        return result
    
    # Buscar coincidencias con proveedores conocidos
    supplier_key = supplier_name.strip().upper() if supplier_name else ""
    matched_provider = None
    
    # Buscar coincidencia exacta primero
    if supplier_key in PROVIDER_CONFIG:
        matched_provider = supplier_key
    else:
        # Buscar coincidencia parcial
        for prov in PROVIDER_CONFIG:
            if prov in supplier_key:
                matched_provider = prov
                break
    
    # Si encontramos un proveedor configurado
    if matched_provider:
        config = PROVIDER_CONFIG[matched_provider]
        multiplier = config["price_multiplier"]
        
        # Verificación adicional antes de la división
        if not isinstance(multiplier, (int, float)) or multiplier == 0:
            logger.error(f"Multiplicador inválido para proveedor {matched_provider}: {multiplier}")
            result["price_net"] = round(price, 2)
        else:
            try:
                adjusted_price = round(price / multiplier, 2)
                
                result.update({
                    "price_net": adjusted_price,
                    "provider_matched": matched_provider,
                    "tax_rate": config["tax_rate"],
                    "recargo_rate": config["recargo_rate"],
                    "aplica_recargo": config["aplica_recargo"]
                })
                
                logger.info(f"Precio ajustado para proveedor '{supplier_name}' ({matched_provider}): "
                          f"{price} → {adjusted_price} (factor: {multiplier}, "
                          f"IVA: {config['tax_rate']}%, RE: {config['recargo_rate']}%)")
            except (TypeError, ValueError) as e:
                logger.error(f"Error al ajustar precio para proveedor {matched_provider}: {str(e)}")
                logger.error(f"Tipo de precio: {type(price)}, valor: {price}")
                logger.error(f"Tipo de multiplicador: {type(multiplier)}, valor: {multiplier}")
                result["price_net"] = round(price, 2)
    else:
        # Si no hay coincidencias, devolver el precio tal cual
        result["price_net"] = round(price, 2)
        logger.info(f"No se encontró configuración para '{supplier_name}', usando precio original: {price}")
    
    return result


def get_price_net(supplier_name: Optional[str], price: Union[float, int, str, None]) -> float:
    """Función de compatibilidad que devuelve solo el precio neto.
    
    Mantiene la compatibilidad con el código existente que espera solo el precio.
    
    Args:
        supplier_name: Nombre del proveedor
        price: Precio bruto
        
    Returns:
        Precio neto como float
    """
    result = adjust_price_for_supplier(supplier_name, price)
    return result["price_net"]


def extract_tax_info(line_item: Dict[str, Any], supplier_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Extrae y normaliza la información de impuestos de una línea de factura OCR.
    
    Args:
        line_item: Diccionario con la información de la línea de factura.
        supplier_name: Nombre del proveedor para aplicar reglas específicas.
        
    Returns:
        Diccionario con la información normalizada de impuestos:
        - tax_type: Tipo de impuesto normalizado ('iva_21', 'iva_10', 'iva_4')
        - tax_rate: Porcentaje de impuesto (21.0, 10.0, 4.0)
        - apply_recargo_equivalencia: Booleano indicando si se aplica recargo
        - recargo_rate: Porcentaje de recargo de equivalencia (5.2, 1.4, 0.5, 0.0)
        - supplier_matched: Proveedor coincidente en la configuración (o None)
    """
    result = {
        "tax_type": "iva_21",  # Por defecto IVA 21%
        "tax_rate": 21.0,
        "apply_recargo_equivalencia": False,
        "recargo_rate": 0.0,
        "supplier_matched": None
    }
    
    # 1. Primero verificar si tenemos información del proveedor en PROVIDER_CONFIG
    if supplier_name:
        supplier_key = supplier_name.strip().upper()
        matched_provider = None
        
        # Buscar coincidencia exacta primero
        if supplier_key in PROVIDER_CONFIG:
            matched_provider = supplier_key
        else:
            # Buscar coincidencia parcial
            for prov in PROVIDER_CONFIG:
                if prov in supplier_key:
                    matched_provider = prov
                    break
        
        # Si encontramos un proveedor configurado, usar su configuración
        if matched_provider:
            config = PROVIDER_CONFIG[matched_provider]
            result.update({
                "tax_rate": config["tax_rate"],
                "apply_recargo_equivalencia": config["aplica_recargo"],
                "recargo_rate": config["recargo_rate"],
                "supplier_matched": matched_provider
            })
            
            # Asignar el tipo de impuesto según la tasa
            if result["tax_rate"] == 21.0:
                result["tax_type"] = "iva_21"
            elif result["tax_rate"] == 10.0:
                result["tax_type"] = "iva_10"
            elif result["tax_rate"] == 4.0:
                result["tax_type"] = "iva_4"
            
            logger.info(f"Configuración de impuestos aplicada para proveedor '{supplier_name}' "
                      f"({matched_provider}): IVA {result['tax_rate']}%, "
                      f"RE: {result['apply_recargo_equivalencia']} ({result['recargo_rate']}%)")
    
    # 2. Extraer información explícita de impuestos del item (puede sobrescribir la configuración del proveedor)
    tax_info = line_item.get("tax_type", "") or line_item.get("tax", "") or ""
    tax_rate = line_item.get("tax_rate", None)
    
    # Normalizar tax_info a string
    if not isinstance(tax_info, str):
        tax_info = str(tax_info).lower() if tax_info else ""
    else:
        tax_info = tax_info.lower()
    
    # Detectar tipo de impuesto por texto
    if "21" in tax_info or "21%" in tax_info or "iva21" in tax_info or "iva 21" in tax_info or "iva_21" in tax_info:
        result["tax_type"] = "iva_21"
        result["tax_rate"] = 21.0
    elif "10" in tax_info or "10%" in tax_info or "iva10" in tax_info or "iva 10" in tax_info or "iva_10" in tax_info:
        result["tax_type"] = "iva_10"
        result["tax_rate"] = 10.0
    elif "4" in tax_info or "4%" in tax_info or "iva4" in tax_info or "iva 4" in tax_info or "iva_4" in tax_info:
        result["tax_type"] = "iva_4"
        result["tax_rate"] = 4.0
    
    # Si hay un tax_rate explícito, usarlo para determinar el tipo de impuesto
    if tax_rate is not None:
        try:
            if isinstance(tax_rate, str):
                # Limpiar y convertir a float
                clean_rate = ''.join(c for c in tax_rate if c.isdigit() or c == '.')
                tax_rate = float(clean_rate)
            else:
                tax_rate = float(tax_rate)
                
            # Asignar tipo de impuesto según el rate
            if 20 <= tax_rate <= 22:  # Margen para IVA 21%
                result["tax_type"] = "iva_21"
                result["tax_rate"] = 21.0
            elif 9 <= tax_rate <= 11:  # Margen para IVA 10%
                result["tax_type"] = "iva_10"
                result["tax_rate"] = 10.0
            elif 3 <= tax_rate <= 5:  # Margen para IVA 4%
                result["tax_type"] = "iva_4"
                result["tax_rate"] = 4.0
        except (ValueError, TypeError):
            logger.warning(f"No se pudo convertir el tax_rate '{tax_rate}' a float")
    
    # 3. Detectar recargo de equivalencia explícito (puede sobrescribir la configuración del proveedor)
    recargo_info = line_item.get("apply_recargo_equivalencia", None) or line_item.get("recargo_equivalencia", None)
    if recargo_info is not None:
        if isinstance(recargo_info, bool):
            result["apply_recargo_equivalencia"] = recargo_info
        elif isinstance(recargo_info, str):
            result["apply_recargo_equivalencia"] = recargo_info.lower() in ['true', 'yes', 'si', 'sí', '1', 'verdadero']
        else:
            try:
                result["apply_recargo_equivalencia"] = bool(recargo_info)
            except (ValueError, TypeError):
                pass
    
    # 4. Buscar recargo de equivalencia en el nombre, descripción o cualquier campo de texto
    for field in ["name", "description", "product_description", "line_description", "notes"]:
        text = line_item.get(field, "") or ""
        if isinstance(text, str) and any(term in text.lower() for term in [
            'recargo', 'r.e.', 'r. e.', 're', 'equivalencia', 'rec. equiv.', 'rec.equiv', 'r.equiv'
        ]):
            result["apply_recargo_equivalencia"] = True
            break
    
    # 5. Buscar valores específicos de recargo de equivalencia
    recargo_rate = line_item.get("recargo_rate", None) or line_item.get("re_rate", None)
    if recargo_rate is not None:
        try:
            if isinstance(recargo_rate, str):
                clean_rate = ''.join(c for c in recargo_rate if c.isdigit() or c == '.')
                recargo_rate = float(clean_rate)
            else:
                recargo_rate = float(recargo_rate)
                
            # Si hay un valor de recargo, asumimos que se aplica
            if recargo_rate > 0:
                result["apply_recargo_equivalencia"] = True
                result["recargo_rate"] = recargo_rate
        except (ValueError, TypeError):
            logger.warning(f"No se pudo convertir el recargo_rate '{recargo_rate}' a float")
    
    # 6. Asignar recargo_rate según el tipo de IVA si aplica recargo pero no tenemos tasa específica
    if result["apply_recargo_equivalencia"] and result["recargo_rate"] == 0.0:
        if result["tax_rate"] == 21.0:
            result["recargo_rate"] = 5.2  # Recargo para IVA 21%
        elif result["tax_rate"] == 10.0:
            result["recargo_rate"] = 1.4  # Recargo para IVA 10%
        elif result["tax_rate"] == 4.0:
            result["recargo_rate"] = 0.5  # Recargo para IVA 4%
    
    return result
