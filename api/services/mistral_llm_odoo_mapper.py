from typing import List, Dict, Any, Optional
from api.services.odoo_service import odoo_service
from api.models.schemas import ProductCreate, ProviderCreate
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

    productos_creados = []
    for prod in productos:
        # Buscar categoría, si no existe se crea (puedes mejorar esto según tu lógica)
        categoria_nombre = prod.get("categoria") or "Sin categoría"
        # Aquí deberías tener un helper para buscar/crear categoría, por simplicidad la dejamos como string

        # Buscar producto por código
        codigo = prod.get("codigo") or prod.get("default_code")
        if not codigo:
            logging.warning(f"Producto sin código: {prod}")
            continue
        producto_existente = odoo_service.product_service.find_product_by_code(codigo)
        vals = ProductCreate(
            name=prod.get("nombre") or prod.get("descripcion") or "Producto sin nombre",
            default_code=codigo,
            list_price=prod.get("pvp_final_cliente") or prod.get("pvp_web") or prod.get("importe_bruto") or 0.0,
            categ_id=None,  # Aquí puedes mapear a ID real si tienes el helper
            active=True,
            seller_ids=[proveedor_id] if proveedor_id else [],
            description_sale=prod.get("descripcion"),
            # ...otros campos según tu modelo
        )
        if producto_existente:
            odoo_service.product_service.update_product(producto_existente.id, vals.dict(exclude_unset=True))
            logging.info(f"Producto actualizado: {codigo}")
        else:
            odoo_service.product_service.create_product(vals)
            logging.info(f"Producto creado: {codigo}")
        productos_creados.append(codigo)
    return productos_creados
