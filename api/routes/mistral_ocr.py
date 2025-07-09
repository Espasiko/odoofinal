from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form, Request, Body
from fastapi.responses import JSONResponse
from starlette.requests import Request
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import tempfile
import os
import logging
import json
from datetime import datetime
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

@router.post("/save-verified-invoice")
async def save_verified_invoice(
    invoice_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Guarda una factura en Odoo después de que el usuario ha verificado y posiblemente editado los datos.
    
    Args:
        invoice_data: Datos de la factura verificados por el usuario
        current_user: Usuario autenticado
        
    Returns:
        JSONResponse con el resultado de la operación
    """
    logger.info(f"Guardando factura verificada por usuario {current_user.username}")
    
    try:
        # Extraer datos del proveedor
        supplier_name = invoice_data.get('supplier_name')
        supplier_vat = invoice_data.get('supplier_vat')
        
        logger.info(f"Procesando proveedor verificado: {supplier_name}, VAT: {supplier_vat}")
        
        # Verificar si tenemos suficiente información para identificar/crear un proveedor
        if not supplier_name and not supplier_vat:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "Se requiere al menos el nombre o el NIF/VAT del proveedor"
                }
            )
        
        # Buscar proveedor por NIF/VAT primero
        supplier_id: int | None = None
        if supplier_vat:
            vat_ids = odoo_provider_service._execute_kw('res.partner', 'search', [[['vat', '=', supplier_vat]]], {'limit': 1})
            if vat_ids:
                supplier_id = vat_ids[0]
                logger.info(f"Proveedor encontrado por VAT: ID {supplier_id}")

        # Si no se encontró por VAT, buscar por nombre
        if not supplier_id and supplier_name:
            providers = odoo_provider_service.get_providers(search_term=supplier_name, limit=1)
            if providers:
                supplier_id = providers[0].id
                logger.info(f"Proveedor encontrado por nombre: ID {supplier_id}")

        # Preparar datos del proveedor para Odoo
        provider_vals = odoo_provider_service.front_to_odoo_partner_dict(invoice_data)
        
        if supplier_id:
            # Actualizar proveedor existente
            logger.info(f"Actualizando proveedor existente ID {supplier_id} con datos: {provider_vals}")
            updated_provider = odoo_provider_service.update_provider(supplier_id, provider_vals)
            if updated_provider:
                logger.info(f"Proveedor actualizado correctamente: {updated_provider.name} (ID: {updated_provider.id})")
            else:
                logger.error(f"Error al actualizar proveedor ID {supplier_id}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "message": f"Error al actualizar el proveedor ID {supplier_id}"
                    }
                )
        else:
            # Crear nuevo proveedor
            # Asegurar que tenga un nombre
            if not provider_vals.get('name'):
                provider_vals['name'] = supplier_name or 'Proveedor sin nombre'
            
            logger.info(f"Creando nuevo proveedor con datos: {provider_vals}")
            new_provider = odoo_provider_service.create_supplier(provider_vals)
            
            if new_provider:
                logger.info(f"Nuevo proveedor creado correctamente: {new_provider.name} (ID: {new_provider.id})")
                supplier_id = new_provider.id
            else:
                logger.error("Error al crear nuevo proveedor")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "message": "Error al crear el nuevo proveedor"
                    }
                )
        
        # Preparar datos de la factura para Odoo
        invoice_lines = []
        for line_item in invoice_data.get('line_items', []):
            if line_item.get('name') or line_item.get('description'):
                invoice_lines.append({
                    'name': line_item.get('description') or line_item.get('name', 'Producto/Servicio'),
                    'quantity': parse_decimal(line_item.get('quantity', 1)),
                    'price_unit': parse_decimal(line_item.get('price_unit') or line_item.get('unit_price', 0)),
                    'default_code': line_item.get('default_code') or line_item.get('code')
                })
        
        # Si no hay líneas específicas, crear una línea general
        if not invoice_lines and invoice_data.get('total_amount'):
            invoice_lines.append({
                'name': f"Factura {invoice_data.get('invoice_number', 'Sin número')}",
                'quantity': 1,
                'price_unit': parse_decimal(invoice_data.get('subtotal', invoice_data.get('total_amount', 0)))
            })
        
        # Crear factura en Odoo
        invoice_date_iso = parse_date(invoice_data.get('invoice_date'))
        invoice_result = odoo_invoice_service.create_supplier_invoice(
            partner_id=supplier_id,
            invoice_number=invoice_data.get('invoice_number'),
            invoice_date=invoice_date_iso,
            lines=invoice_lines
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Factura guardada correctamente en Odoo",
                "odoo_invoice": invoice_result,
                "supplier_id": supplier_id
            }
        )
        
    except Exception as e:
        logger.error(f"Error guardando factura verificada: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Error al guardar la factura: {str(e)}"
            }
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

class VerifiedInvoiceData(BaseModel):
    verified_data: Dict[str, Any]
    create_in_odoo: bool = False

@router.post("/process-invoice")
async def process_invoice(
    request: Request,
    file: UploadFile = File(None),
    create_in_odoo: bool = Form(False),
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    # Log de todos los parámetros recibidos para depuración
    logger.info(f"Endpoint /process-invoice llamado con: file={file}, create_in_odoo={create_in_odoo}")
    logger.info(f"Headers de la solicitud: {request.headers.get('content-type', 'No content-type')}")
    
    # Verificar que se ha proporcionado un archivo
    if not file:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "Debe proporcionar un archivo para procesar"
            }
        )
    
    temp_file_path = None
    invoice_data = None
    response_data = {}
    
    try:
        # Validar tipo de archivo
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in [".pdf", ".png", ".jpg", ".jpeg", ".avif"]:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": f"Formato de archivo no soportado: {file_extension}. Use PDF, PNG, JPG, JPEG o AVIF."
                }
            )
        
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        # Procesar con OCR
        ocr_service = get_mistral_ocr_service()
        invoice_data = ocr_service.process_invoice(temp_file_path)
        
        # Preparar respuesta
        response_data = {
            "success": True,
            "message": "Factura procesada exitosamente con Mistral OCR",
            "filename": file.filename,
            "file_type": file_extension,
            "processed_by": current_user.username,
            "invoice_data": invoice_data,
            "ocr_confidence": "unknown",
            "ocr_id": f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.splitext(file.filename)[0]}"
        }
        
        # Si se solicita, crear la factura en Odoo
        if create_in_odoo:
            try:
                # Crear proveedor si no existe
                supplier_data = None
                if 'supplier_vat' in invoice_data and invoice_data['supplier_vat']:
                    # Normalizar VAT/NIF para búsqueda (con y sin guion)
                    vat = invoice_data['supplier_vat'].replace('-', '')
                    supplier_data = {
                        'name': invoice_data.get('supplier_name', 'Proveedor desconocido'),
                        'vat': vat,
                        'email': invoice_data.get('supplier_email'),
                        'phone': invoice_data.get('supplier_phone'),
                        'street': invoice_data.get('supplier_address'),
                        'city': invoice_data.get('supplier_city'),
                        'zip': invoice_data.get('supplier_zip'),
                        'country': invoice_data.get('supplier_country', 'España'),
                        'comment': f"Proveedor importado desde factura OCR: {file.filename}",
                        'is_company': True,
                        'supplier_rank': 1
                    }
                    
                    # Buscar proveedor existente o crear uno nuevo
                    supplier = odoo_provider_service.create_supplier(supplier_data)
                    supplier_id = supplier.id if supplier else None
                    logger.info(f"Proveedor creado: {supplier}")
                    if not supplier_id:
                        raise Exception("No se pudo crear el proveedor")
                    logger.info(f"Proveedor encontrado o creado con ID: {supplier_id}")
                    
                    # Crear factura en Odoo
                    invoice_service = OdooInvoiceService()
                    
                    # Preparar líneas de factura
                    invoice_lines = []
                    if 'line_items' in invoice_data and invoice_data['line_items']:
                        for item in invoice_data['line_items']:
                            invoice_lines.append({
                                'name': item.get('name', 'Producto sin nombre'),
                                'price_unit': item.get('price_unit', 0.0),
                                'quantity': item.get('quantity', 1.0),
                                'default_code': item.get('default_code', ''),
                                'tax_id': [(6, 0, [1])]  # IVA por defecto
                            })
                    
                    # Crear factura
                    from datetime import datetime  # Asegurar que datetime está disponible en este scope
                    invoice_result = invoice_service.create_supplier_invoice(
                        supplier_id,
                        invoice_data.get('invoice_number', ''),
                        invoice_data.get('invoice_date', datetime.now().strftime('%Y-%m-%d')),
                        invoice_lines
                    )
                    invoice_id = invoice_result.get('id') if invoice_result.get('created', False) else None
                    logger.info(f"Resultado de crear factura: {invoice_result}")
                    
                    response_data["odoo_invoice_id"] = invoice_id
                    response_data["odoo_supplier_id"] = supplier_id
                    response_data["message"] += " y creada en Odoo"
                    
            except Exception as e:
                logger.error(f"Error al crear factura en Odoo: {str(e)}")
                response_data["odoo_error"] = str(e)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Error al procesar factura: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Error al procesar factura: {str(e)}"
            }
        )
    
    finally:
        # Limpiar archivos temporales
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal {temp_file_path}: {e}")

@router.post("/process-verified-invoice")
async def process_verified_invoice(
    verified_data_model: VerifiedInvoiceData,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """
    Procesa datos de factura ya verificados por el usuario y opcionalmente los crea en Odoo.
    
    Args:
        verified_data_model: Modelo con datos verificados y flag create_in_odoo
        current_user: Usuario autenticado
        
    Returns:
        JSONResponse con los datos procesados y resultado de la operación
    """
    # Log de todos los parámetros recibidos para depuración
    logger.info(f"Endpoint /process-verified-invoice llamado con: verified_data_model={verified_data_model}")
    
    # Extraer datos verificados y flag create_in_odoo del modelo
    verified_data = verified_data_model.verified_data
    create_in_odoo = verified_data_model.create_in_odoo
    logger.info(f"Datos verificados recibidos del modelo: {verified_data}")
    logger.info(f"Crear en Odoo: {create_in_odoo}")
    
    invoice_data = verified_data
    response_data = {}
    
    try:
        # Preparar respuesta
        from datetime import datetime  # Asegurar que datetime está disponible en este scope
        response_data = {
            "success": True,
            "message": "Datos de factura verificados recibidos correctamente",
            "processed_by": current_user.username,
            "invoice_data": invoice_data,
            "ocr_id": f"{datetime.now().strftime('%Y%m%d%H%M%S')}_verified"
        }
        
        # Si se solicita, crear la factura en Odoo
        if create_in_odoo:
            try:
                # Crear proveedor si no existe
                supplier_data = None
                if 'supplier_vat' in invoice_data and invoice_data['supplier_vat']:
                    # Normalizar VAT/NIF para búsqueda (con y sin guion)
                    vat = invoice_data['supplier_vat'].replace('-', '')
                    supplier_data = {
                        'name': invoice_data.get('supplier_name', 'Proveedor desconocido'),
                        'vat': vat,
                        'email': invoice_data.get('supplier_email'),
                        'phone': invoice_data.get('supplier_phone'),
                        'street': invoice_data.get('supplier_address'),
                        'city': invoice_data.get('supplier_city'),
                        'zip': invoice_data.get('supplier_zip'),
                        'country': invoice_data.get('supplier_country', 'España'),
                        'comment': f"Proveedor importado desde factura verificada por {current_user.username}",
                        'is_company': True,
                        'supplier_rank': 1
                    }
                    
                    # Buscar proveedor existente o crear uno nuevo
                    supplier = odoo_provider_service.create_supplier(supplier_data)
                    supplier_id = supplier.id if supplier else None
                    logger.info(f"Proveedor creado: {supplier}")
                    if not supplier_id:
                        raise Exception("No se pudo crear el proveedor")
                    logger.info(f"Proveedor encontrado o creado con ID: {supplier_id}")
                    
                    # Crear factura en Odoo
                    invoice_service = OdooInvoiceService()
                    
                    # Preparar líneas de factura
                    invoice_lines = []
                    if 'line_items' in invoice_data and invoice_data['line_items']:
                        for item in invoice_data['line_items']:
                            invoice_lines.append({
                                'name': item.get('name', 'Producto sin nombre'),
                                'price_unit': item.get('price_unit', 0.0),
                                'quantity': item.get('quantity', 1.0),
                                'default_code': item.get('default_code', ''),
                                'tax_id': [(6, 0, [1])]  # IVA por defecto
                            })
                    
                    # Crear factura
                    from datetime import datetime
                    invoice_result = invoice_service.create_supplier_invoice(
                        supplier_id,
                        invoice_data.get('invoice_number', ''),
                        invoice_data.get('invoice_date', datetime.now().strftime('%Y-%m-%d')),
                        invoice_lines
                    )
                    invoice_id = invoice_result.get('id') if invoice_result.get('created', False) else None
                    logger.info(f"Resultado de crear factura: {invoice_result}")
                    
                    response_data["odoo_invoice_id"] = invoice_id
                    response_data["odoo_supplier_id"] = supplier_id
                    response_data["message"] += " y creada en Odoo"
                    
            except Exception as e:
                logger.error(f"Error al crear factura en Odoo: {str(e)}")
                response_data["odoo_error"] = str(e)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
        
    except Exception as e:
        logger.error(f"Error al procesar datos verificados: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Error al procesar datos verificados: {str(e)}"
            }
        )
    
    
    """
    Procesa una factura usando Mistral OCR y opcionalmente la crea en Odoo.
    Puede recibir un archivo para procesar o datos ya verificados por el usuario.
    
    Args:
        file: Archivo de factura a procesar (opcional si se proporcionan verified_data)
        create_in_odoo: Si crear la factura en Odoo automáticamente
        verified_data: Datos de factura ya verificados por el usuario (opcional si se proporciona file)
        current_user: Usuario autenticado
        
    Returns:
        JSONResponse con los datos de la factura extraídos o procesados
    """
    temp_file_path = None
    invoice_data = None
    response_data = {}
    
    # Determinar si estamos procesando un archivo o datos verificados
    processing_file = file is not None
    processing_verified_data = verified_data is not None
    
    if not processing_file and not processing_verified_data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "Debe proporcionar un archivo o datos verificados"
            }
        )
    
    try:
        # Caso 1: Procesando un archivo con OCR
        if processing_file:
            # Validar tipo de archivo
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in [".pdf", ".png", ".jpg", ".jpeg", ".avif"]:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "message": f"Formato de archivo no soportado: {file_extension}. Use PDF, PNG, JPG, JPEG o AVIF."
                    }
                )
            
            # Guardar archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file_path = temp_file.name
                content = await file.read()
                temp_file.write(content)
            
            # Procesar con OCR
            ocr_service = get_mistral_ocr_service()
            invoice_data = ocr_service.process_invoice(temp_file_path)
            
            # Preparar respuesta
            response_data = {
                "success": True,
                "message": "Factura procesada exitosamente con Mistral Free OCR",
                "filename": file.filename,
                "file_type": file_extension,
                "processed_by": current_user.username,
                "invoice_data": invoice_data,
                "ocr_confidence": "unknown",
                "ocr_id": f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.splitext(file.filename)[0]}"
            }
        
        # Caso 2: Procesando datos ya verificados por el usuario
        else:
            logger.info(f"Procesando datos verificados por usuario {current_user.username}")
            invoice_data = verified_data
            
            logger.info(f"Datos verificados recibidos: {invoice_data}")
            
            if not invoice_data:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "success": False,
                        "message": "No se recibieron datos verificados válidos"
                    }
                )
            
            # Preparar respuesta
            response_data = {
                "success": True,
                "message": "Datos de factura verificados recibidos correctamente",
                "processed_by": current_user.username,
                "invoice_data": invoice_data,
                "ocr_id": f"{datetime.now().strftime('%Y%m%d%H%M%S')}_verified"
            }
        
        # Si se solicita, crear la factura en Odoo
        if create_in_odoo:
            try:
                # Los datos pueden estar directamente en invoice_data o dentro de extracted_data
                if 'extracted_data' in invoice_data:
                    extracted_data = invoice_data.get('extracted_data', {})
                else:
                    # Si no hay extracted_data, usar directamente invoice_data
                    extracted_data = invoice_data
                
                # Buscar o crear proveedor en Odoo
                supplier_name = extracted_data.get('supplier_name')
                supplier_vat = extracted_data.get('supplier_vat')
                
                logger.info(f"Procesando proveedor: {supplier_name}, VAT: {supplier_vat}")
                logger.info(f"Datos completos de la factura: {extracted_data}")
                
                # Verificar si tenemos suficiente información para crear un proveedor
                if supplier_name or supplier_vat:
                    # Buscar proveedor por NIF/VAT primero
                    supplier_id: int | None = None
                    if supplier_vat:
                        # Normalizar formato de VAT para búsqueda (eliminar o añadir guion según sea necesario)
                        normalized_vat = supplier_vat.replace('-', '')
                        vat_with_dash = f"{normalized_vat[:1]}-{normalized_vat[1:]}" if len(normalized_vat) > 1 else normalized_vat
                        
                        # Buscar con ambos formatos
                        vat_ids = odoo_provider_service._execute_kw('res.partner', 'search', [[['vat', 'in', [supplier_vat, normalized_vat, vat_with_dash]]]], {'limit': 1})
                        if vat_ids:
                            supplier_id = vat_ids[0]
                            logger.info(f"Proveedor encontrado por VAT: {supplier_vat} / {normalized_vat} / {vat_with_dash}, ID: {supplier_id}")

                    # Si no se encontró por VAT, buscar por nombre
                    if not supplier_id and supplier_name:
                        providers = odoo_provider_service.get_providers(search_term=supplier_name, limit=1)
                        if providers:
                            supplier_id = providers[0].id

                    if supplier_id:
                        # Actualizar datos faltantes usando el método front_to_odoo_partner_dict
                        update_vals = odoo_provider_service.front_to_odoo_partner_dict(extracted_data)
                        if update_vals:
                            logger.info(f"Actualizando proveedor existente ID {supplier_id} con datos: {update_vals}")
                            updated_provider = odoo_provider_service.update_provider(supplier_id, update_vals)
                            if updated_provider:
                                logger.info(f"Proveedor actualizado correctamente: {updated_provider.name} (ID: {updated_provider.id})")
                            else:
                                logger.error(f"Error al actualizar proveedor ID {supplier_id}")
                    else:
                        # Crear nuevo proveedor usando el método front_to_odoo_partner_dict
                        provider_vals = odoo_provider_service.front_to_odoo_partner_dict(extracted_data)
                        # Asegurar que tenga un nombre
                        if not provider_vals.get('name'):
                            provider_vals['name'] = supplier_name or 'Proveedor sin nombre'
                        
                        logger.info(f"Creando nuevo proveedor con datos: {provider_vals}")
                        # Usar create_supplier en lugar de create_provider para asegurar compatibilidad
                        new_provider = odoo_provider_service.create_supplier(provider_vals)
                        
                        if new_provider:
                            logger.info(f"Nuevo proveedor creado correctamente: {new_provider.name} (ID: {new_provider.id})")
                            supplier_id = new_provider.id
                        else:
                            logger.error("Error al crear nuevo proveedor")
                            supplier_id = None
                    
                    # Preparar datos de la factura para Odoo
                    invoice_lines = []
                    for line_item in extracted_data.get('line_items', []):
                        if line_item.get('name'):
                            invoice_lines.append({
                                'name': line_item.get('name', 'Producto/Servicio'),
                                'quantity': parse_decimal(line_item.get('quantity', 1)),
                                'price_unit': adjust_price_for_supplier(supplier_name, parse_decimal(line_item.get('price_unit', 0))),
                                'default_code': line_item.get('default_code')
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
                    if invoice_result.get('created', False):
                        logger.info(f"Factura creada en Odoo: {invoice_result}")
                    else:
                        logger.warning(f"No se pudo crear la factura en Odoo: {invoice_result}")
                    
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
        
        logger.info(f"Factura procesada exitosamente por usuario {current_user.username}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data
        )
        
        # Si se solicita, crear la factura en Odoo
        if create_in_odoo:
            try:
                # Los datos pueden estar directamente en invoice_data o dentro de extracted_data
                if 'extracted_data' in invoice_data:
                    extracted_data = invoice_data.get('extracted_data', {})
                else:
                    # Si no hay extracted_data, usar directamente invoice_data
                    extracted_data = invoice_data
                
                # Buscar o crear proveedor en Odoo
                supplier_name = extracted_data.get('supplier_name')
                supplier_vat = extracted_data.get('supplier_vat')
                
                logger.info(f"Procesando proveedor: {supplier_name}, VAT: {supplier_vat}")
                logger.info(f"Datos completos de la factura: {extracted_data}")
                
                # Verificar si tenemos suficiente información para crear un proveedor
                if supplier_name or supplier_vat:
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
                        # Actualizar datos faltantes usando el método front_to_odoo_partner_dict
                        update_vals = odoo_provider_service.front_to_odoo_partner_dict(extracted_data)
                        if update_vals:
                            logger.info(f"Actualizando proveedor existente ID {supplier_id} con datos: {update_vals}")
                            updated_provider = odoo_provider_service.update_provider(supplier_id, update_vals)
                            if updated_provider:
                                logger.info(f"Proveedor actualizado correctamente: {updated_provider.name} (ID: {updated_provider.id})")
                            else:
                                logger.error(f"Error al actualizar proveedor ID {supplier_id}")
                    else:
                        # Crear nuevo proveedor usando el método front_to_odoo_partner_dict
                        provider_vals = odoo_provider_service.front_to_odoo_partner_dict(extracted_data)
                        # Asegurar que tenga un nombre
                        if not provider_vals.get('name'):
                            provider_vals['name'] = supplier_name or 'Proveedor sin nombre'
                        
                        logger.info(f"Creando nuevo proveedor con datos: {provider_vals}")
                        # Usar create_supplier en lugar de create_provider para asegurar compatibilidad
                        new_provider = odoo_provider_service.create_supplier(provider_vals)
                        
                        if new_provider:
                            logger.info(f"Nuevo proveedor creado correctamente: {new_provider.name} (ID: {new_provider.id})")
                            supplier_id = new_provider.id
                        else:
                            logger.error("Error al crear nuevo proveedor")
                            supplier_id = None
                    
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