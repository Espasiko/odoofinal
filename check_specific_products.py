import xmlrpc.client

# Odoo connection details
url = "http://localhost:8069"
db = "manus_odoo-bd"
username = "yo@mail.com"
password = "admin"

print("Connecting to Odoo...")
try:
    # Connect to Odoo
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    
    # Search for specific products
    product_names = [
        "1 SARTEN POLKA 18 (NEGRO MANGO TURQUESA)",
        "CAFETERA 66 DROP&THERMO TIME",
        "colchon blandito",
        "150 PIEZAS DE PAPEL FREIDORA AIRE DE 5 A 6,5L"
    ]
    
    print("\nCurrent state of products:")
    for name in product_names:
        print(f"\nSearching for: {name}")
        try:
            product_ids = models.execute_kw(db, uid, password,
                'product.template', 'search_read',
                [[['name', '=', name]]],
                {'fields': ['name', 'type', 'sale_ok', 'purchase_ok', 'categ_id']}
            )
            
            if not product_ids:
                print(f"  - Not found")
                continue
                
            for p in product_ids:
                print(f"  - ID: {p.get('id')}")
                print(f"    Type: {p.get('type')}")
                print(f"    Category: {p.get('categ_id', [None, ''])[1]}")
                print(f"    Can be sold: {p.get('sale_ok')}")
                print(f"    Can be purchased: {p.get('purchase_ok')}")
                
        except Exception as e:
            print(f"  - Error checking product: {str(e)}")
            
except Exception as e:
    print(f"Error connecting to Odoo: {str(e)}")
    if 'common' in locals():
        try:
            version = common.version()
            print(f"Odoo version: {version.get('server_serie')}")
        except:
            print("Could not get Odoo version")
