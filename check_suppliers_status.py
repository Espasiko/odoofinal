#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Diagnóstico de Proveedores
Verifica el estado actual de los proveedores en Odoo y la conectividad del sistema
"""

import xmlrpc.client
import psycopg2
import sys
from datetime import datetime

# Configuración
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'manus_odoo-bd'
ODOO_USERNAME = 'yo@mail.com'
ODOO_PASSWORD = 'admin'

# PostgreSQL
PG_HOST = 'localhost'
PG_PORT = 5432
PG_DB = 'manus_odoo-bd'
PG_USER = 'odoo'
PG_PASSWORD = 'odoo'

def test_odoo_connection():
    """Prueba la conexión con Odoo"""
    try:
        print("🔍 Probando conexión con Odoo...")
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if uid:
            print(f"✅ Conexión Odoo exitosa - Usuario ID: {uid}")
            return True, uid
        else:
            print("❌ Error de autenticación en Odoo")
            return False, None
    except Exception as e:
        print(f"❌ Error conectando a Odoo: {e}")
        return False, None

def test_postgres_connection():
    """Prueba la conexión con PostgreSQL"""
    try:
        print("🔍 Probando conexión con PostgreSQL...")
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexión PostgreSQL exitosa - {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        return False

def get_suppliers_via_odoo():
    """Obtiene proveedores vía Odoo XML-RPC"""
    try:
        print("\n📋 Obteniendo proveedores vía Odoo XML-RPC...")
        
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            print("❌ Error de autenticación")
            return []
        
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # Buscar proveedores
        supplier_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'search',
            [[['supplier_rank', '>', 0]]],
            {'limit': 50}
        )
        
        if not supplier_ids:
            print("⚠️  No se encontraron proveedores")
            return []
        
        # Obtener datos de proveedores
        suppliers = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'read',
            [supplier_ids],
            {'fields': ['id', 'name', 'email', 'phone', 'street', 'city', 'country_id', 'supplier_rank', 'is_company', 'active']}
        )
        
        print(f"✅ Encontrados {len(suppliers)} proveedores:")
        for supplier in suppliers:
            country = supplier.get('country_id', [False, ''])[1] if supplier.get('country_id') else 'N/A'
            status = "✅ Activo" if supplier.get('active', True) else "❌ Inactivo"
            print(f"  - ID: {supplier['id']} | {supplier['name']} | {supplier.get('email', 'Sin email')} | {country} | {status}")
        
        return suppliers
        
    except Exception as e:
        print(f"❌ Error obteniendo proveedores: {e}")
        return []

def get_suppliers_via_postgres():
    """Obtiene proveedores directamente de PostgreSQL"""
    try:
        print("\n🗄️  Obteniendo proveedores vía PostgreSQL...")
        
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()
        
        query = """
        SELECT 
            rp.id, 
            rp.name, 
            rp.email, 
            rp.phone, 
            rp.street, 
            rp.city, 
            rc.name as country,
            rp.supplier_rank,
            rp.is_company,
            rp.active
        FROM res_partner rp
        LEFT JOIN res_country rc ON rp.country_id = rc.id
        WHERE rp.supplier_rank > 0
        ORDER BY rp.name
        LIMIT 50;
        """
        
        cursor.execute(query)
        suppliers = cursor.fetchall()
        
        if not suppliers:
            print("⚠️  No se encontraron proveedores en la base de datos")
            return []
        
        print(f"✅ Encontrados {len(suppliers)} proveedores en PostgreSQL:")
        for supplier in suppliers:
            status = "✅ Activo" if supplier[9] else "❌ Inactivo"
            print(f"  - ID: {supplier[0]} | {supplier[1]} | {supplier[2] or 'Sin email'} | {supplier[6] or 'N/A'} | {status}")
        
        cursor.close()
        conn.close()
        return suppliers
        
    except Exception as e:
        print(f"❌ Error consultando PostgreSQL: {e}")
        return []

def check_product_types():
    """Verifica los tipos de productos importados"""
    try:
        print("\n📦 Verificando tipos de productos...")
        
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            print("❌ Error de autenticación")
            return
        
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # Contar productos por tipo
        for product_type, description in [('product', 'Goods/Productos'), ('consu', 'Consumibles'), ('service', 'Servicios')]:
            count = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'search_count',
                [[['detailed_type', '=', product_type]]]
            )
            print(f"  - {description}: {count} productos")
        
        # Buscar productos CECOTEC específicamente
        cecotec_products = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'search_count',
            [[['name', 'ilike', 'CECOTEC']]]
        )
        print(f"  - Productos CECOTEC: {cecotec_products}")
        
    except Exception as e:
        print(f"❌ Error verificando productos: {e}")

def main():
    """Función principal"""
    print("=== DIAGNÓSTICO DE SISTEMA MANUSODOO ===")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Probar conexiones
    odoo_ok, uid = test_odoo_connection()
    postgres_ok = test_postgres_connection()
    
    if not odoo_ok:
        print("\n❌ Sin conexión a Odoo. Verifique que los servicios estén ejecutándose:")
        print("   ./start.sh")
        return
    
    if not postgres_ok:
        print("\n❌ Sin conexión a PostgreSQL. Verifique la configuración de la base de datos.")
        return
    
    # Obtener proveedores por ambos métodos
    odoo_suppliers = get_suppliers_via_odoo()
    postgres_suppliers = get_suppliers_via_postgres()
    
    # Verificar tipos de productos
    check_product_types()
    
    # Resumen
    print("\n=== RESUMEN ===")
    print(f"✅ Conexión Odoo: {'OK' if odoo_ok else 'FALLO'}")
    print(f"✅ Conexión PostgreSQL: {'OK' if postgres_ok else 'FALLO'}")
    print(f"📋 Proveedores (Odoo): {len(odoo_suppliers)}")
    print(f"🗄️  Proveedores (PostgreSQL): {len(postgres_suppliers)}")
    
    if len(odoo_suppliers) != len(postgres_suppliers):
        print("⚠️  ALERTA: Diferencia en el número de proveedores entre Odoo y PostgreSQL")
    
    print("\n💡 Próximos pasos:")
    print("   1. Si no hay proveedores, ejecute scripts de creación de datos de prueba")
    print("   2. Si hay productos marcados como 'consu', ejecute el script de importación corregido")
    print("   3. Verifique que FastAPI esté sincronizando correctamente con Odoo")

if __name__ == '__main__':
    main()
