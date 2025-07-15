#!/usr/bin/env python3
"""
Script para validar la importación de productos NEVIR en Odoo 18.
Este script:
1. Verifica la estructura del Excel de NEVIR
2. Valida los datos antes de la importación
3. Utiliza el endpoint FastAPI para la importación con IA
4. Verifica la correcta creación/actualización en Odoo
5. Genera un informe detallado del proceso
"""
import os
import sys
import json
import time
import logging
import asyncio
import requests
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('validate_nevir_import.log')
    ]
)
logger = logging.getLogger("validate_nevir_import")

# Importar las funciones necesarias
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.services.odoo_provider_service import OdooProviderService
from api.services.odoo_product_service import OdooProductService

# Cargar variables de entorno
load_dotenv()

# URL del endpoint
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ENDPOINT = "/api/v1/importer/"
URL = f"{BASE_URL}{ENDPOINT}"

class NevitImportValidator:
    """Clase para validar la importación de productos NEVIR en Odoo"""
    
    def __init__(self, excel_path: str):
        """
        Inicializa el validador con la ruta al archivo Excel
        
        Args:
            excel_path: Ruta al archivo Excel de NEVIR
        """
        self.excel_path = excel_path
        self.provider_service = OdooProviderService()
        self.product_service = OdooProductService()
        self.validation_results = {
            "excel_structure": False,
            "data_quality": False,
            "import_success": False,
            "odoo_verification": False,
            "errors": [],
            "warnings": [],
            "stats": {
                "total_products": 0,
                "valid_products": 0,
                "products_with_warnings": 0,
                "products_with_errors": 0,
                "imported_products": 0,
                "verified_products": 0
            }
        }
        
    async def validate_excel_structure(self) -> bool:
        """
        Verifica que el Excel tenga la estructura esperada
        
        Returns:
            bool: True si la estructura es válida, False en caso contrario
        """
        logger.info(f"Validando estructura del Excel: {self.excel_path}")
        
        try:
            # Verificar que el archivo existe
            if not os.path.exists(self.excel_path):
                self.validation_results["errors"].append(f"El archivo {self.excel_path} no existe")
                return False
            
            # Verificar que se puede abrir como Excel
            try:
                xls = pd.ExcelFile(self.excel_path)
            except Exception as e:
                self.validation_results["errors"].append(f"Error al abrir el archivo Excel: {str(e)}")
                return False
            
            # Verificar que contiene las hojas necesarias
            required_sheets = ['DATOS_PROVEEDOR', 'PRODUCTOS']
            missing_sheets = [sheet for sheet in required_sheets if sheet not in xls.sheet_names]
            
            if missing_sheets:
                self.validation_results["errors"].append(f"Faltan las siguientes hojas en el Excel: {missing_sheets}")
                return False
            
            # Verificar estructura de la hoja DATOS_PROVEEDOR
            df_proveedor = pd.read_excel(self.excel_path, sheet_name='DATOS_PROVEEDOR')
            if 'campo' not in df_proveedor.columns or 'valor' not in df_proveedor.columns:
                self.validation_results["errors"].append("La hoja DATOS_PROVEEDOR debe tener las columnas 'campo' y 'valor'")
                return False
            
            # Verificar campos mínimos del proveedor
            required_provider_fields = ['name', 'vat']
            provider_fields = df_proveedor['campo'].tolist()
            missing_provider_fields = [field for field in required_provider_fields if field not in provider_fields]
            
            if missing_provider_fields:
                self.validation_results["warnings"].append(f"Faltan los siguientes campos del proveedor: {missing_provider_fields}")
            
            # Verificar estructura de la hoja PRODUCTOS
            df_productos = pd.read_excel(self.excel_path, sheet_name='PRODUCTOS')
            if len(df_productos.columns) < 3:
                self.validation_results["errors"].append("La hoja PRODUCTOS debe tener al menos 3 columnas")
                return False
            
            # Todo correcto
            self.validation_results["excel_structure"] = True
            logger.info("Estructura del Excel validada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error validando estructura del Excel: {str(e)}")
            self.validation_results["errors"].append(f"Error validando estructura del Excel: {str(e)}")
            return False
    
    async def validate_data_quality(self) -> bool:
        """
        Valida la calidad de los datos en el Excel
        
        Returns:
            bool: True si los datos son válidos, False en caso contrario
        """
        logger.info("Validando calidad de los datos")
        
        try:
            # Leer datos del proveedor
            df_proveedor = pd.read_excel(self.excel_path, sheet_name='DATOS_PROVEEDOR')
            proveedor_data = {}
            for _, row in df_proveedor.iterrows():
                campo = row['campo']
                valor = row['valor']
                if pd.notna(valor):
                    proveedor_data[campo] = valor
            
            # Verificar datos mínimos del proveedor
            if 'name' not in proveedor_data or not proveedor_data['name']:
                self.validation_results["errors"].append("El proveedor debe tener un nombre")
                return False
            
            # Leer datos de productos
            df_productos = pd.read_excel(self.excel_path, sheet_name='PRODUCTOS')
            productos_data = []
            for _, row in df_productos.iterrows():
                producto = {}
                for column in df_productos.columns:
                    if pd.notna(row[column]):
                        producto[column.lower()] = row[column]
                productos_data.append(producto)
            
            # Estadísticas iniciales
            self.validation_results["stats"]["total_products"] = len(productos_data)
            valid_products = 0
            products_with_warnings = 0
            products_with_errors = 0
            
            # Validar cada producto
            for idx, producto in enumerate(productos_data):
                product_valid = True
                product_warnings = []
                
                # Verificar nombre
                if 'nombre' not in producto and 'name' not in producto:
                    product_warnings.append(f"Producto {idx+1} sin nombre")
                    product_valid = False
                
                # Verificar referencia
                has_reference = False
                for ref_field in ['codigo', 'default_code', 'barcode', 'ean13', 'referencia']:
                    if ref_field in producto and producto[ref_field]:
                        has_reference = True
                        break
                
                if not has_reference:
                    product_warnings.append(f"Producto {idx+1} sin referencia")
                
                # Verificar precios
                if ('precio' not in producto and 'price' not in producto and 
                    'precio_venta' not in producto and 'list_price' not in producto):
                    product_warnings.append(f"Producto {idx+1} sin precio de venta")
                
                # Contabilizar producto
                if product_valid:
                    valid_products += 1
                else:
                    products_with_errors += 1
                
                if product_warnings:
                    products_with_warnings += 1
                    for warning in product_warnings:
                        self.validation_results["warnings"].append(warning)
            
            # Actualizar estadísticas
            self.validation_results["stats"]["valid_products"] = valid_products
            self.validation_results["stats"]["products_with_warnings"] = products_with_warnings
            self.validation_results["stats"]["products_with_errors"] = products_with_errors
            
            # Validación exitosa si hay al menos un producto válido
            if valid_products > 0:
                self.validation_results["data_quality"] = True
                logger.info(f"Datos validados: {valid_products}/{len(productos_data)} productos válidos")
                return True
            else:
                self.validation_results["errors"].append("No hay productos válidos para importar")
                return False
            
        except Exception as e:
            logger.error(f"Error validando calidad de los datos: {str(e)}")
            self.validation_results["errors"].append(f"Error validando calidad de los datos: {str(e)}")
            return False
    
    async def import_data_via_api(self) -> bool:
        """
        Importa los datos utilizando el endpoint FastAPI
        
        Returns:
            bool: True si la importación fue exitosa, False en caso contrario
        """
        logger.info(f"Importando datos vía API: {URL}")
        
        try:
            # Obtener token de autenticación
            token = self._get_auth_token()
            if not token:
                self.validation_results["errors"].append("No se pudo obtener el token de autenticación")
                return False
            
            # Preparar headers con el token
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            # Extraer nombre del proveedor del Excel
            df_proveedor = pd.read_excel(self.excel_path, sheet_name='DATOS_PROVEEDOR')
            proveedor_data = {}
            for _, row in df_proveedor.iterrows():
                campo = row['campo']
                valor = row['valor']
                if pd.notna(valor):
                    proveedor_data[campo] = valor
            
            proveedor_nombre = proveedor_data.get('name', 'NEVIR')
            
            # Preparar datos del formulario
            data = {
                "proveedor_nombre": proveedor_nombre
            }
            
            # Preparar el archivo
            files = {
                "file": (os.path.basename(self.excel_path), open(self.excel_path, "rb"), 
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            }
            
            # Hacer la solicitud
            logger.info(f"Enviando solicitud a {URL} para proveedor {proveedor_nombre}...")
            response = requests.post(URL, headers=headers, data=data, files=files)
            
            # Verificar respuesta
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Importación exitosa: {result.get('message')}")
                
                # Actualizar estadísticas
                self.validation_results["stats"]["imported_products"] = result.get("total_creados_o_actualizados", 0)
                self.validation_results["import_success"] = True
                
                # Guardar detalles de la importación
                self.import_details = result
                
                return True
            else:
                logger.error(f"Error en la importación: {response.status_code}")
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text
                
                self.validation_results["errors"].append(f"Error en la importación: {error_detail}")
                return False
            
        except Exception as e:
            logger.error(f"Error importando datos vía API: {str(e)}")
            self.validation_results["errors"].append(f"Error importando datos vía API: {str(e)}")
            return False
        finally:
            # Cerrar el archivo
            files["file"][1].close()
    
    async def verify_odoo_data(self) -> bool:
        """
        Verifica que los datos se hayan creado correctamente en Odoo
        
        Returns:
            bool: True si la verificación fue exitosa, False en caso contrario
        """
        logger.info("Verificando datos en Odoo")
        
        try:
            if not hasattr(self, 'import_details'):
                self.validation_results["errors"].append("No hay detalles de importación para verificar")
                return False
            
            # Extraer IDs de productos importados
            productos_creados = self.import_details.get("productos_creados_o_actualizados", [])
            product_ids = [p.get("id") for p in productos_creados if p.get("id")]
            
            if not product_ids:
                self.validation_results["errors"].append("No hay productos importados para verificar")
                return False
            
            # Verificar cada producto en Odoo
            verified_count = 0
            for product_id in product_ids:
                try:
                    # Verificar que el producto existe
                    product = self.product_service.get_product_by_id(product_id)
                    if product:
                        # Verificar que tiene proveedor
                        suppliers = self.product_service.get_product_suppliers(product_id)
                        if suppliers:
                            verified_count += 1
                        else:
                            self.validation_results["warnings"].append(f"Producto {product_id} sin proveedor vinculado")
                    else:
                        self.validation_results["errors"].append(f"Producto {product_id} no encontrado en Odoo")
                except Exception as e:
                    logger.error(f"Error verificando producto {product_id}: {str(e)}")
                    self.validation_results["errors"].append(f"Error verificando producto {product_id}: {str(e)}")
            
            # Actualizar estadísticas
            self.validation_results["stats"]["verified_products"] = verified_count
            
            # Verificación exitosa si se verificaron todos los productos
            if verified_count == len(product_ids):
                self.validation_results["odoo_verification"] = True
                logger.info(f"Verificación exitosa: {verified_count}/{len(product_ids)} productos verificados")
                return True
            else:
                logger.warning(f"Verificación parcial: {verified_count}/{len(product_ids)} productos verificados")
                return verified_count > 0
            
        except Exception as e:
            logger.error(f"Error verificando datos en Odoo: {str(e)}")
            self.validation_results["errors"].append(f"Error verificando datos en Odoo: {str(e)}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Genera un informe detallado del proceso de validación
        
        Returns:
            Dict[str, Any]: Informe detallado
        """
        logger.info("Generando informe de validación")
        
        # Calcular resultado global
        overall_success = (
            self.validation_results["excel_structure"] and
            self.validation_results["data_quality"] and
            self.validation_results["import_success"] and
            self.validation_results["odoo_verification"]
        )
        
        # Crear informe
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "excel_file": self.excel_path,
            "overall_success": overall_success,
            "validation_steps": {
                "excel_structure": self.validation_results["excel_structure"],
                "data_quality": self.validation_results["data_quality"],
                "import_success": self.validation_results["import_success"],
                "odoo_verification": self.validation_results["odoo_verification"]
            },
            "statistics": self.validation_results["stats"],
            "errors": self.validation_results["errors"],
            "warnings": self.validation_results["warnings"]
        }
        
        # Guardar informe en archivo
        report_file = f"nevir_import_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Informe guardado en {report_file}")
        return report
    
    def _get_auth_token(self) -> Optional[str]:
        """
        Obtiene un token de autenticación para la API
        
        Returns:
            Optional[str]: Token de autenticación o None si hay error
        """
        auth_url = f"{BASE_URL}/token"
        auth_data = {
            "username": os.getenv("API_USERNAME", "admin"),
            "password": os.getenv("API_PASSWORD", "admin")
        }
        
        try:
            response = requests.post(auth_url, data=auth_data)
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                logger.error(f"Error de autenticación: {response.status_code}")
                logger.error(response.text)
                return None
        except Exception as e:
            logger.error(f"Error obteniendo token: {str(e)}")
            return None

async def main():
    """Función principal"""
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python validate_nevir_import.py <ruta_excel>")
        sys.exit(1)
    
    excel_path = sys.argv[1]
    
    # Iniciar validación
    validator = NevitImportValidator(excel_path)
    
    # Ejecutar pasos de validación
    structure_valid = await validator.validate_excel_structure()
    if not structure_valid:
        logger.error("La estructura del Excel no es válida. Abortando validación.")
        report = validator.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    data_valid = await validator.validate_data_quality()
    if not data_valid:
        logger.error("Los datos no son válidos. Abortando validación.")
        report = validator.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    import_success = await validator.import_data_via_api()
    if not import_success:
        logger.error("La importación falló. Abortando validación.")
        report = validator.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    verification_success = await validator.verify_odoo_data()
    
    # Generar informe final
    report = validator.generate_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # Salir con código de error si la verificación falló
    if not verification_success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
