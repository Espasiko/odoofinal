"""Servicio orquestador: recibe JSON de Mistral OCR y lo integra en Odoo.
Solo es un esqueleto inicial para la fase piloto.
"""
from typing import Dict, Any
from ..adapters.almce_adapter import ALMCEAdapter
from ..models.invoice_models import CoreInvoice
from .odoo_provider_service import odoo_provider_service

class InvoiceImportService:
    def __init__(self):
        self.adapter_map = {
            "ALMCE": ALMCEAdapter(),
        }

    def detect_adapter(self, ocr_json: Dict[str, Any]):
        text = ocr_json["data"]["full_text"].upper()
        if "ALMCE" in text:
            return self.adapter_map["ALMCE"]
        raise ValueError("Proveedor no soportado por adapters todavía")

    def import_invoice(self, ocr_json: Dict[str, Any]):
        adapter = self.detect_adapter(ocr_json)
        core: CoreInvoice = adapter.parse(ocr_json)

        # 1. Proveedor
        supplier_id = odoo_provider_service.create_provider({
            "name": core.supplier.name,
            "vat": core.supplier.vat,
            "street": core.supplier.street,
            "city": core.supplier.city,
            "zip": core.supplier.zip,
            "active": True,
        })

        # 2. Productos
        from .odoo_product_service import odoo_product_service  # lazy import to avoid cycles
        product_ids = []
        order_lines_odoo = []
        for l in core.lines:
            product_vals = {
                "name": l.description[:60],
                "default_code": l.code,
                "type": "consu",
                "uom_id": 1,
                "uom_po_id": 1,
                "name": l.description[:60],
                "default_code": l.code,
                "list_price": l.price_unit,
                "standard_price": l.price_unit,
                "type": "consu",
                "purchase_ok": True,
                "sale_ok": False,
                #"categ_id": None,
            }
            prod_id = odoo_product_service.create_or_update_product(product_vals)
            if prod_id:
                product_ids.append(prod_id)
                order_lines_odoo.append((0, 0, {
                    'product_id': prod_id,
                    'name': l.description[:250],
                    'product_qty': l.qty,
                    'price_unit': l.price_unit,
                    'product_uom': 1,  # UoM base, mejorar más adelante
                }))

        # 3. Purchase Order y factura
        from .odoo_purchase_service import odoo_purchase_service
        po_id = odoo_purchase_service.create_purchase_order(supplier_id, order_lines_odoo) if order_lines_odoo else None
        invoice_id = odoo_purchase_service.create_invoice_from_po(po_id) if po_id else None

        return {
            "supplier_id": supplier_id,
            "invoice_number": core.invoice.number,
            "created_products": product_ids,
            "purchase_order_id": po_id,
            "invoice_id": invoice_id,
            "lines": len(core.lines)
        }

# Singleton para uso sencillo desde rutas u otros servicios
invoice_import_service = InvoiceImportService()
