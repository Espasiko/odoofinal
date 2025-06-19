import xmlrpc.client

# Configuración de conexión
url = "http://localhost:8069"
db = "manus_odoo-bd"
username = "yo@mail.com"
password = "admin"

try:
    print("Conectando a Odoo...")
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    
    # Obtener todos los proveedores (partners con supplier_rank > 0)
    print("\nObteniendo proveedores de Odoo...")
    supplier_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[('supplier_rank', '>', 0)]]
    )
    
    suppliers = models.execute_kw(
        db, uid, password,
        'res.partner', 'read',
        [supplier_ids, ['name', 'email', 'phone', 'supplier_rank', 'is_company']]
    )
    
    print(f"\nTotal de proveedores encontrados: {len(suppliers)}")
    print("\nLista de proveedores:")
    for i, supplier in enumerate(suppliers, 1):
        print(f"{i}. {supplier['name']} (ID: {supplier['id']})")
        print(f"   Email: {supplier.get('email', 'No especificado')}")
        print(f"   Teléfono: {supplier.get('phone', 'No especificado')}")
        print(f"   Es compañía: {supplier.get('is_company', False)}")
        print(f"   Supplier Rank: {supplier.get('supplier_rank', 0)}")
        print("   " + "-" * 50)
    
    # Guardar proveedores para comparación posterior
    with open('odoo_suppliers.txt', 'w') as f:
        for s in suppliers:
            f.write(f"{s['id']},{s['name']}\n")
    
except Exception as e:
    print(f"Error: {str(e)}")
