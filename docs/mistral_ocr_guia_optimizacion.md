# Guía de Optimización de Mistral OCR para Importación de Facturas en Odoo 18

## Novedades y Mejoras Recientes (julio 2025)

### 1. Sistema de Caché OCR
- Implementado un sistema de caché basado en hash SHA-256 del PDF/factura para evitar reprocesamientos innecesarios.
- Permite recuperar resultados OCR previos y acelerar el flujo de importación.
- El endpoint `/process-invoice` de FastAPI ahora consulta la caché antes de procesar un nuevo documento.
- Los datos cacheados incluyen la fecha de almacenamiento y un indicador en la respuesta.

### 2. Prompts Específicos por Proveedor
- Se utiliza una biblioteca de prompts detallados para NEVIR, ABRILA, MIELECTRO y otros.
- Los prompts incluyen:
  - Validación estricta de códigos de producto (ej: patrón NVR-XXXXX para NEVIR).
  - Instrucciones para separar correctamente IVA y Recargo de Equivalencia.
  - Ubicación precisa de los datos del cliente y proveedor.
  - Ejemplos de formatos correctos de campos críticos (CIF/NIF, fechas, totales).
- Se recomienda revisar y ajustar los prompts periódicamente según los errores detectados en la extracción.

### 3. Validación y Normalización Avanzada
- El validador OCR (`ocr_validator.py`) realiza:
  - Validación y corrección de números de factura, fechas y NIF/CIF (incluyendo algoritmo de dígito de control español).
  - Corrección y normalización de datos específicos del cliente "El Pelotazo" y otros clientes frecuentes.
  - Validación de códigos de producto NEVIR y separación de impuestos según reglas del proveedor.
- Se han añadido logs detallados para depuración y trazabilidad.

### 4. Recomendaciones para Minimizar Errores OCR
- Especificar claramente en el prompt el formato esperado de cada campo.
- Usar el modelo de anotaciones estructuradas (`mistral-ocr-2505-annotation`) para obtener datos en JSON siempre que sea posible.
- Implementar validaciones post-OCR para:
  - Códigos de producto (regex/patrón por proveedor)
  - CIF/NIF (validación de dígito de control)
  - Fechas (normalización a YYYY-MM-DD)
  - Separación de impuestos y totales
- Registrar manualmente las correcciones para retroalimentar y mejorar los prompts y validaciones.

### 5. Limpieza y Unificación de Datos en Odoo
- Antes de crear proveedores o productos, comprobar duplicados y unificar registros existentes.
- Mantener los productos con categorías específicas y eliminar duplicados con categorías genéricas.
- Crear el cliente real de la factura si no existe y actualizar los datos del proveedor según la factura real.

---

## Modelos Disponibles y Características

### 1. Modelos OCR de Mistral AI

| Modelo | Descripción | Precio | Uso Recomendado |
|--------|-------------|--------|-----------------|
| `mistral-ocr-latest` | Modelo OCR estándar | 1€ por mil páginas | Uso general, extracción de texto |
| `mistral-ocr-2505-annotation` | Modelo OCR con anotaciones | 3€ por mil páginas | Extracción estructurada de datos |

### 2. Capacidades Principales

- **Extracción de texto completo** manteniendo formato y estructura
- **Procesamiento de tablas** con preservación de filas y columnas
- **Reconocimiento de imágenes** dentro del documento
- **Soporte multilingüe** nativo
- **Procesamiento de hasta 2000 páginas por minuto**
- **Anotaciones estructuradas** para extraer datos en formato JSON

### 3. Formatos Soportados

- **Documentos**: PDF, DOCX, PPTX
- **Imágenes**: PNG, JPEG/JPG, AVIF

---

## Prompt Optimizado Recomendado (Ejemplo para NEVIR)

```python
system_prompt = """Eres un asistente especializado en OCR para facturas NEVIR. Extrae TODO el texto visible, manteniendo el formato original. Presta atención a:

1. DATOS DEL PROVEEDOR:
   - Nombre: NEVIR S.A.
   - CIF: A28966307 (verifica dígito)
   - Dirección: Calle Francisco Rabal, 3, 28806 Alcalá de Henares Madrid

2. DATOS DEL CLIENTE:
   - Busca en la parte superior derecha, puede ser "BONACHERA PLAZA, ANTONIO" o "El Pelotazo"
   - NIF/CIF: 75236270G o B04957403
   - Dirección: CRTA ALICUN 172, 04740 ROQUETAS DE MAR ALMERÍA

3. CÓDIGOS DE PRODUCTO:
   - Patrón: NVR-XXXXX (ejemplo: NVR-5525CVSD)
   - Verifica caracteres dudosos (0/O, 1/I, 5/S)

4. IMPUESTOS:
   - Separa IVA (21%) y Recargo de Equivalencia (5,2%)
   - Indica base imponible, impuestos y total

5. LÍNEAS DE PRODUCTOS:
   - Código, descripción, cantidad, precio unitario, descuento
   - Mantén el formato exacto

No omitas ninguna información. Si un dato no está claro, indícalo como "NO IDENTIFICADO"."""
```

---

## Implementación Recomendada

- Usar el sistema de caché para evitar reprocesamientos.
- Aplicar prompts específicos por proveedor.
- Validar y normalizar todos los campos críticos tras el OCR.
- Unificar y limpiar datos en Odoo antes de crear nuevos registros.
- Registrar y analizar errores para mejorar continuamente los prompts y validaciones.

---

## Ejemplo de Flujo Completo

1. Subida de factura PDF/imagen.
2. Consulta a caché OCR (por hash SHA-256).
3. Si existe, recuperar datos; si no, procesar con Mistral OCR usando prompt específico.
4. Validar y normalizar los datos extraídos.
5. Comprobar duplicados en Odoo y unificar si es necesario.
6. Crear/actualizar proveedor, cliente y productos.
7. Crear la factura en Odoo.
8. Registrar logs y correcciones para aprendizaje continuo.

---

## Conclusión

Con estas mejoras, el sistema OCR de facturas NEVIR y otros proveedores en Odoo 18 es más preciso, eficiente y robusto. La clave está en la combinación de prompts optimizados, validaciones específicas y un flujo de importación inteligente con caché y limpieza de datos.