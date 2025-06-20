#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Importación Automatizada de Productos CECOTEC - ODOO 18 FINAL
Creado: 17/06/2025
ACTUALIZADO: Usa el CSV con 'storable' y es 100% compatible con Odoo 18
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
        print("Conectando a Odoo 18...")
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})

        if not uid:
            raise Exception("Error de autenticación - Verifica usuario y contraseña")

        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        print(f"✓ Conectado exitosamente a Odoo 18 (UID: {uid})")
        return models, uid
    except Exception as e:
        print(f"✗ Error conectando a Odoo: {e}")
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
            print(f"✓ Proveedor CECOTEC encontrado (ID: {proveedor[0]['id']})")
            return proveedor[0]['id']
    except Exception as e:
        print(f"✗ Error creando proveedor CECOTEC: {e}")
        return None

def crear_categoria_cecotec(models, uid):
    """Crea la categoría CECOTEC si no existe"""
    try:
        categoria = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.category', 'search_read',
            [[['name', '=', 'Electrodomésticos CECOTEC']]],
            {'fields': ['id'], 'limit': 1}
        )

        if not categoria:
            print("Creando categoría Electrodomésticos CECOTEC...")
            categoria_data = {
                'name': 'Electrodomésticos CECOTEC',
                'parent_id': False
            }

            categoria_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.category', 'create', [categoria_data]
            )
            print(f"✓ Categoría creada con ID: {categoria_id}")
            return categoria_id
        else:
            print(f"✓ Categoría encontrada (ID: {categoria[0]['id']})")
            return categoria[0]['id']
    except Exception as e:
        print(f"✗ Error creando categoría: {e}")
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
            print(f"✓ Etiqueta creada con ID: {etiqueta_id}")
            return etiqueta_id
        else:
            print(f"✓ Etiqueta encontrada (ID: {etiqueta[0]['id']})")
            return etiqueta[0]['id']
    except Exception as e:
        print(f"✗ Error creando etiqueta: {e}")
        return None

def obtener_impuestos(models, uid):
    """Obtiene los impuestos del 21% para España"""
    try:
        # Buscar impuesto de venta 21%
        impuesto_venta = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'account.tax', 'search_read',
            [[['amount', '=', 21.0], ['type_tax_use', '=', 'sale']]],
            {'fields': ['id', 'name'], 'limit': 1}
        )

        # Buscar impuesto de compra 21%
        impuesto_compra = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'account.tax', 'search_read',
            [[['amount', '=', 21.0], ['type_tax_use', '=', 'purchase']]],
            {'fields': ['id', 'name'], 'limit': 1}
        )

        venta_id = impuesto_venta[0]['id'] if impuesto_venta else None
        compra_id = impuesto_compra[0]['id'] if impuesto_compra else None

        if venta_id:
            print(f"✓ Impuesto venta 21% encontrado (ID: {venta_id})")
        else:
            print("⚠ Impuesto venta 21% no encontrado")

        if compra_id:
            print(f"✓ Impuesto compra 21% encontrado (ID: {compra_id})")
        else:
            print("⚠ Impuesto compra 21% no encontrado")

        return venta_id, compra_id

    except Exception as e:
        print(f"⚠ Error obteniendo impuestos: {e}")
        return None, None

def validar_campo(valor, tipo, default=None):
    """Valida y convierte campos del CSV de forma robusta"""
    if valor is None or str(valor).strip() == '' or str(valor).lower() == 'nan':
        return default

    try:
        valor_str = str(valor).strip()

        if tipo == 'float':
            return float(valor_str)
        elif tipo == 'int':
            return int(float(valor_str))  # Convertir a float primero por si hay decimales
        elif tipo == 'bool':
            return valor_str.lower() in ['true', '1', 'yes', 'sí', 'si']
        else:
            return valor_str
    except (ValueError, AttributeError):
        return default

def procesar_csv_productos(archivo_csv, models, uid, referencias):
    """Procesa el archivo CSV optimizado para Odoo 18"""
    productos_creados = 0
    productos_actualizados = 0
    productos_error = 0
    errores = []

    print(f"\n=== PROCESANDO ARCHIVO CSV PARA ODOO 18 ===")
    print(f"Archivo: {archivo_csv}")

    try:
        with open(archivo_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            print(f"Columnas encontradas: {reader.fieldnames}")

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Validar campos obligatorios
                    nombre = validar_campo(row.get('name'), 'str')
                    codigo = validar_campo(row.get('default_code'), 'str')

                    if not nombre or not codigo:
                        raise ValueError(f"Faltan campos obligatorios: name='{nombre}', default_code='{codigo}'")

                    print(f"\nProcesando: {codigo} - {nombre}")

                    # Obtener tipo del CSV (ya debería ser 'storable')
                    tipo_csv = validar_campo(row.get('type'), 'str', 'storable').lower()

                    # Validar que sea un tipo válido para Odoo 18
                    tipos_validos = ['storable', 'consu', 'service']
                    if tipo_csv not in tipos_validos:
                        tipo_final = 'storable'  # Por defecto, bien de inventario
                        print(f"  ⚠ Tipo '{tipo_csv}' no válido para Odoo 18, usando 'storable'")
                    else:
                        tipo_final = tipo_csv

                    print(f"  → Tipo de producto: {tipo_final} ({'bien de inventario' if tipo_final == 'storable' else tipo_final})")

                    # Preparar datos del producto
                    producto_data = {
                        'name': nombre,
                        'default_code': codigo,
                        'list_price': validar_campo(row.get('list_price'), 'float', 0.0),
                        'standard_price': validar_campo(row.get('standard_price'), 'float', 0.0),
                        'type': tipo_final,  # 'storable' para bienes de inventario en Odoo 18
                        'sale_ok': validar_campo(row.get('sale_ok'), 'bool', True),
                        'purchase_ok': validar_campo(row.get('purchase_ok'), 'bool', True),
                        'active': validar_campo(row.get('active'), 'bool', True),
                        'available_in_pos': validar_campo(row.get('available_in_pos'), 'bool', True),
                        'to_weight': validar_campo(row.get('to_weight'), 'bool', False),
                        'is_published': validar_campo(row.get('is_published'), 'bool', True),
                        'website_sequence': validar_campo(row.get('website_sequence'), 'int', 1),
                        'description_sale': validar_campo(row.get('description_sale'), 'str', f"Producto {nombre} de CECOTEC"),
                        'description_purchase': validar_campo(row.get('description_purchase'), 'str', f"Producto {nombre} de CECOTEC para compra")
                    }

                    # Agregar código de barras si existe
                    barcode = validar_campo(row.get('barcode'), 'str')
                    if barcode:
                        producto_data['barcode'] = barcode

                    # Agregar referencias si existen
                    if referencias.get('categoria_cecotec'):
                        producto_data['categ_id'] = referencias['categoria_cecotec']

                    if referencias.get('etiqueta_cecotec'):
                        producto_data['product_tag_ids'] = [(6, 0, [referencias['etiqueta_cecotec']])]

                    if referencias.get('impuesto_venta'):
                        producto_data['taxes_id'] = [(6, 0, [referencias['impuesto_venta']])]

                    if referencias.get('impuesto_compra'):
                        producto_data['supplier_taxes_id'] = [(6, 0, [referencias['impuesto_compra']])]

                    # Verificar si el producto ya existe
                    producto_existente = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                        'product.template', 'search',
                        [[['default_code', '=', codigo]]]
                    )

                    if producto_existente:
                        # Actualizar producto existente
                        producto_id = producto_existente[0]
                        models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                            'product.template', 'write',
                            [producto_id, producto_data]
                        )
                        productos_actualizados += 1
                        print(f"  ✓ Producto actualizado (ID: {producto_id})")
                    else:
                        # Crear nuevo producto
                        producto_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                            'product.template', 'create',
                            [producto_data]
                        )
                        productos_creados += 1
                        print(f"  ✓ Producto creado (ID: {producto_id})")

                    # Gestionar información del proveedor
                    if referencias.get('proveedor_cecotec') and producto_data['standard_price'] > 0:
                        try:
                            # Buscar información existente del proveedor
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
                                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                    'product.supplierinfo', 'write',
                                    [existing_supplier[0], supplier_info]
                                )
                                print(f"  ✓ Info proveedor actualizada")
                            else:
                                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                                    'product.supplierinfo', 'create',
                                    [supplier_info]
                                )
                                print(f"  ✓ Info proveedor creada")
                        except Exception as e:
                            print(f"  ⚠ Error gestionando proveedor: {e}")

                except Exception as e:
                    productos_error += 1
                    error_msg = f"Fila {row_num}: {str(e)}"
                    errores.append(error_msg)
                    print(f"  ✗ Error en fila {row_num}: {e}")

    except Exception as e:
        print(f"✗ Error leyendo archivo CSV: {e}")
        return 0, 0, 0, [str(e)]

    return productos_creados, productos_actualizados, productos_error, errores

def main():
    """Función principal"""
    print("=" * 70)
    print("      IMPORTACIÓN AUTOMATIZADA DE PRODUCTOS CECOTEC")
    print("                    ODOO 18 - VERSIÓN FINAL")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()

    # Conectar a Odoo
    models, uid = conectar_odoo()
    if not models or not uid:
        print("✗ Error: No se pudo conectar a Odoo")
        print("Verifica que Odoo esté ejecutándose y las credenciales sean correctas")
        sys.exit(1)

    # Obtener/crear referencias
    print("\n=== CONFIGURANDO REFERENCIAS ===")
    referencias = {}

    referencias['proveedor_cecotec'] = crear_proveedor_cecotec(models, uid)
    referencias['categoria_cecotec'] = crear_categoria_cecotec(models, uid)
    referencias['etiqueta_cecotec'] = crear_etiqueta_cecotec(models, uid)

    impuesto_venta, impuesto_compra = obtener_impuestos(models, uid)
    referencias['impuesto_venta'] = impuesto_venta
    referencias['impuesto_compra'] = impuesto_compra

    # Verificar referencias críticas
    referencias_ok = sum(1 for v in referencias.values() if v is not None)
    print(f"\n✓ Referencias configuradas: {referencias_ok}/5")

    # Procesar archivo CSV actualizado para Odoo 18
    archivo_csv = '/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/PVP_CECOTEC_template_ODOO18.csv'

    if not os.path.exists(archivo_csv):
        print(f"✗ Error: No se encuentra el archivo {archivo_csv}")
        print("Asegúrate de que el archivo CSV esté en la ruta correcta")
        print("Usa el archivo: PVP_CECOTEC_template_ODOO18.csv")
        sys.exit(1)

    productos_creados, productos_actualizados, productos_error, errores = procesar_csv_productos(
        archivo_csv, models, uid, referencias
    )

    # Resumen final
    print("\n" + "=" * 70)
    print("                  RESUMEN DE IMPORTACIÓN")
    print("=" * 70)
    print(f"✓ Productos creados:      {productos_creados}")
    print(f"✓ Productos actualizados: {productos_actualizados}")
    print(f"✗ Productos con errores:  {productos_error}")
    print(f"📊 Total procesados:      {productos_creados + productos_actualizados + productos_error}")

    if productos_creados > 0 or productos_actualizados > 0:
        print(f"\n🎉 ¡Importación exitosa en Odoo 18!")
        print(f"   Todos los productos configurados como 'storable' (bienes de inventario)")
        print(f"   Ubicación: Inventario > Productos > Productos")
        print(f"   Busca por: CONGA, CECOFRY, CECOBLENDER, CUMBIA")

    if errores:
        print(f"\n⚠ ERRORES ENCONTRADOS:")
        for error in errores[:5]:  # Mostrar solo los primeros 5 errores
            print(f"   - {error}")
        if len(errores) > 5:
            print(f"   ... y {len(errores) - 5} errores más")

    print("\n" + "=" * 70)
    print("                IMPORTACIÓN COMPLETADA")
    print("=" * 70)

if __name__ == '__main__':
    main()
