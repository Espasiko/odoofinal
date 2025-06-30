"""Adapter para facturas/albaranes de ALMCE.
Convierte el JSON crudo devuelto por Mistral OCR en un objeto CoreInvoice.
Por ahora solo es un esqueleto con regex pendientes.
"""
from typing import Any, Dict
import re
from datetime import datetime
from ..models.invoice_models import CoreInvoice, SupplierInfo, InvoiceMeta, InvoiceLine, Totals

class ALMCEAdapter:
    CIF_PATTERN = re.compile(r"C\.I\.F\.:\s*(B-\d{8,})", re.I)
    DATE_PATTERN = re.compile(r"\|\s*(\d{2}/\d{2}/\d{2})\s*\|")
    NUMBER_PATTERN = re.compile(r"\|\s*(\d{8,})\s*\|")

    LINE_PATTERN = re.compile(
        r"\|\s*(?P<code>\d+)\s*\|\s*(?P<desc>.*?)\|\s*(?P<qty>-?\d+(?:,\d+)?)\s*\|\s*(?P<price>(?:-?[\d,.]+\s*)+?)\|\s*(?P<total>-?[\d,.]+)\s*\|",
        re.S
    )

    TOTAL_PATTERN = re.compile(r"TOTAL IMP\.[^|]+\|\s*([\d,.]+)")

    def parse(self, ocr_json: Dict[str, Any]) -> CoreInvoice:
        text = ocr_json["data"]["full_text"]

        # Supplier cif
        cif_match = self.CIF_PATTERN.search(text)
        vat = cif_match.group(1) if cif_match else None

        # Factura number & date (first table row)
        date_match = self.DATE_PATTERN.search(text)
        num_match = self.NUMBER_PATTERN.search(text)
        inv_date = datetime.strptime(date_match.group(1), "%d/%m/%y").date() if date_match else datetime.today().date()
        number = num_match.group(1) if num_match else "UNKNOWN"

        # Lines
        lines = []
        # --- Regex parse ---
        for m in self.LINE_PATTERN.finditer(text):
            raw_qty = m.group("qty")
            raw_price = m.group("price")
            raw_total = m.group("total")

            # Si el precio tiene números adicionales (p.e. "171.33 32.10") cogemos el primero
            price_token = raw_price.strip().split()[0]
            total_token = raw_total.strip().split()[0]

            try:
                qty = float(raw_qty.replace(",", "."))
            except ValueError:
                print(f"ALMCEAdapter WARN: qty parse error -> '{raw_qty}'")
                continue
            try:
                price_unit = float(price_token.replace(",", "."))
            except ValueError:
                print(f"ALMCEAdapter WARN: price parse error -> '{raw_price}'")
                continue
            try:
                subtotal = float(total_token.replace(",", "."))
            except ValueError:
                print(f"ALMCEAdapter WARN: total parse error -> '{raw_total}'")
                subtotal = qty * price_unit
            lines.append(InvoiceLine(
                code=m.group("code"),
                description=m.group("desc").strip(),
                qty=qty,
                price_unit=price_unit,
                subtotal=subtotal,
            ))

        # Totals (simple parse, mejorar para IVA/RE)
        total_match = self.TOTAL_PATTERN.search(text)
        grand_total = float(total_match.group(1).replace(",", ".")) if total_match else sum(l.subtotal for l in lines)
        totals = Totals(base=grand_total, tax_rate=0, tax_amount=0, grand_total=grand_total)

        # Si no se capturó ninguna línea con regex, hacer fallback simple
        if not lines:
            for line in text.splitlines():
                if '|' not in line:
                    continue
                cols = [c.strip() for c in line.split('|') if c.strip()]
                if len(cols) < 5:
                    continue
                code = cols[0]
                qty_str = cols[-3]
                price_str = cols[-2].split()[0]
                total_str = cols[-1]
                if not code.isdigit():
                    continue
                try:
                    qty = float(qty_str.replace(',', '.'))
                    price_unit = float(price_str.replace(',', '.'))
                    subtotal = float(total_str.replace(',', '.'))
                except ValueError:
                    continue
                lines.append(InvoiceLine(code=code, description=' '.join(cols[1:-3]), qty=qty, price_unit=price_unit, subtotal=subtotal))

        supplier = SupplierInfo(name="ALMCE S.L.", vat=vat)
        invoice_meta = InvoiceMeta(number=number, date=inv_date, type="invoice")
        return CoreInvoice(supplier=supplier, invoice=invoice_meta, totals=totals, lines=lines)
