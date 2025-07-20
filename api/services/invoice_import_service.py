"""Servicio orquestador: recibe JSON de Mistral OCR y lo integra en Odoo.
Solo es un esqueleto inicial para la fase piloto.
"""
from typing import Dict, Any
from ..adapters.almce_adapter import ALMCEAdapter
from ..models.invoice_models import CoreInvoice
from .odoo_provider_service import odoo_provider_service

class InvoiceImportService:
    def __init__(self):
        self.adapter_map = {
            "ALMCE": ALMCEAdapter(),
        }

    def detect_adapter(self, ocr_json: Dict[str, Any]):
        text = ocr_json["data"]["full_text"].upper()
        if "ALMCE" in text:
            return self.adapter_map["ALMCE"]
        raise ValueError("Proveedor no soportado por adapters todavía")

    def import_invoice(self, ocr_json: Dict[str, Any], update_if_exists: bool = False):
        """
        Importa una factura a Odoo
        
        Args:
            ocr_json: Datos de la factura extraídos por OCR
            update_if_exists: Si se debe actualizar la factura si ya existe
            
        Returns:
            Dict con información sobre la factura creada
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Si se proporciona un supplier_id en los datos, usarlo directamente
        supplier_id = ocr_json.get("supplier_id")
        
        if not supplier_id:
            # Si no hay supplier_id, intentar detectar el proveedor con el adapter
            try:
                adapter = self.detect_adapter(ocr_json)
                core: CoreInvoice = adapter.parse(ocr_json)
                
                # Crear o actualizar el proveedor
                supplier_id = odoo_provider_service.create_provider({
                    "name": core.supplier.name,
                    "vat": core.supplier.vat,
                    "street": core.supplier.street,
                    "city": core.supplier.city,
                    "zip": core.supplier.zip,
                    "active": True,
                }, update_if_exists=update_if_exists)
            except Exception as e:
                logger.error(f"Error al detectar proveedor: {str(e)}")
                raise ValueError(f"No se pudo detectar el proveedor: {str(e)}")
        else:
            # Si hay supplier_id, obtener los datos del core directamente de ocr_json
            try:
                # Intentar usar los datos estructurados si están disponibles
                if "invoice_data" in ocr_json:
                    core_data = ocr_json["invoice_data"]
                else:
                    core_data = ocr_json
                
                # Crear un objeto CoreInvoice básico con los datos disponibles
                from ..models.invoice_models import CoreInvoice, Supplier, Invoice, InvoiceLine
                
                # Crear líneas de factura
                lines = []
                for line in core_data.get("lines", []):
                    lines.append(InvoiceLine(
                        code=line.get("product_code", ""),
                        description=line.get("name", "Producto sin nombre"),
                        qty=line.get("quantity", 1),
                        price_unit=line.get("price_unit", 0.0),
                        price_subtotal=line.get("price_subtotal", 0.0)
                    ))
                
                # Crear objeto CoreInvoice
                core = CoreInvoice(
                    supplier=Supplier(
                        name=core_data.get("supplier_name", ""),
                        vat=core_data.get("supplier_vat", ""),
                        street=core_data.get("supplier_address", ""),
                        city=core_data.get("supplier_city", ""),
                        zip=core_data.get("supplier_zip", "")
                    ),
                    invoice=Invoice(
                        number=core_data.get("invoice_number", ""),
                        date=core_data.get("invoice_date", ""),
                        total=core_data.get("total_amount", 0.0)
                    ),
                    lines=lines
                )
            except Exception as e:
                logger.error(f"Error al procesar datos de factura: {str(e)}")
                raise ValueError(f"No se pudieron procesar los datos de la factura: {str(e)}")
        

        # 2. Productos
        from .odoo_product_service import odoo_product_service  # lazy import to avoid cycles
        from .product_transform import prepare_product_vals
        product_ids = []
        order_lines_odoo = []
        for l in core.lines:
            # Usar util de transformación para asegurar formato correcto
            product_input = {
                'name': l.description[:60],
                'default_code': l.code,
                'list_price': l.price_unit,
                'standard_price': l.price_unit,
                'purchase_ok': True,
                'sale_ok': False,
                'type': 'consu',
            }
            product_vals = prepare_product_vals(product_input)
            # Añadir supplier_id explícitamente si existe
            if supplier_id:
                product_vals['supplier_id'] = supplier_id
            logger.info(f"[TEST-LOG] Llamando a create_or_update_product con: {product_vals}")
            prod_id, is_new = odoo_product_service.create_or_update_product(product_vals)
            logger.info(f"[TEST-LOG] Resultado de create_or_update_product: ID={prod_id}, es_nuevo={is_new}")
            if prod_id:
                product_ids.append(prod_id)
                order_lines_odoo.append((0, 0, {
                    'product_id': prod_id,
                    'name': l.description[:250],
                    'product_qty': l.qty,
                    'price_unit': l.price_unit,
                    'product_uom': 1,  # UoM base, mejorar más adelante
                }))

        # 3. Purchase Order y factura
        from .odoo_purchase_service import odoo_purchase_service
        po_id = odoo_purchase_service.create_purchase_order(supplier_id, order_lines_odoo) if order_lines_odoo else None
        invoice_id = odoo_purchase_service.create_invoice_from_po(po_id) if po_id else None

        return {
            "supplier_id": supplier_id,
            "invoice_number": core.invoice.number,
            "created_products": product_ids,
            "purchase_order_id": po_id,
            "invoice_id": invoice_id,
            "invoice_error": getattr(odoo_purchase_service, 'last_error', None),
            "lines": len(core.lines)
        }

# Singleton para uso sencillo desde rutas u otros servicios
invoice_import_service = InvoiceImportService()
