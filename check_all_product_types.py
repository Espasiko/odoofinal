import xmlrpc.client

# Odoo connection details
url = "http://localhost:8069"
db = "manus_odoo-bd"
username = "yo@mail.com"
password = "admin"

try:
    print("Conectando a Odoo...")
    # Conectar a Odoo
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    
    # Obtener todos los productos con su tipo
    print("\nObteniendo información de productos...")
    products = models.execute_kw(
        db, uid, password,
        'product.template', 'search_read',
        [[], ['name', 'type', 'sale_ok', 'purchase_ok']],
        {'limit': 10000}  # Ajusta según sea necesario
    )
    
    # Contar por tipo
    type_counts = {}
    for p in products:
        p_type = p.get('type', 'ninguno')
        if p_type not in type_counts:
            type_counts[p_type] = 0
        type_counts[p_type] += 1
    
    # Mostrar resumen
    print("\nResumen de tipos de producto:")
    for p_type, count in type_counts.items():
        print(f"- {p_type.upper()}: {count} productos")
    
    # Mostrar ejemplos de productos sin tipo
    if 'ninguno' in type_counts or None in type_counts:
        print("\nAlgunos productos sin tipo (o tipo 'ninguno'):")
        none_type_products = [p for p in products if not p.get('type') or p.get('type') == 'ninguno']
        for p in none_type_products[:10]:  # Mostrar solo los primeros 10
            print(f"- {p['name']} (ID: {p['id']}): tipo='{p.get('type')}', venta={p.get('sale_ok')}, compra={p.get('purchase_ok')}")
        
        if len(none_type_products) > 10:
            print(f"... y {len(none_type_products) - 10} productos más sin tipo")
    
    # Verificar configuración de venta/compra
    sale_ok_products = sum(1 for p in products if p.get('sale_ok'))
    purchase_ok_products = sum(1 for p in products if p.get('purchase_ok'))
    
    print(f"\nProductos disponibles para venta: {sale_ok_products}/{len(products)}")
    print(f"Productos disponibles para compra: {purchase_ok_products}/{len(products)}")
    
except Exception as e:
    print(f"Error: {str(e)}")
