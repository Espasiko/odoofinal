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
        # Usar la configuración del objeto config en lugar de leer directamente las variables de entorno
        self._url = self.config["url"]
        self._db = self.config["db"]
        self._username = self.config["username"]
        self._password = self.config["password"]
        
        # Asegurarse de que la URL no contenga caracteres de control
        if any(ord(char) < 32 for char in self._url):
            self._url = "".join(char for char in self._url if ord(char) >= 32)
        
        logging.info(f"Inicializando OdooBaseService con URL: {self._url}, DB: {self._db}, Usuario: {self._username}")
    
    def _get_connection(self) -> None:
        """
        Establece la conexión con Odoo usando las credenciales de entorno.
        """
        try:
            logging.info(f"Intentando conectar a Odoo en: {self._url}, DB: {self._db}")
            
            # Asegurarse de que estamos usando la URL correcta de Odoo
            if not self._url or not self._url.startswith("http"):
                self._url = "http://odoo:8069"  # URL por defecto dentro de Docker
                logging.warning(f"URL de Odoo no válida, usando URL por defecto: {self._url}")
            
            # Añadir log para depuración de conexión
            logging.info(f"Configuración de conexión: URL={self._url}, DB={self._db}, Usuario={self._username}")

            # Asegurarse de que la URL esté correctamente formateada
            clean_url = self._url.strip()
            if clean_url.endswith("/"):
                clean_url = clean_url[:-1]  # Eliminar barra final si existe
                
            logging.info(f"Conectando a Odoo con URL limpia: {clean_url}")
            self._common = xmlrpc.client.ServerProxy(f"{clean_url}/xmlrpc/2/common")
            logging.info("Conexión común establecida con Odoo.")
            self._uid = self._common.authenticate(self._db, self._username, self._password, {})
            logging.info(f"Autenticación exitosa con UID: {self._uid}")
            self._models = xmlrpc.client.ServerProxy(f"{clean_url}/xmlrpc/2/object")
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
                
            # Sanitizar valores None en args para evitar errores de XML-RPC
            sanitized_args = self._sanitize_values(args)
            
            # Configurar el servidor XML-RPC para permitir valores None
            if not hasattr(self._models, '_ServerProxy__allow_none') or not self._models._ServerProxy__allow_none:
                # Crear un nuevo ServerProxy con allow_none=True si es necesario
                # Limpiar la URL antes de reconectar
                clean_url = self._url.strip()
                if clean_url.endswith("/"):
                    clean_url = clean_url[:-1]  # Eliminar barra final si existe
                    
                self._models = xmlrpc.client.ServerProxy(
                    f"{clean_url}/xmlrpc/2/object",
                    allow_none=True
                )
                logging.info("Reconectado a Odoo con allow_none=True")
                
            return self._models.execute_kw(
                self._db,
                self._uid,
                self._password,
                model,
                method,
                sanitized_args,
                kwargs
            )
        except Exception as e:
            logging.error(f"Error ejecutando {method} en {model}: {e}", exc_info=True)
            return None
    
    def _sanitize_values(self, value):
        """Sanitiza valores para XML-RPC, reemplazando None por valores vacíos apropiados"""
        if value is None:
            return False  # XML-RPC usa False en lugar de None
        elif isinstance(value, list):
            return [self._sanitize_values(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._sanitize_values(v) for k, v in value.items()}
        elif isinstance(value, str) and not value.strip():
            # Cadenas vacías o solo espacios se convierten a False
            return False
        return value
            
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