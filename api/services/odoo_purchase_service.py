"""Servicio para operaciones de compra en Odoo (purchase.order y account.move)."""
from typing import List, Dict, Any
import datetime
from .odoo_base_service import OdooBaseService
import logging

class OdooPurchaseService(OdooBaseService):
    def __init__(self):
        super().__init__()
        self.last_error: str | None = None
    """Encapsula la creación de pedidos de compra y facturas de proveedor."""

    def _get_tax_21_purchase(self) -> int | None:
        """Devuelve el ID del impuesto de compra 21% (IVA) en Odoo."""
        try:
            if not self._models:
                self._get_connection()
            domain = [["type_tax_use", "=", "purchase"], ["amount", "=", 21]]
            tax_ids = self._execute_kw('account.tax', 'search', [domain], {'limit': 1})
            return tax_ids[0] if tax_ids else None
        except Exception as e:
            logging.error(f"Error obteniendo impuesto 21%: {e}")
            return None

    def _get_expense_account(self) -> int | None:
        """Devuelve una cuenta de gastos (600…) genérica."""
        try:
            if not self._models:
                self._get_connection()
            acc_ids = self._execute_kw('account.account', 'search', [[['code', '=like', '600%']]], {'limit': 1})
            return acc_ids[0] if acc_ids else None
        except Exception as e:
            logging.error(f"Error obteniendo cuenta de gastos: {e}")
            return None

    def _get_company_currency(self) -> int | None:
        """Devuelve la moneda principal de la compañía (usualmente EUR)."""
        try:
            if not self._models:
                self._get_connection()
            company_ids = self._execute_kw('res.company', 'search', [[['id', '>', 0]]], {'limit': 1})
            if not company_ids:
                return 1  # EUR por defecto
            currency_rec = self._execute_kw('res.company', 'read', [[company_ids[0]]], {'fields': ['currency_id']})[0]['currency_id']
            return 1
        except Exception as e:
            logging.error(f"Error obteniendo moneda de compañía: {e}")
            return None

    def _get_purchase_journal(self) -> int | None:
        """Devuelve el diario (journal) de compras por defecto."""
        try:
            if not self._models:
                self._get_connection()
            journal_ids = self._execute_kw('account.journal', 'search', [[['type', '=', 'purchase']]], {'limit': 1})
            return journal_ids[0] if journal_ids else None
        except Exception as e:
            logging.error(f"Error obteniendo diario de compras: {e}")
            return None

    def create_purchase_order(self, supplier_id: int, order_lines: List[Dict[str, Any]]) -> int | None:
        """Crea un borrador de purchase.order y devuelve su ID."""
        try:
            if not self._models:
                self._get_connection()

            tax_21 = self._get_tax_21_purchase()
            if tax_21:
                for line in order_lines:
                    line[2]['taxes_id'] = [(6, 0, [tax_21])]

            po_vals = {
                'partner_id': supplier_id,
                'order_line': order_lines,
                'state': 'draft',
            }
            po_id = self._execute_kw('purchase.order', 'create', [po_vals])
            logging.info(f"Purchase order creado ID={po_id}")
            return po_id
        except Exception as e:
            logging.error(f"Error creando purchase.order: {e}")
            return None

    def create_invoice_from_po(self, po_id: int) -> int | None:
        self.last_error = None
        """Crea factura de proveedor a partir del pedido mediante acción estándar."""
        try:
            if not self._models:
                self._get_connection()

            # Confirmar el pedido si sigue en borrador (necesario para facturar)
            self._execute_kw('purchase.order', 'button_confirm', [[po_id]])

            inv_ids = self._execute_kw('purchase.order', 'action_create_invoice', [[po_id]])
            if isinstance(inv_ids, list) and inv_ids:
                return inv_ids[0]

            # Fallback: crear factura manualmente
            po = self._execute_kw('purchase.order', 'read', [[po_id]], {'fields': ['partner_id', 'order_line']})[0]
            line_vals = []
            for line_tuple in po['order_line']:
                # order_line ids list
                line = self._execute_kw('purchase.order.line', 'read', [[line_tuple]], {'fields': ['product_id', 'name', 'price_unit', 'product_qty']})[0]
                line_vals.append((0, 0, {
                    'product_id': line['product_id'][0],
                    'name': line['name'],
                    'quantity': line['product_qty'],
                    'price_unit': line['price_unit'],
                    'tax_ids': [],
                    'account_id': (line.get('account_id') and line['account_id'][0]) or self._get_expense_account(),
                }))

            move_vals = {
                'move_type': 'in_invoice',
                'partner_id': po['partner_id'][0],
                'invoice_origin': f'PO{po_id}',
                'invoice_date': datetime.date.today().isoformat(),
                'currency_id': self._get_company_currency() or False,
                'invoice_line_ids': line_vals,
                'journal_id': self._get_purchase_journal() or False,
            }
            inv_id = self._execute_kw('account.move', 'create', [move_vals])
            try:
                # validar factura para que pase de borrador a publicada
                self._execute_kw('account.move', 'action_post', [[inv_id]])
            except Exception as e:
                logging.warning(f"No se pudo validar la factura {inv_id}: {e}")
            return inv_id
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"Error creando factura desde PO {po_id}: {e}")
            return None

# instancia singleton
odoo_purchase_service = OdooPurchaseService()
