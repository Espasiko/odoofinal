from typing import Dict, Any

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

def prepare_product_vals(product_data) -> Dict[str, Any]:
    """Return a dict with only the fields that Odoo accepts.

    `product_data` can be a Pydantic model (ProductCreate / OdooProductUpdate) or
    any object exposing `model_dump(exclude_unset=True)`.
    """
    raw = product_data.model_dump(exclude_unset=True)
    vals: Dict[str, Any] = {}

    for key, value in raw.items():
        odoo_key = FIELD_MAPPINGS.get(key, key)
        if odoo_key in ALLOWED_FIELDS and value not in (None, ""):
            vals[odoo_key] = value
    return vals
