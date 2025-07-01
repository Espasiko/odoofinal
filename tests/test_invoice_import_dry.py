import json
from pathlib import Path
from unittest.mock import patch
from api.services.invoice_import_service import invoice_import_service

SAMPLE_JSON_PATH = Path(__file__).resolve().parent.parent / "facturas_jsons" / "ALMCE" / "ocr_result_1.json"

# fallback if no sample path exists; create minimal json inline
def minimal_json():
    return {
        "data": {
            "full_text": "ALMCE S.L. | 01/05/25 | 25001234 | TOTAL IMP. | 121,00",
        }
    }

def test_import_invoice_dry():
    ocr_json = json.loads(SAMPLE_JSON_PATH.read_text()) if SAMPLE_JSON_PATH.exists() else minimal_json()

    from api.models.invoice_models import SupplierInfo, InvoiceMeta, InvoiceLine, Totals, CoreInvoice
    dummy_core = CoreInvoice(
            supplier=SupplierInfo(name="ALMCE S.L.", vat="B-14891592"),
            invoice=InvoiceMeta(number="123", date="2025-05-01", type="invoice"),
            totals=Totals(base=10, tax_rate=0, tax_amount=0, grand_total=10),
            lines=[InvoiceLine(code="ABC", description="Prod", qty=1, price_unit=10, subtotal=10)]
        )

    with patch("api.services.invoice_import_service.ALMCEAdapter.parse", return_value=dummy_core), \
         patch("api.services.odoo_provider_service.odoo_provider_service.create_provider", return_value=99) as p_sup, \
         patch("api.services.odoo_product_service.odoo_product_service.create_or_update_product", return_value=123) as p_prod, \
         patch("api.services.odoo_purchase_service.odoo_purchase_service.create_purchase_order", return_value=456) as p_po, \
         patch("api.services.odoo_purchase_service.odoo_purchase_service.create_invoice_from_po", return_value=789) as p_inv:

        result = invoice_import_service.import_invoice(ocr_json)

        assert result["supplier_id"] == 99
        assert result["created_products"] == [123]
        assert result["purchase_order_id"] == 456
        assert result["invoice_id"] == 789
        p_sup.assert_called_once()
        p_prod.assert_called_once()
        p_po.assert_called_once()
        p_inv.assert_called_once()
