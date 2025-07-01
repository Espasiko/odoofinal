import requests
import os

# --- Configuración ---
BASE_URL = "http://localhost:8000"
TOKEN_URL = f"{BASE_URL}/token"
PRODUCTS_URL = f"{BASE_URL}/api/v1/products"

# Credenciales de la API (no de Odoo)
API_USERNAME = "admin"
API_PASSWORD = "admin_password_secure"

# Productos a archivar
PRODUCTS_TO_ARCHIVE = {
    "Virtual Interior Design": None, # ID: 3
    "FURN_0789": None              # ID: 22
}

# --- Funciones de Ayuda ---

def get_token(session):
    print("1️⃣  Paso 1: Obteniendo token de autenticación...")
    try:
        response = session.post(TOKEN_URL, data={"username": API_USERNAME, "password": API_PASSWORD})
        response.raise_for_status()
        token = response.json().get("access_token")
        if token:
            print("✅ Token obtenido con éxito.")
            session.headers.update({"Authorization": f"Bearer {token}"})
            return token
        else:
            print("❌ ERROR: No se encontró 'access_token' en la respuesta.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: No se pudo obtener el token. Causa: {e}")
        return None

def find_product_ids(session):
    print("\n2️⃣  Paso 2: Buscando IDs de los productos a archivar...")
    try:
        response = session.get(f"{PRODUCTS_URL}?size=1000&include_inactive=true")
        response.raise_for_status()
        products = response.json().get('data', [])
        
        found_all = True
        for product in products:
            # Buscar por nombre
            if product.get('name') in PRODUCTS_TO_ARCHIVE:
                PRODUCTS_TO_ARCHIVE[product.get('name')] = product.get('id')
                print(f"  - ✅ Encontrado: '{product.get('name')}' con ID: {product.get('id')}")
            # Buscar por referencia (default_code)
            if product.get('default_code') and product.get('default_code') in PRODUCTS_TO_ARCHIVE:
                PRODUCTS_TO_ARCHIVE[product.get('default_code')] = product.get('id')
                print(f"  - ✅ Encontrado: Producto con referencia '{product.get('default_code')}' y ID: {product.get('id')}")

        # Verificar si se encontraron todos
        for name, product_id in PRODUCTS_TO_ARCHIVE.items():
            if not product_id:
                print(f"  - ❌ AVISO: No se encontró el producto '{name}'.")
                found_all = False
        
        if not found_all:
            print("⚠️  Algunos productos no se encontraron.")

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: No se pudieron obtener los productos. Causa: {e}")

def archive_product_by_id(session, product_id):
    if not product_id:
        return
    print(f"\n3️⃣  Paso 3: Intentando archivar el producto con ID: {product_id}...")
    try:
        delete_url = f"{PRODUCTS_URL}/{product_id}"
        response = session.delete(delete_url)
        if response.status_code == 204:
            print(f"✅ ÉXITO: Producto {product_id} archivado correctamente.")
        else:
            print(f"❌ ERROR: No se pudo archivar el producto {product_id}. Causa: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Fallo en la solicitud para archivar el producto {product_id}. Causa: {e}")

# --- Flujo Principal ---
def main():
    print("--- INICIANDO PRUEBA DE ARCHIVADO DE PRODUCTOS EXISTENTES ---")
    with requests.Session() as session:
        token = get_token(session)
        if not token:
            print("\n--- Prueba abortada por fallo de autenticación ---")
            return

        find_product_ids(session)

        for name, product_id in PRODUCTS_TO_ARCHIVE.items():
            if product_id:
                archive_product_by_id(session, product_id)
            else:
                print(f"\nSkipping archivo para '{name}' porque no se encontró su ID.")

    print("\n--- PRUEBA FINALIZADA ---")

if __name__ == "__main__":
    main()
