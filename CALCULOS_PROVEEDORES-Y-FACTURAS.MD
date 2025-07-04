# Análisis y Plan de Implementación de Cálculos para Proveedores y Facturas

## 1. Análisis de Formato y Estructura de Precios en Proveedores

Basado en el análisis de los archivos Excel y las facturas, hemos identificado diferentes formas en que los proveedores manejan los descuentos, IVA y precios finales:

### Estructura por Proveedor

#### 1. ALMCE

**Formato en Excel:**
- Columna "IMPORTE BRUTO": Precio base del producto
- Columna "DTO": Igual al importe bruto (no parece aplicar descuento adicional)
- Columna "IVA 21% + RECARGO 5,2%": Muestra el precio con IVA+recargo ya aplicado (26.2%)
- Columna "PRECIO CON MARGEN": Aplican margen de 20-25% sobre precio con IVA
- Columnas "P.V.P WEB" y "P.V.P FINAL CLIENTE": Precios finales de venta

**En Factura:**
- Base: Precio neto sin IVA ni recargo
- IVA: 21% aplicado sobre base
- REC (Recargo): 5.20% adicional sobre base

Ejemplo en factura: Base -116.33€ → IVA -24.43€ → Recargo -6.05€ → Total -146.81€

#### 2. BSH (Bosch-Siemens-Hausgeräte)

**Formato en Excel:**
- "IMPORTE BRUTO": Precio base original
- "DTO. IMPLANTACION": Descuento específico para implantación (muy importante)
- "TOTAL": Precio bruto menos descuento
- "IVA 21% + RECARGO 5,2%": Precio con IVA y recargo ya aplicado
- "MARGEN": Precio con margen comercial

**En Factura:**
- Muestra "Precio" (inicial), "Reducción", "Dto. F. Discount", "Dto. Total"
- Calcula "Neto Unitario" después de todos los descuentos
- Aplica IVA 21% y Recargo de Equivalencia 5.2% sobre el neto

Ejemplo: Batidora Varilla → Precio 33€ → Dto. Total 1.74€ → Neto 32.43€ × 2 unidades = 64.85€

#### 3. CECOTEC

**Formato en Excel:**
- "IMPORTE BRUTO": Precio base sin descuentos
- "DTO": Columna presente pero sin valores (no aplican descuento fijo)
- "TOTAL": Mismo valor que importe bruto
- "IVA 21% + RECARGO 5,2%": Aplicado sobre precio base
- "MARGEN": Calcula el precio con margen aplicado

**En Factura:**
- Muestra "Precio Ud." sin descuentos directos
- "Total BI" (Base Imponible)
- IVA separado (21%)
- "Rec. Financ." (Recargo) calculado separadamente (5.2%)

Ejemplo: Swiss Negro → 9.98€ base → 2.10€ IVA → 0.52€ Recargo → 12.60€ Total

#### 4. BECKEN-TEGALUXE

**Formato en Excel:**
- Similar a otros proveedores
- No muestra descuentos aplicados directamente en la tabla principal
- Incluye columna de "MARGEN" para calcular precio final

#### 5. ELECTRODIRECTO

**Formato en Excel único:**
- Separa explícitamente "RECARGO 5,20%" e "IVA 21%" en columnas diferentes
- "TOTAL" es la suma del importe bruto + recargo + IVA
- "MARGEN 30%" aplica un margen fijo del 30% al total

Ejemplo: A/A BEKO → 205.00€ base → 10.66€ recargo → 248.05€ IVA → 258.71€ total → 336.32€ con margen

### Resumen de Diferencias Principales

1. **Aplicación de Descuentos:**
   - BSH: Aplica descuentos específicos por implantación, muy significativos (30-135€)
   - ALMCE: No muestra descuentos directos en la tabla analizada
   - CECOTEC: No muestra descuentos en tabla pero podría aplicarlos en negociaciones
   - ELECTRODIRECTO: No muestra descuentos en la tabla

2. **Tratamiento del IVA y Recargo:**
   - ALMCE y BSH: Combinan IVA+Recargo en una columna (26.2% total)
   - ELECTRODIRECTO: Separa IVA y Recargo en columnas diferentes
   - CECOTEC: Combina ambos en cálculo final

3. **Cálculo de Márgenes:**
   - ALMCE: Margen 20-25% sobre precio con IVA+recargo
   - BSH: Margen variable según producto
   - ELECTRODIRECTO: Margen fijo del 30%
   - CECOTEC y BECKEN: Margen variable sin porcentaje explícito

4. **Coincidencia con Facturas:**
   - BSH: Las facturas coinciden con la estructura del Excel, mostrando precio original, descuentos y precio neto final
   - ALMCE: La factura muestra un abono (devolución) con la misma estructura de cálculo que el Excel
   - CECOTEC: La factura muestra un abono con estructura similar a Excel, pero simplificada

## 2. Análisis de la Implementación Existente

### Endpoints Actuales

#### Proveedores:
- `GET /api/v1/providers`: Lista paginada de proveedores
- `GET /api/v1/providers/all`: Lista todos los proveedores
- `GET /api/v1/providers/{provider_id}`: Obtiene proveedor específico
- `POST /api/v1/providers`: Crea nuevo proveedor
- `PUT /api/v1/providers/{provider_id}`: Actualiza proveedor existente
- `DELETE /api/v1/providers/{provider_id}`: Elimina proveedor

#### Productos:
- `GET /api/v1/products`: Lista paginada de productos con filtros
- `GET /api/v1/products/{product_id}`: Obtiene producto específico
- `POST /api/v1/products`: Crea nuevo producto
- `PUT /api/v1/products/{product_id}`: Actualiza producto
- `DELETE /api/v1/products/{product_id}`: Archiva producto (marca como inactivo)

#### OCR/Facturas:
- `POST /api/v1/mistral-ocr/process-document`: Procesa documento con OCR
- `POST /api/v1/mistral-ocr/process-invoice`: Procesa factura con OCR

### Modelos Existentes

#### Producto:
```python
class ProductBase(BaseModel):
    name: Optional[str] = None
    default_code: Optional[str] = None
    list_price: Optional[float] = None  # Precio de venta
    standard_price: Optional[float] = None  # Coste
    categ_id: Optional[int] = None
    # ... otros campos ...
```

#### Proveedor:
```python
class Provider(BaseModel):
    id: int
    name: str
    email: Optional[Union[str, bool, None]] = None
    # ... otros campos ...
    # No tiene campos específicos para precios y descuentos
```

## 3. Plan de Implementación

### Fase 1: Extensión de Modelos

1. **Ampliar el modelo de Proveedor:**

```python
class ProviderPricingInfo(BaseModel):
    discount_type: Optional[str] = None  # 'fixed', 'percentage', 'none'
    discount_value: Optional[float] = 0.0  # Valor del descuento
    include_vat_in_margin: bool = False  # Si el margen se calcula sobre precio+IVA
    default_margin: Optional[float] = 25.0  # Margen por defecto (%)
    separate_surcharge: bool = False  # Si separar recargo e IVA
    vat_rate: Optional[float] = 21.0  # % IVA
    surcharge_rate: Optional[float] = 5.2  # % Recargo
    price_calculation_method: str = 'standard'  # 'standard', 'almce', 'bsh', 'electrodirecto'
```

2. **Ampliar el modelo de Producto:**

```python
class ProductPricing(BaseModel):
    base_price: Optional[float] = None  # Precio base (IMPORTE BRUTO)
    discount_amount: Optional[float] = None  # Descuento aplicado
    net_price: Optional[float] = None  # Precio neto (después de descuento)
    vat_amount: Optional[float] = None  # Importe del IVA
    surcharge_amount: Optional[float] = None  # Importe del recargo
    margin_amount: Optional[float] = None  # Importe del margen
    pvp_suggested: Optional[float] = None  # PVP sugerido
    pvp_final: Optional[float] = None  # PVP final
    provider_id: Optional[int] = None  # Proveedor asociado
    provider_name: Optional[str] = None  # Nombre del proveedor
    last_purchase_date: Optional[datetime] = None  # Fecha última compra
    discount_end_date: Optional[datetime] = None  # Fecha fin promoción
```

### Fase 2: Endpoints Nuevos

1. **Endpoint para configurar cálculos por proveedor:**

```python
@router.put("/providers/{provider_id}/pricing", response_model=ProviderPricingInfo)
async def set_provider_pricing(
    provider_id: int,
    pricing_info: ProviderPricingInfo,
    current_user: User = Depends(get_current_active_user)
)
```

2. **Endpoint para calcular precios finales:**

```python
@router.post("/products/calculate-pricing", response_model=ProductPricing)
async def calculate_product_pricing(
    product_data: Dict[str, Any],
    provider_id: int,
    current_user: User = Depends(get_current_active_user)
)
```

3. **Endpoint para actualizar precios desde facturas OCR:**

```python
@router.post("/products/update-from-invoice", response_model=List[ProductPricing])
async def update_prices_from_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_active_user)
)
```

### Fase 3: Implementación de Front-End

1. **Componente de Configuración de Proveedor:**
   - Formulario para configurar cálculos específicos del proveedor
   - Selección del método de cálculo
   - Configuración de márgenes y descuentos predeterminados

2. **Componente de Tabla de Productos con Cálculos:**
   - Columnas para mostrar todos los componentes del precio
   - Celdas editables para precios base, descuentos y márgenes
   - Cálculo automático de PVP basado en configuración

3. **Integración con OCR:**
   - Importación directa de precios desde facturas escaneadas
   - Mapeo automático de productos por código o nombre
   - Actualización masiva de precios

### Fase 4: Algoritmos de Cálculo

1. **Implementar diferentes estrategias de cálculo:**

```python
def calculate_pricing(base_price, provider_config, quantity=1):
    # Paso 1: Aplicar descuento
    if provider_config.discount_type == 'fixed':
        net_price = base_price - provider_config.discount_value
    elif provider_config.discount_type == 'percentage':
        net_price = base_price * (1 - provider_config.discount_value / 100)
    else:
        net_price = base_price
        
    # Paso 2: Calcular IVA y recargo
    vat_amount = net_price * (provider_config.vat_rate / 100)
    surcharge_amount = net_price * (provider_config.surcharge_rate / 100)
    
    # Paso 3: Calcular precio con impuestos
    price_with_taxes = net_price + vat_amount + surcharge_amount
    
    # Paso 4: Aplicar margen
    if provider_config.include_vat_in_margin:
        margin_base = price_with_taxes
    else:
        margin_base = net_price
        
    margin_amount = margin_base * (provider_config.default_margin / 100)
    pvp_suggested = margin_base + margin_amount
    
    return {
        'base_price': base_price,
        'net_price': net_price,
        'vat_amount': vat_amount,
        'surcharge_amount': surcharge_amount,
        'price_with_taxes': price_with_taxes,
        'margin_amount': margin_amount,
        'pvp_suggested': pvp_suggested,
        'pvp_final': pvp_suggested  # Inicialmente igual al sugerido
    }
```

### Fase 5: Testing y Validación

1. **Crear casos de prueba para cada proveedor:**
   - Probar con datos reales de facturas
   - Verificar que los cálculos coinciden con los excels
   - Validar descuentos, IVA, recargo y márgenes

2. **Pruebas de integración:**
   - Comprobar que el flujo completo funciona correctamente
   - Validar la importación desde OCR
   - Comprobar actualizaciones desde la UI

## 4. Cronograma de Implementación

1. **Semana 1:** Extensión de modelos y backend
2. **Semana 2:** Implementación de endpoints y lógica de cálculo
3. **Semana 3:** Desarrollo de componentes de UI
4. **Semana 4:** Integración con OCR y pruebas
5. **Semana 5:** Ajustes finales, documentación y despliegue

## 5. Consideraciones Finales

- Será necesario mantener compatibilidad con los formatos actuales de proveedores
- El sistema debe ser flexible para acomodar nuevos proveedores con formatos diferentes
- Es fundamental que los cálculos sean precisos para evitar errores en precios finales
- La integración con Odoo debe respetar las reglas fiscales y de contabilidad
- Se recomienda implementar un sistema de verificación manual antes de aplicar cambios masivos
