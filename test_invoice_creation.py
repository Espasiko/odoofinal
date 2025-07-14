#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from datetime import datetime
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio api al path para poder importar los módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

# Importar el servicio de facturas
from api.services.odoo_invoice_service import OdooInvoiceService

def test_create_invoice():
    """Prueba la creación de una factura de proveedor"""
    
    # Crear instancia del servicio
    invoice_service = OdooInvoiceService()
    
    # ID del proveedor (ALMCE, ID 53)
    partner_id = 53
    
    # Datos de la factura
    invoice_number = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    invoice_date = datetime.now().strftime('%Y-%m-%d')
    
    # Líneas de la factura
    lines = [
        {
            "name": "Producto de prueba 1",
            "quantity": 2,
            "price_unit": 100.0,
        },
        {
            "name": "Producto de prueba 2",
            "quantity": 1,
            "price_unit": 50.0,
        }
    ]
    
    # Crear la factura
    logger.info(f"Creando factura de prueba para el proveedor {partner_id}")
    try:
        result = invoice_service.create_supplier_invoice(
            partner_id=partner_id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            lines=lines
        )
        
        logger.info(f"Resultado de la creación: {json.dumps(result, indent=2)}")
        
        # Si la factura se creó correctamente, obtener los detalles
        if result.get("success") and result.get("id"):
            invoice_id = result["id"]
            logger.info(f"Factura creada con ID: {invoice_id}")
            
            # Si el ID es una lista, extraer el primer elemento
            if isinstance(invoice_id, list):
                invoice_id = invoice_id[0]
                logger.info(f"Extrayendo ID de la lista: {invoice_id}")
            
            # Obtener detalles de la factura
            invoice_data = invoice_service._execute_kw(
                "account.move",
                "read",
                [[invoice_id]],
                {"fields": ["name", "ref", "partner_id", "journal_id", "company_id", "invoice_line_ids"]}
            )
            
            if invoice_data:
                logger.info(f"Detalles de la factura: {json.dumps(invoice_data[0], indent=2, default=str)}")
                
                # Obtener líneas de la factura
                line_ids = invoice_data[0]["invoice_line_ids"]
                line_data = invoice_service._execute_kw(
                    "account.move.line",
                    "read",
                    [line_ids],
                    {"fields": ["name", "account_id", "quantity", "price_unit"]}
                )
                
                logger.info(f"Líneas de la factura: {json.dumps(line_data, indent=2, default=str)}")
            else:
                logger.error("No se pudieron obtener los detalles de la factura")
        else:
            logger.error(f"Error al crear la factura: {result.get('error', 'Error desconocido')}")
    
    except Exception as e:
        logger.error(f"Error al crear la factura: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_create_invoice()
