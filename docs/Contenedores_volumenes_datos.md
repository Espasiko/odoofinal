# Documentación de Contenedores y Volúmenes

## 📦 Contenedores en Uso

### 1. Base de Datos (PostgreSQL)
- **Nombre del servicio**: `db`
- **Imagen**: `postgres:13`
- **Puerto**: 5432
- **Variables de entorno**:
  - `POSTGRES_DB`: odoo
  - `POSTGRES_USER`: odoo
  - `POSTGRES_PASSWORD`: odoo
- **Volumenes**:
  - `manusodoo-roto_odoo-db-data` → `/var/lib/postgresql/data/pgdata`

### 2. Odoo
- **Nombre del servicio**: `odoo`
- **Imagen**: `odoo:15.0`
- **Puertos**:
  - 8069 (web interface)
  - 8071-8072 (longpolling)
- **Volúmenes**:
  - `manusodoo-roto_odoo-web-data` → `/var/lib/odoo`
  - `./config` → `/etc/odoo`
  - `./addons` → `/mnt/extra-addons`

### 3. Adminer
- **Nombre del servicio**: `adminer`
- **Imagen**: `adminer`
- **Puerto**: 8080

### 4. FastAPI
- **Nombre del servicio**: `fastapi`
- **Puerto**: 8000
- **Volúmenes**:
  - `./api` → `/app`

## 💾 Volúmenes

### Volúmenes Nombrados
1. **manusodoo-roto_odoo-db-data**
   - **Propósito**: Almacena la base de datos de PostgreSQL
   - **Ubicación Host**: `/var/lib/docker/volumes/manusodoo-roto_odoo-db-data`
   - **Importancia**: Crítico - Contiene todos los datos de la aplicación

2. **manusodoo-roto_odoo-web-data**
   - **Propósito**: Almacena datos de sesiones y archivos subidos de Odoo
   - **Ubicación Host**: `/var/lib/docker/volumes/manusodoo-roto_odoo-web-data`
   - **Importancia**: Importante - Contiene archivos subidos y datos de sesión

### Volúmenes Bind Mount
1. **Configuración de Odoo**
   - **Host**: `./config`
   - **Contenedor**: `/etc/odoo`
   - **Contenido**: Archivos de configuración de Odoo

2. **Addons personalizados**
   - **Host**: `./addons`
   - **Contenedor**: `/mnt/extra-addons`
   - **Contenido**: Módulos personalizados de Odoo

3. **Código FastAPI**
   - **Host**: `./api`
   - **Contenedor**: `/app`
   - **Contenido**: Código fuente de la API

## 🌐 Redes
- **Nombre**: `manusodoo-roto_default`
- **Tipo**: bridge
- **Subred**: 172.18.0.0/16
- **Gateway**: 172.18.0.1

## 🔒 Consideraciones de Seguridad
1. **Puertos expuestos**:
   - 5432 (PostgreSQL) - Expuesto solo localmente
   - 8069 (Odoo) - Acceso web
   - 8080 (Adminer) - Interfaz de administración de base de datos
   - 8000 (FastAPI) - API REST

2. **Credenciales por defecto**:
   - PostgreSQL: odoo/odoo
   - Odoo: admin/admin
   - Adminer: Sin autenticación (solo acceso local)

## 🔄 Comandos Útiles

### Ver logs de contenedores
```bash
docker-compose logs -f [servicio]
```

### Hacer backup de volúmenes
```bash
docker run --rm -v manusodoo-roto_odoo-db-data:/source -v $(pwd):/backup alpine tar czf /backup/db-backup-$(date +%Y%m%d).tar.gz -C /source .
```

### Restaurar base de datos
1. Detener los contenedores
2. Restaurar el backup
3. Iniciar los contenedores

## ⚠️ Advertencias
1. Nunca ejecutar comandos que eliminen volúmenes sin hacer backup
2. Verificar siempre las rutas de montaje antes de ejecutar contenedores
3. Mantener copias de seguridad periódicas de los volúmenes críticos
