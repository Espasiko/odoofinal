#!/usr/bin/env python3
"""
Script para gestionar la importación de productos NEVIR en Odoo 18 con integración de IA.
Este script:
1. Valida el archivo Excel de entrada
2. Utiliza el endpoint FastAPI para la importación con IA
3. Verifica la correcta creación/actualización en Odoo
4. Genera informes detallados del proceso
"""
import os
import sys
import json
import time
import logging
import asyncio
import argparse
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
        logging.FileHandler('nevir_import_manager.log')
    ]
)
logger = logging.getLogger("nevir_import_manager")

# Importar las funciones necesarias
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from validate_nevir_import import NevitImportValidator
from verify_nevir_database import OdooDatabaseVerifier

# Cargar variables de entorno
load_dotenv()

class NevitImportManager:
    """Clase para gestionar la importación de productos NEVIR en Odoo"""
    
    def __init__(self, excel_path: str, use_ai: bool = True, verify_db: bool = True):
        """
        Inicializa el gestor de importación
        
        Args:
            excel_path: Ruta al archivo Excel de NEVIR
            use_ai: Si se debe usar IA para la importación
            verify_db: Si se debe verificar la base de datos después de la importación
        """
        self.excel_path = excel_path
        self.use_ai = use_ai
        self.verify_db = verify_db
        self.proveedor_nombre = None
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "excel_file": excel_path,
            "use_ai": use_ai,
            "verify_db": verify_db,
            "validation_success": False,
            "import_success": False,
            "db_verification_success": False,
            "overall_success": False,
            "errors": [],
            "warnings": [],
            "stats": {
                "total_products": 0,
                "imported_products": 0,
                "verified_products": 0
            }
        }
    
    async def extract_provider_name(self) -> str:
        """
        Extrae el nombre del proveedor del Excel
        
        Returns:
            str: Nombre del proveedor
        """
        try:
            # Leer datos del proveedor
            df_proveedor = pd.read_excel(self.excel_path, sheet_name='DATOS_PROVEEDOR')
            proveedor_data = {}
            for _, row in df_proveedor.iterrows():
                campo = row['campo']
                valor = row['valor']
                if pd.notna(valor):
                    proveedor_data[campo] = valor
            
            # Obtener nombre del proveedor
            proveedor_nombre = proveedor_data.get('name', 'NEVIR')
            self.proveedor_nombre = proveedor_nombre
            return proveedor_nombre
        except Exception as e:
            logger.error(f"Error extrayendo nombre del proveedor: {str(e)}")
            self.proveedor_nombre = "NEVIR"
            return "NEVIR"
    
    async def run_validation(self) -> bool:
        """
        Ejecuta la validación del Excel
        
        Returns:
            bool: True si la validación fue exitosa, False en caso contrario
        """
        logger.info(f"Validando Excel: {self.excel_path}")
        
        try:
            # Crear validador
            validator = NevitImportValidator(self.excel_path)
            
            # Validar estructura del Excel
            structure_valid = await validator.validate_excel_structure()
            if not structure_valid:
                logger.error("La estructura del Excel no es válida")
                self.results["errors"].extend(validator.validation_results["errors"])
                return False
            
            # Validar calidad de los datos
            data_valid = await validator.validate_data_quality()
            if not data_valid:
                logger.error("Los datos no son válidos")
                self.results["errors"].extend(validator.validation_results["errors"])
                self.results["warnings"].extend(validator.validation_results["warnings"])
                return False
            
            # Actualizar estadísticas
            self.results["stats"]["total_products"] = validator.validation_results["stats"]["total_products"]
            
            # Validación exitosa
            self.results["validation_success"] = True
            logger.info("Validación exitosa")
            return True
            
        except Exception as e:
            logger.error(f"Error en la validación: {str(e)}")
            self.results["errors"].append(f"Error en la validación: {str(e)}")
            return False
    
    async def run_import(self) -> bool:
        """
        Ejecuta la importación del Excel
        
        Returns:
            bool: True si la importación fue exitosa, False en caso contrario
        """
        logger.info(f"Importando Excel: {self.excel_path}")
        
        try:
            # Extraer nombre del proveedor si no se ha hecho
            if not self.proveedor_nombre:
                await self.extract_provider_name()
            
            # Preparar la importación
            if self.use_ai:
                # Usar el endpoint FastAPI con IA
                logger.info("Usando endpoint FastAPI con IA")
                validator = NevitImportValidator(self.excel_path)
                import_success = await validator.import_data_via_api()
                
                if import_success:
                    # Actualizar estadísticas
                    self.results["stats"]["imported_products"] = validator.validation_results["stats"]["imported_products"]
                    self.results["import_success"] = True
                    logger.info(f"Importación exitosa: {self.results['stats']['imported_products']} productos importados")
                    
                    # Guardar detalles de la importación
                    self.import_details = validator.import_details
                    return True
                else:
                    logger.error("La importación falló")
                    self.results["errors"].extend(validator.validation_results["errors"])
                    return False
            else:
                # Usar el script de importación sin IA
                logger.info("Usando script de importación sin IA")
                
                # Ejecutar el script test_nevir_import.py
                cmd = [
                    sys.executable,
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_nevir_import.py"),
                    self.excel_path
                ]
                
                import subprocess
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"Error en la importación: {stderr.decode('utf-8')}")
                    self.results["errors"].append(f"Error en la importación: {stderr.decode('utf-8')}")
                    return False
                
                # Intentar extraer estadísticas
                try:
                    output = stdout.decode('utf-8')
                    import re
                    match = re.search(r'(\d+) productos creados o actualizados', output)
                    if match:
                        self.results["stats"]["imported_products"] = int(match.group(1))
                except Exception:
                    self.results["stats"]["imported_products"] = 0
                
                self.results["import_success"] = True
                logger.info(f"Importación exitosa: {self.results['stats']['imported_products']} productos importados")
                return True
            
        except Exception as e:
            logger.error(f"Error en la importación: {str(e)}")
            self.results["errors"].append(f"Error en la importación: {str(e)}")
            return False
    
    async def run_db_verification(self) -> bool:
        """
        Ejecuta la verificación de la base de datos
        
        Returns:
            bool: True si la verificación fue exitosa, False en caso contrario
        """
        if not self.verify_db:
            logger.info("Verificación de base de datos desactivada")
            return True
        
        logger.info(f"Verificando base de datos para proveedor: {self.proveedor_nombre}")
        
        try:
            # Crear verificador
            verifier = OdooDatabaseVerifier(self.proveedor_nombre)
            
            # Verificar tablas
            tables_valid = await verifier.verify_database_tables()
            if not tables_valid:
                logger.error("Las tablas de la base de datos no son válidas")
                self.results["errors"].extend(verifier.verification_results["errors"])
                return False
            
            # Verificar proveedor
            provider_valid = await verifier.verify_provider()
            if not provider_valid:
                logger.error(f"El proveedor {self.proveedor_nombre} no es válido")
                self.results["errors"].extend(verifier.verification_results["errors"])
                return False
            
            # Verificar productos
            products_valid = await verifier.verify_products()
            if not products_valid:
                logger.error("Los productos no son válidos")
                self.results["errors"].extend(verifier.verification_results["errors"])
                self.results["warnings"].extend(verifier.verification_results["warnings"])
                return False
            
            # Verificar relaciones
            relations_valid = await verifier.verify_product_supplier_relations()
            
            # Actualizar estadísticas
            self.results["stats"]["verified_products"] = verifier.verification_results["stats"]["products_with_supplier"]
            
            # Verificación exitosa si hay relaciones válidas
            self.results["db_verification_success"] = relations_valid
            
            if relations_valid:
                logger.info("Verificación de base de datos exitosa")
            else:
                logger.warning("Verificación de base de datos con advertencias")
                self.results["warnings"].extend(verifier.verification_results["warnings"])
            
            return relations_valid
            
        except Exception as e:
            logger.error(f"Error en la verificación de base de datos: {str(e)}")
            self.results["errors"].append(f"Error en la verificación de base de datos: {str(e)}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Genera un informe detallado del proceso
        
        Returns:
            Dict[str, Any]: Informe detallado
        """
        logger.info("Generando informe final")
        
        # Calcular resultado global
        self.results["overall_success"] = (
            self.results["validation_success"] and
            self.results["import_success"] and
            (self.results["db_verification_success"] if self.verify_db else True)
        )
        
        # Guardar informe en archivo
        report_file = f"nevir_import_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Informe guardado en {report_file}")
        return self.results

async def main():
    """Función principal"""
    # Configurar argumentos
    parser = argparse.ArgumentParser(description='Importar productos NEVIR en Odoo 18')
    parser.add_argument('excel_path', help='Ruta al archivo Excel de NEVIR')
    parser.add_argument('--no-ai', dest='use_ai', action='store_false', help='No usar IA para la importación')
    parser.add_argument('--no-verify', dest='verify_db', action='store_false', help='No verificar la base de datos')
    parser.set_defaults(use_ai=True, verify_db=True)
    
    args = parser.parse_args()
    
    # Verificar que el archivo existe
    if not os.path.exists(args.excel_path):
        print(f"Error: El archivo {args.excel_path} no existe")
        sys.exit(1)
    
    # Iniciar gestor de importación
    manager = NevitImportManager(args.excel_path, args.use_ai, args.verify_db)
    
    # Extraer nombre del proveedor
    await manager.extract_provider_name()
    
    # Ejecutar validación
    validation_success = await manager.run_validation()
    if not validation_success:
        logger.error("La validación falló. Abortando importación.")
        report = manager.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    # Ejecutar importación
    import_success = await manager.run_import()
    if not import_success:
        logger.error("La importación falló.")
        report = manager.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    # Ejecutar verificación de base de datos
    if args.verify_db:
        db_verification_success = await manager.run_db_verification()
        if not db_verification_success:
            logger.warning("La verificación de base de datos encontró problemas.")
    
    # Generar informe final
    report = manager.generate_report()
    
    # Mostrar resumen
    print("\n=== RESUMEN DE IMPORTACIÓN ===")
    print(f"Archivo Excel: {args.excel_path}")
    print(f"Proveedor: {manager.proveedor_nombre}")
    print(f"Uso de IA: {'Sí' if args.use_ai else 'No'}")
    print(f"Verificación de BD: {'Sí' if args.verify_db else 'No'}")
    print(f"Productos totales: {report['stats']['total_products']}")
    print(f"Productos importados: {report['stats']['imported_products']}")
    
    if args.verify_db:
        print(f"Productos verificados: {report['stats']['verified_products']}")
    
    print(f"Resultado: {'ÉXITO' if report['overall_success'] else 'ERROR'}")
    
    if report['errors']:
        print("\nErrores:")
        for error in report['errors']:
            print(f"- {error}")
    
    if report['warnings']:
        print("\nAdvertencias:")
        for warning in report['warnings']:
            print(f"- {warning}")
    
    print(f"\nInforme detallado guardado en: {os.path.abspath(f'nevir_import_report_{time.strftime('%Y%m%d_%H%M%S')}.json')}")
    
    # Salir con código de error si la importación falló
    if not report['overall_success']:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
