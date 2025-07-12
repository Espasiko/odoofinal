import logging
import sys
import os
import time
import traceback

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_odoo_product_service')

# Establecer PYTHONPATH para incluir el directorio raíz del proyecto
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ['PYTHONPATH'] = root_dir + ':' + os.environ.get('PYTHONPATH', '')
sys.path.insert(0, root_dir)
logger.info(f'PYTHONPATH establecido a: {os.environ["PYTHONPATH"]}')
logger.info(f'sys.path actualizado: {sys.path}')

# Importar el servicio usando la ruta completa desde el paquete api.services
from api.services.odoo_product_service import OdooProductService
from api.utils.config import config

def test_odoo_connection():
    """Prueba la conexión con el servidor Odoo"""
    logger.info('Iniciando prueba de conexión con Odoo')
    
    # Obtener configuración de Odoo desde el archivo de configuración
    odoo_config = config.get_odoo_config()
    odoo_url = odoo_config.get('url', 'http://odoo:8069')
    odoo_db = odoo_config.get('db', 'fresh_odoo_db')
    odoo_user = odoo_config.get('username', 'admin')
    odoo_password = odoo_config.get('password', 'admin')
    
    logger.info(f'Configuración de Odoo: URL={odoo_url}, DB={odoo_db}, User={odoo_user}')
    
    # Crear instancia del servicio con configuración específica
    service = OdooProductService(url=odoo_url, db=odoo_db, username=odoo_user, password=odoo_password)
    
    try:
        # Probar la conexión
        service._get_connection()
        logger.info('¡Conexión con Odoo establecida exitosamente!')
        return True
    except Exception as e:
        logger.error(f'Error al conectar con Odoo: {str(e)}', exc_info=True)
        return False

def test_front_to_odoo_product_dict():
    """Prueba la conversión de producto frontend a formato Odoo"""
    logger.info('Iniciando prueba de front_to_odoo_product_dict')
    
    # Obtener configuración de Odoo
    odoo_config = config.get_odoo_config()
    odoo_url = odoo_config.get('url', 'http://odoo:8069')
    odoo_db = odoo_config.get('db', 'fresh_odoo_db')
    odoo_user = odoo_config.get('username', 'admin')
    odoo_password = odoo_config.get('password', 'admin')
    
    # Crear instancia del servicio
    service = OdooProductService(url=odoo_url, db=odoo_db, username=odoo_user, password=odoo_password)
    
    # Datos de prueba
    test_product = {
        'nombre': 'Producto de Prueba',
        'codigo': 'TEST123',
        'precio_venta': '99.99',
        'precio_coste': '50.00',
        'category': 'Electrónica',
        'descripcion': 'Descripción de prueba'
    }
    proveedor_nombre = 'Proveedor Test'
    
    try:
        # Ejecutar la conversión
        result = service.front_to_odoo_product_dict(test_product, proveedor_nombre)
        
        logger.info(f'Resultado de la conversión: {result}')
        
        # Validaciones básicas
        assert result['nombre'] == 'Producto de Prueba', 'Nombre incorrecto'
        assert result['default_code'] == 'TEST123', 'Código incorrecto'
        assert result['precio_venta'] == 99.99, 'Precio de venta incorrecto'
        assert result['precio_coste'] == 50.0, 'Precio de coste incorrecto'
        assert result['categoria'] == 'Electrónica', 'Categoría incorrecta'
        assert result['type'] == 'consu', 'Tipo incorrecto'
        
        logger.info('¡Todas las validaciones pasaron exitosamente!')
        return result
    except Exception as e:
        logger.error(f'Error durante la prueba: {str(e)}', exc_info=True)
        raise

def test_create_product_in_odoo():
    """Prueba la creación de un producto en Odoo"""
    logger.info('Iniciando prueba de creación de producto en Odoo')
    
    # Primero asegurarse de que podemos conectar
    if not test_odoo_connection():
        logger.error('No se puede probar la creación de producto sin conexión a Odoo')
        return False
    
    # Obtener configuración de Odoo
    odoo_config = config.get_odoo_config()
    odoo_url = odoo_config.get('url', 'http://odoo:8069')
    odoo_db = odoo_config.get('db', 'fresh_odoo_db')
    odoo_user = odoo_config.get('username', 'admin')
    odoo_password = odoo_config.get('password', 'admin')
    
    # Crear instancia del servicio
    service = OdooProductService(url=odoo_url, db=odoo_db, username=odoo_user, password=odoo_password)
    
    # Usar el producto transformado
    test_product = {
        'nombre': 'Producto de Prueba Integración',
        'codigo': 'TEST_INT_001',
        'precio_venta': '149.99',
        'precio_coste': '75.00',
        'category': 'Electrónica/Pruebas',
        'descripcion': 'Producto creado durante prueba de integración'
    }
    proveedor_nombre = 'Proveedor Integración'
    
    try:
        # Transformar el producto
        product_dict = service.front_to_odoo_product_dict(test_product, proveedor_nombre)
        logger.info(f'Producto transformado para Odoo: {product_dict}')
        
        # Crear el producto en Odoo
        product_id = service.create_product(product_dict)
        logger.info(f'Producto creado en Odoo con ID: {product_id}')
        
        # Verificar que el producto fue creado buscándolo
        search_result = service._execute_kw('product.template', 'search_read', [[('default_code', '=', 'TEST_INT_001')]], {'fields': ['id', 'name']})
        if search_result and len(search_result) > 0:
            logger.info(f'Producto encontrado en Odoo: {search_result[0]}')
            assert search_result[0]['name'] == 'Producto de Prueba Integración', 'Nombre del producto creado no coincide'
            return True
        else:
            logger.error('No se encontró el producto creado en Odoo')
            return False
    except Exception as e:
        logger.error(f'Error durante la creación de producto en Odoo: {str(e)}', exc_info=True)
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Starting OdooProductService integration test")
    try:
        # Instantiate the service without passing connection parameters
        # as they are read internally from config
        service = OdooProductService()
        logger.info("OdooProductService instantiated successfully")
        
        # Test connection to Odoo server
        connection = service._get_connection()
        if connection:
            logger.info("Successfully connected to Odoo server")
        else:
            logger.error("Failed to connect to Odoo server")
            sys.exit(1)
        
        # Test product data transformation
        sample_product = {
            "productId": "TEST123",
            "name": "Test Product",
            "description": "This is a test product",
            "price": 99.99,
            "currency": "USD",
            "stock": 100,
            "images": ["http://example.com/image1.jpg"],
            "supplier": "Test Supplier",
            "code": f"TEST-{int(time.time())}",  # Unique code with timestamp
            "brand": "Test Brand",
            "categories": ["Electronics", "Test"],
            "extra": {"weight": 1.5, "color": "Blue"}
        }
        logger.info(f"Transforming sample product data: {sample_product['name']}")
        odoo_product_data = service.front_to_odoo_product_dict(sample_product)
        logger.info(f"Transformed product data: {odoo_product_data}")
        
        # Test creating a product in Odoo
        logger.info("Attempting to create product in Odoo")
        product_id = service.create_product(odoo_product_data)
        if product_id:
            logger.info(f"Product created successfully with ID: {product_id}")
        else:
            logger.error("Failed to create product in Odoo")
            sys.exit(1)
        
        # Verify product creation by searching for it
        logger.info(f"Searching for product with code: {odoo_product_data['default_code']}")
        search_result = service.search_product(odoo_product_data['default_code'])
        if search_result:
            logger.info(f"Product found in Odoo: {search_result}")
        else:
            logger.warning(f"Product not found in Odoo with code: {odoo_product_data['default_code']}")
        
        logger.info("OdooProductService integration test completed successfully")
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
