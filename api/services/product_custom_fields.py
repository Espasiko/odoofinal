from typing import Optional, Dict, Any
import logging

"""
Módulo para gestionar los campos personalizados de productos en Odoo.
Este módulo extrae la lógica de campos personalizados de odoo_product_service.py
para mejorar la modularidad y mantenibilidad.
"""

def initialize_custom_fields(service) -> bool:
    """
    Inicializa los campos personalizados necesarios en Odoo.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        
    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario
    """
    try:
        if not hasattr(service, '_models') or not service._models:
            if hasattr(service, '_get_connection'):
                service._get_connection()
                
        # Crear campos personalizados para márgenes y alertas si no existen
        ensure_custom_field(service, 'product.template', 'x_margen_calculado', 'float', 'Margen Calculado (%)')
        ensure_custom_field(service, 'product.template', 'x_alerta_margen', 'boolean', 'Alerta de Margen')
        logging.info("Campos personalizados para márgenes y alertas verificados/creados correctamente")
        return True
    except Exception as e:
        logging.error(f"Error al inicializar campos personalizados: {str(e)}")
        return False

def ensure_custom_field(service, model_name: str, field_name: str, field_type: str, field_label: str) -> bool:
    """
    Verifica si un campo personalizado existe en un modelo de Odoo y lo crea si no existe.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        model_name: Nombre del modelo en Odoo (ej: 'product.template')
        field_name: Nombre del campo a crear (ej: 'x_margen_calculado')
        field_type: Tipo de campo (ej: 'float', 'boolean', etc.)
        field_label: Etiqueta visible del campo
        
    Returns:
        bool: True si el campo ya existía o se creó correctamente, False en caso de error
    """
    try:
        # Verificar si el campo ya existe
        field_exists = service._execute_kw(
            'ir.model.fields',
            'search_count',
            [[('model', '=', model_name), ('name', '=', field_name)]]
        )
        
        if field_exists:
            logging.debug(f"Campo {field_name} ya existe en {model_name}")
            return True
            
        # Crear el campo si no existe
        field_data = {
            'model': model_name,
            'name': field_name,
            'field_description': field_label,
            'ttype': field_type,
            'state': 'manual',
            'store': True
        }
        
        service._execute_kw('ir.model.fields', 'create', [field_data])
        logging.info(f"Campo personalizado {field_name} creado en {model_name}")
        return True
    except Exception as e:
        logging.error(f"Error al crear campo personalizado {field_name}: {str(e)}")
        return False

def check_available_fields(service, model_name: str) -> Dict[str, Any]:
    """
    Obtiene la lista de campos disponibles en un modelo de Odoo.
    
    Args:
        service: Instancia de OdooBaseService con método _execute_kw
        model_name: Nombre del modelo en Odoo (ej: 'product.template')
        
    Returns:
        Dict[str, Any]: Diccionario con información de los campos disponibles
    """
    try:
        fields_data = service._execute_kw(
            model_name,
            'fields_get',
            [],
            {'attributes': ['string', 'help', 'type']}
        )
        logging.debug(f"Campos disponibles en {model_name}: {len(fields_data)} campos")
        return fields_data
    except Exception as e:
        logging.error(f"Error al obtener campos de {model_name}: {str(e)}")
        return {}
