#!/usr/bin/env python3
import xmlrpc.client
import sys
from pprint import pprint

# Configuración de conexión a Odoo
url = 'http://localhost:8069'
db = 'fresh_odoo_db'  # Usando la base de datos correcta según las credenciales
username = 'admin'  # Según las credenciales actualizadas
password = 'admin'

# Conectar a Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
if not uid:
    print("Error de autenticación. Verifique las credenciales.")
    sys.exit(1)

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Buscar el proveedor NEVIR
partner_ids = models.execute_kw(db, uid, password, 'res.partner', 'search', 
                               [[('name', '=', 'NEVIR'), ('supplier_rank', '>', 0)]])
print(f"Proveedores encontrados con nombre 'NEVIR': {len(partner_ids)}")

if partner_ids:
    partner_data = models.execute_kw(db, uid, password, 'res.partner', 'read', 
                                    [partner_ids], {'fields': ['id', 'name', 'supplier_rank', 'email', 'vat']})
    print("\nDatos del proveedor NEVIR:")
    pprint(partner_data)

# Buscar productos del proveedor NEVIR
if partner_ids:
    # Buscar productos que tengan a NEVIR como proveedor
    supplier_info_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search', 
                                         [[('partner_id', 'in', partner_ids)]])
    print(f"\nRelaciones producto-proveedor encontradas: {len(supplier_info_ids)}")
    
    if supplier_info_ids:
        supplier_info_data = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', 
                                              [supplier_info_ids], 
                                              {'fields': ['id', 'partner_id', 'product_tmpl_id', 'product_name', 'product_code']})
        print("\nDatos de las relaciones producto-proveedor:")
        pprint(supplier_info_data)
        
        # Obtener IDs de plantillas de productos
        product_tmpl_ids = [item['product_tmpl_id'][0] for item in supplier_info_data if item['product_tmpl_id']]
        
        if product_tmpl_ids:
            product_data = models.execute_kw(db, uid, password, 'product.template', 'read', 
                                           [product_tmpl_ids], 
                                           {'fields': ['id', 'name', 'default_code', 'list_price', 'standard_price', 'categ_id']})
            print("\nDatos de los productos:")
            pprint(product_data)

# Buscar específicamente el congelador vertical
product_ids = models.execute_kw(db, uid, password, 'product.template', 'search', 
                               [[('name', 'ilike', 'CONGELADOR VERTICAL')]])
print(f"\nProductos encontrados con 'CONGELADOR VERTICAL' en el nombre: {len(product_ids)}")

if product_ids:
    product_data = models.execute_kw(db, uid, password, 'product.template', 'read', 
                                    [product_ids], 
                                    {'fields': ['id', 'name', 'default_code', 'list_price', 'standard_price', 'categ_id']})
    print("\nDatos de los productos 'CONGELADOR VERTICAL':")
    pprint(product_data)

# Buscar categorías creadas
category_ids = models.execute_kw(db, uid, password, 'product.category', 'search', 
                                [[('name', '=', 'CONGELADOR')]])
print(f"\nCategorías encontradas con nombre 'CONGELADOR': {len(category_ids)}")

if category_ids:
    category_data = models.execute_kw(db, uid, password, 'product.category', 'read', 
                                     [category_ids], {'fields': ['id', 'name', 'parent_id', 'complete_name']})
    print("\nDatos de las categorías:")
    pprint(category_data)
