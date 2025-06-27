import requests

BASE_URL = "http://localhost:8000/api/v1/products"
TOKEN = "admin"  # Cambia esto por un JWT real si es necesario
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 1. Crear un producto para pruebas (si necesitas uno nuevo)
def create_product():
    resp = requests.post(BASE_URL, json={
        "nombre": "Monitor Test PUT",
        "precio": 199.99,
        "proveedor": {"id": 25}
    }, headers=HEADERS)
    print("POST create:", resp.status_code, resp.json())
    assert resp.status_code == 200
    return resp.json()["id"]

# 2. Actualizar el producto creado
def update_product(product_id):
    resp = requests.put(
        f"{BASE_URL}/{product_id}",
        json={"name": "Monitor PUT Actualizado", "list_price": "222.50"},
        headers=HEADERS
    )
    print("PUT update:", resp.status_code, resp.json())
    assert resp.status_code == 200
    assert resp.json()["name"] == "Monitor PUT Actualizado"
    assert resp.json()["list_price"] == 222.50

# 3. Archivar el producto
def archive_product(product_id):
    resp = requests.delete(f"{BASE_URL}/{product_id}", headers=HEADERS)
    print("DELETE archive:", resp.status_code, resp.json())
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Producto archivado")

if __name__ == "__main__":
    pid = create_product()
    update_product(pid)
    archive_product(pid)
