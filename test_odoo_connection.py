import xmlrpc.client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_odoo_connection():
    """Prueba la conexión con Odoo e intenta obtener proveedores"""
    # Configuración de conexión
    odoo_url = os.getenv("VITE_ODOO_URL", "http://localhost:8069")
    odoo_db = os.getenv("VITE_ODOO_DB", "manus_odoo-bd")
    odoo_username = "yo@mail.com"
    odoo_password = "admin"
    
    print(f"=== PRUEBA DE CONEXIÓN CON ODOO ===\n")
    print(f"URL: {odoo_url}")
    print(f"Base de datos: {odoo_db}")
    print(f"Usuario: {odoo_username}")
    
    try:
        # 1. Autenticación
        print("\n1. Autenticando...")
        common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
        uid = common.authenticate(odoo_db, odoo_username, odoo_password, {})
        
        if not uid:
            print("✗ Error: No se pudo autenticar con las credenciales proporcionadas")
            return False
            
        print(f"✓ Autenticación exitosa. UID: {uid}")
        
        # 2. Obtener modelos
        print("\n2. Conectando a los modelos...")
        models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')
        print("✓ Conexión exitosa a los modelos")
        
        # 3. Buscar proveedores (partners con supplier_rank > 0)
        print("\n3. Buscando proveedores...")
        provider_ids = models.execute_kw(
            odoo_db, uid, odoo_password,
            'res.partner', 'search',
            [[['supplier_rank', '>', 0]]],
            {'limit': 100}
        )
        
        if not provider_ids:
            print("✗ No se encontraron proveedores")
            return False
            
        print(f"✓ Se encontraron {len(provider_ids)} proveedores")
        
        # 4. Obtener detalles de los proveedores
        print("\n4. Obteniendo detalles de los proveedores...")
        providers = models.execute_kw(
            odoo_db, uid, odoo_password,
            'res.partner', 'read',
            [provider_ids],
            {'fields': ['id', 'name', 'email', 'phone', 'supplier_rank', 'is_company']}
        )
        
        # 5. Mostrar resultados
        print("\n=== PROVEEDORES ENCONTRADOS ===\n")
        for i, provider in enumerate(providers, 1):
            print(f"{i}. ID: {provider['id']}")
            print(f"   Nombre: {provider.get('name', 'Sin nombre')}")
            print(f"   Email: {provider.get('email', 'No especificado')}")
            print(f"   Teléfono: {provider.get('phone', 'No especificado')}")
            print(f"   Tipo: {'Empresa' if provider.get('is_company') else 'Contacto'}")
            print(f"   Supplier Rank: {provider.get('supplier_rank', 0)}")
            print()
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_odoo_connection()
