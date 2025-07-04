from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import tempfile
import os
import logging
from ..services.mistral_ocr_service import get_mistral_ocr_service
from ..services.odoo_provider_service import odoo_provider_service
from ..services.odoo_invoice_service import OdooInvoiceService
from ..utils.parsing import parse_date, parse_decimal
from ..utils.price_utils import adjust_price_for_supplier
from ..services.auth_service import get_current_user
from ..models.schemas import User

logger = logging.getLogger(__name__)

# Servicio de facturas
odoo_invoice_service = OdooInvoiceService()

router = APIRouter(
    prefix="/api/v1/mistral-ocr",
    tags=["Mistral OCR"],
    responses={404: {"description": "Not found"}}
)

@router.post("/process-document")
async def process_document(
    file: UploadFile = File(...),
    include_images: bool = True,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Procesa un documento (PDF o imagen) usando Mistral OCR
    
    Args:
        file: Archivo a procesar (PDF, PNG, JPG, JPEG, AVIF)
        include_images: Si incluir imágenes extraídas en base64
        current_user: Usuario autenticado
        
    Returns:
        JSONResponse con los datos extraídos del documento
    """
    temp_file_path = None
    
    try:
        # Validar formato de archivo
        file_extension = os.path.splitext(file.filename)[1].lower()
        service = get_mistral_ocr_service()
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
        
        # Procesar documento según el tipo
        if file_extension == '.pdf':
            ocr_result = service.process_pdf_document(
                temp_file_path, 
                include_images=include_images
            )
        else:
            ocr_result = service.process_image_document(
                temp_file_path, 
                include_images=include_images
            )
        
        logger.info(f"Documento procesado exitosamente por usuario {current_user.username}: {file.filename}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Documento procesado exitosamente",
                "filename": file.filename,
                "file_type": file_extension,
                "processed_by": current_user.username,
                "data": ocr_result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando documento {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno procesando el documento: {str(e)}"
        )
    finally:
        # Limpiar archivo temporal
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal {temp_file_path}: {e}")

@router.post("/process-invoice")
async def process_invoice(
    file: UploadFile = File(...),
    create_in_odoo: bool = False,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Procesa una factura usando Mistral OCR y opcionalmente la crea en Odoo
    
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
        service = get_mistral_ocr_service()
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
        
        # Procesar documento con OCR
        if file_extension == '.pdf':
            ocr_result = service.process_pdf_document(temp_file_path, include_images=False)
        else:
            ocr_result = service.process_image_document(temp_file_path, include_images=False)
        
        if not ocr_result.get('success', False):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se pudo procesar el documento con OCR"
            )
        
        # Inicializar invoice_data como un diccionario vacío
        invoice_data = {
            'extracted_data': {},
            'confidence': 'low'
        }
        
        # Extraer datos de factura con IA si es un documento de factura
        try:
            if ocr_result.get('document_type') == 'invoice':
                invoice_data = await service.extract_invoice_data_with_ai(ocr_result)
            else:
                # Si no es una factura, intentar extraer datos genéricos
                invoice_data = {
                    'extracted_data': {
                        'document_type': ocr_result.get('document_type', 'unknown'),
                        'text': ocr_result.get('text', '')[:1000]  # Limitar texto para evitar respuestas muy grandes
                    },
                    'confidence': ocr_result.get('confidence', 0)
                }
        except Exception as e:
            logger.error(f"Error al extraer datos de factura con IA: {e}")
            # No propagar la excepción, usar datos vacíos
        
        response_data = {
            "success": True,
            "message": "Documento procesado exitosamente",
            "filename": file.filename,
            "file_type": file_extension,
            "processed_by": current_user.username,
            "invoice_data": invoice_data,
            "ocr_confidence": invoice_data.get('confidence', 'unknown')
        }
        
        # Si se solicita, crear la factura en Odoo
        if create_in_odoo:
            try:
                extracted_data = invoice_data.get('extracted_data', {})
                
                # Buscar o crear proveedor en Odoo
                supplier_name = extracted_data.get('supplier_name')
                supplier_vat = extracted_data.get('supplier_vat')
                
                if supplier_name:
                    # Buscar proveedor por NIF/VAT primero
                    supplier_id: int | None = None
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
                        # Actualizar datos faltantes
                        update_vals = {
                            'vat': supplier_vat or None,
                            'email': extracted_data.get('supplier_email'),
                            'phone': extracted_data.get('supplier_phone') or extracted_data.get('supplier_mobile'),
                            'street': extracted_data.get('supplier_address'),
                            'city': extracted_data.get('supplier_city')
                        }
                        update_vals = {k: v for k, v in update_vals.items() if v}
                        if update_vals:
                            odoo_provider_service.update_provider(supplier_id, update_vals)
                    else:
                        # Crear nuevo proveedor
                        provider_vals = {
                            'name': supplier_name or 'Proveedor sin nombre',
                            'vat': supplier_vat,
                            'is_company': True,
                            'supplier_rank': 1,
                            'email': extracted_data.get('supplier_email'),
                            'phone': extracted_data.get('supplier_phone') or extracted_data.get('supplier_mobile'),
                            'street': extracted_data.get('supplier_address'),
                            'city': extracted_data.get('supplier_city')
                        }
                        provider_vals = {k: v for k, v in provider_vals.items() if v}
                        new_provider = odoo_provider_service.create_provider(provider_vals)
                        supplier_id = new_provider.id
                    
                    # Preparar datos de la factura para Odoo
                    invoice_lines = []
                    for line_item in extracted_data.get('line_items', []):
                        if line_item.get('description'):
                            invoice_lines.append({
                                'name': line_item.get('description', 'Producto/Servicio'),
                                'quantity': parse_decimal(line_item.get('quantity', 1)),
                                'price_unit': adjust_price_for_supplier(supplier_name, parse_decimal(line_item.get('unit_price', 0))),
                                'default_code': line_item.get('code')
                            })
                    
                    # Si no hay líneas específicas, crear una línea general
                    if not invoice_lines and extracted_data.get('total_amount'):
                        invoice_lines.append({
                            'name': f"Factura {extracted_data.get('invoice_number', 'Sin número')}",
                            'quantity': 1,
                            'price_unit': adjust_price_for_supplier(supplier_name, parse_decimal(extracted_data.get('subtotal', extracted_data.get('total_amount', 0))))
                        })
                    
                    # Crear factura en Odoo
                    invoice_date_iso = parse_date(extracted_data.get('invoice_date'))
                    invoice_result = odoo_invoice_service.create_supplier_invoice(
                        partner_id=supplier_id,
                        invoice_number=extracted_data.get('invoice_number'),
                        invoice_date=invoice_date_iso,
                        lines=invoice_lines
                    )
                    response_data['odoo_invoice'] = invoice_result

                    # ---- Trazabilidad de inserciones (punto 11) ----
                    try:
                        from datetime import datetime
                        import csv, pathlib
                        log_path = pathlib.Path(__file__).parent.parent / 'logs'
                        log_path.mkdir(exist_ok=True)
                        log_file = log_path / 'invoice_import_log.csv'
                        log_row = [datetime.utcnow().isoformat(), file.filename, invoice_result.get('id'), supplier_id, extracted_data.get('invoice_number')]
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
        
        logger.info(f"Factura procesada exitosamente por usuario {current_user.username}: {file.filename}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando factura {file.filename}: {e}")
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
                logger.warning(f"No se pudo eliminar archivo temporal {temp_file_path}: {e}")

@router.post("/process-from-url")
async def process_document_from_url(
    document_url: str,
    include_images: bool = True,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Procesa un documento desde una URL usando Mistral OCR
    
    Args:
        document_url: URL del documento a procesar
        include_images: Si incluir imágenes extraídas en base64
        current_user: Usuario autenticado
        
    Returns:
        JSONResponse con los datos extraídos del documento
    """
    try:
        # Procesar documento desde URL
        service = get_mistral_ocr_service()
        ocr_result = service.process_document_from_url(
            document_url, 
            include_images=include_images
        )
        
        logger.info(f"Documento desde URL procesado exitosamente por usuario {current_user.username}: {document_url}")
        
        # Extraer datos de factura con IA si es un documento de factura
        invoice_data = None
        if ocr_result.get('document_type') == 'invoice':
            invoice_data = await service.extract_invoice_data_with_ai(ocr_result)
            ocr_result['invoice_data'] = invoice_data
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Documento procesado exitosamente",
                "document_url": document_url,
                "processed_by": current_user.username,
                "data": ocr_result
            }
        )
        
    except Exception as e:
        logger.error(f"Error procesando documento desde URL {document_url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno procesando el documento: {str(e)}"
        )

@router.get("/supported-formats")
async def get_supported_formats() -> JSONResponse:
    """
    Obtiene los formatos de archivo soportados por Mistral OCR
    
    Returns:
        JSONResponse con la lista de formatos soportados
    """
    try:
        service = get_mistral_ocr_service()
        supported_formats = service.get_supported_formats()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "supported_formats": supported_formats,
                "max_file_size": "50MB",
                "description": "Formatos de archivo soportados por Mistral OCR"
            }
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo formatos soportados: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )