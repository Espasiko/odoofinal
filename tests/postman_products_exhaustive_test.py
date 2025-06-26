import requests

BASE_URL = "http://localhost:8000/api/v1/products"
TOKEN_URL = "http://localhost:8000/token"
USERNAME = "yo@mail.com"
PASSWORD = "admin"

def get_token():
    resp = requests.post(TOKEN_URL, data={"username": USERNAME, "password": PASSWORD})
    resp.raise_for_status()
    token = resp.json()["access_token"]
    return token

def print_result(label, resp):
    try:
        print(f"{label}: {resp.status_code}", resp.json())
    except Exception:
        print(f"{label}: {resp.status_code}", resp.text)

def test_create_valid(headers):
    data = {
        "nombre": "Producto Test Exhaustivo",
        "precio": 123.45,
        "proveedor": {"id": 25}
    }
    resp = requests.post(BASE_URL, json=data, headers=headers)
    print_result("POST valid", resp)
    assert resp.status_code == 200
    # Usar template_id para updates y archive
    ids = resp.json()
    return ids["template_id"]

def test_create_missing_nombre(headers):
    data = {
        "precio": 99.99,
        "proveedor": {"id": 25}
    }
    resp = requests.post(BASE_URL, json=data, headers=headers)
    print_result("POST missing nombre", resp)
    assert resp.status_code == 400

def test_create_invalid_precio(headers):
    data = {
        "nombre": "Producto Precio Invalido",
        "precio": "abc",
        "proveedor": {"id": 25}
    }
    resp = requests.post(BASE_URL, json=data, headers=headers)
    print_result("POST invalid precio", resp)
    assert resp.status_code == 400

def test_create_empty_nombre(headers):
    data = {
        "nombre": " ",
        "precio": 10,
        "proveedor": {"id": 25}
    }
    resp = requests.post(BASE_URL, json=data, headers=headers)
    print_result("POST empty nombre", resp)
    assert resp.status_code == 400

def test_update_valid(product_id, headers):
    data = {"name": "Nombre Actualizado", "list_price": 999.99}
    resp = requests.put(f"{BASE_URL}/{product_id}", json=data, headers=headers)
    print_result("PUT valid", resp)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Nombre Actualizado"
    assert float(resp.json()["price"]) == 999.99

def test_update_invalid_precio(product_id, headers):
    data = {"list_price": "no-es-numero"}
    resp = requests.put(f"{BASE_URL}/{product_id}", json=data, headers=headers)
    print_result("PUT invalid precio", resp)
    assert resp.status_code == 400

def test_update_empty_nombre(product_id, headers):
    data = {"name": "  "}
    resp = requests.put(f"{BASE_URL}/{product_id}", json=data, headers=headers)
    print_result("PUT empty name", resp)
    assert resp.status_code == 400

def test_archive(product_id, headers):
    resp = requests.delete(f"{BASE_URL}/{product_id}", headers=headers)
    print_result("DELETE archive", resp)
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Producto archivado")

def run_all():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    test_create_missing_nombre(headers)
    test_create_invalid_precio(headers)
    test_create_empty_nombre(headers)
    template_id = test_create_valid(headers)
    test_update_valid(template_id, headers)
    test_update_invalid_precio(template_id, headers)
    test_update_empty_nombre(template_id, headers)
    test_archive(template_id, headers)

if __name__ == "__main__":
    run_all()