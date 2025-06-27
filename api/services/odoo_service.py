import gc
import xmlrpc.client
from typing import List, Optional, Dict, Any
from ..utils.config import config
from ..models.schemas import Product, Provider, Customer, Sale, ProductCreate

class OdooService:
    """Servicio para interactuar con Odoo via XML-RPC"""
    
    def __init__(self):
        self.config = config.get_odoo_config()
        self._common = None
        self._models = None
        self._uid = None
        self._url = self.config["url"]  # Usar siempre la URL de configuración/env
    
    def _get_connection(self):
        """Establece conexión con Odoo"""
        import logging
        logger = logging.getLogger("odoo_connection")
        logger.warning(f"[LOG ODOO_URL] Conectando a Odoo con URL: {self._url}")
        try:
            print(f"Intentando conectar a Odoo con URL: {self._url}")
            if not self._common:
                print(f"Creando proxy para {self._url}/xmlrpc/2/common")
                self._common = xmlrpc.client.ServerProxy(f'{self._url}/xmlrpc/2/common')
            
            if not self._uid:
                print(f"Autenticando en Odoo con DB: {self.config['db']}, Usuario: {self.config['username']}")
                self._uid = self._common.authenticate(
                    self.config["db"],
                    self.config["username"],
                    self.config["password"],
                    {}
                )
                print(f"Autenticación completada, UID: {self._uid}")
            
            if not self._models and self._uid:
                print(f"Creando proxy para {self._url}/xmlrpc/2/object")
                self._models = xmlrpc.client.ServerProxy(f'{self._url}/xmlrpc/2/object')
            
            return self._uid is not None
        except Exception as e:
            print(f"Error detallado conectando con Odoo en {self._url}: {str(e)}")
            raise
            return False
    
    def _cleanup_connection(self):
        if self._common:
            del self._common
            self._common = None
        if self._models:
            del self._models
            self._models = None
        gc.collect()
    
    def _execute_kw(self, model: str, method: str, args: list, kwargs: dict = None) -> Any:
        if not self._get_connection():
            return None
        try:
            if kwargs is None:
                kwargs = {}
            return self._models.execute_kw(
                self.config["db"],
                self._uid,
                self.config["password"],
                model,
                method,
                args,
                kwargs
            )
        except Exception as e:
            print(f"Error ejecutando {method} en {model}: {e}")
            return None
    # ... (resto del código de OdooService, clases y métodos auxiliares, igual que rama fasbien) ...

# Importar servicios refactorizados
from .odoo_service_refactored import OdooServiceRefactored

# Crear alias para mantener compatibilidad
class OdooServiceCompatible(OdooServiceRefactored):
    """Clase de compatibilidad que mantiene la interfaz original"""
    pass

# Instancia del servicio (ahora usando la versión refactorizada)
odoo_service = OdooServiceCompatible()
