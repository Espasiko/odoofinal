import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

def connect_to_db():
    """Conectar a la base de datos PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="manus_odoo-bd",
            user="odoo",
            password="odoo"
        )
        print("✓ Conexión exitosa a la base de datos")
        return conn
    except Exception as e:
        print(f"✗ Error al conectar a la base de datos: {str(e)}")
        return None

def get_suppliers_from_db():
    """Obtener proveedores de la base de datos"""
    conn = connect_to_db()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Consulta para obtener proveedores (partners con supplier_rank > 0)
            query = """
                SELECT id, name, email, phone, supplier_rank, ref, vat, website, active
                FROM res_partner
                WHERE supplier_rank > 0
                ORDER BY supplier_rank DESC, name
            """
            
            cur.execute(query)
            suppliers = cur.fetchall()
            
            # Convertir a lista de diccionarios
            result = []
            for row in suppliers:
                supplier = dict(row)
                result.append(supplier)
            
            return result
    except Exception as e:
        print(f"✗ Error al ejecutar la consulta: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

def main():
    print("=== VERIFICACIÓN DE PROVEEDORES EN LA BASE DE DATOS ===\n")
    
    # Obtener proveedores de la base de datos
    suppliers = get_suppliers_from_db()
    
    if not suppliers:
        print("No se encontraron proveedores en la base de datos.")
        return
    
    print(f"Total de proveedores encontrados: {len(suppliers)}\n")
    
    # Mostrar información de los proveedores
    print("Lista de proveedores:")
    print("-" * 80)
    for i, supplier in enumerate(suppliers, 1):
        print(f"{i}. {supplier['name']} (ID: {supplier['id']})")
        print(f"   Email: {supplier['email'] or 'No especificado'}")
        print(f"   Teléfono: {supplier['phone'] or 'No especificado'}")
        print(f"   Referencia: {supplier['ref'] or 'N/A'}")
        print(f"   NIF/CIF: {supplier['vat'] or 'No especificado'}")
        print(f"   Página web: {supplier['website'] or 'No especificada'}")
        print(f"   Activo: {'Sí' if supplier['active'] else 'No'}")
        print(f"   Supplier Rank: {supplier['supplier_rank']}")
        print("-" * 80)
    
    # Guardar en archivo para comparación
    with open('db_suppliers.txt', 'w') as f:
        for supplier in suppliers:
            f.write(f"{supplier['id']},{supplier['name']}\n")
    
    print("\n✓ Lista de proveedores guardada en 'db_suppliers.txt'")

if __name__ == "__main__":
    main()
