# Proceso de Mapeo y Migración de CSV/Excel a Odoo con Campos Personalizados

## 1. Visión General del Proceso

El proceso de mapeo y migración de datos desde archivos CSV/Excel a Odoo es fundamental para aprovechar la información histórica de la tienda de electrodomésticos. Este documento detalla la metodología, herramientas y pasos necesarios para realizar una migración exitosa, considerando la estructura específica de los archivos proporcionados y los requisitos de campos personalizados en Odoo.

```
┌─────────────────┐     ┌─────────────────────────┐     ┌─────────────────┐
│                 │     │                         │     │                 │
│  Archivos       │     │  Middleware             │     │  Odoo           │
│  CSV/Excel      │────►│  (FastAPI)             │────►│  (Modelos       │
│                 │     │                         │     │   Extendidos)   │
└─────────────────┘     └─────────────────────────┘     └─────────────────┘
                              ▲
                              │
                              ▼
                        ┌─────────────┐
                        │             │
                        │  Proceso de │
                        │  Mapeo y    │
                        │  Validación │
                        │             │
                        └─────────────┘
```

## 2. Análisis de Archivos Fuente

### 2.1 Estructura Común Identificada

Tras analizar los archivos CSV proporcionados (CECOTEC, BSH, BECKEN-TEGALUXE, ALMCE), se han identificado las siguientes características comunes:

#### 2.1.1 Campos Principales
- **CÓDIGO**: Identificador único del producto
- **DESCRIPCIÓN**: Nombre y descripción del producto
- **UNID.**: Cantidad de unidades
- **IMPORTE BRUTO**: Precio de compra sin descuentos
- **DTO**: Descuento aplicado
- **TOTAL**: Importe tras descuento
- **IVA**: Impuesto aplicado (generalmente "IVA 21% + RECARGO 5,2%")
- **MARGEN**: Margen de beneficio aplicado
- **PVP WEB**: Precio de venta en web
- **P.V.P FINAL CLIENTE**: Precio final de venta
- **BENEFICIO UNITARIO**: Beneficio por unidad
- **BENEFICIO TOTAL**: Beneficio total
- **VENDIDAS**: Unidades vendidas
- **QUEDAN EN TIENDA**: Stock actual

#### 2.1.2 Estructura Organizativa
- Los archivos están organizados por categorías de productos
- Cada categoría tiene múltiples productos
- Existen filas vacías o de totales entre categorías
- Algunos archivos contienen notas o comentarios adicionales

#### 2.1.3 Particularidades y Variaciones
- Formatos de números y moneda inconsistentes entre archivos
- Algunas columnas pueden estar vacías en ciertos registros
- Existen diferencias en la nomenclatura de columnas entre archivos
- Algunos archivos incluyen información de marca/fabricante en la descripción

### 2.2 Mapeo a Modelos de Odoo

#### 2.2.1 Modelos Estándar Relevantes
- **product.template**: Para información general de productos
- **product.product**: Para variantes específicas
- **product.category**: Para categorías de productos
- **product.supplierinfo**: Para información de proveedores
- **stock.quant**: Para información de inventario
- **account.move**: Para facturas y movimientos contables

#### 2.2.2 Campos Personalizados Requeridos
Para capturar toda la información de los archivos CSV, se necesitan los siguientes campos personalizados:

**En product.template:**
```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    x_codigo_proveedor = fields.Char(string='Código de Proveedor')
    x_margen = fields.Float(string='Margen (%)')
    x_pvp_web = fields.Float(string='PVP Web')
    x_beneficio_unitario = fields.Float(string='Beneficio Unitario', compute='_compute_beneficio')
    x_marca = fields.Char(string='Marca')
    x_modelo = fields.Char(string='Modelo')
    x_historico_ventas = fields.Integer(string='Unidades Históricas Vendidas')
    x_notas_importacion = fields.Text(string='Notas de Importación')
    
    def _compute_beneficio(self):
        for record in self:
            record.x_beneficio_unitario = record.list_price - record.standard_price
```

**En product.category:**
```python
class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    x_codigo_categoria = fields.Char(string='Código de Categoría')
    x_margen_categoria = fields.Float(string='Margen de Categoría (%)')
```

**En product.supplierinfo:**
```python
class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'
    
    x_descuento_proveedor = fields.Float(string='Descuento Proveedor (%)')
    x_importe_bruto = fields.Float(string='Importe Bruto')
    x_importe_neto = fields.Float(string='Importe Neto')
```

## 3. Proceso de Migración

### 3.1 Arquitectura del Proceso

#### 3.1.1 Componentes Principales
- **Extractor de Datos**: Lee y normaliza los archivos CSV/Excel
- **Transformador**: Mapea y convierte los datos al formato de Odoo
- **Validador**: Verifica la integridad y coherencia de los datos
- **Cargador**: Inserta los datos en Odoo mediante la API
- **Registrador**: Mantiene un log detallado del proceso

#### 3.1.2 Flujo de Datos
1. Lectura de archivos fuente
2. Normalización y limpieza de datos
3. Transformación según mapeo definido
4. Validación de datos transformados
5. Carga en Odoo
6. Verificación post-carga
7. Generación de informe de resultados

### 3.2 Implementación del Proceso

#### 3.2.1 Servicio de Migración en FastAPI

```python
# Ejemplo conceptual del servicio de migración en FastAPI

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
import pandas as pd
import numpy as np
import logging
import json
import os
from typing import List, Dict, Any, Optional
import xmlrpc.client

# Configuración
ODOO_URL = "http://localhost:8070"
ODOO_DB = "manus_odoo-bd"
ODOO_USERNAME = "admin"
ODOO_PASSWORD = "admin_password_secure"

# Modelos
class MigrationResult(BaseModel):
    job_id: str
    status: str
    total_records: int
    processed_records: int
    failed_records: int
    log_url: Optional[str] = None

class MigrationStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str

# Servicio de migración
class MigrationService:
    def __init__(self):
        self.logger = logging.getLogger("migration")
        self.jobs = {}
    
    def connect_odoo(self):
        """Establece conexión con Odoo"""
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
        return models, uid
    
    def normalize_dataframe(self, df, provider):
        """Normaliza el DataFrame según el proveedor"""
        # Eliminar filas vacías
        df = df.dropna(how='all')
        
        # Normalizar nombres de columnas
        column_mapping = {
            'CÓDIGO': 'codigo',
            'DESCRIPCIÓN': 'descripcion',
            'UNID.': 'unidades',
            'IMPORTE BRUTO': 'importe_bruto',
            'DTO': 'descuento',
            'TOTAL': 'total',
            'IVA 21% + RECARGO 5,2%': 'iva',
            'MARGEN': 'margen',
            'PVP WEB': 'pvp_web',
            'P.V.P FINAL CLIENTE': 'pvp_final',
            'BENEFICIO UNITARIO': 'beneficio_unitario',
            'BENEFICIO TOTAL': 'beneficio_total',
            'VENDIDAS': 'vendidas',
            'QUEDAN EN TIENDA': 'stock'
        }
        
        # Ajustar según variaciones en los archivos
        if provider == 'CECOTEC':
            # Ajustes específicos para CECOTEC
            pass
        elif provider == 'BSH':
            # Ajustes específicos para BSH
            column_mapping['DTO. IMPLANTACION'] = 'descuento'
        elif provider == 'BECKEN':
            # Ajustes específicos para BECKEN
            pass
        elif provider == 'ALMCE':
            # Ajustes específicos para ALMCE
            pass
        
        # Renombrar columnas
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Convertir tipos de datos
        for col in ['importe_bruto', 'descuento', 'total', 'iva', 'margen', 
                   'pvp_web', 'pvp_final', 'beneficio_unitario', 'beneficio_total']:
            if col in df.columns:
                df[col] = self._convert_to_float(df[col])
        
        for col in ['unidades', 'vendidas', 'stock']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Añadir columna de proveedor
        df['proveedor'] = provider
        
        # Extraer categoría
        df['categoria'] = self._extract_category(df, provider)
        
        return df
    
    def _convert_to_float(self, series):
        """Convierte una serie a valores float, manejando diferentes formatos"""
        if series.dtype == 'object':
            # Limpiar strings y convertir a float
            return pd.to_numeric(
                series.astype(str)
                .str.replace('€', '')
                .str.replace(',', '.')
                .str.replace(' ', '')
                .str.strip(),
                errors='coerce'
            ).fillna(0)
        return series
    
    def _extract_category(self, df, provider):
        """Extrae la categoría de producto basada en la estructura del archivo"""
        # Implementación específica según el formato de cada proveedor
        # Esta es una versión simplificada
        categories = []
        current_category = "Sin categoría"
        
        for idx, row in df.iterrows():
            if pd.isna(row['codigo']) and not pd.isna(row['descripcion']):
                # Posible fila de categoría
                current_category = row['descripcion']
            categories.append(current_category)
        
        return pd.Series(categories)
    
    def transform_to_odoo(self, df):
        """Transforma los datos normalizados al formato de Odoo"""
        products = []
        categories = set()
        supplier_info = []
        
        # Procesar categorías
        for cat in df['categoria'].unique():
            if pd.notna(cat) and cat != "Sin categoría":
                categories.add(cat)
        
        # Procesar productos
        for idx, row in df.iterrows():
            if pd.isna(row['codigo']) or pd.isna(row['descripcion']):
                continue  # Saltar filas sin código o descripción
            
            # Extraer marca/modelo de la descripción
            marca, modelo = self._extract_brand_model(row['descripcion'], row['proveedor'])
            
            # Crear producto
            product = {
                'name': row['descripcion'],
                'default_code': row['codigo'],
                'type': 'product',  # Producto almacenable
                'categ_id': row['categoria'],
                'list_price': row['pvp_final'] if pd.notna(row['pvp_final']) else 0,
                'standard_price': row['importe_bruto'] if pd.notna(row['importe_bruto']) else 0,
                'x_codigo_proveedor': row['codigo'],
                'x_margen': row['margen'] if pd.notna(row['margen']) else 0,
                'x_pvp_web': row['pvp_web'] if pd.notna(row['pvp_web']) else 0,
                'x_marca': marca,
                'x_modelo': modelo,
                'x_historico_ventas': row['vendidas'] if pd.notna(row['vendidas']) else 0,
            }
            products.append(product)
            
            # Información de proveedor
            supplier = {
                'product_code': row['codigo'],
                'product_name': row['descripcion'],
                'min_qty': 1,
                'price': row['importe_bruto'] if pd.notna(row['importe_bruto']) else 0,
                'x_descuento_proveedor': row['descuento'] if pd.notna(row['descuento']) else 0,
                'x_importe_bruto': row['importe_bruto'] if pd.notna(row['importe_bruto']) else 0,
                'x_importe_neto': row['total'] if pd.notna(row['total']) else 0,
                'proveedor': row['proveedor']
            }
            supplier_info.append(supplier)
        
        return {
            'products': products,
            'categories': list(categories),
            'supplier_info': supplier_info
        }
    
    def _extract_brand_model(self, description, provider):
        """Extrae marca y modelo de la descripción"""
        # Implementación específica según el formato de cada proveedor
        # Esta es una versión simplificada
        if provider == 'BSH':
            # BSH incluye la marca entre paréntesis al inicio
            if '(' in description and ')' in description:
                marca = description.split('(')[1].split(')')[0]
                modelo = description.replace(f'({marca})', '').strip()
                return marca, modelo
        
        # Para otros proveedores o casos no específicos
        parts = description.split(' ')
        if len(parts) > 1:
            return parts[0], ' '.join(parts[1:])
        return provider, description
    
    def validate_data(self, data):
        """Valida los datos transformados"""
        errors = []
        warnings = []
        
        # Validar productos
        for i, product in enumerate(data['products']):
            # Verificar campos obligatorios
            if not product['name']:
                errors.append(f"Producto {i+1}: Falta nombre")
            
            if not product['default_code']:
                errors.append(f"Producto {i+1}: Falta código")
            
            # Verificar coherencia de precios
            if product['list_price'] < product['standard_price']:
                warnings.append(f"Producto {product['default_code']}: Precio de venta menor que costo")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def load_to_odoo(self, data, job_id):
        """Carga los datos en Odoo"""
        models, uid = self.connect_odoo()
        results = {
            'categories_created': 0,
            'products_created': 0,
            'supplier_info_created': 0,
            'errors': []
        }
        
        try:
            # 1. Crear/actualizar categorías
            category_ids = {}
            for category in data['categories']:
                # Buscar si ya existe
                category_id = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'product.category', 'search',
                    [[['name', '=', category]]]
                )
                
                if category_id:
                    category_ids[category] = category_id[0]
                else:
                    # Crear nueva categoría
                    new_id = models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        'product.category', 'create',
                        [{'name': category}]
                    )
                    category_ids[category] = new_id
                    results['categories_created'] += 1
                
                # Actualizar progreso
                self.update_job_status(job_id, 'processing', 
                                      f"Procesando categorías: {results['categories_created']}/{len(data['categories'])}")
            
            # 2. Crear/actualizar productos
            for i, product in enumerate(data['products']):
                # Obtener ID de categoría
                if product['categ_id'] in category_ids:
                    product['categ_id'] = category_ids[product['categ_id']]
                else:
                    # Categoría por defecto
                    product['categ_id'] = 1
                
                # Buscar si ya existe
                product_id = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'product.template', 'search',
                    [[['default_code', '=', product['default_code']]]]
                )
                
                if product_id:
                    # Actualizar producto existente
                    models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        'product.template', 'write',
                        [product_id, product]
                    )
                else:
                    # Crear nuevo producto
                    models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        'product.template', 'create',
                        [product]
                    )
                    results['products_created'] += 1
                
                # Actualizar progreso
                if i % 10 == 0:
                    self.update_job_status(job_id, 'processing', 
                                          f"Procesando productos: {i+1}/{len(data['products'])}")
            
            # 3. Crear/actualizar información de proveedores
            # Primero obtener todos los productos para mapear códigos a IDs
            product_templates = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'search_read',
                [[]], {'fields': ['id', 'default_code']}
            )
            product_map = {p['default_code']: p['id'] for p in product_templates if p['default_code']}
            
            # Obtener proveedores
            suppliers = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'res.partner', 'search_read',
                [[['supplier_rank', '>', 0]]], {'fields': ['id', 'name']}
            )
            supplier_map = {s['name']: s['id'] for s in suppliers}
            
            for i, supplier_info in enumerate(data['supplier_info']):
                if supplier_info['product_code'] not in product_map:
                    results['errors'].append(f"No se encontró producto con código {supplier_info['product_code']}")
                    continue
                
                product_tmpl_id = product_map[supplier_info['product_code']]
                
                # Buscar o crear proveedor
                supplier_name = supplier_info['proveedor']
                if supplier_name not in supplier_map:
                    # Crear nuevo proveedor
                    new_supplier_id = models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        'res.partner', 'create',
                        [{'name': supplier_name, 'supplier_rank': 1}]
                    )
                    supplier_map[supplier_name] = new_supplier_id
                
                supplier_id = supplier_map[supplier_name]
                
                # Preparar datos de supplierinfo
                supplierinfo_data = {
                    'product_tmpl_id': product_tmpl_id,
                    'name': supplier_id,
                    'product_code': supplier_info['product_code'],
                    'product_name': supplier_info['product_name'],
                    'min_qty': supplier_info['min_qty'],
                    'price': supplier_info['price'],
                    'x_descuento_proveedor': supplier_info['x_descuento_proveedor'],
                    'x_importe_bruto': supplier_info['x_importe_bruto'],
                    'x_importe_neto': supplier_info['x_importe_neto']
                }
                
                # Buscar si ya existe
                supplierinfo_id = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'product.supplierinfo', 'search',
                    [[
                        ['product_tmpl_id', '=', product_tmpl_id],
                        ['name', '=', supplier_id]
                    ]]
                )
                
                if supplierinfo_id:
                    # Actualizar existente
                    models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        'product.supplierinfo', 'write',
                        [supplierinfo_id, supplierinfo_data]
                    )
                else:
                    # Crear nuevo
                    models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        'product.supplierinfo', 'create',
                        [supplierinfo_data]
                    )
                    results['supplier_info_created'] += 1
                
                # Actualizar progreso
                if i % 10 == 0:
                    self.update_job_status(job_id, 'processing', 
                                          f"Procesando info de proveedores: {i+1}/{len(data['supplier_info'])}")
            
            # 4. Actualizar inventario
            # Implementación pendiente
            
            return results
            
        except Exception as e:
            self.logger.exception(f"Error al cargar datos en Odoo: {str(e)}")
            results['errors'].append(f"Error general: {str(e)}")
            return results
    
    def update_job_status(self, job_id, status, message, progress=None):
        """Actualiza el estado de un trabajo de migración"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = status
            self.jobs[job_id]['message'] = message
            if progress is not None:
                self.jobs[job_id]['progress'] = progress
    
    async def process_file(self, file_path, provider, job_id):
        """Procesa un archivo CSV/Excel y lo carga en Odoo"""
        try:
            # Inicializar job
            self.jobs[job_id] = {
                'status': 'starting',
                'message': 'Iniciando procesamiento',
                'progress': 0,
                'results': {}
            }
            
            # Leer archivo
            self.update_job_status(job_id, 'reading', 'Leyendo archivo', 5)
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Formato de archivo no soportado: {file_path}")
            
            # Normalizar datos
            self.update_job_status(job_id, 'normalizing', 'Normalizando datos', 20)
            normalized_df = self.normalize_dataframe(df, provider)
            
            # Transformar a formato Odoo
            self.update_job_status(job_id, 'transforming', 'Transformando datos', 40)
            transformed_data = self.transform_to_odoo(normalized_df)
            
            # Validar datos
            self.update_job_status(job_id, 'validating', 'Validando datos', 60)
            validation = self.validate_data(transformed_data)
            
            if not validation['valid']:
                self.update_job_status(job_id, 'error', 
                                      f"Errores de validación: {validation['errors']}", 100)
                self.jobs[job_id]['results'] = {
                    'success': False,
                    'errors': validation['errors'],
                    'warnings': validation['warnings']
                }
                return
            
            # Cargar en Odoo
            self.update_job_status(job_id, 'loading', 'Cargando datos en Odoo', 80)
            results = self.load_to_odoo(transformed_data, job_id)
            
            # Finalizar
            if results['errors']:
                self.update_job_status(job_id, 'completed_with_errors', 
                                      f"Completado con {len(results['errors'])} errores", 100)
            else:
                self.update_job_status(job_id, 'completed', 
                                      'Migración completada exitosamente', 100)
            
            self.jobs[job_id]['results'] = {
                'success': len(results['errors']) == 0,
                'categories_created': results['categories_created'],
                'products_created': results['products_created'],
                'supplier_info_created': results['supplier_info_created'],
                'errors': results['errors'],
                'warnings': validation['warnings']
            }
            
        except Exception as e:
            self.logger.exception(f"Error en proceso de migración: {str(e)}")
            self.update_job_status(job_id, 'error', f"Error: {str(e)}", 100)
            self.jobs[job_id]['results'] = {
                'success': False,
                'errors': [str(e)]
            }

# Endpoints FastAPI
app = FastAPI()
migration_service = MigrationService()

@app.post("/api/migration/upload", response_model=MigrationResult)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    provider: str = None
):
    """Endpoint para subir y procesar un archivo CSV/Excel"""
    if not provider:
        raise HTTPException(status_code=400, detail="Se requiere especificar el proveedor")
    
    # Validar proveedor
    valid_providers = ['CECOTEC', 'BSH', 'BECKEN', 'ALMCE']
    if provider not in valid_providers:
        raise HTTPException(
            status_code=400, 
            detail=f"Proveedor no válido. Opciones: {', '.join(valid_providers)}"
        )
    
    # Guardar archivo
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Generar ID de trabajo
    import uuid
    job_id = str(uuid.uuid4())
    
    # Iniciar procesamiento en segundo plano
    background_tasks.add_task(
        migration_service.process_file,
        file_path,
        provider,
        job_id
    )
    
    return MigrationResult(
        job_id=job_id,
        status="started",
        total_records=0,
        processed_records=0,
        failed_records=0,
        log_url=f"/api/migration/status/{job_id}"
    )

@app.get("/api/migration/status/{job_id}", response_model=MigrationStatus)
async def get_migration_status(job_id: str):
    """Obtiene el estado de un trabajo de migración"""
    if job_id not in migration_service.jobs:
        raise HTTPException(status_code=404, detail="Trabajo de migración no encontrado")
    
    job = migration_service.jobs[job_id]
    return MigrationStatus(
        job_id=job_id,
        status=job['status'],
        progress=job.get('progress', 0),
        message=job.get('message', '')
    )

@app.get("/api/migration/results/{job_id}")
async def get_migration_results(job_id: str):
    """Obtiene los resultados detallados de un trabajo de migración"""
    if job_id not in migration_service.jobs:
        raise HTTPException(status_code=404, detail="Trabajo de migración no encontrado")
    
    job = migration_service.jobs[job_id]
    if 'results' not in job:
        raise HTTPException(status_code=400, detail="Resultados aún no disponibles")
    
    return job['results']
```

#### 3.2.2 Interfaz de Usuario en Refine

Para facilitar el proceso de migración, se implementará una interfaz de usuario en el dashboard de Refine con las siguientes características:

1. **Formulario de carga**:
   - Selección de archivo CSV/Excel
   - Selección de proveedor
   - Opciones de configuración avanzada

2. **Monitorización de progreso**:
   - Barra de progreso
   - Estado actual del proceso
   - Mensajes informativos

3. **Visualización de resultados**:
   - Resumen de elementos creados/actualizados
   - Lista de errores y advertencias
   - Opciones para corregir problemas

4. **Historial de migraciones**:
   - Registro de migraciones anteriores
   - Estadísticas de éxito/error
   - Posibilidad de reintento

### 3.3 Validaciones y Reglas de Negocio

#### 3.3.1 Validaciones Básicas
- **Formato de datos**: Verificación de tipos y formatos
- **Campos obligatorios**: Comprobación de presencia de campos clave
- **Unicidad**: Detección de duplicados por código
- **Coherencia**: Verificación de relaciones entre campos

#### 3.3.2 Reglas de Negocio Específicas
- **Precios**: El precio de venta debe ser mayor que el costo
- **Márgenes**: Validación de márgenes mínimos por categoría
- **Stock**: No permitir valores negativos en inventario
- **Categorización**: Asignación automática a jerarquía de categorías

#### 3.3.3 Manejo de Excepciones
- **Datos faltantes**: Estrategias para campos no disponibles
- **Formatos inconsistentes**: Normalización de variaciones
- **Errores de carga**: Mecanismos de reintento y recuperación
- **Conflictos**: Resolución de conflictos en actualizaciones

## 4. Extensiones y Personalizaciones en Odoo

### 4.1 Módulo Personalizado para Importación

Para facilitar la integración con el middleware y la gestión de campos personalizados, se desarrollará un módulo específico en Odoo:

```python
# __manifest__.py
{
    'name': 'Electrodomésticos - Importación CSV/Excel',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Extensiones para importación de datos de electrodomésticos',
    'description': """
        Este módulo añade campos personalizados y funcionalidades para:
        - Importación de datos desde CSV/Excel
        - Gestión de información específica de proveedores
        - Seguimiento de histórico de ventas
        - Cálculo de márgenes y beneficios
    """,
    'author': 'Tu Empresa',
    'depends': ['base', 'product', 'stock', 'account'],
    'data': [
        'views/product_views.xml',
        'views/category_views.xml',
        'views/supplier_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
```

### 4.2 Vistas Personalizadas

Para visualizar y gestionar los campos personalizados, se crearán vistas específicas:

```xml
<!-- views/product_views.xml -->
<record id="product_template_form_view_import_extension" model="ir.ui.view">
    <field name="name">product.template.form.import.extension</field>
    <field name="model">product.template</field>
    <field name="inherit_id" ref="product.product_template_form_view"/>
    <field name="arch" type="xml">
        <xpath expr="//page[@name='general_information']" position="after">
            <page string="Información de Importación" name="import_info">
                <group>
                    <group>
                        <field name="x_codigo_proveedor"/>
                        <field name="x_marca"/>
                        <field name="x_modelo"/>
                    </group>
                    <group>
                        <field name="x_margen"/>
                        <field name="x_pvp_web"/>
                        <field name="x_beneficio_unitario"/>
                        <field name="x_historico_ventas"/>
                    </group>
                </group>
                <field name="x_notas_importacion"/>
            </page>
        </xpath>
    </field>
</record>
```

### 4.3 Reportes Personalizados

Para aprovechar la información importada, se crearán reportes específicos:

```xml
<!-- report/product_margin_report.xml -->
<record id="action_product_margin_report" model="ir.actions.act_window">
    <field name="name">Informe de Márgenes por Producto</field>
    <field name="res_model">product.template</field>
    <field name="view_mode">pivot,graph</field>
    <field name="context">{'search_default_filter_to_sell': True}</field>
    <field name="domain">[('x_margen', '>', 0)]</field>
</record>

<record id="product_margin_pivot_view" model="ir.ui.view">
    <field name="name">product.margin.pivot</field>
    <field name="model">product.template</field>
    <field name="arch" type="xml">
        <pivot string="Análisis de Márgenes">
            <field name="categ_id" type="row"/>
            <field name="x_marca" type="row"/>
            <field name="x_margen" type="measure"/>
            <field name="x_beneficio_unitario" type="measure"/>
            <field name="x_historico_ventas" type="measure"/>
        </pivot>
    </field>
</record>
```

## 5. Proceso de Migración Paso a Paso

### 5.1 Preparación

1. **Análisis de archivos**:
   - Revisar estructura y contenido de cada archivo CSV/Excel
   - Identificar particularidades y posibles problemas
   - Documentar mapeo de campos

2. **Configuración del entorno**:
   - Instalar módulo personalizado en Odoo
   - Configurar middleware FastAPI
   - Preparar entorno de pruebas

3. **Definición de reglas**:
   - Establecer criterios de validación
   - Definir estrategias para casos especiales
   - Documentar proceso de resolución de conflictos

### 5.2 Ejecución

1. **Migración por fases**:
   - Comenzar con categorías de productos
   - Continuar con productos base
   - Finalizar con información de proveedores e inventario

2. **Validación incremental**:
   - Verificar resultados después de cada fase
   - Corregir problemas antes de continuar
   - Documentar incidencias y soluciones

3. **Monitorización**:
   - Seguimiento de progreso en tiempo real
   - Detección temprana de errores
   - Ajuste de parámetros según necesidad

### 5.3 Verificación

1. **Comprobación de datos**:
   - Verificar integridad de datos migrados
   - Comparar totales y estadísticas
   - Validar relaciones entre entidades

2. **Pruebas funcionales**:
   - Comprobar operaciones de negocio con datos migrados
   - Verificar cálculos y reportes
   - Validar flujos de trabajo

3. **Correcciones finales**:
   - Ajustar inconsistencias detectadas
   - Completar datos faltantes
   - Optimizar configuraciones

## 6. Consideraciones Adicionales

### 6.1 Rendimiento

- **Procesamiento por lotes**: Migración en bloques para evitar sobrecarga
- **Optimización de consultas**: Minimizar llamadas a la API de Odoo
- **Caché inteligente**: Almacenamiento temporal de datos frecuentes
- **Monitorización de recursos**: Control de uso de memoria y CPU

### 6.2 Seguridad

- **Validación de entradas**: Prevención de inyecciones y ataques
- **Control de acceso**: Permisos específicos para operaciones de migración
- **Auditoría**: Registro detallado de todas las operaciones
- **Respaldo**: Copias de seguridad antes de migraciones masivas

### 6.3 Mantenimiento

- **Documentación**: Registro detallado del proceso y decisiones
- **Versionado**: Control de cambios en scripts y configuraciones
- **Automatización**: Programación de migraciones periódicas
- **Monitorización**: Alertas para detección temprana de problemas

## 7. Próximos Pasos

1. **Desarrollo del módulo Odoo**:
   - Implementación de modelos extendidos
   - Creación de vistas personalizadas
   - Configuración de reglas y permisos

2. **Implementación del servicio de migración**:
   - Desarrollo de endpoints FastAPI
   - Implementación de lógica de procesamiento
   - Integración con Odoo mediante API

3. **Desarrollo de la interfaz de usuario**:
   - Creación de componentes en Refine
   - Implementación de flujos de trabajo
   - Diseño de visualizaciones de resultados

4. **Pruebas y validación**:
   - Pruebas con datos reales
   - Verificación de rendimiento
   - Validación de resultados

5. **Documentación y capacitación**:
   - Manual de usuario
   - Guía técnica
   - Sesiones de formación
