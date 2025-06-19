import xmlrpc.client

# Configuración de conexión
url = "http://localhost:8069"
db = "manus_odoo-bd"
username = "yo@mail.com"
password = "admin"

def fix_products():
    try:
        print("Conectando a Odoo...")
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        
        # 1. Obtener todos los productos que necesitan ser actualizados
        print("\nBuscando productos que necesitan actualización...")
        product_ids = models.execute_kw(
            db, uid, password,
            'product.template', 'search',
            [[('type', 'in', ['storable', False])]]  # Buscar productos con tipo 'storable' o sin tipo
        )
        
        print(f"Encontrados {len(product_ids)} productos para actualizar")
        
        if not product_ids:
            print("No se encontraron productos que necesiten actualización.")
            return
        
        # 2. Obtener nombres de los productos para mostrar en el resumen
        products_info = models.execute_kw(
            db, uid, password,
            'product.template', 'read',
            [product_ids, ['name', 'type', 'sale_ok', 'purchase_ok']]
        )
        
        # Mostrar resumen de lo que se va a cambiar
        print("\nResumen de cambios a realizar (primeros 5 productos):")
        for p in products_info[:5]:
            print(f"- {p['name']}: tipo={p.get('type', 'sin tipo')} -> 'consu', venta={p.get('sale_ok', False)} -> True, compra={p.get('purchase_ok', False)} -> True")
        
        if len(products_info) > 5:
            print(f"... y {len(products_info) - 5} productos más")
        
        # 3. Actualizar los productos
        print("\nActualizando productos...")
        update_vals = {
            'type': 'consu',  # Cambiar a 'consu' (Bienes)
            'sale_ok': True,  # Disponible para venta
            'purchase_ok': True,  # Disponible para compra
        }
        
        # Actualizar todos los productos de una vez
        models.execute_kw(
            db, uid, password,
            'product.template', 'write',
            [product_ids, update_vals]
        )
        
        print("✅ Actualización completada con éxito")
        
        # 4. Verificar los cambios
        print("\nVerificando los cambios...")
        updated_products = models.execute_kw(
            db, uid, password,
            'product.template', 'read',
            [product_ids, ['name', 'type', 'sale_ok', 'purchase_ok']]
        )
        
        # Mostrar resumen de la verificación
        print("\nResumen de productos actualizados (primeros 5):")
        for p in updated_products[:5]:
            print(f"- {p['name']}: tipo={p['type']}, venta={p['sale_ok']}, compra={p['purchase_ok']}")
        
        if len(updated_products) > 5:
            print(f"... y {len(updated_products) - 5} productos más")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("=== INICIO DE ACTUALIZACIÓN DE TIPOS DE PRODUCTO ===")
    print("Este script actualizará los productos con tipo 'storable' o sin tipo a 'consu'.")
    print("También los marcará como disponibles para venta y compra.")
    
    # Mostrar resumen antes de la confirmación
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        
        # Contar productos por tipo
        domain = ['|', ('type', '=', 'storable'), ('type', '=', False)]
        count = models.execute_kw(db, uid, password, 'product.template', 'search_count', [domain])
        print(f"\nSe actualizarán aproximadamente {count} productos.")
        
    except Exception as e:
        print(f"No se pudo obtener el conteo de productos: {str(e)}")
    
    confirm = input("\n¿Deseas continuar con la actualización? (s/n): ")
    if confirm.lower() == 's':
        fix_products()
    else:
        print("Operación cancelada por el usuario.")
    print("=== FIN DEL PROCESO ===")
