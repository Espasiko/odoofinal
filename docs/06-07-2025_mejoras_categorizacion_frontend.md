# Mejoras en categorización de productos y plan de mejora frontend

**Fecha**: 06/07/2025  
**Autor**: Equipo de desarrollo  
**Proyecto**: Manusodoo-Roto

## 1. Resumen ejecutivo

Este documento detalla las mejoras realizadas en el sistema de categorización automática de productos y el plan de mejora para el frontend de la aplicación. El objetivo es optimizar la visualización de datos críticos como categorías, precios de compra, márgenes y proveedores, facilitando la toma de decisiones comerciales.

## 2. Mejoras en la categorización de productos

### 2.1. Consolidación de scripts

Se han eliminado scripts redundantes, manteniendo únicamente `recategorizar_mejorado.py` como la solución definitiva para la recategorización de productos. Los scripts eliminados fueron:
- `recategorizar_standalone.py`
- `recategorizar_productos.py`

### 2.2. Ampliación del diccionario de palabras clave

Se ha expandido el diccionario de palabras clave para mejorar la detección automática de categorías, incluyendo términos como:
- "frigo", "2pta" → Frigoríficos
- "arca", "arcon" → Congeladores
- "inverter" → Aires acondicionados
- "pizzapan" → Placas de inducción

### 2.3. Resultados obtenidos

La ejecución del script mejorado ha logrado:
- Reducir el número de productos sin categorizar de 19 a 8
- Verificar que no hay productos con "Producto sin nombre"
- Asignar correctamente categorías a productos de refrigeración, aires acondicionados y electrodomésticos de cocina

### 2.4. Productos pendientes de categorizar

Los 8 productos que permanecen en la categoría "All" son principalmente artículos de ferretería y accesorios:
- `(KUKEN) QUITAPELUSAS PILAS`
- `43004323 | 75236270G | 670 968 607 | 1 | | CÓDIGO | DESCR`
- `ALCAYATA ROSCA ZINC (16X30)`
- `CUTTER RETRACTIL PLASTICO`
- `FLEXOMETRO STEIN F/GOMA FRENO`
- `GUANTE POLYSTER HIGIENICO` (2 productos)
- `PRECINTO POLIPRO. TRANSPARENTE`

## 3. Análisis del frontend para productos

### 3.1. Estado actual

El análisis del componente `products.tsx` y el servicio `odooService.ts` ha revelado:
- La tabla de productos no muestra categorías de productos
- No se visualizan los precios de compra (`standard_price`)
- No se calculan ni muestran márgenes ni beneficios
- No se muestra el proveedor asociado a cada producto

### 3.2. Estructura de datos de producto

La interfaz `Product` en `odooService.ts` incluye los campos necesarios, pero no todos se están utilizando en el frontend:
```typescript
export interface Product {
  id: number;
  name: string;
  default_code: string | null;
  list_price: number;
  standard_price: number;  // Precio de compra (no mostrado actualmente)
  categ_id: number | null; // ID de categoría (no mostrado actualmente)
  // ... otros campos
}
```

## 4. Análisis del flujo de actualización de precios

### 4.1. Flujo actual

El análisis del código ha revelado el siguiente comportamiento:

1. **Importación desde Excel**:
   - Los productos se crean/actualizan con los precios del Excel
   - El precio de venta se guarda en `list_price`
   - El precio de compra se guarda en `standard_price`

2. **Importación desde facturas**:
   - Las facturas se procesan mediante OCR
   - Se crean líneas de factura en Odoo
   - **No se actualizan** los precios de compra de los productos

3. **Conflictos de precios**:
   - Los precios de Excel prevalecen sobre los de facturas
   - No hay sincronización automática entre facturas y datos maestros de productos

### 4.2. Problemas identificados

- Los precios de compra aparecen como 0€ en el frontend
- No hay historial de cambios de precios
- No se aprovecha la información de precios de las facturas para actualizar los datos maestros

## 5. Plan de mejoras

### 5.1. Frontend de productos

1. **Nuevas columnas para la tabla de productos**:
   - Categoría
   - Precio de compra
   - Margen (%)
   - Beneficio unitario (€)
   - Proveedor

2. **Implementación técnica**:
   - Modificar el componente `products.tsx`
   - Asegurar que la API devuelva todos los campos necesarios
   - Implementar cálculos de margen y beneficio

### 5.2. Mejora de operaciones CRUD para proveedores

1. **Componente de listado de proveedores**:
   - Implementar tabla con paginación
   - Mostrar campos clave: nombre, NIF, email, teléfono, dirección

2. **Formulario completo de proveedor**:
   - Implementar formulario con todos los campos relevantes
   - Incluir validación de NIF/CIF español
   - Añadir campos para condiciones comerciales

3. **Integración con productos**:
   - Mostrar relación entre proveedores y productos
   - Permitir filtrar productos por proveedor

### 5.3. Mejoras en la gestión de precios

1. **Opción para actualizar precios desde facturas**:
   - Implementar toggle en la interfaz de importación
   - Añadir lógica en el backend para actualizar el `standard_price`

2. **Historial de precios**:
   - Crear tabla para registrar cambios de precios
   - Mostrar tendencia de precios por producto

## 6. Próximos pasos

1. Implementar las mejoras en el frontend para mostrar todos los datos relevantes
2. Desarrollar el módulo de gestión de proveedores
3. Implementar la lógica de actualización de precios desde facturas
4. Crear el historial de precios para seguimiento

## 7. Conclusiones

Las mejoras realizadas en la categorización de productos han sido exitosas, reduciendo significativamente el número de productos sin categorizar. El plan de mejora para el frontend permitirá visualizar información crítica para la toma de decisiones comerciales, como márgenes y beneficios por producto.

La implementación de estas mejoras facilitará la gestión diaria del negocio y proporcionará una visión más clara de la rentabilidad de cada producto.