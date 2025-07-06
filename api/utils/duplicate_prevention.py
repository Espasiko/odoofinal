#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilidades para prevenir duplicados durante la importación de productos
Este módulo se integra con el proceso de importación de Excel para validar
y prevenir la creación de duplicados basados en código, nombre o combinación de ambos.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class DuplicateValidator:
    """Clase para validar y prevenir duplicados durante la importación"""
    
    def __init__(self, odoo_service):
        """
        Inicializa el validador con una conexión al servicio de Odoo
        
        Args:
            odoo_service: Instancia de OdooService para consultas a la API
        """
        self.odoo_service = odoo_service
        # Caché para reducir consultas a Odoo
        self._product_code_cache = {}
        self._product_name_cache = {}
        self._partner_cache = {}
        self._category_cache = {}
    
    def _load_existing_products(self) -> None:
        """Carga productos existentes en la caché para consultas rápidas"""
        logger.info("Cargando productos existentes para validación de duplicados...")
        
        # Obtener todos los productos con sus códigos
        products = self.odoo_service.execute_kw(
            'product.product', 
            'search_read', 
            [[['active', '=', True]]], 
            {'fields': ['id', 'default_code', 'name', 'product_tmpl_id']}
        )
        
        # Construir caché por código y por nombre
        for product in products:
            if product.get('default_code'):
                code = product['default_code'].strip().upper()
                self._product_code_cache[code] = product
            
            if product.get('name'):
                name = product['name'].strip().upper()
                self._product_name_cache[name] = product
        
        logger.info(f"Caché de productos cargada: {len(products)} productos")
    
    def _load_existing_partners(self) -> None:
        """Carga proveedores existentes en la caché"""
        logger.info("Cargando proveedores existentes para validación...")
        
        partners = self.odoo_service.execute_kw(
            'res.partner', 
            'search_read', 
            [[['supplier_rank', '>', 0]]], 
            {'fields': ['id', 'name', 'vat', 'email']}
        )
        
        for partner in partners:
            if partner.get('name'):
                name = partner['name'].strip().upper()
                self._partner_cache[name] = partner
                
            if partner.get('vat'):
                vat = partner['vat'].strip().upper().replace('-', '').replace(' ', '')
                self._partner_cache[vat] = partner
        
        logger.info(f"Caché de proveedores cargada: {len(partners)} proveedores")
    
    def _load_existing_categories(self) -> None:
        """Carga categorías existentes en la caché"""
        logger.info("Cargando categorías existentes para validación...")
        
        categories = self.odoo_service.execute_kw(
            'product.category', 
            'search_read', 
            [[]], 
            {'fields': ['id', 'name', 'parent_id']}
        )
        
        for category in categories:
            if category.get('name'):
                name = category['name'].strip().upper()
                self._category_cache[name] = category
        
        logger.info(f"Caché de categorías cargada: {len(categories)} categorías")
    
    def load_all_data(self) -> None:
        """Carga todos los datos necesarios para validación"""
        self._load_existing_products()
        self._load_existing_partners()
        self._load_existing_categories()
    
    def is_product_duplicate(self, product_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verifica si un producto es duplicado basado en código o nombre
        
        Args:
            product_data: Diccionario con datos del producto a verificar
            
        Returns:
            Tupla (es_duplicado, producto_existente)
        """
        # Asegurar que la caché esté cargada
        if not self._product_code_cache:
            self._load_existing_products()
        
        # Verificar por código (prioridad alta)
        if product_data.get('default_code'):
            code = product_data['default_code'].strip().upper()
            if code in self._product_code_cache:
                return True, self._product_code_cache[code]
        
        # Verificar por nombre exacto (prioridad media)
        if product_data.get('name'):
            name = product_data['name'].strip().upper()
            if name in self._product_name_cache:
                return True, self._product_name_cache[name]
        
        return False, None
    
    def is_partner_duplicate(self, partner_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verifica si un proveedor es duplicado basado en nombre, VAT o email
        
        Args:
            partner_data: Diccionario con datos del proveedor
            
        Returns:
            Tupla (es_duplicado, proveedor_existente)
        """
        # Asegurar que la caché esté cargada
        if not self._partner_cache:
            self._load_existing_partners()
        
        # Verificar por VAT (prioridad alta)
        if partner_data.get('vat'):
            vat = partner_data['vat'].strip().upper().replace('-', '').replace(' ', '')
            if vat in self._partner_cache:
                return True, self._partner_cache[vat]
        
        # Verificar por nombre exacto (prioridad media)
        if partner_data.get('name'):
            name = partner_data['name'].strip().upper()
            if name in self._partner_cache:
                return True, self._partner_cache[name]
        
        # Verificar por email (prioridad baja)
        if partner_data.get('email'):
            email = partner_data['email'].strip().lower()
            for partner in self._partner_cache.values():
                if partner.get('email') and partner['email'].strip().lower() == email:
                    return True, partner
        
        return False, None
    
    def is_category_duplicate(self, category_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verifica si una categoría es duplicada basada en nombre y padre
        
        Args:
            category_data: Diccionario con datos de la categoría
            
        Returns:
            Tupla (es_duplicado, categoría_existente)
        """
        # Asegurar que la caché esté cargada
        if not self._category_cache:
            self._load_existing_categories()
        
        # Verificar por nombre exacto
        if category_data.get('name'):
            name = category_data['name'].strip().upper()
            
            # Si tenemos información del padre, verificar nombre+padre
            if category_data.get('parent_id'):
                parent_id = category_data['parent_id']
                for category in self._category_cache.values():
                    if (category.get('name', '').strip().upper() == name and 
                        category.get('parent_id') and 
                        category['parent_id'][0] == parent_id):
                        return True, category
            
            # Si no hay padre o no encontramos con padre, verificar solo por nombre
            if name in self._category_cache:
                return True, self._category_cache[name]
        
        return False, None
    
    def update_cache_with_new_product(self, product_data: Dict[str, Any], product_id: int) -> None:
        """
        Actualiza la caché con un nuevo producto creado
        
        Args:
            product_data: Datos del producto
            product_id: ID del producto creado
        """
        if product_data.get('default_code'):
            code = product_data['default_code'].strip().upper()
            self._product_code_cache[code] = {**product_data, 'id': product_id}
        
        if product_data.get('name'):
            name = product_data['name'].strip().upper()
            self._product_name_cache[name] = {**product_data, 'id': product_id}
    
    def update_cache_with_new_partner(self, partner_data: Dict[str, Any], partner_id: int) -> None:
        """
        Actualiza la caché con un nuevo proveedor creado
        
        Args:
            partner_data: Datos del proveedor
            partner_id: ID del proveedor creado
        """
        if partner_data.get('name'):
            name = partner_data['name'].strip().upper()
            self._partner_cache[name] = {**partner_data, 'id': partner_id}
        
        if partner_data.get('vat'):
            vat = partner_data['vat'].strip().upper().replace('-', '').replace(' ', '')
            self._partner_cache[vat] = {**partner_data, 'id': partner_id}
    
    def update_cache_with_new_category(self, category_data: Dict[str, Any], category_id: int) -> None:
        """
        Actualiza la caché con una nueva categoría creada
        
        Args:
            category_data: Datos de la categoría
            category_id: ID de la categoría creada
        """
        if category_data.get('name'):
            name = category_data['name'].strip().upper()
            self._category_cache[name] = {**category_data, 'id': category_id}

# Ejemplo de uso en el proceso de importación:
"""
from api.utils.duplicate_prevention import DuplicateValidator

# En el proceso de importación
validator = DuplicateValidator(odoo_service)
validator.load_all_data()  # Cargar datos existentes

# Para cada producto a importar
is_duplicate, existing_product = validator.is_product_duplicate(product_data)
if is_duplicate:
    # Usar el producto existente (existing_product['id'])
    product_id = existing_product['id']
    logger.info(f"Usando producto existente: {product_id}")
else:
    # Crear nuevo producto
    product_id = odoo_service.create_product(product_data)
    # Actualizar caché
    validator.update_cache_with_new_product(product_data, product_id)
"""