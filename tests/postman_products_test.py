import requests

BASE_URL = "http://localhost:8000/api/v1/products"

def test_valid():
    resp = requests.post(BASE_URL, json={
        "nombre": "Monitor 4K",
        "precio": 299.99,
        "proveedor": {"id": 25}
    })
    print("Valid POST:", resp.status_code, resp.json())
    assert resp.status_code == 200
    assert "id" in resp.json()

def test_invalid_type():
    resp = requests.post(BASE_URL, json={
        "nombre": "Teclado",
        "precio": "precio-invalido",
        "proveedor": {"id": 30}
    })
    print("Invalid price type:", resp.status_code, resp.json())
    assert resp.status_code == 400
    assert "precio" in resp.json()["detail"]

def test_missing_nombre():
    resp = requests.post(BASE_URL, json={
        "precio": 49.99,
        "proveedor": {"id": 25}
    })
    print("Missing nombre:", resp.status_code, resp.json())
    assert resp.status_code == 400
    assert "nombre" in resp.json()["detail"]

if __name__ == "__main__":
    test_valid()
    test_invalid_type()
    test_missing_nombre()
