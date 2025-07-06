from typing import Dict, Any
import logging
from .product_categorization import get_category_for_product

"""Utility functions for transforming incoming product data (Pydantic models)
into the `vals` dict accepted by Odoo's XML-RPC `create` / `write` methods.
Keeping this logic isolated makes `OdooProductService` slimmer and easier to test.
"""

ALLOWED_FIELDS = {
    'name', 'default_code', 'list_price', 'standard_price', 'categ_id',
    'barcode', 'active', 'type', 'weight', 'sale_ok', 'purchase_ok',
    'available_in_pos', 'to_weight', 'is_published', 'website_sequence',
    'description_sale', 'description_purchase', 'public_categ_ids',
    'seller_ids', 'taxes_id', 'supplier_taxes_id',
    'property_account_income_id', 'property_account_expense_id'
}

FIELD_MAPPINGS = {
    'price': 'list_price',
    'cost': 'standard_price',
    'code': 'default_code',
}

def prepare_product_vals(product_data, supplier_name=None) -> Dict[str, Any]:
    """Return a dict with only the fields that Odoo accepts.

    `product_data` can be a Pydantic model (ProductCreate / OdooProductUpdate) or
    any object exposing `model_dump(exclude_unset=True)`.
    
    Args:
        product_data: Datos del producto (Pydantic model o dict)
        supplier_name: Nombre del proveedor (opcional)
        
    Returns:
        Dict con valores válidos para Odoo
    """
    raw = product_data.model_dump(exclude_unset=True) if hasattr(product_data, 'model_dump') else product_data
    vals: Dict[str, Any] = {}

    # Normalización para asegurar que el campo de coste siempre se mapee correctamente
    # Si existe 'IMPORTE BRUTO' en los datos originales, lo mapeamos a 'cost'
    if 'IMPORTE BRUTO' in raw:
        try:
            # Elimina símbolo euro y espacios, convierte a float
            importe_bruto = raw['IMPORTE BRUTO']
            if isinstance(importe_bruto, str):
                importe_bruto = importe_bruto.replace('€', '').replace(',', '.').strip()
            vals['standard_price'] = float(importe_bruto)
        except Exception as e:
            logging.warning(f"Error al procesar IMPORTE BRUTO: {e}")
            
    # También mapeamos el campo de precio de venta si viene con el nombre del Excel
    if 'P.V.P FINAL CLIENTE' in raw:
        try:
            pvp_final = raw['P.V.P FINAL CLIENTE']
            if isinstance(pvp_final, str):
                pvp_final = pvp_final.replace('€', '').replace(',', '.').strip()
            vals['list_price'] = float(pvp_final)
        except Exception as e:
            logging.warning(f"Error al procesar P.V.P FINAL CLIENTE: {e}")

    # Mapeo estándar para el resto de campos
    for key, value in raw.items():
        # Ignorar PVP WEB
        if key.strip().upper() == 'PVP WEB':
            continue
        odoo_key = FIELD_MAPPINGS.get(key, key)
        if odoo_key in ALLOWED_FIELDS and value not in (None, "") and odoo_key not in vals:
            vals[odoo_key] = value
            
    # Inferir categoría si no está definida
    if 'categ_id' not in vals and 'name' in vals:
        product_name = vals.get('name', '')
        category_id = get_category_for_product(product_name, supplier_name)
        if category_id and category_id != 1:  # Si encontramos una categoría distinta de "All"
            vals['categ_id'] = category_id
            logging.info(f"Categoría inferida para '{product_name}': {category_id}")
            
    return vals
