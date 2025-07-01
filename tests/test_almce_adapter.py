import json
from pathlib import Path
from api.adapters.almce_adapter import ALMCEAdapter
from api.models.invoice_models import CoreInvoice

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "facturas_jsons" / "ALMCE"
SAMPLE_FILE = max(SAMPLE_DIR.glob("ocr_result_*.json"))  # latest file


def test_parse_almce_sample():
    adapter = ALMCEAdapter()
    ocr_json = json.loads(SAMPLE_FILE.read_text())
    core: CoreInvoice = adapter.parse(ocr_json)

    # Supplier
    assert core.supplier.name.upper().startswith("ALMCE")
    assert core.supplier.vat == "B-14891592"

    # Invoice meta
    assert core.invoice.number.isdigit()
    assert core.invoice.currency == "EUR"

    # Lines
    assert len(core.lines) > 0
    for line in core.lines:
        assert line.qty > 0
        assert line.price_unit > 0
        assert line.subtotal > 0

    # Totals
    assert core.totals.grand_total >= sum(l.subtotal for l in core.lines)
