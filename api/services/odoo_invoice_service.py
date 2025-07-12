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
        re_ids = self._execute_kw("account.tax", "search", [[["type_tax_use","=","purchase"],["amount","=",5.2]]], {"limit":1})
        self.RE_TAX_ID = re_ids[0] if re_ids else 0

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

    def _get_purchase_journal_id(self) -> int:
        """
        Obtiene el ID del diario de compras (purchase journal) de Odoo.
        Si no encuentra un diario de tipo 'purchase', intenta buscar cualquier diario.
        
        Returns:
            int: ID del diario de compras, o 1 si no se encuentra (para evitar errores)
        """
        try:
            # Primero intentar buscar diario de tipo compra
            logger.info("Buscando diario de compras...")
            journal_ids = self._execute_kw(
                "account.journal",
                "search",
                [["type", "=", "purchase"]],
                {"limit": 1}
            )
            
            if journal_ids:
                logger.info(f"Diario de compras encontrado con ID: {journal_ids[0]}")
                return journal_ids[0]
            
            # Si no hay diario de compras, buscar cualquier diario
            logger.warning("No se encontró diario de compras, buscando cualquier diario...")
            all_journal_ids = self._execute_kw(
                "account.journal",
                "search",
                [],
                {"limit": 1}
            )
            
            if all_journal_ids:
                logger.info(f"Usando diario alternativo con ID: {all_journal_ids[0]}")
                return all_journal_ids[0]
                
            # Si aún no hay diarios, devolver 1 como fallback (suele ser el diario por defecto)
            logger.error("No se encontró ningún diario en el sistema, usando ID 1 como fallback")
            return 1
            
        except Exception as e:
            logger.error(f"Error al obtener el diario de compras: {e}")
            # Devolver 1 como fallback para evitar error de campo obligatorio
            return 1
            
    def create_supplier_invoice(
        self,
        partner_id: int,
        invoice_number: str,
        invoice_date: str,
        lines: List[Dict[str, Any]],
        due_date: str = None,
        journal_id: int = None,
        move_type: str = "in_invoice",
        currency_id: int = 1,
        ref: str = None,
        narration: str = None
    ) -> Dict[str, Any]:
        """
        Crea factura de proveedor si no existe.
        
        Args:
            partner_id: ID del proveedor
            invoice_number: Número de factura
            invoice_date: Fecha de factura en formato ISO (YYYY-MM-DD)
            lines: Lista de líneas de factura
            due_date: Fecha de vencimiento en formato ISO (opcional)
            journal_id: ID del diario de compras (opcional)
            move_type: Tipo de movimiento (por defecto "in_invoice")
            currency_id: ID de la moneda (por defecto 1, EUR)
            ref: Referencia externa (opcional)
            narration: Notas adicionales (opcional)
            
        Returns:
            Dict con created, duplicate y id o error
        """
        existing_id = self.find_supplier_invoice(partner_id, invoice_number)
        if existing_id:
            return {"created": False, "duplicate": True, "id": existing_id, "success": True, "invoice_id": existing_id}

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
                "tax_ids": [(6, 0, [t for t in [self.INVOICE_TAX_ID, self.RE_TAX_ID] if t])],
            }))
            
        # Si no se proporciona journal_id, obtenerlo dinámicamente
        if not journal_id:
            journal_id = self._get_purchase_journal_id()
            
        # Construir valores para la factura
        vals = {
            "move_type": move_type,
            "partner_id": partner_id,
            "invoice_date": invoice_date,
            "ref": ref or invoice_number,
            "invoice_line_ids": invoice_line_ids,
            "journal_id": journal_id,
            "currency_id": currency_id
        }
        
        # Añadir campos opcionales si están presentes
        if due_date:
            vals["invoice_date_due"] = due_date
        if narration:
            vals["narration"] = narration
            
        try:
            invoice_id = self._execute_kw("account.move", "create", [[vals]])
            if invoice_id:
                return {"success": True, "created": True, "invoice_id": invoice_id}
            return {"success": False, "created": False, "error": "Odoo devolvió ID vacío"}
        except Exception as e:
            logger.error(f"Error creando factura: {e}")
            return {"success": False, "created": False, "error": str(e)}
