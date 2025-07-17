# Plan de Implementación: Consolidación de Importación Excel-OCR-Odoo (17/07/2025)

## 1. Objetivos del Plan

Implementar un sistema unificado y robusto para:

1. **Limpiar y normalizar Excels desestructurados** de proveedores (NEVIR, ABRILA, MIELECTRO, etc.)
2. **Procesar facturas mediante OCR** con Mistral AI y extraer datos estructurados
3. **Consolidar datos** de múltiples fuentes (Excel, OCR, códigos de barras)
4. **Permitir revisión y corrección visual** antes de guardar en Odoo
5. **Implementar validación cruzada** y logging para mejorar la precisión con el tiempo

## 2. Componentes Existentes a Aprovechar

### Frontend (React)
- `ImportExcelChunk.tsx`: Importación por lotes con feedback visual
- `ImportInvoice.tsx`: Procesamiento OCR de facturas
- `OdooContext.tsx`: Gestión de autenticación y tokens
- Hooks personalizados para productos, proveedores y clientes

### Backend (FastAPI)
- `excel_importer.py`: Endpoints para importación de Excel
- `mistral_free_ocr.py`: Procesamiento OCR con Mistral
- `ocr_validator.py`: Validación de datos extraídos
- `ocr_cache_service.py`: Caché para resultados OCR
- `provider_prompts.py`: Prompts específicos por proveedor
- `product_transform.py`: Transformación de datos para Odoo

## 3. Plan de Implementación Detallado

### Fase 1: Preprocesador Unificado de Excels (2 días)

#### 1.1 Backend: Servicio de Normalización de Excel
```python
# Nuevo archivo: api/services/excel_normalizer_service.py

class ExcelNormalizerService:
    def detect_headers(self, df):
        """Detecta automáticamente la fila de cabecera buscando palabras clave"""
        # Implementar lógica para buscar palabras como "nombre", "código", "precio"
        
    def clean_empty_cells(self, df):
        """Elimina filas y columnas vacías"""
        # Implementar limpieza de datos
        
    def extract_embedded_fields(self, df):
        """Extrae campos incrustados en texto usando regex"""
        # Implementar extracción de NIF, teléfono, etc. de celdas de texto
        
    def normalize_monetary_values(self, df):
        """Normaliza valores monetarios (quita símbolos, convierte a float)"""
        # Implementar normalización
        
    def normalize_dates(self, df):
        """Convierte fechas a formato ISO (YYYY-MM-DD)"""
        # Implementar normalización de fechas
        
    def suggest_column_mapping(self, df):
        """Sugiere mapeo de columnas a campos de Odoo"""
        # Implementar sugerencias basadas en nombres de columna y contenido
```

#### 1.2 Endpoint para Preprocesamiento de Excel
```python
# Modificar: api/routes/excel_importer.py

@router.post("/preprocess-excel")
async def preprocess_excel(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    """Preprocesa un Excel y devuelve estructura normalizada con sugerencias de mapeo"""
    # Implementar lógica de preprocesamiento usando ExcelNormalizerService
    # Devolver JSON con datos normalizados y sugerencias de mapeo
```

### Fase 2: Mejora del Procesamiento OCR (2 días)

#### 2.1 Ampliar Biblioteca de Prompts
```python
# Modificar: api/services/provider_prompts.py

# Añadir más prompts específicos para ABRILA, MIELECTRO, etc.
# Mejorar prompts existentes con ejemplos de validación

PROMPTS = {
    "NEVIR": """Eres un asistente especializado en OCR para facturas NEVIR...""",
    "ABRILA": """Eres un asistente especializado en OCR para facturas ABRILA...""",
    "MIELECTRO": """Eres un asistente especializado en OCR para facturas MIELECTRO...""",
    "GENERICO": """Eres un asistente especializado en OCR para facturas..."""
}
```

#### 2.2 Mejorar Validador OCR
```python
# Modificar: api/services/ocr_validator.py

# Añadir validaciones específicas por proveedor
# Implementar validación de códigos de producto por patrón
# Mejorar validación de NIF/CIF
# Implementar separación de impuestos (IVA vs Recargo)
```

### Fase 3: Componente de Consolidación Frontend (3 días)

#### 3.1 Crear Componente de Wizard de Consolidación
```tsx
// Nuevo archivo: src/components/ConsolidationWizard.tsx

import React, { useState, useEffect } from 'react';
import { Table, Form, Input, Button, Steps, Alert, Tabs } from 'antd';
import { useOdooContext } from '../OdooContext';

const ConsolidationWizard = ({ 
  excelData, 
  ocrData, 
  barcodeData,
  onSave,
  onCancel 
}) => {
  // Implementar componente de wizard con pasos:
  // 1. Selección de fuente de datos
  // 2. Mapeo de columnas (para Excel)
  // 3. Revisión y corrección de datos
  // 4. Validación y guardado
  
  // Mostrar advertencias y permitir corrección manual
  // Implementar validación cruzada entre fuentes
  // Guardar mapeos exitosos para futuras importaciones
};

export default ConsolidationWizard;
```

#### 3.2 Crear Página Unificada de Importación
```tsx
// Nuevo archivo: src/pages/UnifiedImport.tsx

import React, { useState } from 'react';
import { Tabs, Card, Upload, Button, message } from 'antd';
import { ImportOutlined, FileExcelOutlined, CameraOutlined, FilePdfOutlined } from '@ant-design/icons';
import ImportExcelChunk from '../ImportExcelChunk';
import ImportInvoice from '../ImportInvoice';
import ConsolidationWizard from '../components/ConsolidationWizard';

const UnifiedImport = () => {
  // Implementar página con pestañas para:
  // - Importación de Excel
  // - Procesamiento de facturas OCR
  // - Escaneo de códigos de barras
  // - Consolidación y revisión
  
  // Permitir flujo entre pestañas y envío de datos al wizard de consolidación
};

export default UnifiedImport;
```

#### 3.3 Integrar en Rutas y Menú
```tsx
// Modificar: src/App.tsx y src/components/sider.tsx

// Añadir ruta a la nueva página
// Añadir enlace en el menú lateral
```

### Fase 4: Endpoints de Consolidación Backend (2 días)

#### 4.1 Servicio de Consolidación
```python
# Nuevo archivo: api/services/data_consolidation_service.py

class DataConsolidationService:
    def __init__(self):
        self.product_service = OdooProductService()
        self.invoice_service = OdooInvoiceService()
        
    def consolidate_product_data(self, sources):
        """Consolida datos de productos de múltiples fuentes"""
        # Implementar lógica de consolidación
        # Detectar y resolver conflictos
        # Validar datos consolidados
        
    def validate_cross_references(self, data):
        """Valida referencias cruzadas entre productos, proveedores, etc."""
        # Implementar validación cruzada
        
    def generate_unique_identifiers(self, products):
        """Genera identificadores únicos para productos sin código"""
        # Implementar generación de códigos basados en nombre y proveedor
```

#### 4.2 Endpoint de Consolidación
```python
# Nuevo archivo: api/routes/data_consolidation.py

@router.post("/consolidate-data")
async def consolidate_data(
    data: ConsolidationRequest,
    token: str = Depends(oauth2_scheme)
):
    """Consolida datos de múltiples fuentes y los prepara para guardar en Odoo"""
    # Implementar lógica de consolidación usando DataConsolidationService
    # Devolver datos consolidados con advertencias y sugerencias
```

### Fase 5: Sistema de Logging y Aprendizaje (1 día)

#### 5.1 Servicio de Logging Avanzado
```python
# Nuevo archivo: api/services/advanced_logging_service.py

class AdvancedLoggingService:
    def log_import_attempt(self, source, data, result):
        """Registra intento de importación con detalles"""
        # Implementar logging detallado
        
    def log_correction(self, original_data, corrected_data):
        """Registra correcciones manuales para aprendizaje"""
        # Implementar registro de correcciones
        
    def analyze_common_errors(self):
        """Analiza patrones de errores comunes"""
        # Implementar análisis de errores
```

#### 5.2 Integrar Logging en Endpoints
```python
# Modificar endpoints existentes para usar AdvancedLoggingService
# Registrar intentos, errores y correcciones
```

### Fase 6: Documentación y Pruebas (2 días)

#### 6.1 Documentación de API
```python
# Actualizar documentación de API con nuevos endpoints
# Añadir ejemplos de uso y respuestas
```

#### 6.2 Guía de Usuario
```markdown
# Crear guía de usuario para el nuevo sistema de importación
# Incluir capturas de pantalla y ejemplos
```

#### 6.3 Pruebas Manuales
```
# Definir casos de prueba para validar el sistema completo
# Probar con datos reales de diferentes proveedores
```

## 4. Cronograma de Implementación

| Fase | Descripción | Duración | Dependencias |
|------|-------------|----------|--------------|
| 1 | Preprocesador Unificado de Excels | 2 días | Ninguna |
| 2 | Mejora del Procesamiento OCR | 2 días | Ninguna |
| 3 | Componente de Consolidación Frontend | 3 días | Fase 1 |
| 4 | Endpoints de Consolidación Backend | 2 días | Fase 1, 2 |
| 5 | Sistema de Logging y Aprendizaje | 1 día | Fase 3, 4 |
| 6 | Documentación y Pruebas | 2 días | Todas |

**Tiempo total estimado**: 12 días laborables

## 5. Recursos Necesarios

### Desarrollo
- 1 desarrollador backend (Python, FastAPI)
- 1 desarrollador frontend (React, TypeScript)
- Acceso a API de Mistral AI para OCR y procesamiento de texto

### Pruebas
- Conjunto de Excels reales de diferentes proveedores
- Conjunto de facturas PDF/imagen para OCR
- Acceso a instancia de Odoo 18 de prueba

## 6. Métricas de Éxito

1. **Tasa de éxito en importación**: >95% de productos importados correctamente
2. **Precisión OCR**: >90% de campos extraídos correctamente
3. **Tiempo de procesamiento**: <30 segundos para Excel, <60 segundos para OCR
4. **Usabilidad**: <5 minutos para completar una importación completa
5. **Reducción de errores**: >80% menos errores manuales en entrada de datos

## 7. Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Excels extremadamente desestructurados | Alta | Medio | Implementar fallback manual para mapeo de columnas |
| Facturas con baja calidad de imagen | Media | Alto | Añadir preprocesamiento de imagen y OCR con múltiples intentos |
| Duplicados no detectados | Media | Alto | Implementar validación cruzada con datos existentes |
| Rendimiento lento en procesamiento | Baja | Medio | Optimizar caché y procesamiento asíncrono |

## 8. Conclusión

Este plan aprovecha los componentes existentes y los extiende para crear un sistema unificado de importación, procesamiento y consolidación de datos. El enfoque se centra en la robustez, la validación cruzada y la corrección manual antes de guardar en Odoo, maximizando la precisión y minimizando el trabajo manual.

La implementación se realizará de forma incremental, permitiendo probar y ajustar cada componente antes de avanzar a la siguiente fase. El resultado final será un sistema que ahorre cientos de horas de entrada manual de datos y mejore significativamente la calidad de los datos en Odoo.
