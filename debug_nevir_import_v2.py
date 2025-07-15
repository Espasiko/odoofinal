#!/usr/bin/env python3
"""
Script para depurar la importación de productos NEVIR en Odoo 18.
Este script carga el Excel formateado y prueba la importación de cada producto individualmente
con logging detallado para identificar por qué algunos productos fallan.
"""
import os
import sys
import json
import logging
import pandas as pd
from pprint import pformat

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_nevir_import.log')
    ]
)
logger = logging.getLogger("debug_nevir_import")

# Añadir los directorios necesarios al path para poder importar los módulos
project_root = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.join(project_root, 'api')
api_services_dir = os.path.join(api_dir, 'services')

# Asegurar que todos los directorios necesarios están en el path
for path in [project_root, api_dir, api_services_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Importar los servicios necesarios
try:
    # Importar directamente desde el módulo completo
    from api.services.odoo_base_service import OdooBaseService
    logger.info("Módulo odoo_base_service importado correctamente")
except ImportError as e:
    logger.error(f"Error al importar odoo_base_service: {e}")
    # Intentar importar de otra manera
    try:
        import api.services.odoo_base_service
        OdooBaseService = api.services.odoo_base_service.OdooBaseService
        logger.info("Módulo odoo_base_service importado correctamente (método alternativo)")
    except ImportError as e2:
        logger.error(f"Error al importar odoo_base_service (método alternativo): {e2}")
        sys.exit(1)

class DebugOdooService(OdooBaseService):
    """Clase para depurar operaciones de Odoo con logging detallado"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("DebugOdooService")
        self.logger.setLevel(logging.DEBUG)
        
        # Sobrescribir la URL para usar localhost en lugar de odoo
        self._url = "http://localhost:8069"
        self.logger.info(f"Sobrescribiendo URL de conexión a Odoo: {self._url}")
        
        # Forzar reconexión con la nueva URL
        self._common = None
        self._models = None
        self._uid = None
    
    def _execute_kw(self, model, method, args, kw=None):
        """Sobrescribe _execute_kw para añadir logging detallado"""
        self.logger.debug(f"ODOO API CALL: {model}.{method}")
        self.logger.debug(f"ARGS: {pformat(args)}")
        self.logger.debug(f"KW: {pformat(kw)}")
        
        try:
            result = super()._execute_kw(model, method, args, kw)
            self.logger.debug(f"RESULT: {pformat(result)}")
            return result
        except Exception as e:
            self.logger.error(f"ERROR en {model}.{method}: {str(e)}")
            raise
    
    def create_test_product(self, product_data):
        """Crea un producto de prueba con valores mínimos"""
        self.logger.info(f"Creando producto de prueba con datos: {pformat(product_data)}")
        
        # Valores mínimos requeridos para Odoo 18
        vals = {
            'name': product_data.get('nombre', 'Producto Test'),
            'type': 'consu',
            'sale_ok': True,
            'purchase_ok': True,
            'active': True,
            'categ_id': 1  # Categoría por defecto (All)
        }
        
        # Añadir campos adicionales si están presentes
        if 'default_code' in product_data:
            vals['default_code'] = product_data['default_code']
        if 'barcode' in product_data:
            vals['barcode'] = product_data['barcode']
        if 'list_price' in product_data:
            vals['list_price'] = float(product_data['list_price'])
        if 'standard_price' in product_data:
            vals['standard_price'] = float(product_data['standard_price'])
        
        try:
            # Intentar crear el producto
            self.logger.info(f"Enviando a Odoo: {pformat(vals)}")
            product_id = self._execute_kw('product.template', 'create', [vals])
            self.logger.info(f"Producto creado con ID: {product_id}")
            return product_id
        except Exception as e:
            self.logger.error(f"Error al crear producto: {str(e)}")
            
            # Intentar identificar campos problemáticos
            for key, value in vals.items():
                try:
                    self.logger.debug(f"Probando campo individual: {key} = {value}")
                    test_vals = {'name': 'Test ' + key, 'type': 'consu'}
                    test_vals[key] = value
                    self._execute_kw('product.template', 'create', [test_vals])
                    self.logger.debug(f"Campo {key} OK")
                except Exception as field_error:
                    self.logger.error(f"Campo problemático: {key} = {value}, Error: {str(field_error)}")
            
            return None

def cargar_excel(ruta_excel):
    """Carga el Excel formateado y devuelve los datos de productos"""
    logger.info(f"Cargando Excel desde: {ruta_excel}")
    try:
        # Cargar hoja de productos
        df_productos = pd.read_excel(ruta_excel, sheet_name='PRODUCTOS')
        logger.info(f"Excel cargado correctamente. Productos encontrados: {len(df_productos)}")
        
        # Convertir DataFrame a lista de diccionarios
        productos = df_productos.to_dict('records')
        logger.info(f"Datos convertidos a diccionarios: {len(productos)} productos")
        
        return productos
    except Exception as e:
        logger.error(f"Error al cargar el Excel: {str(e)}")
        return []

def probar_producto_individual(servicio, producto):
    """Prueba la creación de un producto individual en Odoo"""
    nombre = producto.get('nombre', 'Sin nombre')
    logger.info(f"Probando producto: {nombre}")
    
    # Normalizar campos
    producto_normalizado = {}
    for key, value in producto.items():
        if value is not None and value != "":
            producto_normalizado[key] = value
    
    # Convertir campos numéricos
    for campo in ['precio_coste', 'precio_venta']:
        if campo in producto_normalizado:
            try:
                producto_normalizado[campo] = float(producto_normalizado[campo])
            except (ValueError, TypeError):
                logger.warning(f"Error al convertir {campo} a float")
    
    # Asegurar que el código de barras sea una cadena de texto
    if 'barcode' in producto_normalizado:
        producto_normalizado['barcode'] = str(producto_normalizado['barcode'])
        logger.info(f"Código de barras convertido a cadena: {producto_normalizado['barcode']}")
    
    # Mapear campos a nombres de Odoo
    if 'precio_coste' in producto_normalizado:
        producto_normalizado['standard_price'] = producto_normalizado['precio_coste']
    if 'precio_venta' in producto_normalizado:
        producto_normalizado['list_price'] = producto_normalizado['precio_venta']
    if 'referencia_proveedor' in producto_normalizado:
        producto_normalizado['default_code'] = producto_normalizado['referencia_proveedor']
    
    # Asegurar campos obligatorios para Odoo 18
    producto_normalizado['type'] = 'consu'
    producto_normalizado['sale_ok'] = True
    producto_normalizado['purchase_ok'] = True
    producto_normalizado['active'] = True
    
    # Probar creación
    logger.info(f"Datos normalizados: {pformat(producto_normalizado)}")
    product_id = servicio.create_test_product(producto_normalizado)
    
    if product_id:
        logger.info(f"✅ Producto {nombre} creado exitosamente con ID: {product_id}")
        return True
    else:
        logger.error(f"❌ Fallo al crear producto {nombre}")
        return False

def consultar_estructura_bd():
    """Consulta la estructura de la tabla product_template en Odoo"""
    logger.info("Consultando estructura de la tabla product_template")
    servicio = DebugOdooService()
    
    try:
        # Obtener campos del modelo product.template
        fields_info = servicio._execute_kw(
            'product.template', 
            'fields_get', 
            [], 
            {'attributes': ['string', 'help', 'type', 'required']}
        )
        
        # Filtrar campos requeridos
        required_fields = {k: v for k, v in fields_info.items() if v.get('required', False)}
        logger.info(f"Campos requeridos en product.template: {pformat(required_fields)}")
        
        # Obtener información sobre el tipo de campo 'type'
        if 'type' in fields_info:
            type_field = fields_info['type']
            logger.info(f"Campo 'type': {pformat(type_field)}")
            
            # Si es un campo de selección, obtener valores posibles
            if type_field.get('type') == 'selection':
                selection_values = servicio._execute_kw(
                    'product.template',
                    'fields_get',
                    ['type'],
                    {'attributes': ['selection']}
                )
                logger.info(f"Valores posibles para 'type': {pformat(selection_values)}")
        
        return fields_info
    except Exception as e:
        logger.error(f"Error al consultar estructura de BD: {str(e)}")
        return {}

def main():
    # Ruta al archivo Excel formateado
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                             'ejemplos/proveedores_exl_csv/PVP_NEVIR_FORMATEADO_V2.xlsx')
    
    if not os.path.exists(excel_path):
        logger.error(f"El archivo {excel_path} no existe")
        return 1
    
    # Consultar estructura de la BD
    estructura_bd = consultar_estructura_bd()
    
    # Cargar productos del Excel
    productos = cargar_excel(excel_path)
    if not productos:
        logger.error("No se pudieron cargar productos del Excel")
        return 1
    
    # Crear servicio de Odoo con logging detallado
    servicio = DebugOdooService()
    
    # Probar cada producto individualmente
    exitos = 0
    fallos = 0
    
    for idx, producto in enumerate(productos):
        logger.info(f"--- Producto {idx+1}/{len(productos)} ---")
        if probar_producto_individual(servicio, producto):
            exitos += 1
        else:
            fallos += 1
    
    # Resumen final
    logger.info(f"=== Resumen de importación ===")
    logger.info(f"Total productos: {len(productos)}")
    logger.info(f"Productos creados exitosamente: {exitos}")
    logger.info(f"Productos fallidos: {fallos}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
