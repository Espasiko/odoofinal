# Plan de Mejora del Sistema OCR para Facturas
**Fecha: 18/07/2025**

## Objetivos Generales
- Mejorar la precisión en la extracción de datos de facturas
- Reducir errores en la identificación de proveedores y datos fiscales
- Optimizar el procesamiento de tablas y cálculos
- Facilitar la identificación previa del proveedor por parte del usuario

## 1. Validación y Corrección de Datos

### 1.1 Sistema de Validación de CIF/NIF
- **Estado actual**: Implementado en `nif_cif_validator.py` con correcciones específicas para errores comunes
- **Mejoras planificadas**:
  - Ampliar diccionario de CIF/NIF conocidos para todos los proveedores analizados
  - Mejorar algoritmo de corrección para detectar más errores típicos de OCR
  - Implementar validación de dígito de control para todos los tipos de documentos (NIF, NIE, CIF)
  - Añadir registro de correcciones para retroalimentar el sistema

### 1.2 Validación Cruzada OCR-Tabula
- **Estado actual**: Tabula se usa para mejorar datos pero sin validación cruzada sistemática
- **Mejoras planificadas**:
  - Implementar comparación automática entre datos extraídos por OCR y Tabula
  - Establecer reglas de prioridad (qué fuente es más confiable para cada tipo de dato)
  - Crear sistema de alertas para discrepancias significativas
  - Generar informe de confianza para cada campo extraído

### 1.3 Verificación de Cálculos Matemáticos
- **Estado actual**: Validación básica implementada pero no sistemática
- **Mejoras planificadas**:
  - Verificar suma de líneas = base imponible
  - Verificar base × tipo impositivo = cuota impuesto
  - Verificar base × tipo recargo = importe recargo
  - Verificar base + impuestos + recargos = total factura
  - Implementar tolerancia configurable para diferencias por redondeo
  - Añadir corrección automática de errores matemáticos menores

## 2. Mejoras en la Interfaz de Usuario

### 2.1 Selección Previa de Proveedor
- **Implementación**:
  - Añadir desplegable con lista de proveedores existentes en Odoo
  - Cargar automáticamente el NIF/CIF al seleccionar un proveedor
  - Permitir búsqueda por nombre o NIF/CIF
  - Actualizar la lista de proveedores en tiempo real

### 2.2 Campo de NIF/CIF
- **Implementación**:
  - Añadir campo para introducir manualmente el NIF/CIF
  - Implementar validación en tiempo real del formato
  - Autocompletar proveedores al escribir el NIF/CIF
  - Guardar esta información para enviarla junto con la factura al OCR

## 3. Mejoras en el Procesamiento OCR

### 3.1 Prompt Mejorado para Mistral OCR
- **Estado actual**: Prompt general sin información específica de proveedores
- **Mejoras planificadas**:
  - Implementar el prompt mejorado con información de los 13 proveedores analizados
  - Incluir instrucciones específicas para cada tipo de documento
  - Añadir validaciones específicas por proveedor
  - Incorporar la información previa del proveedor seleccionado por el usuario

### 3.2 Optimización de Tabula
- **Estado actual**: Configuración genérica para todos los documentos
- **Mejoras planificadas**:
  - Implementar configuraciones específicas por proveedor
  - Mejorar detección de orientación de página
  - Optimizar extracción de tablas complejas
  - Implementar post-procesamiento específico por proveedor

## 4. Implementación Técnica

### 4.1 Modificaciones en Frontend (React)
- Actualizar `ImportInvoice.tsx` para añadir:
  - Desplegable de proveedores
  - Campo de NIF/CIF
  - Validación en tiempo real
  - Envío de datos adicionales al backend

### 4.2 Modificaciones en Backend (FastAPI)
- Actualizar endpoint `/process-invoice` para:
  - Recibir información previa del proveedor
  - Incluir esta información en el prompt de OCR
  - Seleccionar configuración de Tabula según proveedor
  - Implementar validación cruzada OCR-Tabula

### 4.3 Servicios OCR
- Modificar `mistral_ocr_client.py` para:
  - Utilizar el prompt mejorado
  - Incorporar información previa del proveedor
  - Mejorar extracción de datos específicos

### 4.4 Validación
- Ampliar `ocr_validator.py` para:
  - Implementar todas las validaciones matemáticas
  - Mejorar validación de CIF/NIF
  - Añadir validación cruzada OCR-Tabula

## 5. Cronograma de Implementación

1. **Semana 1**: Implementación del prompt mejorado y pruebas iniciales
2. **Semana 2**: Modificaciones en frontend para añadir selección de proveedor
3. **Semana 3**: Implementación de validación cruzada OCR-Tabula
4. **Semana 4**: Mejoras en validación matemática y pruebas finales

## 6. Métricas de Éxito

- Reducción de errores en extracción de datos >30%
- Mejora en tiempo de procesamiento >20%
- Reducción de intervenciones manuales >40%
- Satisfacción del usuario >90%

## 7. Próximos Pasos

- Implementar sistema de aprendizaje continuo
- Desarrollar base de conocimiento de proveedores
- Activar sistema de caché OCR
- Implementar detección automática de proveedores por logo
