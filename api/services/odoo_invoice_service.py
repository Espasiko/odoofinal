from typing import List, Dict, Any, Optional
import logging
from .odoo_base_service import OdooBaseService

logger = logging.getLogger("odoo_invoice_service")

class OdooInvoiceService(OdooBaseService):
    """Servicio para creación y consulta de facturas de proveedor (account.move)"""

    def __init__(self):
        super().__init__()
        # Obtener impuesto compra 21 %
        tax_ids = self._execute_kw(
            "account.tax",
            "search",
            [[["type_tax_use", "=", "purchase"], ["amount", "=", 21]]],
            {"limit": 1}
        )
        self.INVOICE_TAX_ID = tax_ids[0] if tax_ids else 0

    def find_supplier_invoice(self, partner_id: int, ref: str) -> Optional[int]:
        """Devuelve el ID de la factura si existe ya."""
        domain = [
            ("partner_id", "=", partner_id),
            ("move_type", "=", "in_invoice"),
            ("ref", "=", ref)
        ]
        ids = self._execute_kw("account.move", "search", [domain], {"limit": 1})
        return ids[0] if ids else None

    def _ensure_product(self, default_code: str, name: str) -> int:
        """Busca product.product por default_code, si no existe crea stub y devuelve product_id"""
        product_domain = [("default_code", "=", default_code)]
        product_ids = self._execute_kw("product.product", "search", [product_domain], {"limit": 1})
        if product_ids:
            return product_ids[0]

        template_vals = {
            "name": name or default_code,
            "default_code": default_code,
            "type": "product",
        }
        template_id = self._execute_kw("product.template", "create", [[template_vals]])
        # product.product se crea automáticamente; buscarlo
        product_ids = self._execute_kw("product.product", "search", [[("product_tmpl_id", "=", template_id)]], {"limit": 1})
        return product_ids[0] if product_ids else 0

    def create_supplier_invoice(
        self,
        partner_id: int,
        invoice_number: str,
        invoice_date: str,
        lines: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Crea factura de proveedor si no existe. Devuelve dict con created, duplicate y id."""
        existing_id = self.find_supplier_invoice(partner_id, invoice_number)
        if existing_id:
            return {"created": False, "duplicate": True, "id": existing_id}

        # Preparar invoice_line_ids
        invoice_line_ids = []
        for l in lines:
            product_id = 0
            default_code = l.get("default_code")
            if default_code:
                product_id = self._ensure_product(default_code, l.get("name"))
            invoice_line_ids.append((0, 0, {
                "product_id": product_id or False,
                "name": l.get("name"),
                "quantity": l.get("quantity", 1.0),
                "price_unit": l.get("price_unit", 0.0),
                "tax_ids": [(6, 0, [self.INVOICE_TAX_ID])],
            }))
        vals = {
            "move_type": "in_invoice",
            "partner_id": partner_id,
            "invoice_date": invoice_date,
            "ref": invoice_number,
            "invoice_line_ids": invoice_line_ids,
        }
        try:
            invoice_id = self._execute_kw("account.move", "create", [[vals]])
            if invoice_id:
                return {"created": True, "id": invoice_id}
            return {"created": False, "error": "Odoo devolvió ID vacío"}
        except Exception as e:
            logger.error(f"Error creando factura: {e}")
            return {"created": False, "error": str(e)}
