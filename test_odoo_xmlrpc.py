#!/usr/bin/env python3
import xmlrpc.client

try:
    # Conectar al servicio común de Odoo
    common = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/common')
    
    # Intentar autenticación
    uid = common.authenticate('postgres', 'admin', 'admin', {})
    
    if uid:
        print(f"✓ Autenticación exitosa. UID: {uid}")
        
        # Probar conexión al servicio de objetos
        models = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/object')
        
        # Probar una consulta simple
        result = models.execute_kw('postgres', uid, 'admin', 'res.users', 'search_read', 
                                 [[['id', '=', uid]]], {'fields': ['name', 'login']})
        
        print(f"✓ Consulta exitosa. Usuario: {result[0]['name']} ({result[0]['login']})")
        print("✓ Conexión XML-RPC a Odoo funcionando correctamente")
    else:
        print("✗ Error de autenticación")
        
except Exception as e:
    print(f"✗ Error de conexión: {e}")