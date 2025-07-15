#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar y crear un diario de compras para la compañía "El pelotazo" (ID 1) en Odoo 18

Este script utiliza XML-RPC para conectarse a Odoo y verificar si existe un diario de compras
para la compañía "El pelotazo" (ID 1). Si no existe, lo crea.

Uso:
    python3 crear_diario_compras.py
"""

import xmlrpc.client
import logging
import sys
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de conexión a Odoo
ODOO_URL = "http://localhost:8069"
ODOO_DB = "fresh_odoo_db"  # Nombre correcto de la base de datos según la memoria
ODOO_USER = "admin"
ODOO_PASSWORD = "admin"

def verificar_o_crear_diario_compras(company_id=1):
    """
    Verifica si existe un diario de compras para la compañía especificada.
    Si no existe, lo crea.
    
    Args:
        company_id (int): ID de la compañía para la que verificar/crear el diario de compras
        
    Returns:
        dict: Información del diario de compras encontrado o creado
    """
    try:
        # Conectar con Odoo
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        
        if not uid:
            logger.error("Error de autenticación con Odoo")
            return {"success": False, "error": "Error de autenticación"}
            
        logger.info(f"Conexión exitosa a Odoo como usuario ID: {uid}")
        
        # Crear proxy para llamar a métodos
        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
        
        # Verificar si la compañía existe
        company = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.company',
            'search_read',
            [[('id', '=', company_id)]],
            {'fields': ['name']}
        )
        
        if not company:
            logger.error(f"La compañía con ID {company_id} no existe")
            return {"success": False, "error": f"La compañía con ID {company_id} no existe"}
            
        company_name = company[0]['name']
        logger.info(f"Verificando diario de compras para la compañía: {company_name} (ID: {company_id})")
        
        # Verificar si ya existe un diario de compras para esta compañía
        existing_journals = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.journal',
            'search_read',
            [[('company_id', '=', company_id), ('type', '=', 'purchase')]],
            {'fields': ['id', 'name', 'code', 'default_account_id']}
        )
        
        if existing_journals:
            journal = existing_journals[0]
            logger.info(f"Ya existe un diario de compras para la compañía {company_id}: {journal}")
            return {"success": True, "journal": journal, "exists": True}
        
        logger.info(f"No existe un diario de compras para la compañía {company_id}. Creando uno nuevo...")
        
        # Buscar una cuenta contable de gastos para usar como default_account_id
        expense_accounts = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.account',
            'search_read',
            [[('account_type', '=', 'expense')]],
            {'fields': ['id', 'name', 'code_store']}
        )
        
        # Filtrar las cuentas para la compañía específica
        company_expense_accounts = []
        for account in expense_accounts:
            # En Odoo 18, verificamos si la cuenta tiene código para esta compañía
            if account.get('code_store') and str(company_id) in account.get('code_store', {}):
                company_expense_accounts.append(account)
        
        if not company_expense_accounts:
            logger.error(f"No se encontraron cuentas de gastos para la compañía {company_id}")
            return {"success": False, "error": "No hay cuentas de gastos disponibles"}
        
        # Usar la primera cuenta de gastos encontrada
        default_account_id = company_expense_accounts[0]['id']
        account_name = company_expense_accounts[0]['name']
        if isinstance(account_name, dict):
            account_name = account_name.get('es_ES', list(account_name.values())[0])
        logger.info(f"Usando cuenta contable: {account_name} (ID: {default_account_id})")
        
        # Crear el diario de compras con los campos correctos según Odoo 18
        journal_vals = {
            'name': {"es_ES": "Facturas de proveedores", "en_US": "Vendor Bills"},
            'code': 'BILL',
            'type': 'purchase',
            'default_account_id': default_account_id,
            'company_id': company_id,
            'show_on_dashboard': True,
        }
        
        journal_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.journal',
            'create',
            [journal_vals]
        )
        
        logger.info(f"Diario de compras creado con ID: {journal_id}")
        
        # Obtener información del diario creado
        new_journal = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.journal',
            'read',
            [[journal_id]],
            {'fields': ['id', 'name', 'code', 'default_account_id']}
        )[0]
        
        return {"success": True, "journal": new_journal, "exists": False}
        
    except Exception as e:
        logger.error(f"Error al verificar/crear el diario de compras: {e}")
        return {"success": False, "error": str(e)}

def main():
    logger.info("Iniciando verificación/creación de diario de compras para la compañía 'El pelotazo' (ID: 1)")
    result = verificar_o_crear_diario_compras(company_id=1)
    
    if result["success"]:
        if result.get("exists", False):
            journal = result["journal"]
            journal_name = journal["name"]
            if isinstance(journal_name, dict):
                journal_name = journal_name.get("es_ES", list(journal_name.values())[0])
            logger.info(f"Diario de compras encontrado: {journal_name} (ID: {journal['id']})")
            logger.info(f"Cuenta contable asociada: ID {journal.get('default_account_id', [0, ''])[0]}")
        else:
            journal = result["journal"]
            journal_name = journal["name"]
            if isinstance(journal_name, dict):
                journal_name = journal_name.get("es_ES", list(journal_name.values())[0])
            logger.info(f"Diario de compras creado: {journal_name} (ID: {journal['id']})")
    else:
        logger.error(f"Error: {result.get('error', 'Desconocido')}")

if __name__ == "__main__":
    main()
