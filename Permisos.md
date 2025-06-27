# Permisos y sincronización de archivos en el entorno Docker

## 1. ¿El script `start.sh` arranca bien los servicios?
- El script `start.sh`:
  - Verifica que Docker y Docker Compose estén instalados y corriendo.
  - Detiene cualquier contenedor previo para evitar conflictos.
  - Lanza los servicios en este orden: primero la base de datos, luego Odoo, Adminer y FastAPI.
  - Espera activamente a que cada servicio esté disponible (incluyendo comprobación HTTP para Odoo y FastAPI).
  - Instala dependencias Python y Node.js si faltan.
  - Puede lanzar el frontend si se le pasa `--with-frontend`.
  - Muestra el estado final y puertos de todos los servicios.
- **Resultado:** El script es robusto y sí arranca bien los servicios, según el log y el resultado de `docker-compose ps` (todos los contenedores relevantes están "Up" y escuchando en los puertos correctos).

## 2. ¿Configuración del shell y Docker en los contenedores es igual?
- El script `start.sh` y la configuración de Docker Compose están alineados:
  - Los puertos expuestos y los nombres de servicios son coherentes.
  - FastAPI arranca con `uvicorn main:app --reload --host 0.0.0.0 --port 8000` tanto en shell como en Docker.
  - Odoo escucha en `8069`, Adminer en `8080`, DB en `5432` (interno) y `5434` (externo).
  - Las variables de entorno, especialmente `ODOO_URL`, están correctamente pasadas a FastAPI desde Docker Compose.
  - **No hay diferencias críticas** entre cómo se arrancan los servicios desde shell y desde Docker. Si necesitas lanzar algo manualmente en shell, usa los mismos comandos y variables que ves en el compose y en el script.
  - Si hubiera alguna diferencia menor, la referencia correcta es la de Docker Compose (la que ya está funcionando).

## 3. ¿Tienes herramientas y permisos para escribir en los contenedores y que los cambios se reflejen sin reconstruir?
- **Volúmenes y sincronización:**
  - El código fuente está montado como volumen en el contenedor FastAPI (y probablemente en Odoo si tienes addons personalizados).
  - Cualquier cambio en los archivos del host se refleja automáticamente en el contenedor al reiniciar el servicio (`docker-compose restart fastapi` o similar), sin necesidad de reconstruir la imagen.
- **Permisos:**
  - Tienes permisos de escritura en los archivos del proyecto y puedes ejecutar scripts (`start.sh`, `stop.sh`, etc.).
  - Los contenedores están corriendo con los volúmenes correctos, así que puedes modificar código, reiniciar el servicio y ver los cambios al instante.
- **Herramientas:**
  - Tienes acceso a Docker, Docker Compose, bash/zsh, y las utilidades necesarias para desarrollo y admin (curl, npm, pip, etc.) tanto en el host como en los contenedores.
  - Puedes entrar a cualquier contenedor con `docker-compose exec <servicio> bash` y editar/ver archivos.

---

### Resumen
- ✅ El script `start.sh` arranca correctamente todos los servicios y verifica su estado.
- ✅ La configuración de shell y Docker está alineada; la referencia válida es la de Docker Compose.
- ✅ Tienes permisos y herramientas para editar archivos y que los cambios se reflejen tras reiniciar el contenedor, sin reconstruir.
- ✅ Esto aplica a todos los contenedores relevantes (FastAPI, Odoo, DB, Adminer).

---

**Actualizado: 25-06-2025.**
