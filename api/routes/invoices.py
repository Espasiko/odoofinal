"""Rutas para importación de facturas OCR"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from ..services.invoice_import_service import invoice_import_service

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])

@router.post("/import-ocr", status_code=status.HTTP_201_CREATED)
async def import_invoice_ocr(ocr_json: Dict[str, Any]):
    """Importa una factura OCR y la integra en Odoo"""
    try:
        result = invoice_import_service.import_invoice(ocr_json)
        return {"success": True, "data": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


@router.post("/purchase-orders/{po_id}/invoice", status_code=status.HTTP_201_CREATED)
async def create_invoice_from_po_endpoint(po_id: int):
    """Genera una factura de proveedor a partir de un Purchase Order existente."""
    try:
        from ..services.odoo_purchase_service import odoo_purchase_service  # local para evitar ciclos
        invoice_id = odoo_purchase_service.create_invoice_from_po(po_id)
        return {
            "success": True,
            "data": {
                "purchase_order_id": po_id,
                "invoice_id": invoice_id,
                "error": odoo_purchase_service.last_error,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
