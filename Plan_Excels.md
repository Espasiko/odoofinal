# Plan Estratégico para la Importación de Tarifas de Proveedores (Versión Final)

## 1. El Problema: La Complejidad Variable

La importación de tarifas de proveedores a través de archivos Excel presenta un desafío significativo debido a la **alta variabilidad y falta de estandarización** entre los formatos. Un enfoque de desarrollo rígido está destinado al fracaso.

El objetivo es diseñar y construir un **sistema de importación robusto, escalable e inteligente** que pueda adaptarse a los "dialectos" de cada proveedor, normalizar sus datos y cargarlos de forma consistente en Odoo.

## 2. Análisis de Proveedores: "El Mapa de la Locura" Definitivo

Tras un análisis exhaustivo de todos los archivos de proveedores, hemos identificado un conjunto de variaciones clave que el sistema debe ser capaz de manejar. Esta tabla es el mapa completo de la complejidad a la que nos enfrentamos.

| Característica | **ALMCE** | **BSH** | **CECOTEC** | **ABRILA** | **EAS-JOHNSON** | **ELECTRODIRECTO** | **MIELECTRO** | **ORBEGOZO** | **NEVIR** | **UFESA** | **VITROKITCHEN** | **JATA** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Estructura** | Multi-hoja | Hoja única | Hoja única | Hoja única | Hoja única | Hoja única | Hoja única + Flag `VENDIDO` | Hoja única + `VENDIDO` + `ROTO` | Hoja única + `VENDIDO` | **Multi-hoja + Hoja de Reglas** | Hoja única | **Hoja única + `VENDIDO`** |
| **Categoría** | Nombre hoja | Fila sep. | Fila sep. | Fila sep. | Fila sep. | Fila sep. | Fila sep. | Fila sep. | Fila sep. | Fila sep. | Fila sep. | **Fila sep.** |
| **Marca** | Implícita | En desc. | Implícita | Implícita | En desc. | En desc. | En desc. | Implícita | Implícita | Implícita | **Implícita** | **Implícita** |
| **Descuentos** | Ninguno | `DTO. IMPL.` | `DTO` (var) | `DTO.` (final) | `DTO (%)` + `OTROS` | Ninguno | Lógica Ambigüa | **¡Cascada (4 DTOs)!** | **"Falso DTO"** | **Cascada %** | **Coste en col. DTO** | **"Falso DTO"** |
| **Coste Real** | `IMPORTE BRUTO` | `TOTAL` | `TOTAL` | `DTO.` | `Bruto - DTOs` | `IMPORTE BRUTO` | Incierto | `Bruto - Suma(DTOs)` | `DTO.` | `Bruto - DTOs %` | **Última col. `DTO.`** | **`DTO.`** |
| **Impuestos** | Combinados | Combinados | Combinados | Combinados | Combinados | **Desglosados** | Combinados | Combinados | Combinados | Combinados | Combinados | **Combinados** |
| **Posición** | Col `A` | Col `B` | Col `A` | Col `B` | Col `B` | Col `B` | Col `B` | Col `A` | Col `B` | Col `B` | Col `B` | **Col `A`** |

**Conclusión Final del Análisis:** La complejidad es aún mayor de lo previsto. Los patrones de descuento, en particular, requieren una IA para su interpretación. La existencia de "hojas de reglas" (UFESA) confirma que la estrategia de dos fases (Pre-procesador + Intérprete IA) es la correcta.

## 3. La Estrategia: "Organizar la Locura" en 3 Fases

### Fase 1: El Pre-procesador de Excel (El "Normalizador")

- **Objetivo:** Convertir cualquier Excel en un JSON limpio y con metadatos, sin interpretar la lógica de negocio.
- **Responsabilidades:**
    1.  **Buscar activamente hojas de reglas** (ej. `CALCULO TARIFA`) y extraerlas como metadatos.
    2.  Iterar sobre las hojas de producto, detectando dinámicamente la cabecera.
    3.  Extraer los datos de cada fila a un diccionario, incluyendo indicadores de estado (`VENDIDO`, `ROTO`).
- **Salida:** Un JSON que contiene tanto los datos "crudos" como las "reglas" si existen.

### Fase 2: El Intérprete de Negocio con IA (El "Cerebro")

- **Objetivo:** Convertir los datos normalizados en información de negocio estructurada y lista para Odoo.
- **Responsabilidades:**
    1.  Enviar el JSON (datos + reglas) a la API de **Mistral**.
    2.  Utilizar un **prompt de IA dinámico y contextual**.
    3.  **El prompt instruirá a la IA para:**
        -   **Prioridad 1:** Buscar y aplicar las reglas explícitas de los metadatos (lógica `UFESA`).
        -   **Prioridad 2:** Si no hay reglas, aplicar patrones de cálculo inferidos (cascadas, falsos DTOs, etc.).
        -   Extraer `nombre`, `marca`, `codigo_referencia`, `categoria` y `stock`.
        -   Generar un **JSON final y perfecto** para el mapeo a Odoo.

### Fase 3: Mapeo y Carga en Odoo (El "Motor")

- **Objetivo:** Persistir los datos procesados por la IA en Odoo de forma segura.
- **Responsabilidades:**
    1.  Lógica robusta de **`find_or_create`** para `res.partner`, `product.category`, y `account.tax`.
    2.  Crear o actualizar `product.product`.
    3.  Construir correctamente el campo `seller_ids`.
    4.  Crear **Ajustes de Inventario** para el `stock`.

## 4. Próximos Pasos Propuestos

1.  **Aprobación del Plan Final:** Revisión y validación de esta hoja de ruta completa.
2.  **Fase 0 - Estabilización:** Corregir errores críticos existentes en la API (ej. herencia de modelos Pydantic).
3.  **Desarrollo Fase 1:** Implementar el script del Pre-procesador.
4.  **Desarrollo Fase 2:** Diseñar el prompt final de la IA y la lógica de comunicación.
5.  **Desarrollo Fase 3:** Reforzar los servicios de Odoo para manejar la carga de datos procesados.