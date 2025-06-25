import xmlrpc.client
import gc
from typing import Any, Optional
from ..utils.config import config

class OdooBaseService:
    """Servicio base para interactuar con Odoo via XML-RPC"""
    
    def __init__(self):
        self.config = config.get_odoo_config()
        self._common = None
        self._models = None
        self._uid = None
        self._url = 'http://172.18.0.5:8069'  # IP correcta del contenedor Odoo - Actualizado 2025-06-25
    
    def _get_connection(self):
        """Establece conexión con Odoo"""
        try:
            if not self._common:
                self._common = xmlrpc.client.ServerProxy(f'{self._url}/xmlrpc/2/common')
            
            if not self._uid:
                self._uid = self._common.authenticate(
                    self.config["db"],
                    self.config["username"],
                    self.config["password"],
                    {}
                )
            
            if not self._models and self._uid:
                self._models = xmlrpc.client.ServerProxy(f'{self._url}/xmlrpc/2/object')
            
            return self._uid is not None
        except Exception as e:
            print(f"Error detallado conectando con Odoo en {self._url}: {str(e)}")
            raise
            return False
    
    def _cleanup_connection(self):
        """Limpia las conexiones y libera memoria"""
        if self._common:
            del self._common
            self._common = None
        if self._models:
            del self._models
            self._models = None
        gc.collect()
    
    def _execute_kw(self, model: str, method: str, args: list, kwargs: dict = None) -> Any:
        """Ejecuta una llamada a Odoo"""
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
    
    def _get_category_name(self, categ_id) -> str:
        """Obtiene el nombre de una categoría"""
        if not categ_id:
            return "Sin categoría"
        
        try:
            category = self._execute_kw(
                'product.category',
                'read',
                [categ_id[0]],
                {'fields': ['name']}
            )
            return category[0]['name'] if category else "Sin categoría"
        except:
            return "Sin categoría"