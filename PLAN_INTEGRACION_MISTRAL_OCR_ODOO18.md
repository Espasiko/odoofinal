# 📋 PLAN DE INTEGRACIÓN MISTRAL OCR CON ODOO 18

## 🎯 Objetivo
Integrar los datos extraídos por Mistral OCR de facturas de proveedores directamente en Odoo 18 mediante FastAPI, respetando los campos obligatorios y la estructura de tablas necesaria para una integración completa.

## 📊 Análisis de Datos Extraídos por Mistral OCR

### Datos Disponibles del OCR (Ejemplo FA25000633.PDF)
```json
{
  "vendor_info": {
    "name": "ALMACENES CECOTEC S.L.",
    "address": "C/ ISAAC NEWTON, 4 PARQUE TECNOLÓGICO DE VALENCIA 46980 PATERNA (VALENCIA)",
    "tax_id": "B98683270",
    "phone": "96 321 81 00"
  },
  "customer_info": {
    "name": "MANUS ROTO S.L.",
    "address": "C/ ISAAC NEWTON, 4 PARQUE TECNOLÓGICO DE VALENCIA 46980 PATERNA (VALENCIA)",
    "tax_id": "B98683270"
  },
  "invoice_data": {
    "number": "FA25000633",
    "date": "25/11/2024",
    "due_date": "25/12/2024",
    "payment_terms": "30 días"
  },
  "line_items": [
    {
      "code": "01951",
      "description": "FRIGORÍFICO PUERTA FRANCESA BOLERO",
      "quantity": 1,
      "unit_price": 521.66,
      "total": 521.66
    }
  ],
  "totals": {
    "subtotal": 521.66,
    "tax_rate": 21,
    "tax_amount": 109.55,
    "total": 631.21
  }
}
```

## 🗄️ Estructura de Tablas en Odoo 18

### Tablas Principales para Facturas de Proveedor

#### 1. `account_move` (Facturas)
**Campos Obligatorios:**
- `move_type`: 'in_invoice' (factura de proveedor)
- `partner_id`: ID del proveedor
- `invoice_date`: Fecha de la factura
- `ref`: Número de factura del proveedor
- `company_id`: ID de la empresa
- `currency_id`: ID de la moneda
- `journal_id`: ID del diario contable

**Campos Opcionales Importantes:**
- `invoice_date_due`: Fecha de vencimiento
- `payment_reference`: Referencia de pago
- `narration`: Notas adicionales
- `amount_untaxed`: Base imponible
- `amount_tax`: Importe de impuestos
- `amount_total`: Total de la factura

#### 2. `account_move_line` (Líneas de Factura)
**Campos Obligatorios:**
- `move_id`: ID de la factura (account_move)
- `account_id`: ID de la cuenta contable
- `name`: Descripción de la línea
- `quantity`: Cantidad
- `price_unit`: Precio unitario

**Campos Opcionales Importantes:**
- `product_id`: ID del producto
- `tax_ids`: IDs de los impuestos aplicados
- `price_subtotal`: Subtotal sin impuestos
- `price_total`: Total con impuestos

#### 3. `res_partner` (Proveedores)
**Campos Obligatorios:**
- `name`: Nombre del proveedor
- `supplier_rank`: > 0 para proveedores

**Campos Opcionales Importantes:**
- `vat`: NIF/CIF
- `street`: Dirección
- `city`: Ciudad
- `zip`: Código postal
- `country_id`: ID del país
- `phone`: Teléfono
- `email`: Email

#### 4. `product_template` / `product_product` (Productos)
**Campos Obligatorios:**
- `name`: Nombre del producto
- `type`: Tipo de producto ('product', 'consu', 'service')

**Campos Opcionales Importantes:**
- `default_code`: Código interno
- `list_price`: Precio de venta
- `standard_price`: Precio de coste
- `categ_id`: ID de la categoría
- `purchase_ok`: Disponible para compra

## 🔧 Implementación del Plan

### Fase 1: Extensión del Servicio Mistral OCR

#### 1.1 Crear Endpoint de Integración con Odoo
```python
# api/routes/odoo_integration.py
from fastapi import APIRouter, HTTPException, UploadFile, File
from api.services.mistral_ocr_service import MistralOCRService
from api.services.odoo_integration_service import OdooIntegrationService

router = APIRouter(prefix="/api/v1/odoo", tags=["Odoo Integration"])

@router.post("/process-invoice")
async def process_invoice_to_odoo(
    file: UploadFile = File(...),
    auto_create_vendor: bool = True,
    auto_create_products: bool = True
):
    """Procesa una factura con OCR e integra directamente en Odoo"""
    # 1. Procesar con Mistral OCR
    ocr_result = await MistralOCRService.process_document(file)
    
    # 2. Integrar en Odoo
    odoo_result = await OdooIntegrationService.create_vendor_bill(
        ocr_data=ocr_result,
        auto_create_vendor=auto_create_vendor,
        auto_create_products=auto_create_products
    )
    
    return {
        "ocr_result": ocr_result,
        "odoo_integration": odoo_result
    }
```

#### 1.2 Crear Servicio de Integración con Odoo
```python
# api/services/odoo_integration_service.py
import xmlrpc.client
from typing import Dict, Any, Optional
from api.utils.config import Config

class OdooIntegrationService:
    def __init__(self):
        self.config = Config()
        self.url = self.config.ODOO_URL
        self.db = self.config.ODOO_DB
        self.username = self.config.ODOO_USERNAME
        self.password = self.config.ODOO_PASSWORD
        
        # Conexiones XML-RPC
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        
        # Autenticación
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
    
    async def create_vendor_bill(self, ocr_data: Dict, auto_create_vendor: bool = True, auto_create_products: bool = True) -> Dict[str, Any]:
        """Crea una factura de proveedor en Odoo basada en datos OCR"""
        try:
            # 1. Buscar o crear proveedor
            vendor_id = await self._get_or_create_vendor(ocr_data['vendor_info'], auto_create_vendor)
            
            # 2. Buscar o crear productos
            line_items = []
            for item in ocr_data['line_items']:
                product_id = await self._get_or_create_product(item, auto_create_products)
                line_items.append({
                    'product_id': product_id,
                    'name': item['description'],
                    'quantity': item['quantity'],
                    'price_unit': item['unit_price'],
                })
            
            # 3. Crear factura
            invoice_data = {
                'move_type': 'in_invoice',
                'partner_id': vendor_id,
                'invoice_date': self._parse_date(ocr_data['invoice_data']['date']),
                'invoice_date_due': self._parse_date(ocr_data['invoice_data']['due_date']),
                'ref': ocr_data['invoice_data']['number'],
                'invoice_line_ids': [(0, 0, line) for line in line_items]
            }
            
            invoice_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'create', [invoice_data]
            )
            
            return {
                'success': True,
                'invoice_id': invoice_id,
                'vendor_id': vendor_id,
                'message': f'Factura {ocr_data["invoice_data"]["number"]} creada exitosamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error al crear la factura en Odoo'
            }
    
    async def _get_or_create_vendor(self, vendor_info: Dict, auto_create: bool) -> int:
        """Busca un proveedor por NIF o lo crea si no existe"""
        # Buscar por NIF
        vendor_ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.partner', 'search',
            [['vat', '=', vendor_info['tax_id']]]
        )
        
        if vendor_ids:
            return vendor_ids[0]
        
        if not auto_create:
            raise Exception(f"Proveedor con NIF {vendor_info['tax_id']} no encontrado")
        
        # Crear nuevo proveedor
        vendor_data = {
            'name': vendor_info['name'],
            'vat': vendor_info['tax_id'],
            'street': vendor_info.get('address', ''),
            'phone': vendor_info.get('phone', ''),
            'supplier_rank': 1,
            'customer_rank': 0
        }
        
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.partner', 'create', [vendor_data]
        )
    
    async def _get_or_create_product(self, item_info: Dict, auto_create: bool) -> Optional[int]:
        """Busca un producto por código o lo crea si no existe"""
        if not item_info.get('code'):
            return None
        
        # Buscar por código interno
        product_ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'search',
            [['default_code', '=', item_info['code']]]
        )
        
        if product_ids:
            return product_ids[0]
        
        if not auto_create:
            return None
        
        # Crear nuevo producto
        product_data = {
            'name': item_info['description'],
            'default_code': item_info['code'],
            'type': 'product',
            'purchase_ok': True,
            'sale_ok': True,
            'standard_price': item_info['unit_price']
        }
        
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.template', 'create', [product_data]
        )
    
    def _parse_date(self, date_str: str) -> str:
        """Convierte fecha DD/MM/YYYY a YYYY-MM-DD"""
        from datetime import datetime
        try:
            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
            return date_obj.strftime('%Y-%m-%d')
        except:
            return date_str
```

### Fase 2: Configuración de Odoo

#### 2.1 Actualizar Configuración
```python
# api/utils/config.py - Añadir configuración de Odoo
class Config:
    # ... configuración existente ...
    
    # Configuración Odoo
    ODOO_URL: str = "http://localhost:8069"
    ODOO_DB: str = "manus-odoo-bd"
    ODOO_USERNAME: str = "yo@mail.com"
    ODOO_PASSWORD: str = "admin"
    
    # Configuración de integración
    AUTO_CREATE_VENDORS: bool = True
    AUTO_CREATE_PRODUCTS: bool = True
    DEFAULT_PRODUCT_CATEGORY: str = "All/Saleable"
    DEFAULT_JOURNAL_ID: int = 1  # Diario de compras
```

#### 2.2 Variables de Entorno
```bash
# .env - Añadir variables de Odoo
ODOO_URL=http://localhost:8069
ODOO_DB=manus-odoo-bd
ODOO_USERNAME=yo@mail.com
ODOO_PASSWORD=admin
AUTO_CREATE_VENDORS=true
AUTO_CREATE_PRODUCTS=true
```

### Fase 3: Interfaz Web Mejorada

#### 3.1 Actualizar Template HTML
```html
<!-- templates/mistral_ocr.html - Añadir sección de integración Odoo -->
<div class="integration-section">
    <h3>🔗 Integración con Odoo</h3>
    <div class="form-group">
        <label>
            <input type="checkbox" id="autoCreateVendor" checked>
            Crear proveedor automáticamente si no existe
        </label>
    </div>
    <div class="form-group">
        <label>
            <input type="checkbox" id="autoCreateProducts" checked>
            Crear productos automáticamente si no existen
        </label>
    </div>
    <button id="processToOdoo" class="btn btn-success" disabled>
        📊 Procesar e Integrar en Odoo
    </button>
</div>
```

### Fase 4: Testing y Validación

#### 4.1 Script de Prueba
```python
# test_odoo_integration.py
import requests
import json

def test_odoo_integration():
    """Prueba la integración completa OCR + Odoo"""
    
    # 1. Subir factura de prueba
    with open('ejemplos/ALMCE/FA25000633.PDF', 'rb') as f:
        files = {'file': f}
        data = {
            'auto_create_vendor': True,
            'auto_create_products': True
        }
        
        response = requests.post(
            'http://localhost:8002/api/v1/odoo/process-invoice',
            files=files,
            data=data
        )
    
    print("Resultado de la integración:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    return response.json()

if __name__ == "__main__":
    test_odoo_integration()
```

## 📋 Checklist de Implementación

### ✅ Completado
- [x] Mistral OCR completamente funcional
- [x] Extracción perfecta de datos de facturas
- [x] API endpoints básicos
- [x] Documentación y memoria

### 🔄 Por Implementar
- [ ] Servicio de integración con Odoo (`OdooIntegrationService`)
- [ ] Endpoint `/api/v1/odoo/process-invoice`
- [ ] Configuración de variables de entorno para Odoo
- [ ] Manejo de errores y validaciones
- [ ] Interfaz web mejorada con opciones de Odoo
- [ ] Scripts de testing de integración
- [ ] Documentación de la integración

### 🧪 Testing Requerido
- [ ] Conexión con Odoo 18
- [ ] Creación de proveedores
- [ ] Creación de productos
- [ ] Creación de facturas de proveedor
- [ ] Validación de datos obligatorios
- [ ] Manejo de errores de duplicados

## 🚀 Próximos Pasos

1. **Implementar `OdooIntegrationService`** - Servicio principal de integración
2. **Crear endpoint de integración** - API para procesar e integrar
3. **Configurar variables de entorno** - Credenciales de Odoo
4. **Testing exhaustivo** - Validar toda la cadena de integración
5. **Documentación completa** - Guías de uso y troubleshooting

## 💡 Consideraciones Importantes

- **Seguridad**: Las credenciales de Odoo deben estar en variables de entorno
- **Validación**: Verificar que todos los campos obligatorios estén presentes
- **Duplicados**: Implementar lógica para evitar duplicación de proveedores/productos
- **Errores**: Manejo robusto de errores de conexión y validación
- **Performance**: Optimizar consultas a Odoo para grandes volúmenes
- **Logging**: Registrar todas las operaciones para auditoría

---

**Estado**: ✅ Plan completo y listo para implementación
**Prioridad**: 🔥 Alta - Integración crítica para MVP
**Estimación**: 2-3 días de desarrollo + 1 día de testing