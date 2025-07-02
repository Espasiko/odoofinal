import xmlrpc.client
import gc
import os
import logging
from typing import Any, Optional
from ..utils.config import config

class OdooBaseService:
    """Servicio base para interactuar con Odoo via XML-RPC"""
    
    def __init__(self):
        self.config = config.get_odoo_config()
        self._common = None
        self._models = None
        self._uid = None
        self._url = os.getenv("ODOO_URL", "http://localhost:8069")
        self._db = os.getenv("ODOO_DB", "manus_odoo-bd")
        self._username = os.getenv("ODOO_USERNAME", "admin")
        self._password = os.getenv("ODOO_PASSWORD", "admin")
    
    def _get_connection(self) -> None:
        """
        Establece la conexión con Odoo usando las credenciales de entorno.
        """
        try:
            logging.info(f"Intentando conectar a Odoo en: {self._url}, DB: {self._db}")
            
            # Validar que la URL no contenga caracteres de control no válidos
            if any(ord(char) < 32 for char in self._url):
                logging.warning(f"URL de Odoo contiene caracteres no válidos, limpiando URL")
                self._url = "".join(char for char in self._url if ord(char) >= 32)

            self._common = xmlrpc.client.ServerProxy(f"{self._url}/xmlrpc/2/common")
            logging.info("Conexión común establecida con Odoo.")
            self._uid = self._common.authenticate(self._db, self._username, self._password, {})
            logging.info(f"Autenticación exitosa con UID: {self._uid}")
            self._models = xmlrpc.client.ServerProxy(f"{self._url}/xmlrpc/2/object")
            logging.info("Conexión completa con Odoo.")
        except Exception as e:
            logging.error(f"Error al conectar con Odoo: {e}", exc_info=True)
            self._common = None
            self._models = None
            self._uid = None
            raise
    
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
        """Ejecuta una llamada a Odoo mediante XML-RPC.
        Garantiza que la conexión esté establecida y reutiliza la existente
        para evitar reconexiones innecesarias.
        """
        # Asegurar conexión
        if self._models is None:
            self._get_connection()
        # Si continúa sin modelos, abortar
        if self._models is None:
            logging.error("No se pudo establecer la conexión con Odoo; _models es None")
            return None
        try:
            if kwargs is None:
                kwargs = {}
            return self._models.execute_kw(
                self._db,
                self._uid,
                self._password,
                model,
                method,
                args,
                kwargs
            )
        except Exception as e:
            logging.error(f"Error ejecutando {method} en {model}: {e}", exc_info=True)
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