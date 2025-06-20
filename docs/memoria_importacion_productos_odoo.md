# Memoria de Importación de Productos a Odoo

**Fecha:** 19 de Junio de 2025

**Proyecto:** ManusOdoo - El Pelotazo Electrohogar

**Versión de Odoo:** 18

## Resumen

Hemos logrado importar con éxito 9 productos a Odoo utilizando un script de importación directa basado en XML-RPC, evitando problemas previos con la API FastAPI que resultaban en errores 500. Este documento detalla el proceso, los problemas enfrentados, las soluciones aplicadas y los resultados obtenidos.

## Detalles del Script

- **Nombre del Script:** `direct_odoo_import.py`
- **Ubicación:** `/home/espasiko/mainmanusodoo/manusodoo-roto/scripts/direct_odoo_import.py`
- **Función:** Conecta directamente con Odoo a través de XML-RPC en `http://localhost:8069` y crea productos en la base de datos `manus_odoo-bd` utilizando las credenciales proporcionadas (Usuario: `yo@mail.com`, Contraseña: `admin`).
- **Archivo CSV Utilizado:** `/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/PVP_CECOTEC_template_corrected.csv`

## Problemas Enfrentados

1. **Error 500 con FastAPI:** Inicialmente, intentamos importar productos a través de la API FastAPI en `http://localhost:8000/api/v1/products`, pero recibimos errores 500 con el mensaje genérico "Error al crear el producto en Odoo", sin detalles adicionales en los logs.
2. **Falta de Logs Detallados:** No pudimos obtener información específica del error desde los logs del servidor FastAPI, lo que dificultó la depuración.
3. **Valores Incorrectos para el Campo `type`:** Al cambiar a un script de importación directa con XML-RPC, enfrentamos errores relacionados con el valor del campo `type` en `product.template`. Los valores `product` y `storable` no fueron aceptados por Odoo, generando excepciones de `ValueError`.

## Soluciones Aplicadas

1. **Cambio a Importación Directa con XML-RPC:** Desarrollamos un nuevo script `direct_odoo_import.py` para interactuar directamente con Odoo, evitando la API FastAPI y permitiendo obtener errores más específicos.
2. **Ajuste del Campo `type`:** Después de varios intentos y revisando la documentación de Odoo 18, determinamos que el valor correcto para el campo `type` es `consu` (consumible), lo cual fue confirmado por el usuario y resultó en una importación exitosa.
3. **Limitación Inicial y Escalabilidad:** Comenzamos importando solo un producto para depuración, y una vez confirmado el éxito, modificamos el script para procesar todos los productos del archivo CSV.

## Resultados

- **Total de Productos Procesados:** 9
- **Productos Importados con Éxito:** 9
- **Errores:** 0
- **IDs de Productos Importados:** 791 a 799

Los productos importados pueden verificarse en la interfaz web de Odoo en `http://localhost:8069`.

## Conclusiones y Recomendaciones

- La importación directa con XML-RPC es una solución efectiva para evitar problemas con capas intermedias como FastAPI cuando no se dispone de logs detallados.
- Es crucial utilizar valores de campos compatibles con la versión específica de Odoo (en este caso, `consu` para el campo `type` en Odoo 18).
- Se recomienda mantener este script como una herramienta de respaldo para futuras importaciones o depuraciones.
- Para próximas importaciones, validar que los datos en el CSV estén alineados con los campos y formatos esperados por Odoo, consultando la documentación en `/docs/camposodoo.md` y `/docs/19.06-campso provvedoresYcredenciales.md`.

**Responsable:** Cascade AI
