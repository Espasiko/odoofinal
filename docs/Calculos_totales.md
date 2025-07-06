# Estrategia de Cálculo de Precios y Impuestos por Proveedor

> Última actualización: 04-07-2025 16:18 (CEST)

Este documento consolida las comprobaciones realizadas sobre:

* Hojas Excel de tarifas (`/ejemplos/proveedores_exl_csv/*`)
* JSONs generados por el OCR Mistral (`/facturas_jsons/<PROVEEDOR>/ocr_result_*.json`)
* Facturas creadas/verificadas en Odoo 18

El objetivo es definir, por proveedor, si los **precios de línea** procedentes del PDF/Excel incluyen impuestos y, en función de ello, cómo transformar `price_unit` antes de crear la factura en Odoo.

---

## Tabla resumen

| Proveedor | ¿Precio incluye impuestos? | Multiplicador a **dividir** | Impuestos incluidos | Ejemplo / Referencia |
|-----------|---------------------------|-----------------------------|---------------------|----------------------|
| **ALMCE** | Sí | 1,262 | 21 % IVA + 5,2 % RE | Hoja Excel `PVP ALMCE.xlsx` (col G = E×1,262)  \|  JSON `ocr_result_1751291763478.json` (total = base×1,262)|
| **NEVIR** | Sí | 1,262 | 21 % IVA + 5,2 % RE | JSON `ocr_result_1751292415935.json` |
| **WORTEN** | Sí | 1,21 | 21 % IVA | JSON `ocr_result_1751292672259.json` |
| **MI ELECTRO** | Sí | 1,21 | 21 % IVA | JSON `ocr_result_1751292468008.json` |
| **JYSK** | Sí | 1,21 | 21 % IVA | JSON `ocr_result_1751292554040.json` (Base 66,81; Total 80,84)|
| **BSH** | No | – | – | JSON `ocr_result_1751293092851.json` (base = total)|
| **CECOTEC** | No | – | – | JSON `ocr_result_1751293425853.json` |
| **ORBEGOZO** | No | – | – | JSON `ocr_result_1751293245072.json` |
| **EAS & JOHNSON** | No | – | – | JSON `ocr_result_1751293202967.json` |
| **ALFADYSER** | No | – | – | JSON `ocr_result_1751292844562.json` |
| **JATA** | No | – | – | JSON `ocr_result_1751292295056.json` (TOTAL BRUTO = BASE)|

> **Regla:** Si `price_includes_taxes = true` dividir el precio capturado por el multiplicador antes de enviarlo a Odoo.

---

## Método de verificación

1. **Excel / Tarifas**  
   • Analizamos columnas:  
   `E = IMPORTE BRUTO` (coste neto)  
   `G = IVA 21 % + RE 5,2 %`  
   `H = PRECIO CON MARGEN`…  
   Comprobamos que `G ≈ E × 1,262`.

2. **JSON OCR de facturas**  
   • Leemos tablas finales: BASE, IVA, REC., TOTAL.  
   • Calculamos ratio `TOTAL / BASE`.  
     – Si ~1,262 → incluye IVA+RE.  
     – Si ~1,21 → incluye solo IVA.  
     – Si ~1 → ya es neto.

3. **Ejemplos clave**

### ALMCE
* Excel fila 5:  
  `IMPORTE BRUTO 198,92 €`  → `G 251,04 €`  (×1,262)
* JSON (abono 25007710):  
  BASE -116,33 € → TOTAL ‑146,81 € (×1,262)

### JYSK
* JSON 601469863:  
  BASE 66,81 € → IVA 14,03 €; TOTAL 80,84 € (×1,21)

### JATA
* JSON FV25 4540:  
  TOTAL BRUTO = BASE IMPONIBLE = 1.343,43 €  
  IVA listado aparte (282,12 €)  
  → precios línea ya netos.

---

## Implementación en FastAPI

```python
from decimal import Decimal, ROUND_HALF_UP

MULTIPLIERS = {
    "ALMCE": Decimal("1.262"),
    "NEVIR": Decimal("1.262"),
    "WORTEN": Decimal("1.21"),
    "MI ELECTRO": Decimal("1.21"),
    "JYSK": Decimal("1.21"),
}

def get_net_price(provider: str, captured_price: Decimal) -> Decimal:
    mult = MULTIPLIERS.get(provider.upper())
    if mult:
        return (captured_price / mult).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return captured_price  # ya es neto
```

*Para proveedores no mapeados se aplica heurística automática (`total / base`).*

---

## Próximos pasos

1. Añadir flag `price_includes_taxes` y multiplicador en tabla `suppliers` de la BD.  
2. Ajustar endpoint OCR invoice para aplicar `get_net_price`.  
3. Validar importando nuevas facturas y comparando totales Odoo vs PDF.

---

> Documento generado automáticamente por Cascade AI para asegurar trazabilidad de los cálculos de precios e impuestos en la integración Odoo-FastAPI.
