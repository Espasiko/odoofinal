# Especificación Completa del Proyecto ManusOdoo (versión -roto)

## Resumen General
ManusOdoo -roto es una plataforma avanzada de gestión empresarial que integra Odoo 18, PostgreSQL 15, FastAPI y un frontend moderno desarrollado en React 18, Vite y Refine 4.x, con Ant Design 5.x. El proyecto utiliza Docker para orquestar los servicios y cuenta con scripts de automatización, documentación técnica y herramientas de migración y pruebas.

## Estructura de Directorios y Archivos Clave

- **/addons/**: Addons personalizados para Odoo (14 subdirectorios)
- **/backups/**: Copias de seguridad (3 archivos)
- **/config/**: Configuraciones de Odoo (odoo.conf)
- **/jsons/**: Archivos JSON de datos (132 archivos)
- **/odoo_import/**: Scripts y archivos para importación de datos (7 archivos)
- **/plantillasodoo/**: Plantillas y recursos para Odoo (72 archivos)
- **/public/**: Recursos estáticos públicos (4 archivos)
- **/src/**: Código fuente frontend (2 archivos)
- **/static/**: Recursos estáticos (13 archivos)
- **/templates/**: Plantillas para generación de documentos (2 archivos)
- **/tiendafotos/**: Recursos de la tienda de fotos (6 archivos)
- **/venv/**: Entorno virtual de Python
- **node_modules/**: Dependencias de Node.js

### Archivos principales
- **main.py**: Lógica principal del backend y orquestador FastAPI
- **start.sh / stop.sh / dev-dashboard.sh / install.sh**: Scripts de arranque, parada, desarrollo e instalación
- **requirements.txt**: Dependencias Python
- **package.json / package-lock.json**: Dependencias frontend
- **docker-compose.yml**: Orquestación de servicios Docker
- **.env**: Variables de entorno frontend (URLs, nombre de empresa)
- **config/odoo.conf**: Configuración de Odoo (db_host, db_port, db_user, db_password, admin_passwd)
- **README.md, README_INSTALACION.md, DOCUMENTACION_TECNICA.md, MEMORIA_PROYECTO.md, ODOO_INSTALLATION_README.md, plan_implementacion_detallado.md, proceso_mapeo_migracion.md, integracion_facturacion_verifactu.md, MEMORIA_MIGRACION_NODEJS20.md**: Documentación extensa y técnica

## Configuración y Puertos
- **Odoo:**
  - Imagen: odoo:18.0
  - Puerto host: 8070 → contenedor: 8069
  - Configuración en config/odoo.conf:
    - db_host = db
    - db_port = 5432 (interno Docker)
    - db_user = odoo
    - db_password = odoo
    - admin_passwd = admin
- **PostgreSQL:**
  - Imagen: postgres:15
  - Puerto host: 5434 → contenedor: 5432
  - Base de datos principal: manus_odoo-bd
  - Usuario: odoo
  - Contraseña: odoo
- **FastAPI:**
  - Generalmente expuesto en 8000
  - Se comunica con el frontend y el backend Odoo
- **Frontend:**
  - React 18, Vite, Refine 4.x, Ant Design 5.x
  - Variables en .env:
    - VITE_ODOO_URL=http://localhost:8070
    - VITE_API_URL=http://localhost:8000
    - VITE_APP_TITLE=ManusOdoo Dashboard
    - VITE_COMPANY_NAME=El Pelotazo

## Instalación y Puesta en Marcha
1. **Instalación de dependencias:**
   - Python: `pip install -r requirements.txt`
   - Node: `npm install`
2. **Arranque de servicios:**
   - `./start.sh` (orquesta Docker, Odoo, DB, FastAPI, frontend)
   - `docker-compose up -d` (alternativa manual)
3. **Desarrollo frontend:**
   - `./dev-dashboard.sh` para entorno Vite
4. **Parada de servicios:**
   - `./stop.sh` o `docker-compose down`

## Versiones de Herramientas
- **Odoo:** 18.0
- **PostgreSQL:** 15
- **Python:** >=3.10 (verificar en venv)
- **Node.js:** >=18.x
- **React:** 18.2.0
- **Refine:** 4.x
- **Ant Design:** 5.x
- **Vite:** 4.2.0

## Scripts y Utilidades
- **Migración y conversión:**
  - convertidor_proveedores.py, convertir_csv_a_excel.py, script_migracion_categorias.py, script_migracion_excel_odoo.py
- **Pruebas y verificación:**
  - test_api_product.py, test_minimal_server.py, test_odoo_connection.py, test_simple_product.py, test_simple_server.py, test_ultra_simple.py, verificar_instalacion.py, verificar_modulo.py
- **Backup:**
  - backup.sh

## Observaciones Técnicas
- Proyecto modular, permite añadir nuevos addons y scripts fácilmente.
- Amplia documentación técnica y de migración.
- Integración con sistemas de facturación (verifactu), OCR y mapeo de datos.
- Soporte para migraciones desde NodeJS 20 y automatización de procesos.

## Estado Actual
- Proyecto avanzado y funcional.
- Listo para desarrollo, pruebas y despliegue.
- Base de datos y servicios correctamente orquestados por Docker.
- Documentación y scripts de migración exhaustivos.

---

*Este archivo ha sido generado automáticamente para documentar el estado y configuración actual del proyecto ManusOdoo versión -roto.*
