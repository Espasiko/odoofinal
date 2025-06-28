# Memoria Técnica: CRUD de Proveedores y Productos funcionando (FastAPI-Odoo)
**Fecha:** 27/06/2025

---

## 1. Resumen del Proyecto

Integración robusta entre FastAPI y Odoo 18 para la gestión de proveedores y productos, con operaciones CRUD completas (crear, leer, actualizar, eliminar) funcionando de extremo a extremo. El backend FastAPI se comunica con Odoo vía XML-RPC y expone endpoints REST consumidos por un frontend React. La arquitectura está gestionada por Docker Compose para garantizar portabilidad y facilidad de despliegue.

---

## 2. Infraestructura y Contenedores

- **Odoo 18**
  - URL: http://localhost:8069
  - Base de datos: `manus_odoo-bd`
  - Usuario: `yo@mail.com`
  - Contraseña: `admin`
  - PostgreSQL: `localhost:5432` (interno), `localhost:5434` (externo)
  - Adminer (gestor BD): http://localhost:8080

- **FastAPI Backend**
  - URL: http://localhost:8000
  - Gestión: Docker Compose
  - Servicio: `fastapi`
  - Comunicación con Odoo vía XML-RPC

- **Frontend React**
  - URL: http://localhost:3001
  - Consumo de API REST FastAPI

- **Comandos Docker habituales**
  - Reiniciar backend: `docker-compose restart fastapi`
  - Ver logs: `docker-compose logs fastapi`
  - Acceder a Odoo: `docker-compose restart odoo`

---

## 3. Credenciales de Acceso

- **PostgreSQL:**
  - Usuario: `odoo`
  - Contraseña: `odoo`
  - Base de datos: `manus_odoo-bd`
  - Host: `localhost`
  - Puerto: `5432` (interno), `5434` (externo)

- **Odoo:**
  - Usuario/Email: `yo@mail.com`
  - Contraseña: `admin`
  - Nombre: `El pelotazo`
  - ID Usuario: `2`

---

## 4. Endpoints FastAPI principales

- **Proveedores:**
  - Crear: `POST /api/v1/suppliers`
  - Actualizar: `PUT /api/v1/providers/{provider_id}`
  - Obtener todos: `GET /api/v1/providers/all`
  - Obtener uno: `GET /api/v1/providers/{provider_id}`

- **Productos:**
  - Crear: `POST /api/v1/products`
  - Actualizar: `PUT /api/v1/products/{product_id}`
  - Obtener todos: `GET /api/v1/products/all`
  - Obtener uno: `GET /api/v1/products/{product_id}`

- **Dashboard y autenticación:**
  - Stats: `GET /api/v1/dashboard/stats`
  - Token: `POST /api/v1/token`

---

## 5. Capa de Diccionarios y Normalización

Se implementó una capa de diccionario/mapeo para:
- Traducir claves del frontend (español) a claves Odoo (inglés), por ejemplo:
  - `nombre` → `name`
  - `correo_electronico` → `email`
  - `telefono` → `phone`
  - `nif` → `vat`
  - `sitio_web` → `website`
  - `movil` → `mobile`
  - `calle` → `street`
  - `calle2` → `street2`
  - `ciudad` → `city`
  - `codigo_postal` → `zip`
  - `comentarios` → `comment`
  - `activo` → `active`
- Saneamiento de campos string: todos los campos que puedan venir como `None` o `False` se convierten a `""` para evitar errores de validación en Odoo.
- Solo se envían a Odoo los campos válidos y presentes en el diccionario, lo que permite flexibilidad y robustez ante cambios en el frontend.

---

## 6. Pruebas y Validación

- Se realizaron pruebas automáticas y manuales usando scripts Python y Postman.
- Se verificó que los campos principales (`name`, `email`, `phone`, `mobile`, `vat`, `website`, `street`, `city`, `zip`, `comment`, `active`, etc.) se crean y actualizan correctamente en Odoo.
- Se detectó que algunos campos como dirección y NIF pueden requerir validaciones adicionales en Odoo para relaciones futuras (facturación, contabilidad, etc.).

---

## 7. Consideraciones y Buenas Prácticas

- **Siempre reiniciar el backend vía Docker tras cambios en el código.**
- **Revisar los logs de FastAPI y Odoo ante errores 500 o problemas de actualización.**
- **Mantener la capa de diccionarios actualizada si se agregan nuevos campos en el frontend.**
- **Validar que los campos enviados correspondan con los tipos y valores esperados por Odoo.**
- **Para relaciones futuras (facturas, contabilidad, etc.), asegurar que los proveedores tengan los campos clave (`vat`, `street`, etc.) correctamente rellenados.**

---

## 8. Ejemplo de Payloads

### Crear Proveedor (POST /api/v1/suppliers)
```json
{
  "name": "Proveedor Ejemplo",
  "email": "ejemplo@proveedor.com",
  "phone": "123456789",
  "mobile": "987654321",
  "website": "https://proveedorejemplo.com",
  "street": "Calle Ejemplo 1",
  "city": "Madrid",
  "zip": "28001",
  "vat": "ESX1111111X",
  "comment": "Proveedor de prueba",
  "active": true,
  "is_company": true,
  "supplier_rank": 1,
  "customer_rank": 0
}
```

### Actualizar Proveedor (PUT /api/v1/providers/{provider_id})
```json
{
  "email": "nuevo@proveedor.com",
  "phone": "111222333",
  "city": "Barcelona",
  "vat": "ESX2222222X"
}
```

---

## 9. Estado Final

- CRUD de proveedores y productos totalmente funcional desde FastAPI a Odoo.
- Integración estable y probada, lista para ampliaciones futuras (relaciones, facturación, etc.).
- Toda la infraestructura y lógica documentada para futuras consultas y desarrollos.

---

**Autor:** Equipo de desarrollo FastAPI-Odoo · Espasiko · 27/06/2025
