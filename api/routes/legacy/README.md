# Código Legacy de Manusodoo-Roto

Este directorio contiene código que ya no se utiliza en el flujo principal de la aplicación pero se mantiene como referencia histórica o para posibles usos futuros.

## Archivos Legacy

### mistral_llm_excel.py

Este archivo implementaba un endpoint alternativo para la importación de Excel (`/api/v1/mistral-llm/process-excel`) que fue reemplazado por el endpoint actual `/api/v1/importer/` implementado en `excel_importer.py`.

**Características principales:**
- Procesamiento directo con pandas para convertir Excel a texto plano
- Endpoints adicionales de prueba (`/test-minimal`, `/test-excel`)
- Menos estructurado en fases que el endpoint actual
- No incluye respuestas raw de la IA en la respuesta

**Razón de la migración:**
El endpoint actual (`excel_importer.py`) ofrece un procesamiento más robusto y estructurado en tres fases claramente definidas:
1. Pre-procesamiento del Excel con `ExcelPreprocessor`
2. Interpretación con Mistral AI
3. Carga en Odoo con validaciones y transformaciones

## Flujo Actual de Importación de Excel

El flujo actual de importación de Excel utiliza exclusivamente el endpoint `/api/v1/importer/` implementado en `excel_importer.py`:

1. **Frontend**: El componente `ImportExcelChunk.tsx` envía el archivo Excel al endpoint `/api/v1/importer/`
2. **Backend**: El archivo se procesa en tres fases:
   - Preprocesamiento del Excel para extraer datos estructurados
   - Interpretación con Mistral AI para normalizar y enriquecer datos
   - Carga en Odoo con validaciones y transformaciones
3. **Frontend**: Muestra resultados y permite navegar a la lista de productos

### Dependencias Principales

- `ExcelPreprocessor`: Clase especializada para procesar archivos Excel
- `mistral_llm_utils.py`: Utilidades para comunicación con Mistral AI
- `odoo_product_service.py`: Servicio para gestión de productos en Odoo
- `odoo_provider_service.py`: Servicio para gestión de proveedores en Odoo
- `nif_cif_validator.py`: Validador de NIF/CIF españoles

## Notas Importantes

- No eliminar estos archivos sin verificar exhaustivamente que no hay referencias en el código
- Si se necesita restaurar alguna funcionalidad, asegurarse de actualizar también `main.py`
- El código actual en producción utiliza exclusivamente `excel_importer.py`