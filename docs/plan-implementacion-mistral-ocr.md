# Plan de Implementación: Mistral OCR en Odoo

## 1. Información General de Mistral OCR

### 1.1 Características Principales
- **Alta precisión**: 98% de calidad en datos leídos según benchmarks internos
- **Comprensión avanzada**: Reconoce tablas, imágenes, fórmulas matemáticas y layouts complejos
- **Precio competitivo**: 1000 páginas por $1 USD
- **API REST**: Disponible en `https://api.mistral.ai/v1/ocr`

### 1.2 Casos de Uso para El Pelotazo
- Procesamiento automático de facturas de proveedores
- Digitalización de documentos contables
- Extracción de datos de albaranes y pedidos
- Automatización de entrada de datos en el sistema contable

## 2. Análisis del Módulo Existente: pelotazo_extended

### 2.1 Ubicación
```
/home/espasiko/mainmanusodoo/manusodoo-roto/addons/pelotazo_extended/
```

### 2.2 Evaluación de Expansión
**Ventajas de expandir el módulo existente**:
- ✅ Infraestructura ya establecida
- ✅ Integración con funcionalidades actuales
- ✅ Mantenimiento centralizado
- ✅ Configuración unificada

**Recomendación**: Expandir `pelotazo_extended` con funcionalidades OCR

## 3. Fases de Implementación

### Fase 1: Preparación y Configuración (Semana 1)

#### 3.1 Configuración de Cuenta Mistral
- [ ] Crear cuenta en La Plateforme (https://console.mistral.ai/)
- [ ] Obtener API Key desde el dashboard
- [ ] Configurar límites y facturación
- [ ] Documentar credenciales de forma segura

#### 3.2 Instalación de Dependencias
- [ ] Instalar librerías Python necesarias:
  ```bash
  pip install requests
  pip install python-magic
  pip install pillow
  ```
- [ ] Actualizar requirements.txt del proyecto

#### 3.3 Configuración en Odoo
- [ ] Añadir campos de configuración en `res.config.settings`:
  - `mistral_api_key`
  - `mistral_ocr_enabled`
  - `mistral_auto_process`

### Fase 2: Desarrollo del Módulo OCR (Semana 2-3)

#### 3.4 Estructura del Módulo Expandido
```
pelotazo_extended/
├── models/
│   ├── __init__.py
│   ├── res_config_settings.py (expandir)
│   ├── account_move.py (expandir)
│   ├── mistral_ocr.py (nuevo)
│   └── document_processor.py (nuevo)
├── views/
│   ├── res_config_settings_views.xml (expandir)
│   ├── account_move_views.xml (expandir)
│   └── mistral_ocr_views.xml (nuevo)
├── wizards/
│   └── process_document_wizard.py (nuevo)
├── static/
│   └── src/
│       └── js/
│           └── document_upload.js (nuevo)
└── data/
    └── ir_cron_data.xml (nuevo)
```

#### 3.5 Modelos a Desarrollar

**3.5.1 mistral_ocr.py**
```python
class MistralOCR(models.Model):
    _name = 'mistral.ocr'
    _description = 'Mistral OCR Integration'
    
    # Campos principales
    name = fields.Char('Nombre')
    document_type = fields.Selection([...])  # factura, albarán, etc.
    original_file = fields.Binary('Archivo Original')
    processed_data = fields.Text('Datos Procesados')
    confidence_score = fields.Float('Puntuación de Confianza')
    status = fields.Selection([...])  # pendiente, procesado, error
```

**3.5.2 document_processor.py**
```python
class DocumentProcessor(models.Model):
    _name = 'document.processor'
    _description = 'Procesador de Documentos'
    
    def process_with_mistral_ocr(self, file_data):
        # Lógica de integración con Mistral OCR API
        pass
    
    def extract_invoice_data(self, ocr_result):
        # Extracción específica para facturas
        pass
```

#### 3.6 Integración con account.move
```python
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    ocr_processed = fields.Boolean('Procesado con OCR')
    ocr_confidence = fields.Float('Confianza OCR')
    original_document = fields.Binary('Documento Original')
    
    def process_document_ocr(self):
        # Procesar documento con Mistral OCR
        pass
```

### Fase 3: Funcionalidades Específicas (Semana 4)

#### 3.7 Procesamiento Automático de Facturas
- [ ] Detección automática de campos:
  - Número de factura
  - Fecha de emisión
  - Proveedor
  - Importe total
  - Líneas de factura
  - IVA

#### 3.8 Wizard de Procesamiento
- [ ] Interfaz para subir documentos
- [ ] Vista previa del resultado OCR
- [ ] Corrección manual de datos
- [ ] Creación automática de facturas

#### 3.9 Automatización con Cron Jobs
- [ ] Procesamiento automático de documentos en carpeta específica
- [ ] Notificaciones de procesamiento
- [ ] Logs de errores y éxitos

### Fase 4: Integración y Testing (Semana 5)

#### 3.10 Integración con Flujo Contable
- [ ] Creación automática de asientos contables
- [ ] Validación de datos extraídos
- [ ] Reconciliación automática
- [ ] Reportes de procesamiento

#### 3.11 Testing y Validación
- [ ] Pruebas con diferentes tipos de documentos
- [ ] Validación de precisión de datos
- [ ] Pruebas de rendimiento
- [ ] Testing de integración

## 4. Configuración Técnica

### 4.1 API Integration
```python
import requests

class MistralOCRAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1/ocr"
    
    def process_document(self, file_data, document_type="invoice"):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Implementar llamada a la API
        response = requests.post(
            self.base_url,
            headers=headers,
            files={"file": file_data}
        )
        
        return response.json()
```

### 4.2 Seguridad
- [ ] Almacenamiento seguro de API Keys
- [ ] Validación de tipos de archivo
- [ ] Límites de tamaño de archivo
- [ ] Logs de auditoría

## 5. Comandos Disponibles del MCP Odoo Actual

### 5.1 Herramienta Principal: execute_method

**Parámetros**:
- `model` (string): Modelo de Odoo (ej: 'account.move', 'res.partner')
- `method` (string): Método del ORM
- `args` (array): Argumentos posicionales
- `kwargs` (object): Argumentos con nombre

### 5.2 Métodos ORM Soportados

#### Consulta de Datos
- `search`: Buscar registros
- `read`: Leer campos específicos
- `search_read`: Buscar y leer en una operación
- `search_count`: Contar registros

#### Modificación de Datos
- `create`: Crear nuevos registros
- `write`: Actualizar registros existentes
- `unlink`: Eliminar registros

#### Métodos Específicos
- `name_get`: Obtener representación de nombre
- `name_search`: Buscar por nombre
- `fields_get`: Obtener definición de campos
- `default_get`: Obtener valores por defecto

### 5.3 Ejemplos de Comandos Útiles para El Pelotazo

#### Gestión de Facturas
```json
// Buscar facturas pendientes
{
  "model": "account.move",
  "method": "search_read",
  "args": [["state", "=", "draft"]],
  "kwargs": {"fields": ["name", "partner_id", "amount_total"]}
}

// Crear nueva factura
{
  "model": "account.move",
  "method": "create",
  "args": [{
    "move_type": "in_invoice",
    "partner_id": 1,
    "invoice_date": "2024-01-15"
  }]
}
```

#### Gestión de Productos
```json
// Buscar productos por categoría
{
  "model": "product.template",
  "method": "search_read",
  "args": [["categ_id", "=", 1]],
  "kwargs": {"fields": ["name", "list_price", "qty_available"]}
}

// Actualizar precio de producto
{
  "model": "product.template",
  "method": "write",
  "args": [[1], {"list_price": 25.50}]
}
```

#### Gestión de Clientes/Proveedores
```json
// Buscar proveedores
{
  "model": "res.partner",
  "method": "search_read",
  "args": [["is_company", "=", true], ["supplier_rank", ">", 0]],
  "kwargs": {"fields": ["name", "email", "phone"]}
}
```

## 6. Próximos Pasos Inmediatos

1. **Reiniciar Trae IDE** para reconocer el servidor MCP de Odoo
2. **Evaluar el módulo pelotazo_extended** actual
3. **Crear cuenta en Mistral AI** y obtener API Key
4. **Comenzar Fase 1** del plan de implementación
5. **Configurar entorno de desarrollo** para OCR

## 7. Consideraciones Adicionales

### 7.1 Otros Servidores MCP Recomendados

**Para ampliar capacidades**:
- **MCP-Odoo (yourtechtribe)**: Funcionalidades adicionales de integración
- **LLM MCP Module (Odoo Apps)**: Integración con modelos de lenguaje

### 7.2 Métricas de Éxito
- Reducción del 80% en tiempo de entrada de facturas
- Precisión del 95% en extracción de datos
- Procesamiento automático de al menos 100 documentos/mes
- ROI positivo en 3 meses

---

**Fecha de creación**: $(date)
**Estado**: Plan Pendiente de Implementación
**Prioridad**: Alta
**Responsable**: Equipo de Desarrollo