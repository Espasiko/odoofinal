import pytest
from fastapi import HTTPException
from api.services.odoo_product_service import OdooProductService

def test_datos_perfectos():
    data = {"nombre": "TV LED", "precio": 199.99, "proveedor": {"id": 10}}
    result = OdooProductService.front_to_odoo_product_dict(data)
    assert result == {"name": "TV LED", "list_price": 199.99, "supplier_id": 10}

def test_proveedor_vacio():
    data = {"nombre": "Producto", "precio": 10.0, "proveedor": {}}
    result = OdooProductService.front_to_odoo_product_dict(data)
    assert result == {"name": "Producto", "list_price": 10.0, "supplier_id": False}

def test_precio_string_convertible():
    data = {"nombre": "Mouse", "precio": "15.99", "proveedor": {"id": 5}}
    result = OdooProductService.front_to_odoo_product_dict(data)
    assert result == {"name": "Mouse", "list_price": 15.99, "supplier_id": 5}

def test_id_proveedor_invalido():
    data = {"nombre": "Monitor", "precio": 100, "proveedor": {"id": "no-numérico"}}
    with pytest.raises(HTTPException) as exc:
        OdooProductService.front_to_odoo_product_dict(data)
    assert exc.value.status_code == 400
    assert "proveedor.id" in exc.value.detail

def test_campo_faltante_nombre():
    data = {"precio": 49.99, "proveedor": {"id": 2}}
    with pytest.raises(HTTPException) as exc:
        OdooProductService.front_to_odoo_product_dict(data)
    assert exc.value.status_code == 400
    assert "nombre" in exc.value.detail
