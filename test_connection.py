#!/usr/bin/env python3
import os
import xmlrpc.client
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_odoo_connection():
    """Prueba la conexión a Odoo y muestra información detallada"""
    
    # Obtener configuración de variables de entorno
    url = os.getenv("ODOO_URL", "http://odoo:8069")
    db = os.getenv("ODOO_DB", "manus_odoo-bd")
    username = os.getenv("ODOO_USERNAME", "yo@mail.com")
    password = os.getenv("ODOO_PASSWORD", "admin")
    
    logger.info(f"Probando conexión a Odoo con URL: {url}")
    logger.info(f"Base de datos: {db}")
    logger.info(f"Usuario: {username}")
    
    # Limpiar URL
    clean_url = url.strip()
    if clean_url.endswith("/"):
        clean_url = clean_url[:-1]
    
    logger.info(f"URL limpia: {clean_url}")
    
    try:
        # Conectar al endpoint common
        common = xmlrpc.client.ServerProxy(f"{clean_url}/xmlrpc/2/common")
        logger.info("Conexión al endpoint common establecida")
        
        # Obtener versión de Odoo
        version_info = common.version()
        logger.info(f"Versión de Odoo: {version_info.get('server_version', 'Desconocida')}")
        
        # Autenticar
        uid = common.authenticate(db, username, password, {})
        logger.info(f"Autenticación exitosa. UID: {uid}")
        
        # Conectar al endpoint object
        models = xmlrpc.client.ServerProxy(f"{clean_url}/xmlrpc/2/object")
        logger.info("Conexión al endpoint object establecida")
        
        # Probar una llamada simple
        partner_count = models.execute_kw(
            db, uid, password,
            'res.partner', 'search_count',
            [[]]
        )
        logger.info(f"Número de contactos en Odoo: {partner_count}")
        
        # Probar una llamada para obtener facturas
        invoice_count = models.execute_kw(
            db, uid, password,
            'account.move', 'search_count',
            [[('move_type', '=', 'in_invoice')]]
        )
        logger.info(f"Número de facturas de proveedor en Odoo: {invoice_count}")
        
        logger.info("¡Prueba de conexión exitosa!")
        return True
    
    except Exception as e:
        logger.error(f"Error al conectar con Odoo: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    test_odoo_connection()