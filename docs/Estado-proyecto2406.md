# Descripción Completa del Proyecto: Ecosistema de Gestión Odoo con IA

## 1. Visión General del Proyecto

Este proyecto es un ecosistema de software avanzado y multifacético diseñado para automatizar y optimizar la gestión de datos empresariales, centrándose en dos áreas críticas: el **procesamiento inteligente de facturas de proveedores** y la **importación masiva de catálogos de productos**.

La arquitectura combina la robustez del ERP **Odoo 18** como sistema central de registro, con la flexibilidad de un middleware **FastAPI** que orquesta servicios de Inteligencia Artificial de última generación y una interfaz de usuario moderna construida en **React/Refine**. El sistema está completamente orquestado con **Docker**, garantizando un despliegue y mantenimiento consistentes.

El proyecto se divide en dos flujos de trabajo principales y altamente especializados:

1.  **Flujo de OCR de Facturas:** Un sistema de vanguardia que utiliza la **API de Mistral AI** para leer, entender y registrar automáticamente facturas de proveedores en Odoo, eliminando la entrada manual de datos.
2.  **Flujo de Mapeo de Productos:** Una herramienta auxiliar, pero potente, que utiliza heurísticas y procesamiento de lenguaje natural clásico para convertir catálogos de productos de proveedores (en formato Excel/CSV) a un formato compatible para la importación en Odoo.

## 2. Arquitectura Tecnológica y Componentes

El sistema se compone de varias aplicaciones y servicios interconectados, cada uno con un propósito específico.

| Componente | Tecnología | Puerto | Rol Principal |
| :--- | :--- | :--- | :--- |
| **ERP Central** | Odoo 18 | `8069` | Sistema de registro, gestión de negocio. |
| **Base de Datos** | PostgreSQL 15 | `5432` | Almacenamiento de datos para Odoo. |
| **API Gateway** | FastAPI | `8000` | Middleware, orquestador de servicios, API REST. |
| **UI Principal** | React / Refine | `3001` | Interfaz de usuario para gestión general. |
| **UI Mapeo Productos** | Flask | `5000` | Herramienta auxiliar para conversión de catálogos. |
| **Gestor de Base de Datos** | Adminer | `8080` | Interfaz web para gestionar PostgreSQL. |

## 3. Estructura del Proyecto

A continuación se muestra la estructura de directorios más relevante del proyecto, que refleja la separación de responsabilidades entre el backend, el frontend, los scripts y la configuración.

```
/home/espasiko/mainmanusodoo/manusodoo-roto/
├── api/                   # Directorio principal del backend FastAPI
│   ├── routes/            # Endpoints de la API (OCR, productos, proveedores)
│   │   ├── mistral_ocr.py
│   │   ├── ocr.py
│   │   └── products.py
│   ├── services/          # Lógica de negocio (conexión Odoo, servicio Mistral)
│   │   ├── mistral_ocr_service.py
│   │   └── odoo_service.py
│   └── main.py            # Punto de entrada de la aplicación FastAPI
│
├── src/                   # Código fuente del Frontend (React/Vite)
│   ├── components/
│   ├── pages/
│   └── main.tsx           # Punto de entrada del Frontend
│
├── addons/                # Módulos personalizados de Odoo
│
├── docs/                  # Documentación del proyecto
│   ├── Estado-proyecto2406.md
│   └── OCR-Mistral.md
│
├── scripts/               # Scripts de utilidad para manipulación de datos
│   ├── normalize_supplier_data.py
│   └── reassign_all_category_products_with_brands.py
│
├── app_mapeo.py           # Aplicación auxiliar de mapeo de productos (Flask)
├── ia_mapeo.py            # Lógica de mapeo con IA para la app Flask
│
├── docker-compose.yml     # Orquestación de servicios (Odoo, FastAPI, DB)
├── Dockerfile.fastapi     # Definición del contenedor para la API
├── odoo.conf              # Configuración de Odoo
├── requirements.txt       # Dependencias de Python para FastAPI y scripts
└── package.json           # Dependencias y scripts del Frontend (Node.js)
```

## 4. Componentes Detallados

### 4.1. Odoo 18 (ERP Central)

- **Función:** Corazón del sistema. Almacena todos los datos maestros (productos, proveedores, clientes) y transaccionales (facturas, pedidos, inventario).
- **Acceso:** `http://localhost:8069`
- **Credenciales:** `yo@mail.com` / `admin`

### 4.2. FastAPI (API Gateway y Servicios)

- **Función:** Actúa como un intermediario inteligente. Expone una API RESTful que el frontend consume y contiene la lógica para comunicarse con Odoo (vía XML-RPC) y con servicios externos como Mistral AI.
- **Endpoints Clave:**
    - `/api/v1/mistral/invoice`: Procesa una factura utilizando Mistral OCR y la extrae en formato JSON.
    - `/api/v1/products`: Obtiene la lista de productos desde Odoo.
    - `/api/v1/providers`: Obtiene la lista de proveedores.
- **Acceso:** `http://localhost:8000/docs` para la documentación interactiva de Swagger UI.

### 4.3. React/Refine (Frontend Principal)

- **Función:** La cara visible del sistema. Proporciona una interfaz de usuario moderna y reactiva para interactuar con los datos de Odoo a través de la API de FastAPI. Permite visualizar, crear y editar registros sin necesidad de acceder directamente a Odoo.
- **Acceso:** `http://localhost:3001`

### 4.4. Flask (Herramienta de Mapeo de Productos)

- **Función:** Una aplicación web independiente y especializada para resolver el problema de la importación de catálogos. Permite al usuario subir un archivo Excel/CSV de un proveedor, analiza su estructura y lo convierte a un formato CSV estandarizado, listo para ser importado en Odoo.
- **Acceso:** `http://localhost:5000`

### 4.5. Integración con Mistral AI

- **Servicio:** `mistral_ocr_service.py`
- **Endpoint:** `/api/routes/mistral_ocr.py`
- **Funcionamiento:**
    1.  Se sube un documento (PDF, imagen) al endpoint de FastAPI.
    2.  El servicio lo envía a la API de Mistral AI, que realiza el OCR y devuelve el texto.
    3.  Un segundo modelo de Mistral (`mistral-large-latest`) procesa ese texto para extraer información estructurada (NIF, total, líneas de factura) en formato JSON.
    4.  El resultado se devuelve al usuario y puede ser utilizado para crear registros en Odoo.
- **Requisito Clave:** Necesita una variable de entorno `MISTRAL_API_KEY` para funcionar.

## 5. Guía de Inicio Rápido

Esta guía te permitirá levantar todo el ecosistema de desarrollo en tu máquina local.

### 5.1. Prerrequisitos

- **Docker y Docker Compose:** Para orquestar los contenedores.
- **Node.js y npm:** Para ejecutar el frontend de React.
- **Python 3:** Para ejecutar la aplicación de Flask y otros scripts.

### 5.2. Configuración del Entorno

1.  **Crear archivo .env**: Si no existe, crea un archivo `.env` en la raíz del proyecto copiando el ejemplo.
    ```bash
    cp .env.example .env
    ```
    Este archivo es ignorado por Git para proteger tus claves secretas. El `docker-compose.yml` lo utiliza para cargar variables de entorno en los servicios, como la clave de API de Mistral para el contenedor de FastAPI.

    **Importante:** Asegúrate de que la línea `MISTRAL_API_KEY=${MISTRAL_API_KEY}` esté presente en la sección de entorno del servicio `fastapi` dentro de tu `docker-compose.yml` para que la variable se propague correctamente al contenedor.

2.  **Añadir API Key de Mistral**: Abre el archivo `.env` y añade tu clave de API de Mistral AI. El servicio de OCR no funcionará sin ella.
    ```
    MISTRAL_API_KEY="tu_api_key_secreta_de_mistral"
    ```

### 5.3. Comandos de Inicio

Abre varias terminales o utiliza un gestor de terminales como `tmux` para ejecutar los servicios.

**Terminal 1: Servicios Docker (Odoo, FastAPI, DB, Adminer)**

```bash
# Desde la raíz del proyecto
docker-compose up -d
```
Este comando descargará las imágenes necesarias y levantará los contenedores en segundo plano.

**Terminal 2: Interfaz de Usuario Principal (React/Refine)**

```bash
# Desde la raíz del proyecto, donde se encuentra package.json
npm install
npm start
```
Esto instalará las dependencias de Node.js (la primera vez) y arrancará el servidor de desarrollo de React.

**Terminal 3: Herramienta de Mapeo de Productos (Flask)**

```bash
# Desde la raíz del proyecto
# Es recomendable instalar las dependencias si no lo has hecho
# pip install Flask pandas openpyxl matplotlib
python3 app_mapeo.py
```
Esto iniciará la aplicación auxiliar de Flask.

### 5.4. Tabla de Acceso y Credenciales

Una vez que todos los servicios estén en ejecución, puedes acceder a ellos a través de las siguientes URLs. Las credenciales son las definidas en tu `docker-compose.yml` y la memoria del proyecto.

| Servicio | URL de Acceso | Credenciales / Notas |
| :--- | :--- | :--- |
| **Odoo Web** | `http://localhost:8069` | **Usuario:** `yo@mail.com` <br> **Contraseña:** `admin` |
| **API Gateway (FastAPI)** | `http://localhost:8000/docs` | Accede a la documentación interactiva de la API. |
| **UI Principal (React)** | `http://localhost:3001` | Interfaz de usuario principal. |
| **UI Mapeo Productos** | `http://localhost:5000` | Herramienta para convertir catálogos. |
| **Adminer (Gestor DB)** | `http://localhost:8080` | **Sistema:** `PostgreSQL` <br> **Servidor:** `db` <br> **Usuario:** `odoo` <br> **Contraseña:** `odoo` <br> **Base de datos:** `postgres` o `manus_odoo-bd` |
