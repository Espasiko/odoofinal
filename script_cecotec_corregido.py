#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Importación Automatizada de Productos CECOTEC
Creado: 16/06/2025
Propósito: Importar productos desde CSV con configuraciones optimizadas
VERSIÓN CORREGIDA
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
    try:
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
    except Exception as e:
        print(f"Error creando proveedor CECOTEC: {e}")
        return None

def crear_categoria_cecotec(models, uid):
    """Crea la categoría CECOTEC si no existe"""
    try:
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
    except Exception as e:
        print(f"Error creando categoría CECOTEC: {e}")
        return None

def crear_etiqueta_cecotec(models, uid):
    """Crea la etiqueta CECOTEC si no existe"""
    try:
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
    except Exception as e:
        print(f"Error creando etiqueta CECOTEC: {e}")
        return None

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
    try:
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
    except Exception as e:
        print(f"Advertencia: Error obteniendo impuestos: {e}")
        referencias['impuesto_venta'] = None
        referencias['impuesto_compra'] = None
    
    return referencias

def validar_y_convertir_campo(valor, tipo, default=None):
    """Valida y convierte campos del CSV"""
    if not valor or valor.strip() == '':
        return default
    
    try:
        if tipo == 'float':
            return float(valor.strip())
        elif tipo == 'int':
            return int(valor.strip())
        elif tipo == 'bool':
            return valor.strip().lower() in ['true', '1', 'yes', 'sí']
        else:
            return valor.strip()
    except (ValueError, AttributeError):
        return default

def procesar_csv_productos(archivo_csv, models, uid, referencias):
    """Procesa el archivo CSV y crea productos"""
    productos_creados = 0
    productos_actualizados = 0
    productos_error = 0
    errores = []
    
    print(f"Procesando archivo: {archivo_csv}")
    
    try:
        with open(archivo_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Validar campos obligatorios
                    if not row.get('name') or not row.get('default_code'):
                        raise ValueError("Faltan campos obligatorios: name o default_code")
                    
                    # Preparar datos del producto con validaciones
                    tipo = validar_y_convertir_campo(row.get('type', 'product'), 'str', 'product').lower()
                    if tipo not in ['product', 'consu', 'service']:
                        tipo = 'product'
                    
                    producto_data = {
                        'name': validar_y_convertir_campo(row['name'], 'str', ''),
                        'default_code': validar_y_convertir_campo(row['default_code'], 'str', ''),
                        'list_price': validar_y_convertir_campo(row.get('list_price'), 'float', 0.0),
                        'standard_price': validar_y_convertir_campo(row.get('standard_price'), 'float', 0.0),
                        'type': tipo,
                        'sale_ok': validar_y_convertir_campo(row.get('sale_ok'), 'bool', True),
                        'purchase_ok': validar_y_convertir_campo(row.get('purchase_ok'), 'bool', True),
                        'active': validar_y_convertir_campo(row.get('active'), 'bool', True),
                        'available_in_pos': validar_y_convertir_campo(row.get('available_in_pos'), 'bool', False),
                        'to_weight': validar_y_convertir_campo(row.get('to_weight'), 'bool', False),
                        'is_published': validar_y_convertir_campo(row.get('is_published'), 'bool', False),
                        'website_sequence': validar_y_convertir_campo(row.get('website_sequence'), 'int', 1),
                        'description_sale': validar_y_convertir_campo(
                            row.get('description_sale'), 'str', 
                            f"Producto {row['name']} para venta"
                        ),
                        'description_purchase': validar_y_convertir_campo(
                            row.get('description_purchase'), 'str', 
                            f"Producto {row['name']} para compra"
                        )
                    }
                    
                    # Agregar referencias si existen
                    if referencias.get('categoria_cecotec'):
                        producto_data['categ_id'] = referencias['categoria_cecotec']
                    
                    if referencias.get('etiqueta_cecotec'):
                        producto_data['product_tag_ids'] = [(6, 0, [referencias['etiqueta_cecotec']])]
                    
                    if referencias.get('impuesto_venta'):
                        producto_data['taxes_id'] = [(6, 0, [referencias['impuesto_venta']])]
                    
                    if referencias.get('impuesto_compra'):
                        producto_data['supplier_taxes_id'] = [(6, 0, [referencias['impuesto_compra']])]
                    
                    # Agregar barcode si existe
                    barcode = validar_y_convertir_campo(row.get('barcode'), 'str')
                    if barcode:
                        producto_data['barcode'] = barcode
                    
                    # Verificar si el producto ya existe
                    producto_existente = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'product.template', 'search',
                        [[['default_code', '=', producto_data['default_code']]]]
                    )
                    
                    if producto_existente:
                        # CORRECCIÓN: Usar el ID correcto para actualizar
                        producto_id = producto_existente[0]
                        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                            'product.template', 'write',
                            [producto_id, producto_data]  # ✅ Usar el ID, no la lista
                        )
                        productos_actualizados += 1
                        print(f"✓ Producto {producto_data['default_code']} actualizado (ID: {producto_id})")
                    else:
                        # Crear nuevo producto
                        producto_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                            'product.template', 'create',
                            [producto_data]
                        )
                        productos_creados += 1
                        print(f"✓ Producto {producto_data['default_code']} creado con ID: {producto_id}")
                    
                    # Gestionar información del proveedor
                    if referencias.get('proveedor_cecotec') and producto_data['standard_price'] > 0:
                        try:
                            # Buscar si ya existe información del proveedor
                            existing_supplier = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                'product.supplierinfo', 'search',
                                [[['product_tmpl_id', '=', producto_id], 
                                  ['partner_id', '=', referencias['proveedor_cecotec']]]]
                            )
                            
                            supplier_info = {
                                'partner_id': referencias['proveedor_cecotec'],
                                'product_tmpl_id': producto_id,
                                'price': producto_data['standard_price'],
                                'min_qty': 1.0,
                                'delay': 7  # 7 días de plazo de entrega
                            }
                            
                            if existing_supplier:
                                # Actualizar información existente
                                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                    'product.supplierinfo', 'write',
                                    [existing_supplier[0], supplier_info]  # ✅ Usar el ID
                                )
                            else:
                                # Crear nueva información del proveedor
                                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                    'product.supplierinfo', 'create',
                                    [supplier_info]
                                )
                        except Exception as e:
                            print(f"Advertencia: Error gestionando proveedor para {producto_data['default_code']}: {e}")
                    
                except Exception as e:
                    productos_error += 1
                    error_msg = f"Fila {row_num}: {str(e)}"
                    errores.append(error_msg)
                    print(f"✗ Error en fila {row_num}: {e}")
                    
    except Exception as e:
        print(f"Error leyendo archivo CSV: {e}")
        return 0, 0, 0, [str(e)]
    
    return productos_creados, productos_actualizados, productos_error, errores

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
    print(f"✓ Referencias obtenidas")
    
    # Verificar referencias críticas
    referencias_criticas = ['proveedor_cecotec', 'categoria_cecotec', 'etiqueta_cecotec']
    faltantes = [ref for ref in referencias_criticas if not referencias.get(ref)]
    
    if faltantes:
        print(f"Advertencia: Faltan referencias: {faltantes}")
        print("Continuando con las referencias disponibles...")
    
    # Procesar archivo CSV
    archivo_csv = '/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/PVP_CECOTEC_template.csv'
    
    if not os.path.exists(archivo_csv):
        print(f"Error: No se encuentra el archivo {archivo_csv}")
        sys.exit(1)
    
    productos_creados, productos_actualizados, productos_error, errores = procesar_csv_productos(
        archivo_csv, models, uid, referencias
    )
    
    # Resumen final
    print()
    print("=== RESUMEN DE IMPORTACIÓN ===")
    print(f"Productos creados: {productos_creados}")
    print(f"Productos actualizados: {productos_actualizados}")
    print(f"Productos con errores: {productos_error}")
    print(f"Total procesados: {productos_creados + productos_actualizados + productos_error}")
    
    if errores:
        print("\nPrimeros errores encontrados:")
        for error in errores[:5]:  # Mostrar solo los primeros 5 errores
            print(f"  - {error}")
        if len(errores) > 5:
            print(f"  ... y {len(errores) - 5} errores más")
    
    print("\n=== IMPORTACIÓN COMPLETADA ===")

if __name__ == '__main__':
    main()
