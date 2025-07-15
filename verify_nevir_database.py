#!/usr/bin/env python3
"""
Script para verificar la integridad de la base de datos después de importar productos NEVIR.
Este script:
1. Verifica la estructura de las tablas relevantes
2. Comprueba las relaciones entre productos y proveedores
3. Valida la consistencia de los datos importados
4. Genera un informe detallado del estado de la base de datos
"""
import os
import sys
import json
import time
import logging
import asyncio
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('verify_nevir_database.log')
    ]
)
logger = logging.getLogger("verify_nevir_database")

# Importar las funciones necesarias
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.services.odoo_base_service import OdooBaseService

class OdooDatabaseVerifier(OdooBaseService):
    """Clase para verificar la integridad de la base de datos de Odoo"""
    
    def __init__(self, proveedor_nombre: str = "NEVIR"):
        """
        Inicializa el verificador
        
        Args:
            proveedor_nombre: Nombre del proveedor a verificar
        """
        super().__init__()
        self.proveedor_nombre = proveedor_nombre
        self.verification_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "proveedor": proveedor_nombre,
            "tables_verified": False,
            "provider_verified": False,
            "products_verified": False,
            "relations_verified": False,
            "errors": [],
            "warnings": [],
            "stats": {
                "provider_id": None,
                "total_products": 0,
                "products_with_supplier": 0,
                "products_without_supplier": 0,
                "products_with_category": 0,
                "products_without_category": 0
            }
        }
    
    async def verify_database_tables(self) -> bool:
        """
        Verifica que las tablas necesarias existen en la base de datos
        
        Returns:
            bool: True si todas las tablas existen, False en caso contrario
        """
        logger.info("Verificando tablas de la base de datos")
        
        try:
            # Lista de tablas a verificar
            required_tables = [
                'product_template',
                'product_product',
                'product_category',
                'product_supplierinfo',
                'res_partner'
            ]
            
            # Verificar cada tabla
            for table in required_tables:
                try:
                    # Intentar leer un registro de la tabla
                    result = self._execute_kw(
                        table.replace('_', '.'),
                        'search',
                        [[]],
                        {'limit': 1}
                    )
                    
                    if result is None:
                        self.verification_results["errors"].append(f"No se pudo acceder a la tabla {table}")
                        return False
                    
                    logger.info(f"Tabla {table} verificada correctamente")
                    
                except Exception as e:
                    logger.error(f"Error verificando tabla {table}: {str(e)}")
                    self.verification_results["errors"].append(f"Error verificando tabla {table}: {str(e)}")
                    return False
            
            # Verificar estructura de tablas clave
            # 1. product_template
            product_fields = self._execute_kw(
                'product.template',
                'fields_get',
                [],
                {'attributes': ['string', 'type', 'required']}
            )
            
            required_product_fields = ['name', 'default_code', 'list_price', 'standard_price', 'categ_id']
            missing_fields = [field for field in required_product_fields if field not in product_fields]
            
            if missing_fields:
                self.verification_results["errors"].append(f"Faltan campos en product_template: {missing_fields}")
                return False
            
            # 2. product_supplierinfo
            supplier_fields = self._execute_kw(
                'product.supplierinfo',
                'fields_get',
                [],
                {'attributes': ['string', 'type', 'required']}
            )
            
            required_supplier_fields = ['partner_id', 'product_tmpl_id', 'price']
            missing_fields = [field for field in required_supplier_fields if field not in supplier_fields]
            
            if missing_fields:
                self.verification_results["errors"].append(f"Faltan campos en product_supplierinfo: {missing_fields}")
                return False
            
            # Todo correcto
            self.verification_results["tables_verified"] = True
            logger.info("Todas las tablas verificadas correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error verificando tablas: {str(e)}")
            self.verification_results["errors"].append(f"Error verificando tablas: {str(e)}")
            return False
    
    async def verify_provider(self) -> bool:
        """
        Verifica que el proveedor existe en la base de datos
        
        Returns:
            bool: True si el proveedor existe, False en caso contrario
        """
        logger.info(f"Verificando proveedor: {self.proveedor_nombre}")
        
        try:
            # Buscar proveedor por nombre
            provider_ids = self._execute_kw(
                'res.partner',
                'search',
                [[['name', '=', self.proveedor_nombre], ['supplier_rank', '>', 0]]],
                {'limit': 1}
            )
            
            if not provider_ids:
                # Buscar con ILIKE por si hay diferencias en mayúsculas/minúsculas
                provider_ids = self._execute_kw(
                    'res.partner',
                    'search',
                    [[['name', 'ilike', self.proveedor_nombre], ['supplier_rank', '>', 0]]],
                    {'limit': 1}
                )
            
            if not provider_ids:
                self.verification_results["errors"].append(f"No se encontró el proveedor {self.proveedor_nombre}")
                return False
            
            # Leer datos del proveedor
            provider_id = provider_ids[0]
            provider_data = self._execute_kw(
                'res.partner',
                'read',
                [provider_id],
                {'fields': ['name', 'vat', 'email', 'phone', 'supplier_rank']}
            )
            
            if not provider_data:
                self.verification_results["errors"].append(f"No se pudieron leer los datos del proveedor {provider_id}")
                return False
            
            # Guardar ID del proveedor para uso posterior
            self.verification_results["stats"]["provider_id"] = provider_id
            self.provider_id = provider_id
            
            # Verificar que es un proveedor
            if provider_data[0].get('supplier_rank', 0) <= 0:
                self.verification_results["warnings"].append(f"El partner {self.proveedor_nombre} no tiene supplier_rank > 0")
            
            # Todo correcto
            self.verification_results["provider_verified"] = True
            logger.info(f"Proveedor verificado correctamente: ID {provider_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error verificando proveedor: {str(e)}")
            self.verification_results["errors"].append(f"Error verificando proveedor: {str(e)}")
            return False
    
    async def verify_products(self) -> bool:
        """
        Verifica los productos del proveedor
        
        Returns:
            bool: True si hay productos válidos, False en caso contrario
        """
        logger.info("Verificando productos")
        
        try:
            if not hasattr(self, 'provider_id'):
                self.verification_results["errors"].append("No se ha verificado el proveedor primero")
                return False
            
            # Buscar productos vinculados al proveedor
            supplier_info = self._execute_kw(
                'product.supplierinfo',
                'search_read',
                [[['partner_id', '=', self.provider_id]]],
                {'fields': ['product_tmpl_id']}
            )
            
            if not supplier_info:
                self.verification_results["warnings"].append(f"No se encontraron productos vinculados al proveedor {self.proveedor_nombre}")
                return False
            
            # Extraer IDs de productos
            product_ids = [info['product_tmpl_id'][0] for info in supplier_info if info.get('product_tmpl_id')]
            
            if not product_ids:
                self.verification_results["errors"].append("No se encontraron IDs de productos válidos")
                return False
            
            # Leer datos de los productos
            products_data = self._execute_kw(
                'product.template',
                'read',
                [product_ids],
                {'fields': ['name', 'default_code', 'list_price', 'standard_price', 'categ_id', 'active']}
            )
            
            if not products_data:
                self.verification_results["errors"].append("No se pudieron leer los datos de los productos")
                return False
            
            # Actualizar estadísticas
            self.verification_results["stats"]["total_products"] = len(products_data)
            
            # Verificar cada producto
            products_with_category = 0
            products_without_category = 0
            
            for product in products_data:
                # Verificar categoría
                if product.get('categ_id'):
                    products_with_category += 1
                else:
                    products_without_category += 1
                    self.verification_results["warnings"].append(f"Producto {product.get('name')} sin categoría")
                
                # Verificar código
                if not product.get('default_code'):
                    self.verification_results["warnings"].append(f"Producto {product.get('name')} sin código")
                
                # Verificar precios
                if product.get('list_price', 0) <= 0:
                    self.verification_results["warnings"].append(f"Producto {product.get('name')} sin precio de venta")
            
            # Actualizar estadísticas
            self.verification_results["stats"]["products_with_category"] = products_with_category
            self.verification_results["stats"]["products_without_category"] = products_without_category
            
            # Guardar IDs de productos para uso posterior
            self.product_ids = product_ids
            
            # Todo correcto si hay al menos un producto
            if len(products_data) > 0:
                self.verification_results["products_verified"] = True
                logger.info(f"Productos verificados correctamente: {len(products_data)} productos")
                return True
            else:
                self.verification_results["errors"].append("No se encontraron productos")
                return False
            
        except Exception as e:
            logger.error(f"Error verificando productos: {str(e)}")
            self.verification_results["errors"].append(f"Error verificando productos: {str(e)}")
            return False
    
    async def verify_product_supplier_relations(self) -> bool:
        """
        Verifica las relaciones entre productos y proveedores
        
        Returns:
            bool: True si las relaciones son válidas, False en caso contrario
        """
        logger.info("Verificando relaciones producto-proveedor")
        
        try:
            if not hasattr(self, 'product_ids') or not hasattr(self, 'provider_id'):
                self.verification_results["errors"].append("No se han verificado los productos o el proveedor primero")
                return False
            
            # Verificar cada producto
            products_with_supplier = 0
            products_without_supplier = 0
            
            for product_id in self.product_ids:
                # Buscar relación con el proveedor
                supplier_info = self._execute_kw(
                    'product.supplierinfo',
                    'search_read',
                    [[['product_tmpl_id', '=', product_id], ['partner_id', '=', self.provider_id]]],
                    {'fields': ['price', 'product_code']}
                )
                
                if supplier_info:
                    products_with_supplier += 1
                    
                    # Verificar precio
                    if not supplier_info[0].get('price'):
                        product_name = self._get_product_name(product_id)
                        self.verification_results["warnings"].append(f"Producto {product_name} sin precio de proveedor")
                else:
                    products_without_supplier += 1
                    product_name = self._get_product_name(product_id)
                    self.verification_results["warnings"].append(f"Producto {product_name} sin relación con el proveedor {self.proveedor_nombre}")
            
            # Actualizar estadísticas
            self.verification_results["stats"]["products_with_supplier"] = products_with_supplier
            self.verification_results["stats"]["products_without_supplier"] = products_without_supplier
            
            # Todo correcto si hay al menos un producto con proveedor
            if products_with_supplier > 0:
                self.verification_results["relations_verified"] = True
                logger.info(f"Relaciones verificadas correctamente: {products_with_supplier}/{len(self.product_ids)} productos con proveedor")
                return True
            else:
                self.verification_results["errors"].append("No se encontraron productos con relación al proveedor")
                return False
            
        except Exception as e:
            logger.error(f"Error verificando relaciones: {str(e)}")
            self.verification_results["errors"].append(f"Error verificando relaciones: {str(e)}")
            return False
    
    def _get_product_name(self, product_id: int) -> str:
        """
        Obtiene el nombre de un producto por su ID
        
        Args:
            product_id: ID del producto
            
        Returns:
            str: Nombre del producto o ID si no se encuentra
        """
        try:
            product_data = self._execute_kw(
                'product.template',
                'read',
                [product_id],
                {'fields': ['name']}
            )
            
            if product_data and product_data[0].get('name'):
                return product_data[0]['name']
            else:
                return f"ID: {product_id}"
        except Exception:
            return f"ID: {product_id}"
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Genera un informe detallado de la verificación
        
        Returns:
            Dict[str, Any]: Informe detallado
        """
        logger.info("Generando informe de verificación")
        
        # Calcular resultado global
        overall_success = (
            self.verification_results["tables_verified"] and
            self.verification_results["provider_verified"] and
            self.verification_results["products_verified"] and
            self.verification_results["relations_verified"]
        )
        
        # Crear informe
        report = {
            "timestamp": self.verification_results["timestamp"],
            "proveedor": self.proveedor_nombre,
            "overall_success": overall_success,
            "verification_steps": {
                "tables_verified": self.verification_results["tables_verified"],
                "provider_verified": self.verification_results["provider_verified"],
                "products_verified": self.verification_results["products_verified"],
                "relations_verified": self.verification_results["relations_verified"]
            },
            "statistics": self.verification_results["stats"],
            "errors": self.verification_results["errors"],
            "warnings": self.verification_results["warnings"]
        }
        
        # Guardar informe en archivo
        report_file = f"nevir_database_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Informe guardado en {report_file}")
        return report

async def main():
    """Función principal"""
    # Verificar argumentos
    proveedor_nombre = "NEVIR"
    if len(sys.argv) > 1:
        proveedor_nombre = sys.argv[1]
    
    # Iniciar verificación
    verifier = OdooDatabaseVerifier(proveedor_nombre)
    
    # Ejecutar pasos de verificación
    tables_valid = await verifier.verify_database_tables()
    if not tables_valid:
        logger.error("Las tablas de la base de datos no son válidas. Abortando verificación.")
        report = verifier.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    provider_valid = await verifier.verify_provider()
    if not provider_valid:
        logger.error(f"El proveedor {proveedor_nombre} no es válido. Abortando verificación.")
        report = verifier.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    products_valid = await verifier.verify_products()
    if not products_valid:
        logger.error("Los productos no son válidos. Abortando verificación.")
        report = verifier.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    relations_valid = await verifier.verify_product_supplier_relations()
    
    # Generar informe final
    report = verifier.generate_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # Salir con código de error si la verificación falló
    if not relations_valid:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
