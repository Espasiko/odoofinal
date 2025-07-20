# Plan de Mejora OCR y Excel - 17/07/2025

## Objetivo
Mejorar significativamente la precisión en la extracción de datos de facturas mediante OCR y Excel, con especial énfasis en la detección de recargos de equivalencia, descuentos y validación de totales.

## Análisis de la situación actual

### Flujo OCR
- ✅ Extracción inicial de datos
- ✅ Normalización básica de campos
- ❌ Validación cruzada de datos
- ❌ Auto-corrección basada en totales
- ❌ Configuración específica por proveedor

### Flujo Excel
- ✅ Carga de archivos Excel
- ✅ Procesamiento básico de datos
- ❌ Normalización avanzada
- ❌ Validación cruzada
- ❌ Configuración específica por proveedor

## Plan de implementación

### Fase 1: Mejoras inmediatas sin código (17/07/2025)
- Actualizar el prompt de OCR con:
  - Datos fijos del cliente El Pelotazo
  - Instrucciones específicas para detectar recargo de equivalencia
  - Ejemplos de formatos de facturas por proveedor

### Fase 2: Implementación mínima (18/07/2025)
1. **Expandir configuración de proveedores**
   - Modificar `price_utils.py` para incluir más información por proveedor
   - Añadir patrones específicos de descuentos, recargos y formatos de factura

2. **Añadir validación básica de totales**
   - Implementar en `mistral_free_ocr.py` validación de totales vs. líneas
   - Generar advertencias cuando los totales no coinciden

3. **Mejorar prompt dinámicamente**
   - Adaptar el prompt según el proveedor detectado
   - Incluir instrucciones específicas basadas en el proveedor

### Fase 3: Implementación completa (19-21/07/2025)
1. **Sistema de validación cruzada**
   - Crear `utils/validation_utils.py` con funciones de validación
   - Implementar validaciones para:
     - Totales vs. suma de líneas
     - Impuestos aplicados vs. configuración del proveedor
     - Descuentos detectados vs. patrones conocidos

2. **Auto-corrección basada en validación**
   - Implementar corrección automática de errores comunes
   - Ajustar campos cuando se detecten inconsistencias

3. **Aplicar mejoras al flujo Excel**
   - Crear `utils/excel_provider_config.py`
   - Adaptar validaciones para el formato Excel
   - Implementar normalización avanzada para Excel

4. **Diccionario dinámico de proveedores**
   - Crear base de datos de configuraciones por proveedor
   - Incluir patrones, multiplicadores y reglas específicas

### Fase 4: Mejoras avanzadas (opcional, 22-24/07/2025)
1. **Integración con Tabula para PDFs**
   - Añadir extracción de tablas estructuradas
   - Mejorar procesamiento de facturas en formato PDF

2. **Fuzzy matching para productos**
   - Implementar comparación aproximada de referencias
   - Mejorar vinculación con productos existentes

## Detalles de implementación

### 1. Expansión de PRICE_MULTIPLIERS a PROVIDER_CONFIG

```python
# En price_utils.py
PROVIDER_CONFIG = {
    "ABRILÁ": {
        "price_multiplier": 1.262,  # 21% IVA + 5.2% RE
        "aplica_recargo": True,
        "patron_descuento": r"\d+\s*%",
        "formato_factura": r"\d{4}/\d{4}",
        "prompt_addition": """
        Para facturas de ABRILÁ ILUMINACIÓN S.L.:
        - Busca la columna "R.E." junto a "IVA" (siempre aplica 5.2%)
        - Los descuentos aparecen como porcentajes en cada línea
        """
    },
    "FABRILAMP": {
        "price_multiplier": 1.262,
        "aplica_recargo": True,
        "patron_descuento": r"\d+\s*%",
        "formato_factura": r"\d{8}",
        "prompt_addition": """
        Para facturas de FABRILAMP:
        - Siempre aplica recargo de equivalencia (5.2%)
        - Los descuentos aparecen como "XX%" en columna separada
        """
    },
    # Más proveedores...
}

def get_provider_config(supplier_name: Optional[str]) -> Dict:
    """Obtiene la configuración específica del proveedor."""
    if not supplier_name:
        return {}
    
    supplier_upper = supplier_name.upper()
    for key, config in PROVIDER_CONFIG.items():
        if key in supplier_upper:
            return config
    
    return {}
```

### 2. Validación de totales

```python
# En utils/validation_utils.py
def validate_invoice_totals(extracted_data: Dict) -> Tuple[bool, Dict]:
    """Valida que los totales extraídos sean coherentes con los subtotales y los impuestos."""
    calculated_total = 0
    
    # Calcular el total basado en líneas
    for line in extracted_data.get("line_items", []):
        price = float(line.get("price_unit", 0))
        qty = float(line.get("quantity", 0))
        discount = float(line.get("discount", 0)) if line.get("discount") else 0
        
        # Aplicar descuento
        line_subtotal = price * qty * (1 - discount/100)
        
        # Aplicar impuestos
        tax_rate = 0
        recargo_rate = 0
        
        if line.get("tax_type") == "iva_21":
            tax_rate = 21
            recargo_rate = 5.2 if line.get("apply_recargo_equivalencia") else 0
        elif line.get("tax_type") == "iva_10":
            tax_rate = 10
            recargo_rate = 1.4 if line.get("apply_recargo_equivalencia") else 0
        elif line.get("tax_type") == "iva_4":
            tax_rate = 4
            recargo_rate = 0.5 if line.get("apply_recargo_equivalencia") else 0
            
        line_total = line_subtotal * (1 + (tax_rate + recargo_rate)/100)
        calculated_total += line_total
    
    # Comparar con el total extraído
    extracted_total = float(extracted_data.get("total_amount", 0))
    
    if abs(calculated_total - extracted_total) > 0.5:  # Tolerancia de 50 céntimos
        logger.warning(f"Posible error en la extracción: Total calculado ({calculated_total}) difiere del extraído ({extracted_total})")
        return False, {
            "calculated_total": calculated_total,
            "extracted_total": extracted_total,
            "difference": abs(calculated_total - extracted_total)
        }
    
    return True, {}
```

### 3. Mejora del prompt dinámico

```python
# En mistral_free_ocr.py
def generate_enhanced_prompt(ocr_text: str, supplier_name: Optional[str] = None) -> str:
    """Genera un prompt mejorado basado en el proveedor detectado."""
    base_prompt = """
    Analiza esta factura y extrae todos los datos relevantes en formato JSON estructurado.
    
    INFORMACIÓN IMPORTANTE:
    1. El cliente siempre es:
       - Nombre: El Pelotazo
       - CIF/NIF: B01234567
       - Dirección: Carretera Alicún, 123
       - Localidad: Almería
       - Provincia: Almería
       - Código Postal: 04001
    
    2. Presta especial atención a:
       - Recargo de Equivalencia: Busca explícitamente columnas con "R.E." o porcentajes como "5.2%" junto a columnas de IVA
       - Número de factura: Identifica el formato específico del proveedor
       - Descuentos: Busca símbolos "%" cerca de cifras
    """
    
    # Añadir instrucciones específicas del proveedor si se detecta
    if supplier_name:
        provider_config = get_provider_config(supplier_name)
        if provider_config and "prompt_addition" in provider_config:
            base_prompt += "\n\n" + provider_config["prompt_addition"]
    
    return base_prompt
```

### 4. Aplicación al flujo Excel

```python
# En utils/excel_provider_config.py
EXCEL_COLUMN_MAPPINGS = {
    "ABRILÁ": {
        "product_name": ["descripcion", "concepto", "producto"],
        "quantity": ["cantidad", "cant", "uds"],
        "price": ["precio", "importe", "p.u."],
        "discount": ["dto", "descuento", "desc"],
        "tax": ["iva", "impuesto"],
        "recargo": ["r.e.", "recargo", "rec"]
    },
    # Más proveedores...
}

def suggest_column_mapping(df, supplier_name=None):
    """Sugiere mapeo de columnas basado en el proveedor y contenido."""
    if not supplier_name:
        return default_column_mapping(df)
    
    supplier_upper = supplier_name.upper()
    for key, mapping in EXCEL_COLUMN_MAPPINGS.items():
        if key in supplier_upper:
            return apply_mapping(df, mapping)
    
    return default_column_mapping(df)
```

## Impacto esperado

| Fase | Mejora OCR | Mejora Excel | Esfuerzo |
|------|------------|--------------|----------|
| 1    | 20-30%     | 0%           | Mínimo   |
| 2    | 40-50%     | 20-30%       | Bajo     |
| 3    | 60-70%     | 50-60%       | Medio    |
| 4    | 70-80%     | 60-70%       | Alto     |

## Métricas de éxito
- Reducción de errores en detección de recargo de equivalencia
- Mejora en la precisión de descuentos detectados
- Reducción de intervención manual en facturas
- Mayor coincidencia entre totales extraídos y calculados

## Próximos pasos
1. Implementar Fase 1 inmediatamente
2. Evaluar resultados con facturas problemáticas conocidas
3. Continuar con Fase 2 y 3 según resultados
4. Documentar patrones específicos de cada proveedor

---

*Documento preparado por Cascade AI - 17/07/2025*
