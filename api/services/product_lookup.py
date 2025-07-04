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
    # Validar entradas
    if not default_code and not barcode:
        logging.warning("find_existing_product: No se proporcionó default_code ni barcode para buscar")
        return None
        
    # Construir dominio de búsqueda
    domain = []
    
    # Añadir condiciones solo si los valores no son nulos
    conditions = []
    if default_code:
        conditions.append(('default_code', '=', default_code))
    if barcode:
        conditions.append(('barcode', '=', barcode))
    
    # Si hay múltiples condiciones, usamos OR
    if len(conditions) > 1:
        domain = ['|'] + conditions
    else:
        domain = conditions
    
    # Añadir filtro por proveedor si se proporciona
    if supplier_id:
        # En Odoo 18, la relación correcta es seller_ids.partner_id, no seller_ids.name
        domain = ['&'] + domain + [('seller_ids.partner_id', '=', supplier_id)]

    try:
        logging.info(f"Buscando producto existente con dominio: {domain}")
        ids = service._execute_kw('product.template', 'search', [domain], {'limit': 1})
        
        if ids:
            logging.info(f"Producto encontrado con ID: {ids[0]}")
            # Obtener nombre para el log
            try:
                product_data = service._execute_kw(
                    'product.template',
                    'read',
                    [ids[0]],
                    {'fields': ['name', 'default_code']}
                )
                if product_data:
                    logging.info(f"Producto encontrado: {product_data[0].get('name')} [{product_data[0].get('default_code')}]")
            except Exception as e:
                logging.warning(f"No se pudo obtener detalles del producto encontrado: {e}")
                
            return ids[0]
        else:
            logging.info(f"No se encontró producto existente con default_code={default_code} o barcode={barcode}")
            return None
    except Exception as exc:
        logging.error(f"Error en búsqueda de producto: {exc}")
        return None
