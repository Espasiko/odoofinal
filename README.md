# Manusodoo-Roto

Sistema integrado de gestión de productos, proveedores y facturas con OCR para Odoo 18.

## Descripción

Manusodoo-Roto es una solución completa para la gestión de productos y facturas en Odoo 18, con un enfoque especial en la importación masiva de datos desde Excel y el procesamiento OCR de facturas. El sistema consta de un backend en FastAPI que se integra con Odoo y un frontend en React para una experiencia de usuario moderna.

## Características Principales

- **Importación Masiva de Excel**: Carga de productos y proveedores desde archivos Excel con procesamiento por chunks
- **OCR de Facturas**: Extracción automática de datos de facturas mediante Mistral AI
- **Caché OCR**: Sistema de caché para evitar reprocesamiento de facturas idénticas
- **Prompts Específicos por Proveedor**: Mejora de precisión OCR con prompts adaptados a cada proveedor
- **Validación Robusta**: Verificación de NIF/CIF, precios, códigos de barras y otros datos críticos
- **Interfaz Moderna**: Frontend en React con componentes interactivos y feedback visual
- **Despliegue Sencillo**: Configuración completa con Docker Compose

## Arquitectura

### Backend (FastAPI)
- **Rutas**: API REST para productos, proveedores, OCR y facturas
- **Servicios**: Lógica de negocio modular y reutilizable
- **Integración Odoo**: Comunicación directa con la API de Odoo 18
- **Procesamiento OCR**: Extracción y mejora de datos con Mistral AI

### Frontend (React)
- **Componentes**: Interfaz de usuario modular y reutilizable
- **Hooks**: Lógica de negocio encapsulada en hooks personalizados
- **Contexto**: Gestión de estado global con React Context
- **Servicios**: Comunicación con la API del backend

## Requisitos

- Docker y Docker Compose
- Acceso a Internet (para APIs externas como Mistral AI)
- Navegador moderno (Chrome, Firefox, Edge)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/manusodoo-roto.git
cd manusodoo-roto
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales y configuración
```

3. Iniciar los servicios:
```bash
docker-compose up -d
```

4. Acceder a las aplicaciones:
- Odoo: http://localhost:8069
- Adminer: http://localhost:8080
- FastAPI: http://localhost:8000
- Frontend: http://localhost:3001

## Uso

### Importación de Productos desde Excel

1. Preparar el archivo Excel con el formato adecuado
2. Acceder a la sección "Importar Excel" en el frontend
3. Seleccionar el archivo y configurar opciones de importación
4. Iniciar la importación y monitorear el progreso

### Procesamiento OCR de Facturas

1. Acceder a la sección "Importar Factura" en el frontend
2. Subir la imagen o PDF de la factura
3. Verificar y corregir los datos extraídos
4. Confirmar para crear la factura en Odoo

## Scripts de Utilidad

- `formatea_excel_nevir.py`: Formatea archivos Excel de NEVIR al formato estándar
- `test_nevir_import.py`: Prueba la importación de productos NEVIR a Odoo
- `verify_nevir_database.py`: Verifica la integridad de la base de datos

## Estructura del Proyecto

```
manusodoo-roto/
├── api/                    # Backend FastAPI
│   ├── routes/             # Endpoints de la API
│   └── services/           # Servicios y lógica de negocio
├── src/                    # Frontend React
│   ├── components/         # Componentes reutilizables
│   ├── hooks/              # Hooks personalizados
│   ├── pages/              # Páginas de la aplicación
│   └── services/           # Servicios para API
├── config/                 # Configuración de Odoo
├── docs/                   # Documentación
├── docker-compose.yml      # Configuración de servicios
├── Dockerfile.fastapi      # Configuración del backend
├── main.py                 # Punto de entrada del backend
├── requirements.txt        # Dependencias Python
└── vite.config.ts          # Configuración del frontend
```

## Documentación Adicional

Para más información, consulta los siguientes documentos:

- [Estado del Proyecto](./docs/16_07_estado.md)
- [Guía de Optimización OCR](./docs/mistral_ocr_guia_optimizacion.md)

## Licencia

Este proyecto es propiedad de su autor y no está disponible para uso público sin autorización explícita.

## Contacto

Para cualquier consulta o soporte, contactar al administrador del sistema.