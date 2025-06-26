# Memoria técnica: 25-06-MemoriaFasfuncionando

## Rama y estado del código
- El código está en la rama `fasbien` y todos los cambios recientes están commiteados y subidos al remoto.
- Último commit: Fix conexión robusta Odoo <-> FastAPI, bug tipos dashboard, mejoras integración real.

## Configuración Docker Compose
- Proyecto multi-servicio con Odoo 18, FastAPI y React.
- **Odoo**:
  - Imagen: Odoo 18
  - Puerto interno: 8069
  - Puerto externo: 8069
  - Hostname Docker: `odoo`
  - Red Docker: Compartida con FastAPI y frontend
  - Base de datos PostgreSQL:
    - Host: `localhost` (dentro del contenedor DB)
    - Puerto interno: 5432, externo: 5434
    - Base de datos: `manus_odoo-bd`
    - Usuario: `odoo`
    - Contraseña: `odoo`
- **FastAPI**:
  - Imagen: Python 3.11, Uvicorn
  - Puerto interno: 8000
  - Puerto externo: 8000
  - Hostname Docker: `fastapi` (accesible por otros servicios Docker)
  - Variable de entorno ODOO_URL: `http://odoo:8069`
  - Comando de arranque: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
  - Volúmenes: Monta el código fuente
- **Frontend React**:
  - Puerto: 3001
  - Consume endpoints de FastAPI en `http://localhost:8000`

## Credenciales y configuración de acceso
- **Odoo Admin:**
  - Usuario/email: `yo@mail.com`
  - Contraseña: `admin`
  - Nombre: El pelotazo
  - ID usuario: 2
- **FastAPI:**
  - Usa JWT, login en `/token` con usuario/contraseña de Odoo
- **Postgres:**
  - Usuario: `odoo`
  - Contraseña: `odoo`
  - DB: `manus_odoo-bd`
  - Puerto externo: 5434

## Endpoints principales FastAPI
- `/api/v1/products/all` - Lista de productos reales desde Odoo
- `/api/v1/providers` - Lista de proveedores reales desde Odoo
- `/api/v1/dashboard/stats` - Estadísticas de inventario (requiere token)
- `/token` - Login JWT

## Detalles técnicos clave
- El backend FastAPI ahora toma la URL de Odoo de la variable de entorno/configuración SIEMPRE (`http://odoo:8069`), nunca una IP fija.
- Todos los endpoints usan datos reales, sin fallback ni datos simulados (excepto si Odoo no responde).
- El frontend consume datos reales y la integración está verificada.
- Todos los puertos, rutas y credenciales están documentados arriba.

## Observaciones
- Si se reinicia Docker, la red y los nombres de host siguen funcionando.
- Para acceder a Odoo vía web: http://localhost:8069
- Para Adminer (gestor DB): http://localhost:8080
- Para FastAPI docs: http://localhost:8000/docs
- Para frontend: http://localhost:3001

---
**Esta memoria resume toda la configuración, credenciales y rutas críticas del entorno funcionando a 25-06-2025.**
