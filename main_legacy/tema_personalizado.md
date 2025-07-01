# Tema Personalizado - Memoria de Desarrollo

## Resumen

Este documento detalla los problemas encontrados durante el desarrollo y personalización del tema `theme_pelotazo` para Odoo 18, así como las soluciones implementadas y la documentación consultada.

## Problemas Identificados y Resoluciones

### 1. Bloque de Categorías con Fotos Grandes No Deseado

**Problema:**
- El tema incluía un bloque de categorías con fotos grandes que aparecía en la tienda web
- Este bloque era considerado "feo" por el usuario y necesitaba ser eliminado
- A pesar de las modificaciones iniciales, el bloque seguía apareciendo

**Investigación:**
- Se identificaron múltiples plantillas relacionadas con categorías en `shop_categories.xml`:
  - `s_product_categories`: Snippet principal de categorías
  - `product_categories_sidebar`: Plantilla de barra lateral con categorías estáticas
  - `shop_categories_sidebar_integration`: Integración de la barra lateral
  - `mobile_categories_toggle`: Toggle para móviles

**Solución Implementada:**
1. **Eliminación del snippet principal:**
   - Se eliminó completamente la plantilla `s_product_categories` de `shop_categories.xml`
   - Se eliminó su registro como snippet disponible

2. **Desactivación de plantillas relacionadas:**
   - Se comentaron las plantillas `shop_categories_sidebar_integration` y `mobile_categories_toggle`
   - Esto evitó que siguieran llamando a `product_categories_sidebar`

3. **Reinicio del servicio:**
   - Se ejecutó `docker-compose restart odoo` para aplicar los cambios

**Archivos Modificados:**
- `/addons/theme_pelotazo/views/shop_categories.xml`

### 2. Imágenes de Categorías en Barra Lateral No Visibles

**Problema:**
- Las imágenes de categorías en la barra lateral no se mostraban
- Las rutas de las imágenes eran estáticas y no correspondían a archivos existentes

**Análisis:**
- La plantilla `product_categories_sidebar` contenía rutas hardcodeadas como:
  ```xml
  <img src="/theme_pelotazo/static/src/img/categories/electrodomesticos.jpg"/>
  ```
- Estas imágenes no existían en el directorio especificado

**Soluciones Propuestas:**
1. **Opción A:** Crear las imágenes en las rutas especificadas
2. **Opción B:** Modificar la plantilla para usar categorías reales de Odoo
3. **Opción C:** Eliminar completamente la funcionalidad (implementada)



## Documentación Consultada

### Odoo 18 - Desarrollo de Temas
1. **Documentación oficial de Odoo:**
   - Estructura de temas en Odoo 18
   - Sistema de plantillas XML
   - Snippets y su integración

2. **Personalización de plantillas XML:**
   - Estructura de plantillas en Odoo
   - Herencia y modificación de vistas
   - Gestión de snippets



### Herramientas de Desarrollo
1. **Docker y Docker Compose:**
   - Gestión de contenedores Odoo
   - Reinicio de servicios para aplicar cambios

2. **Estructura de archivos Odoo:**
   - Organización de addons
   - Archivos de vistas y plantillas
   - Manifiestos de módulos

## Lecciones Aprendidas

1. **Persistencia de cambios:** Los cambios en plantillas XML requieren reinicio del servicio Odoo para ser efectivos.

2. **Dependencias entre plantillas:** Es importante identificar todas las plantillas que referencian a una plantilla específica antes de eliminarla.

3. **Rutas estáticas vs dinámicas:** Las rutas hardcodeadas en plantillas pueden causar problemas si los archivos no existen.

4. **Gestión de dependencias:** Es fundamental entender las relaciones entre plantillas para evitar errores al eliminar componentes.

## Próximos Pasos

1. **Optimizar el rendimiento del tema** eliminando código no utilizado
2. **Crear las imágenes de categorías** si se decide restaurar la funcionalidad de barra lateral
3. **Mejorar la estructura del tema** siguiendo las mejores prácticas de Odoo
4. **Documentar configuraciones adicionales** según las necesidades del proyecto

## Conclusión

La personalización del tema `theme_pelotazo` requirió una comprensión profunda de la estructura de plantillas de Odoo y las interdependencias entre componentes. La eliminación exitosa del bloque de categorías no deseado proporciona una base sólida para el desarrollo futuro del tema personalizado.