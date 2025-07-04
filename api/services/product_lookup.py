from typing import Optional
import logging

"""Product lookup helpers isolated from the main service class."""

def find_existing_product(service, default_code: Optional[str], barcode: Optional[str], supplier_id: Optional[int] = None) -> Optional[int]:
    """Searches Odoo for an existing product.

    Args:
        service: *Instance of* OdooProductService (has _execute_kw).
        default_code: Internal reference/SKU.
        barcode: EAN/UPC.
        supplier_id: Optional supplier partner id to further filter.

    Returns: product.template ID or None.
    """
    domain = ['|', ('default_code', '=', default_code or False),
                    ('barcode', '=', barcode or False)]
    if supplier_id:
        domain = ['&'] + domain + [('seller_ids.name', '=', supplier_id)]

    try:
        ids = service._execute_kw('product.template', 'search', [domain], {'limit': 1})
        return ids[0] if ids else None
    except Exception as exc:
        logging.error("Product lookup failed: %s", exc)
        return None
