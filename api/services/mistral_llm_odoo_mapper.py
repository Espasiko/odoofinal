from typing import List, Dict, Any, Optional
from api.services.odoo_service import odoo_service
from api.models.schemas import ProductCreate, ProviderCreate, OdooProductUpdate
import logging

def merge_chunked_llm_jsons(json_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Une los JSONs chunked de Mistral LLM en una sola estructura."""
    merged = {"productos": [], "proveedor": None}
    for chunk in json_chunks:
        if "productos" in chunk:
            merged["productos"].extend(chunk["productos"])
        # Si algún chunk trae proveedor, lo guardamos (el primero encontrado)
        if not merged["proveedor"] and chunk.get("proveedor"):
            merged["proveedor"] = chunk["proveedor"]
    return merged

def map_llm_json_to_odoo(merged_json: Dict[str, Any], fallback_supplier: Optional[str] = None) -> List[str]:
    """
    Mapea el JSON unificado de Mistral LLM a productos Odoo, usando helpers existentes.
    fallback_supplier: Si no hay proveedor en el JSON, usar este nombre.
    Devuelve una lista de códigos de productos creados/actualizados.
    """
    productos = merged_json.get("productos", [])
    proveedor_nombre = merged_json.get("proveedor", {}).get("nombre") if merged_json.get("proveedor") else fallback_supplier
    if not proveedor_nombre:
        raise ValueError("No se pudo determinar el proveedor. Es obligatorio para la importación.")

    # Buscar o crear proveedor en Odoo
    proveedor = odoo_service.get_supplier_by_name(proveedor_nombre)
    if not proveedor:
        proveedor_data = ProviderCreate(name=proveedor_nombre)
        proveedor = odoo_service.create_supplier(proveedor_data)
    proveedor_id = proveedor.id if proveedor else None

    productos_creados_o_actualizados = []
    for prod in productos:
        # 1. Resolver Categoría
        categoria_nombre = prod.get("categoria", "Sin Categoría")
        categoria_id = odoo_service.find_or_create_category(categoria_nombre)

        # 2. Preparar datos del proveedor para el producto
        cost_price = prod.get("precio_coste") or prod.get("coste") or 0.0
        seller_info = []
        if proveedor_id:
            # Formato especial de Odoo para crear/actualizar líneas One2many
            seller_info = [(0, 0, {'partner_id': proveedor_id, 'price': cost_price})]

        # 3. Buscar producto por código y preparar datos
        codigo = prod.get("codigo") or prod.get("default_code")
        if not codigo:
            logging.warning(f"Producto sin código, saltando: {prod}")
            continue
        
        # Datos comunes para crear y actualizar
        product_data = {
            "name": prod.get("nombre") or prod.get("descripcion") or "Producto sin nombre",
            "default_code": codigo,
            "list_price": prod.get("pvp_final_cliente") or prod.get("pvp_web") or prod.get("importe_bruto") or 0.0,
            "standard_price": cost_price, # Precio de coste
            "categ_id": categoria_id,
            "active": True,
            "seller_ids": seller_info,
            "description_sale": prod.get("descripcion"),
            "type": "product" # Almacenable
        }

        # 4. Crear o Actualizar
        producto_existente = odoo_service.product_service.find_product_by_code(codigo)
        if producto_existente:
            update_vals = OdooProductUpdate(**product_data).dict(exclude_unset=True)
            odoo_service.update_product(producto_existente.id, update_vals)
            logging.info(f"Producto actualizado: {codigo}")
        else:
            create_vals = ProductCreate(**product_data)
            odoo_service.create_product(create_vals)
            logging.info(f"Producto creado: {codigo}")
        
        productos_creados_o_actualizados.append(codigo)

    return productos_creados_o_actualizados
