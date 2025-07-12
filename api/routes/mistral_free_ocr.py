from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Query, Body
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import tempfile
import os
import re
from datetime import datetime
import json
import logging
from pathlib import Path
import datetime
from ..services.mistral_free_ocr_service import get_mistral_free_ocr_service
from ..services.odoo_provider_service import odoo_provider_service
from ..services.odoo_invoice_service import OdooInvoiceService
from ..utils.parsing import parse_date, parse_decimal
from ..utils.price_utils import adjust_price_for_supplier
from ..services.auth_service import get_current_user
from ..models.schemas import User
from pydantic import BaseModel

class CreateInvoiceRequest(BaseModel):
    ocr_data: Dict[str, Any]
    supplier_id: int
    update_if_exists: Optional[bool] = False

logger = logging.getLogger(__name__)

# Servicio de facturas
odoo_invoice_service = OdooInvoiceService()

# Directorio para almacenar archivos JSON de OCR
OCR_JSON_DIR = Path(__file__).parent.parent / "ocr_data"

# Crear directorio si no existe
OCR_JSON_DIR.mkdir(exist_ok=True)

router = APIRouter(
    prefix="/api/v1/mistral-free-ocr",
    tags=["Mistral Free OCR"],
    responses={404: {"description": "Not found"}}
)

@router.post("/process-invoice")
async def process_invoice_free(
    file: UploadFile = File(...),
    create_in_odoo: str = Form("false"),
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    # Convertir create_in_odoo a booleano
    create_in_odoo = create_in_odoo.lower() == "true"
    logger.info(f"Procesando factura con create_in_odoo={create_in_odoo}")
    """
    Procesa una factura usando Mistral OCR gratuito con Document Annotation
    
    Args:
        file: Archivo de factura a procesar
        create_in_odoo: Si crear la factura en Odoo automáticamente
        current_user: Usuario autenticado
        
    Returns:
        JSONResponse con los datos de la factura extraídos
    """
    temp_file_path = None
    
    try:
        # Validar formato de archivo
        file_extension = os.path.splitext(file.filename)[1].lower()
        service = get_mistral_free_ocr_service()
        supported_formats = service.get_supported_formats()
        
        if file_extension not in supported_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato de archivo no soportado. Formatos válidos: {', '.join(supported_formats)}"
            )
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Validar tamaño de archivo
        if not service.validate_file_size(temp_file_path):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="El archivo excede el límite de 50MB"
            )
        
        # Procesar factura con OCR gratuito
        ocr_result = service.process_invoice_file(temp_file_path)
        
        if not ocr_result.get('success', False):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"No se pudo procesar la factura: {ocr_result.get('error', 'Error desconocido')}"
            )
        
        # Generar un ID único para este procesamiento OCR
        ocr_id = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.splitext(file.filename)[0]}"
        
        # Extraer datos de la factura
        invoice_data = ocr_result.get('invoice_data', {})
        
        # Asegurarse de que invoice_data sea un diccionario y no una cadena
        if isinstance(invoice_data, str):
            try:
                invoice_data = json.loads(invoice_data)
            except json.JSONDecodeError:
                logger.error(f"Error al parsear invoice_data como JSON: {invoice_data}")
                invoice_data = {}
        
        response_data = {
            "success": True,
            "message": "Factura procesada exitosamente con Mistral Free OCR",
            "filename": file.filename,
            "file_type": file_extension,
            "processed_by": current_user.username,
            "invoice_data": invoice_data,
            "ocr_confidence": ocr_result.get('confidence', 'unknown'),
            "ocr_id": ocr_id
        }
        
        # Guardar los resultados del OCR en un archivo JSON para acceso posterior
        try:
            # Guardar tanto los datos OCR como los datos extraídos
            json_data = {
                "ocr_result": ocr_result,
                "extracted_data": invoice_data,
                "metadata": {
                    "filename": file.filename,
                    "processed_at": datetime.datetime.now().isoformat(),
                    "processed_by": current_user.username,
                    "ocr_id": ocr_id
                }
            }
            
            # Guardar en archivo JSON
            json_path = OCR_JSON_DIR / f"{ocr_id}_free.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Datos OCR gratuito guardados en {json_path}")
        except Exception as e:
            logger.error(f"Error guardando datos OCR gratuito en JSON: {e}")
            # No propagar la excepción, continuar con el proceso
        
        # Si se solicita, crear la factura en Odoo
        if create_in_odoo:
            try:
                # Preparar datos del proveedor extraídos del OCR
                supplier_data = {
                    'nombre': invoice_data.get('supplier_name', ''),
                    'nif': invoice_data.get('supplier_vat', ''),
                    'correo_electronico': invoice_data.get('supplier_email'),
                    'telefono': invoice_data.get('supplier_phone'),
                    'direccion': invoice_data.get('supplier_address', ''),
                    'ciudad': invoice_data.get('supplier_city', ''),
                    'codigo_postal': invoice_data.get('supplier_zip', ''),
                    'pais': 'España',
                    'notas': f"Proveedor importado desde factura OCR gratuito: {file.filename}"
                }
                
                # Registrar en logs los datos del proveedor para depuración
                logger.info(f"Datos de proveedor extraídos de OCR gratuito: {supplier_data}")
                
                # Convertir datos del frontend/OCR al formato Odoo usando nuestra función especializada
                odoo_partner_dict = odoo_provider_service.front_to_odoo_partner_dict(supplier_data)
                
                supplier_name = odoo_partner_dict.get('name')
                supplier_vat = odoo_partner_dict.get('vat')
                
                if supplier_name:
                    # Buscar proveedor por NIF/VAT primero
                    supplier_id = None
                    if supplier_vat:
                        vat_ids = odoo_provider_service._execute_kw('res.partner', 'search', [[['vat', '=', supplier_vat]]], {'limit': 1})
                        if vat_ids:
                            supplier_id = vat_ids[0]

                    # Si no se encontró por VAT, buscar por nombre
                    if not supplier_id and supplier_name:
                        providers = odoo_provider_service.get_providers(search_term=supplier_name, limit=1)
                        if providers:
                            supplier_id = providers[0].id

                    if supplier_id:
                        # Actualizar datos usando el diccionario normalizado
                        # Eliminamos campos que no queremos actualizar
                        update_vals = odoo_partner_dict.copy()
                        # No actualizamos estos campos para proveedores existentes
                        for field in ['is_company', 'supplier_rank', 'customer_rank']:
                            if field in update_vals:
                                del update_vals[field]
                                
                        if update_vals:
                            odoo_provider_service.update_provider(supplier_id, update_vals)
                    else:
                        # Crear nuevo proveedor con el diccionario normalizado
                        new_provider = odoo_provider_service.create_provider(odoo_partner_dict)
                        supplier_id = new_provider.id
                    
                    # Preparar datos de la factura para Odoo
                    invoice_lines = []
                    # Verificar que line_items existe y es una lista
                    if 'line_items' in invoice_data and isinstance(invoice_data['line_items'], list):
                        for line_item in invoice_data['line_items']:
                            # Verificar que line_item es un diccionario
                            if isinstance(line_item, dict):
                                invoice_lines.append({
                                    'name': line_item.get('name', ''),
                                    'quantity': line_item.get('quantity', 1.0),
                                    'price_unit': adjust_price_for_supplier(supplier_name, line_item.get('price_unit', 0.0)),
                                    'default_code': line_item.get('default_code', '')
                                })
                            else:
                                logger.warning(f"line_item no es un diccionario: {line_item}")
                    else:
                        logger.warning(f"No se encontraron line_items en invoice_data o no es una lista: {invoice_data}")
                        # Crear una línea genérica si no hay líneas de productos
                        invoice_lines.append({
                            'name': 'Producto sin detallar',
                            'quantity': 1.0,
                            'price_unit': invoice_data.get('total_amount', 0.0),
                            'default_code': ''
                        })
                    
                    # Si no hay líneas específicas, crear una línea general
                    if not invoice_lines and invoice_data.get('total_amount'):
                        invoice_lines.append({
                            'name': f"Factura {invoice_data.get('invoice_number', 'Sin número')}",
                            'quantity': 1,
                            'price_unit': adjust_price_for_supplier(supplier_name, invoice_data.get('subtotal', invoice_data.get('total_amount', 0.0)))
                        })
                    
                    # Crear factura en Odoo
                    invoice_date_iso = parse_date(invoice_data.get('invoice_date', ''))
                    due_date_iso = parse_date(invoice_data.get('due_date', '')) if invoice_data.get('due_date') else None
                    
                    # Registrar información para depuración
                    logger.info(f"Creando factura en Odoo con: supplier_id={supplier_id}, invoice_number={invoice_data.get('invoice_number')}, invoice_date={invoice_date_iso}, due_date={due_date_iso}, lines={len(invoice_lines)}")
                    
                    # Campos obligatorios para Odoo 18
                    # Obtenemos el diario de compras dinámicamente
                    purchase_journal_id = odoo_invoice_service._get_purchase_journal_id()
                    logger.info(f"Usando diario de compras con ID: {purchase_journal_id}")
                    
                    invoice_result = odoo_invoice_service.create_supplier_invoice(
                        partner_id=supplier_id,
                        invoice_number=invoice_data.get('invoice_number', 'Sin número'),
                        invoice_date=invoice_date_iso,
                        due_date=due_date_iso,
                        lines=invoice_lines,
                        journal_id=purchase_journal_id,  # Usar el diario de compras obtenido dinámicamente
                        move_type="in_invoice",  # Tipo de movimiento para facturas de proveedor
                        currency_id=1,  # EUR por defecto
                        amount_total=invoice_data.get('total_amount', 0.0),
                        amount_tax=invoice_data.get('tax_amount', 0.0),
                        amount_untaxed=invoice_data.get('subtotal', invoice_data.get('total_amount', 0.0))
                    )
                    
                    # Registrar el resultado para depuración
                    logger.info(f"Resultado de creación de factura en Odoo: {invoice_result}")
                    
                    # Añadir información de la factura a la respuesta
                    response_data['odoo_invoice'] = invoice_result

                    # ---- Trazabilidad de inserciones ----
                    try:
                        import csv, pathlib
                        log_path = pathlib.Path(__file__).parent.parent / 'logs'
                        log_path.mkdir(exist_ok=True)
                        log_file = log_path / 'invoice_import_free_log.csv'
                        log_row = [datetime.utcnow().isoformat(), file.filename, invoice_result.get('id'), supplier_id, invoice_data.invoice_number]
                        write_header = not log_file.exists()
                        with log_file.open('a', newline='') as f:
                            writer = csv.writer(f)
                            if write_header:
                                writer.writerow(['timestamp_utc', 'filename', 'invoice_id', 'supplier_id', 'invoice_number'])
                            writer.writerow(log_row)
                    except Exception as e:
                        logger.warning(f"No se pudo registrar trazabilidad de factura: {e}")
                    
                else:
                    response_data['odoo_invoice'] = {
                        'created': False,
                        'message': 'No se pudo identificar el proveedor para crear la factura en Odoo'
                    }
                    
            except Exception as e:
                logger.error(f"Error creando factura en Odoo: {e}")
                response_data['odoo_invoice'] = {
                    'created': False,
                    'error': str(e),
                    'message': 'Error al crear la factura en Odoo'
                }
        
        logger.info(f"Factura procesada exitosamente con OCR gratuito por usuario {current_user.username}: {file.filename}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando factura con OCR gratuito {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno procesando la factura: {str(e)}"
        )
    finally:
        # Limpiar archivo temporal
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"No se pudo eliminar el archivo temporal: {e}")

@router.post("/create-invoice")
async def create_invoice_with_supplier(
    request_data: CreateInvoiceRequest,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Crea una factura en Odoo usando los datos del OCR pero con un proveedor seleccionado manualmente
    
    Args:
        request_data: Datos del OCR y el ID del proveedor seleccionado
        current_user: Usuario autenticado
    
    Returns:
        JSONResponse con el resultado de la creación de la factura
    """
    logger.info(f"Creando factura con proveedor manual ID={request_data.supplier_id}")
    
    try:
        # Obtener datos del OCR
        ocr_data = request_data.ocr_data
        invoice_data = ocr_data.get('invoice_data', {})
        
        if not invoice_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se encontraron datos de factura en la solicitud"
            )
        
        # Obtener el proveedor
        supplier_id = request_data.supplier_id
        logger.info(f"Usando proveedor con ID: {supplier_id}")
        
        # Verificar que el proveedor existe
        supplier_details = odoo_provider_service._execute_kw(
            'res.partner', 'read', [[supplier_id]], {'fields': ['name', 'vat']}
        )
        
        if not supplier_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proveedor con ID {supplier_id} no encontrado"
            )
            
        # Preparar líneas de factura
        invoice_lines = []
        if 'line_items' in invoice_data and isinstance(invoice_data['line_items'], list):
            for line_item in invoice_data['line_items']:
                # Verificar que line_item es un diccionario
                if isinstance(line_item, dict):
                    invoice_lines.append({
                        'name': line_item.get('name', ''),
                        'quantity': line_item.get('quantity', 1.0),
                        'price_unit': adjust_price_for_supplier(supplier_details[0]['name'], line_item.get('price_unit', 0.0)),
                        'default_code': line_item.get('default_code', '')
                    })
        
        # Si no hay líneas específicas, crear una línea general
        if not invoice_lines and invoice_data.get('total_amount'):
            invoice_lines.append({
                'name': f"Factura {invoice_data.get('invoice_number', 'Sin número')}",
                'quantity': 1,
                'price_unit': adjust_price_for_supplier(supplier_details[0]['name'], invoice_data.get('subtotal', invoice_data.get('total_amount', 0.0)))
            })
        
        # Crear factura en Odoo
        invoice_date_iso = parse_date(invoice_data.get('invoice_date', ''))
        due_date_iso = parse_date(invoice_data.get('due_date', '')) if invoice_data.get('due_date') else None
        
        # Obtener el diario de compras dinámicamente
        purchase_journal_id = odoo_invoice_service._get_purchase_journal_id()
        logger.info(f"Usando diario de compras con ID: {purchase_journal_id}")
        
        invoice_result = odoo_invoice_service.create_supplier_invoice(
            partner_id=supplier_id,
            invoice_number=invoice_data.get('invoice_number', 'Sin número'),
            invoice_date=invoice_date_iso,
            due_date=due_date_iso,
            lines=invoice_lines,
            journal_id=purchase_journal_id,  # Usar el diario de compras obtenido dinámicamente
            move_type="in_invoice",  # Tipo de movimiento para facturas de proveedor
            currency_id=1,  # EUR por defecto
            # Valores adicionales para la factura
            ref=invoice_data.get('invoice_number', ''),
            narration=f"Factura creada desde OCR con proveedor seleccionado manualmente por {current_user.username}"
        )
        
        if invoice_result.get('success'):
            return JSONResponse({
                "success": True,
                "message": "Factura creada exitosamente en Odoo",
                "invoice_id": invoice_result.get('invoice_id'),
                "invoice_data": invoice_data,
                "supplier_id": supplier_id,
                "supplier_name": supplier_details[0]['name']
            })
        else:
            return JSONResponse({
                "success": False,
                "message": invoice_result.get('error', 'Error desconocido al crear la factura'),
                "invoice_data": invoice_data,
                "supplier_id": supplier_id
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Error al crear factura con proveedor manual: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "message": f"Error al crear factura: {str(e)}"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
