#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Importación Automatizada de Productos CECOTEC
Creado: 16/06/2025
Propósito: Importar productos desde CSV con configuraciones optimizadas
"""

import csv
import xmlrpc.client
import sys
import os
from datetime import datetime

# Configuración de conexión a Odoo
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'manus_odoo-bd'
ODOO_USERNAME = 'yo@mail.com'
ODOO_PASSWORD = 'admin'

def conectar_odoo():
    """Establece conexión con Odoo"""
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            raise Exception("Error de autenticación")
            
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        return models, uid
    except Exception as e:
        print(f"Error conectando a Odoo: {e}")
        return None, None

def crear_proveedor_cecotec(models, uid):
    """Crea el proveedor CECOTEC si no existe"""
    proveedor = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
        'res.partner', 'search_read',
        [[['name', '=', 'CECOTEC']]],
        {'fields': ['id'], 'limit': 1}
    )
    
    if not proveedor:
        print("Creando proveedor CECOTEC...")
        proveedor_data = {
            'name': 'CECOTEC',
            'is_company': True,
            'supplier_rank': 1,
            'customer_rank': 0,
            'category_id': [(6, 0, [])],
            'street': 'Av. Reyes de España, 24',
            'city': 'Valencia',
            'zip': '46010',
            'country_id': 68,  # España
            'phone': '+34 963 210 728',
            'email': 'info@cecotec.es',
            'website': 'https://www.cecotec.es'
        }
        
        proveedor_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'create', [proveedor_data]
        )
        print(f"✓ Proveedor CECOTEC creado con ID: {proveedor_id}")
        return proveedor_id
    else:
        return proveedor[0]['id']

def crear_categoria_cecotec(models, uid):
    """Crea la categoría CECOTEC si no existe"""
    categoria = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
        'product.category', 'search_read',
        [[['name', '=', 'CECOTEC']]],
        {'fields': ['id'], 'limit': 1}
    )
    
    if not categoria:
        print("Creando categoría CECOTEC...")
        categoria_data = {
            'name': 'CECOTEC',
            'parent_id': False
        }
        
        categoria_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.category', 'create', [categoria_data]
        )
        print(f"✓ Categoría CECOTEC creada con ID: {categoria_id}")
        return categoria_id
    else:
        return categoria[0]['id']

def crear_etiqueta_cecotec(models, uid):
    """Crea la etiqueta CECOTEC si no existe"""
    etiqueta = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
        'product.tag', 'search_read',
        [[['name', '=', 'CECOTEC']]],
        {'fields': ['id'], 'limit': 1}
    )
    
    if not etiqueta:
        print("Creando etiqueta CECOTEC...")
        etiqueta_data = {
            'name': 'CECOTEC',
            'color': 5  # Color azul
        }
        
        etiqueta_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.tag', 'create', [etiqueta_data]
        )
        print(f"✓ Etiqueta CECOTEC creada con ID: {etiqueta_id}")
        return etiqueta_id
    else:
        return etiqueta[0]['id']

def obtener_ids_referencia(models, uid):
    """Obtiene IDs de referencias necesarias, creándolas si no existen"""
    referencias = {}
    
    # Crear/obtener proveedor CECOTEC
    referencias['proveedor_cecotec'] = crear_proveedor_cecotec(models, uid)
    
    # Crear/obtener categoría CECOTEC
    referencias['categoria_cecotec'] = crear_categoria_cecotec(models, uid)
    
    # Crear/obtener etiqueta CECOTEC
    referencias['etiqueta_cecotec'] = crear_etiqueta_cecotec(models, uid)
    
    # Impuestos 21%
    impuesto_venta = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
        'account.tax', 'search_read',
        [[['amount', '=', 21.0], ['type_tax_use', '=', 'sale']]],
        {'fields': ['id'], 'limit': 1}
    )
    referencias['impuesto_venta'] = impuesto_venta[0]['id'] if impuesto_venta else None
    
    impuesto_compra = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
        'account.tax', 'search_read',
        [[['amount', '=', 21.0], ['type_tax_use', '=', 'purchase']]],
        {'fields': ['id'], 'limit': 1}
    )
    referencias['impuesto_compra'] = impuesto_compra[0]['id'] if impuesto_compra else None
    
    return referencias

def procesar_csv_productos(archivo_csv, models, uid, referencias):
    """Procesa el archivo CSV y crea productos"""
    productos_creados = 0
    productos_error = 0
    errores = []
    
    print(f"Procesando archivo: {archivo_csv}")
    
    try:
        with open(archivo_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Procesar datos del producto desde CSV (corrección indentación)
                    tipo = row['type'].strip().lower()
                    if tipo in ['product', 'consu', 'service']:
                        tipo_final = tipo
                    else:
                        tipo_final = 'product'
                    producto_data = {
                        'name': row['name'],
                        'default_code': row['default_code'],
                        'list_price': float(row['list_price']),
                        'standard_price': float(row['standard_price']),
                        'type': tipo_final,
                        'sale_ok': row['sale_ok'].lower() == 'true',
                        'purchase_ok': row['purchase_ok'].lower() == 'true',
                        'active': row['active'].lower() == 'true',
                        'available_in_pos': row['available_in_pos'].lower() == 'true',
                        'to_weight': row['to_weight'].lower() == 'true',
                        'is_published': row['is_published'].lower() == 'true',
                        'website_sequence': int(row['website_sequence']) if row['website_sequence'] else 1,
                        'categ_id': referencias['categoria_cecotec'],
                        'product_tag_ids': [(6, 0, [referencias['etiqueta_cecotec']])],
                        'taxes_id': [(6, 0, [referencias['impuesto_venta']])],
                        'supplier_taxes_id': [(6, 0, [referencias['impuesto_compra']])],
                        'description_sale': row['description_sale'] if row['description_sale'] else f"Producto {row['name']} para venta",
                        'description_purchase': row['description_purchase'] if row['description_purchase'] else f"Producto {row['name']} para compra"
                    }
                    
                    # Agregar barcode si existe
                    if row['barcode']:
                        producto_data['barcode'] = row['barcode']
                    
                    # Verificar si el producto ya existe
                    producto_existente = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'product.template', 'search',
                        [[['default_code', '=', row['default_code']]]]
                    )
                    
                    if producto_existente:
                        print(f"Producto {row['default_code']} ya existe, actualizando...")
                        producto_id = producto_existente[0]
                        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                            'product.template', 'write',
                            [producto_existente, producto_data]
                        )
                    else:
                        # Crear nuevo producto
                        producto_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                            'product.template', 'create',
                            [producto_data]
                        )
                        print(f"✓ Producto {row['default_code']} creado con ID: {producto_id}")
                    
                    # Gestionar información del proveedor usando seller_ids
                    if referencias['proveedor_cecotec'] and row.get('seller_ids/partner_id'):
                        # Buscar si ya existe información del proveedor
                        existing_supplier = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                            'product.supplierinfo', 'search',
                            [[['product_tmpl_id', '=', producto_id], 
                              ['partner_id', '=', referencias['proveedor_cecotec']]]]
                        )
                        
                        supplier_info = {
                            'partner_id': referencias['proveedor_cecotec'],
                            'product_tmpl_id': producto_id,
                            'price': float(row['standard_price']),
                            'min_qty': 1.0,
                            'delay': 7  # 7 días de plazo de entrega
                        }
                        
                        if existing_supplier:
                            # Actualizar información existente
                            models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                'product.supplierinfo', 'write',
                                [existing_supplier, supplier_info]
                            )
                        else:
                            # Crear nueva información del proveedor
                            models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                'product.supplierinfo', 'create',
                                [supplier_info]
                            )
                    
                    productos_creados += 1
                    print(f"✓ Producto {row['default_code']} procesado correctamente")
                    
                except Exception as e:
                    productos_error += 1
                    error_msg = f"Fila {row_num}: {str(e)}"
                    errores.append(error_msg)
                    print(f"✗ Error en fila {row_num}: {e}")
                    
    except Exception as e:
        print(f"Error leyendo archivo CSV: {e}")
        return 0, 0, [str(e)]
    
    return productos_creados, productos_error, errores

def main():
    """Función principal"""
    print("=== IMPORTACIÓN AUTOMATIZADA DE PRODUCTOS CECOTEC ===")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Conectar a Odoo
    models, uid = conectar_odoo()
    if not models or not uid:
        print("Error: No se pudo conectar a Odoo")
        sys.exit(1)
    
    print("✓ Conexión a Odoo establecida")
    
    # Obtener referencias
    referencias = obtener_ids_referencia(models, uid)
    print(f"✓ Referencias obtenidas: {referencias}")
    
    # Verificar que tenemos las referencias necesarias
    if not all([referencias['proveedor_cecotec'], referencias['categoria_cecotec'], 
                referencias['etiqueta_cecotec']]):
        print("Error: Faltan referencias necesarias en Odoo")
        print("Ejecute primero las configuraciones previas")
        sys.exit(1)
    
    # Procesar archivo CSV
    archivo_csv = '/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/PVP_CECOTEC_template.csv'
    
    if not os.path.exists(archivo_csv):
        print(f"Error: No se encuentra el archivo {archivo_csv}")
        sys.exit(1)
    
    productos_ok, productos_error, errores = procesar_csv_productos(
        archivo_csv, models, uid, referencias
    )
    
    # Resumen final
    print()
    print("=== RESUMEN DE IMPORTACIÓN ===")
    print(f"Productos procesados correctamente: {productos_ok}")
    print(f"Productos con errores: {productos_error}")
    
    if errores:
        print("\nErrores encontrados:")
        for error in errores[:10]:  # Mostrar solo los primeros 10 errores
            print(f"  - {error}")
        if len(errores) > 10:
            print(f"  ... y {len(errores) - 10} errores más")
    
    print("\n=== IMPORTACIÓN COMPLETADA ===")

if __name__ == '__main__':
    main()