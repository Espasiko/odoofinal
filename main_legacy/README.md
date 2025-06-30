# ManusOdoo - Sistema de Gestión Empresarial

## 📋 Descripción

ManusOdoo es un sistema completo de gestión empresarial basado en Odoo 18.0 con un dashboard personalizado desarrollado en React. El sistema está diseñado para "El Pelotazo", proporcionando funcionalidades de e-commerce, gestión de inventario, ventas, clientes y reportes.

## 🔄 Sistema de Mapeo de Datos de Proveedores

El sistema incluye un conjunto de herramientas para automatizar el proceso de mapeo y conversión de datos de proveedores (en formatos CSV y Excel) al formato requerido por Odoo, utilizando técnicas de inteligencia artificial para mejorar la calidad de los datos.

## 🏗️ Arquitectura del Sistema

### Backend - Odoo 18.0
- **Base de datos**: PostgreSQL 15
- **Puerto**: 8069
- **Empresa**: El Pelotazo
- **Base de datos**: pelotazo
- **Idioma**: Español (España)
- **Moneda**: EUR

### Frontend - Dashboard React
- **Framework**: React + TypeScript
- **UI Library**: Ant Design
- **Herramientas**: Vite, Refine
- **Puerto**: 5173 (desarrollo)
- **Conexión**: API REST con Odoo

### Infraestructura
- **Contenedores**: Docker + Docker Compose
- **Volúmenes persistentes**: Datos de Odoo y PostgreSQL
- **Red**: Comunicación interna entre contenedores

## 🚀 Instalación Rápida

### Prerrequisitos
- Docker y Docker Compose
- Git
- Node.js 18+ (para desarrollo del dashboard)

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/manusodoo.git
cd manusodoo
```

### 2. Instalación automática
```bash
./install.sh
```

Este script:
- Instala Docker y Docker Compose (si no están instalados)
- Instala Node.js y npm
- Configura el entorno

## 🛠️ Sistema de Mapeo de Datos de Proveedores

### Características principales

- **Detección automática de proveedores**: Identifica automáticamente el proveedor basándose en el nombre del archivo y su estructura.
- **Extracción inteligente de atributos**: Extrae atributos como marca, medidas, capacidad, etc. de los nombres de productos.
- **Inferencia de categorías**: Sugiere categorías para productos basándose en su nombre y características.
- **Normalización de nombres**: Estandariza los nombres de productos para mejorar la consistencia.
- **Detección de duplicados**: Identifica posibles productos duplicados basándose en la similitud de nombres.
- **Generación de informes**: Crea informes comparativos con estadísticas y métricas de calidad de datos.
- **Conversión a formato Odoo**: Genera archivos CSV compatibles con la importación de Odoo.

### Estructura del sistema

```
/manusodoo/last/
├── menu_principal.py         # Interfaz principal del sistema
├── convertidor_proveedores.py # Convertidor básico de archivos
├── ia_mapeo.py               # Funciones de IA para mejorar el mapeo
├── analizar_proveedor.py     # Analizador de archivos individuales
├── informe_proveedores.py    # Generador de informes comparativos
├── procesar_lote.py          # Procesador de lotes de archivos
├── demo_convertidor.py       # Demostración interactiva
├── ejemplos/                 # Directorio con archivos de ejemplo
├── odoo_import/              # Directorio para archivos de salida
└── informes/                 # Directorio para informes generados
```

### Uso del Sistema de Mapeo

#### Menú Principal

Ejecute el script `menu_principal.py` para acceder a todas las funcionalidades del sistema:

```bash
python menu_principal.py
```

Desde el menú principal puede:

1. **Analizar archivo individual**: Examina un archivo específico y muestra información detallada.
2. **Procesar lote de archivos**: Convierte múltiples archivos a formato Odoo.
3. **Generar informe comparativo**: Crea un informe HTML con estadísticas de todos los proveedores.
4. **Convertir archivo a formato Odoo**: Transforma un archivo específico al formato de importación de Odoo.
5. **Demostración interactiva**: Muestra el funcionamiento del sistema con ejemplos.
6. **Configuración**: Permite modificar los directorios de trabajo.

#### Uso individual de scripts

También puede ejecutar cada script de forma independiente:

```bash
# Analizar un archivo específico
python analizar_proveedor.py /ruta/al/archivo.xlsx

# Procesar un lote de archivos
python procesar_lote.py

# Generar informe comparativo
python informe_proveedores.py

# Convertir un archivo específico
python convertidor_proveedores.py /ruta/al/archivo.xlsx -o /directorio/salida
```

### Proveedores soportados

El sistema está configurado para detectar y procesar archivos de los siguientes proveedores:

- BSH
- CECOTEC
- ALMCE
- BECKEN
- TEGALUXE
- JOHNSON
- ELECTRODIRECTO
- JATA
- MIELECTRO
- NEVIR
- ORBEGOZO
- UFESA
- VITROKITCHEN

### Personalización

Para adaptar el sistema a sus necesidades específicas, puede modificar:

- **Patrones de detección**: En `convertidor_proveedores.py` para reconocer nuevos proveedores.
- **Mapeo de columnas**: En `convertidor_proveedores.py` para ajustar la correspondencia entre columnas.
- **Patrones de productos**: En `ia_mapeo.py` para mejorar la extracción de atributos.
- **Categorías**: En `ia_mapeo.py` para actualizar las categorías y palabras clave.
- Construye e inicia los contenedores
- Instala dependencias del dashboard

### 3. Iniciar el sistema
```bash
./start.sh
```

### 4. Acceder al sistema
- **Odoo Backend**: http://localhost:8069
- **Dashboard**: http://localhost:5173 (en desarrollo)

## 📁 Estructura del Proyecto

```
manusodoo/
├── 📄 README.md                 # Este archivo
├── 📄 docker-compose.yml        # Configuración de contenedores
├── 📄 package.json             # Dependencias del dashboard
├── 📄 vite.config.ts           # Configuración de Vite
├── 📄 tsconfig.json            # Configuración TypeScript
├── 📄 .gitignore               # Archivos ignorados por Git
├── 📄 .env.example             # Variables de entorno ejemplo
│
├── 🔧 Scripts de gestión
│   ├── install.sh              # Instalación completa
│   ├── start.sh                # Iniciar servicios
│   ├── stop.sh                 # Detener servicios
│   ├── dev-dashboard.sh        # Desarrollo del dashboard
│   └── backup.sh               # Crear backups
│
├── 📂 src/                     # Código fuente del dashboard
│   ├── components/             # Componentes React
│   ├── pages/                  # Páginas del dashboard
│   ├── services/               # Servicios API
│   ├── types/                  # Tipos TypeScript
│   └── utils/                  # Utilidades
│
├── 📂 config/                  # Configuraciones
│   └── odoo.conf.example       # Configuración Odoo ejemplo
│
├── 📂 plantillasodoo/          # Plantillas y datos
│   ├── productos_ejemplo.xlsx  # Plantilla productos
│   ├── clientes_ejemplo.csv    # Plantilla clientes
│   └── inventario_ejemplo.xls  # Plantilla inventario
│
└── 📂 backups/                 # Backups automáticos
    ├── proyecto_YYYYMMDD.tar.gz
    ├── database_YYYYMMDD.sql.gz
    └── volumes_YYYYMMDD.tar.gz
```

## 🛠️ Scripts de Gestión

### `./install.sh`
Instalación completa del sistema:
- Verifica e instala dependencias
- Configura Docker y Node.js
- Construye contenedores
- Inicializa la base de datos
- Instala módulos de Odoo

### `./start.sh`
Inicia todos los servicios:
- Levanta contenedores Docker
- Verifica conectividad
- Muestra estado del sistema
- Proporciona URLs de acceso

### `./stop.sh`
Detiene el sistema de forma segura:
- Para contenedores Docker
- Preserva datos en volúmenes
- Muestra estado final

### `./dev-dashboard.sh`
Modo desarrollo del dashboard:
- Verifica conexión con Odoo
- Instala dependencias npm
- Inicia servidor de desarrollo
- Hot reload automático

### `./backup.sh`
Crea backups completos:
- Backup del código fuente
- Backup de la base de datos
- Backup de volúmenes Docker
- Compresión automática

## 🔧 Configuración

### Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```bash
# Configuración Odoo
ODOO_DB_HOST=db
ODOO_DB_PORT=5432
ODOO_DB_USER=odoo
ODOO_DB_PASSWORD=odoo
ODOO_DB_NAME=manus_odoo-bd

# Configuración Dashboard
VITE_ODOO_URL=http://localhost:8070
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=ManusOdoo Dashboard
VITE_COMPANY_NAME=El Pelotazo
```

### Configuración de Odoo

La configuración principal está en `config/odoo.conf`:

```ini
[options]
addons_path = /mnt/extra-addons
data_dir = /var/lib/odoo
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
logfile = /var/log/odoo/odoo.log
log_level = info
```

## 📊 Módulos de Odoo Instalados

### Módulos Base
- **account**: Contabilidad
- **sale**: Ventas
- **purchase**: Compras
- **stock**: Inventario
- **point_of_sale**: Punto de venta
- **website**: Sitio web
- **website_sale**: E-commerce

### Módulos de Gestión
- **crm**: CRM
- **project**: Gestión de proyectos
- **hr**: Recursos humanos
- **fleet**: Gestión de flota
- **maintenance**: Mantenimiento

### Módulos de Reportes
- **account_reports**: Reportes contables
- **sale_management**: Gestión de ventas
- **stock_account**: Contabilidad de inventario

## 🎨 Dashboard Features

### Páginas Principales
1. **Dashboard**: Resumen ejecutivo con KPIs
2. **Productos**: Gestión de catálogo
3. **Inventario**: Control de stock
4. **Ventas**: Gestión de pedidos
5. **Clientes**: CRM básico
6. **Reportes**: Análisis y estadísticas

### Funcionalidades
- 📊 Gráficos interactivos
- 📱 Diseño responsive
- 🔄 Sincronización en tiempo real
- 🎯 Filtros avanzados
- 📈 KPIs personalizables
- 🌙 Modo oscuro

## 🔄 Desarrollo

### Desarrollo del Dashboard

```bash
# Modo desarrollo
./dev-dashboard.sh

# O manualmente:
npm install
npm run dev
```

### Estructura de Desarrollo

```bash
src/
├── components/
│   ├── Dashboard/
│   ├── Products/
│   ├── Inventory/
│   ├── Sales/
│   ├── Customers/
│   └── Reports/
├── services/
│   ├── odooService.ts
│   ├── apiClient.ts
│   └── authService.ts
├── types/
│   ├── odoo.ts
│   ├── dashboard.ts
│   └── api.ts
└── utils/
    ├── formatters.ts
    ├── validators.ts
    └── constants.ts
```

### API de Odoo

El dashboard se conecta a Odoo mediante:
- **XML-RPC**: Para operaciones CRUD
- **REST API**: Para consultas rápidas
- **WebSocket**: Para actualizaciones en tiempo real

## 📦 Backups y Restauración

### Crear Backup
```bash
./backup.sh
```

Esto crea:
- `manusodoo_project_YYYYMMDD_HHMMSS.tar.gz`: Código fuente
- `manusodoo_database_YYYYMMDD_HHMMSS.sql.gz`: Base de datos
- `manusodoo_volumes_YYYYMMDD_HHMMSS.tar.gz`: Volúmenes Docker

### Restaurar desde Backup

```bash
# 1. Restaurar código
tar -xzf manusodoo_project_YYYYMMDD_HHMMSS.tar.gz

# 2. Restaurar base de datos
gunzip -c manusodoo_database_YYYYMMDD_HHMMSS.sql.gz | docker exec -i last_db_1 psql -U odoo

# 3. Iniciar sistema
./start.sh
```

## 🐛 Solución de Problemas

### Problemas Comunes

#### 1. Contenedores no inician
```bash
# Verificar logs
docker-compose logs

# Reiniciar servicios
./stop.sh
./start.sh
```

#### 2. Dashboard no conecta con Odoo
```bash
# Verificar que Odoo esté ejecutándose
curl http://localhost:8069

# Verificar configuración
cat .env
```

#### 3. Error de permisos
```bash
# Dar permisos a scripts
chmod +x *.sh

# Verificar permisos Docker
sudo usermod -aG docker $USER
```

#### 4. Puerto ocupado
```bash
# Verificar puertos en uso
sudo netstat -tlnp | grep :8069
sudo netstat -tlnp | grep :5173

# Cambiar puertos en docker-compose.yml si es necesario
```

### Logs del Sistema

```bash
# Logs de Odoo
docker logs last_odoo_1

# Logs de PostgreSQL
docker logs last_db_1

# Logs del dashboard
npm run dev # Muestra logs en consola
```

## 🔒 Seguridad

### Configuración de Producción

1. **Cambiar contraseñas por defecto**
2. **Configurar HTTPS**
3. **Restringir acceso a puertos**
4. **Configurar firewall**
5. **Backups automáticos**

### Variables Sensibles

Nunca subir al repositorio:
- Contraseñas de base de datos
- Claves API
- Certificados SSL
- Archivos de configuración con datos sensibles

## 📈 Roadmap

### Próximas Funcionalidades
- [ ] Módulos personalizados de Odoo
- [ ] Integración con APIs externas
- [ ] Dashboard móvil
- [ ] Reportes avanzados
- [ ] Automatización de procesos
- [ ] Integración con sistemas de pago
- [ ] OCR para facturas
- [ ] BI y Analytics

## 🤝 Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico:
- 📧 Email: soporte@elpelotazo.com
- 📱 Teléfono: +34 XXX XXX XXX
- 🌐 Web: https://elpelotazo.com

## 🙏 Agradecimientos

- **Odoo Community**: Por el excelente ERP
- **React Team**: Por el framework frontend
- **Ant Design**: Por los componentes UI
- **Docker**: Por la containerización

---

**ManusOdoo** - Sistema de Gestión Empresarial para El Pelotazo  
*Desarrollado con ❤️ y mucho ☕*
