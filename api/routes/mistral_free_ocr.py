from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Query, Body
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import tempfile
import os
import hashlib
import re
from datetime import datetime
import json
import logging
import traceback
from pathlib import Path
import datetime
from ..services.mistral_free_ocr_service import MistralFreeOCRService
from ..services.ocr_cache_service import OCRCacheService
from ..services.odoo_invoice_service import OdooInvoiceService
from ..services.tabula_extraction_service import TabulaExtractionService
from ..utils.parsing import parse_date, parse_decimal
from ..utils.price_utils import adjust_price_for_supplier, extract_tax_info, get_price_net
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

# Servicio de caché OCR
ocr_cache_service = OCRCacheService()

# Servicio de extracción de tablas con Tabula
tabula_extraction_service = TabulaExtractionService()

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
        service = MistralFreeOCRService()
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
        
        # CACHÉ TEMPORALMENTE DESHABILITADO PARA PRUEBAS
        # Comentamos la verificación de caché para forzar el reprocesamiento
        if False:  # Antes era: if ocr_cache_service.is_in_cache(temp_file_path):
            # Este bloque no se ejecutará porque la condición es False
            pass
        else:
            # Procesar factura con OCR gratuito (no está en caché)
            logger.info(f"Procesando factura con OCR (no en caché): {file.filename}")
            # Procesar la factura con el servicio OCR
            ocr_result = service.process_invoice_file(temp_file_path)
            
            # Mejorar los datos con Tabula si es un PDF
            if file_extension.lower() == '.pdf':
                try:
                    logger.info(f"Mejorando datos con Tabula para: {file.filename}")
                    enhanced_data = tabula_extraction_service.enhance_invoice_data(
                        ocr_result.get('invoice_data', {}),
                        temp_file_path
                    )
                    ocr_result['invoice_data'] = enhanced_data
                    logger.info(f"Datos mejorados con Tabula: recargo_equivalencia={enhanced_data.get('recargo_equivalencia')}")
                except Exception as e:
                    logger.error(f"Error al mejorar datos con Tabula: {str(e)}")
                    # Continuamos con los datos originales sin mejorar
                    logger.info("Continuando con los datos OCR originales sin mejoras de Tabula")
            
            # Validar los totales de la factura
            from ..utils.validation_utils import validate_invoice_totals
            is_valid, validation_details = validate_invoice_totals(ocr_result.get('invoice_data', {}))
            
            # Añadir información de validación al resultado
            ocr_result['validation'] = {
                'totals_valid': is_valid,
                'details': validation_details
            }
            
            if not is_valid:
                logger.warning(f"Validación de totales fallida: {validation_details}")
            
            # Temporalmente deshabilitado el caché para pruebas
            # ocr_cache_service.save_to_cache(temp_file_path, ocr_result)
            logger.info("Caché OCR deshabilitado temporalmente para pruebas")
        
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
                                    'price_unit': get_price_net(supplier_name, line_item.get('price_unit', 0.0)),
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
                            'price_unit': get_price_net(supplier_name, invoice_data.get('subtotal', invoice_data.get('total_amount', 0.0)))
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
                        # Nota: Los siguientes parámetros no son aceptados por la función create_supplier_invoice
                        # amount_total=invoice_data.get('total_amount', 0.0),
                        # amount_tax=invoice_data.get('tax_amount', 0.0),
                        # amount_untaxed=invoice_data.get('subtotal', invoice_data.get('total_amount', 0.0))
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
        error_tb = traceback.format_exc()
        logger.error(f"Error procesando factura con OCR gratuito {file.filename}: {e}")
        logger.error(f"Traceback completo: {error_tb}")
        
        # Verificar si es un error de división entre str y int
        if "unsupported operand type(s) for /: 'str' and 'int'" in str(e):
            logger.error("Se detectó un error de división entre string e int. Revisando valores problemáticos...")
            
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
@router.post("/create-invoice-with-supplier")
async def create_invoice_with_supplier(
    request_data: CreateInvoiceRequest,
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    # Añadir log detallado para depurar la estructura de datos recibida
    logger.info(f"Datos recibidos en create_invoice_with_supplier: {json.dumps(request_data.dict(), indent=2)}")
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
        logger.info(f"Estructura de ocr_data: {json.dumps({k: type(v).__name__ for k, v in ocr_data.items()}, indent=2)}")
        
        # Intentar encontrar los datos de factura en diferentes ubicaciones posibles
        invoice_data = None
        
        # Opción 1: Directamente en ocr_data['invoice_data']
        if 'invoice_data' in ocr_data and isinstance(ocr_data['invoice_data'], dict):
            invoice_data = ocr_data['invoice_data']
            logger.info(f"Datos de factura encontrados en ocr_data['invoice_data']: {json.dumps({k: type(v).__name__ for k, v in invoice_data.items()}, indent=2)}")
        
        # Opción 2: Si ocr_data es directamente los datos de la factura
        elif 'invoice_number' in ocr_data or 'supplier_name' in ocr_data or 'total_amount' in ocr_data or 'line_items' in ocr_data:
            invoice_data = ocr_data
            logger.info(f"Datos de factura encontrados directamente en ocr_data: {json.dumps({k: type(v).__name__ for k, v in invoice_data.items()}, indent=2)}")
        
        # Opción 3: Si ocr_data contiene un campo que tiene los datos de factura
        else:
            for key, value in ocr_data.items():
                if isinstance(value, dict) and any(field in value for field in ['invoice_number', 'supplier_name', 'total_amount', 'line_items']):
                    invoice_data = value
                    logger.info(f"Datos de factura encontrados en ocr_data['{key}']: {json.dumps({k: type(v).__name__ for k, v in invoice_data.items()}, indent=2)}")
                    break
        
        # Verificar si se encontraron datos de factura
        if not invoice_data:
            logger.error(f"No se encontraron datos de factura. Contenido de ocr_data: {json.dumps(ocr_data, indent=2)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se encontraron datos de factura en la solicitud"
            )
        
        # Obtener el proveedor
        supplier_id = request_data.supplier_id
        logger.info(f"Usando proveedor con ID: {supplier_id}")
        
        # Verificar que el proveedor existe
        supplier_details = odoo_provider_service._execute_kw(
            'res.partner', 'read', [[supplier_id]], {'fields': ['name', 'vat', 'street', 'city', 'zip', 'email', 'phone']}
        )
        
        if not supplier_details:
            logger.error(f"No se encontró el proveedor con ID {supplier_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el proveedor con ID {supplier_id}"
            )
            
        # Inicializar diccionario para actualizaciones
        supplier_update_vals = {}
        
        # Actualizar datos del proveedor con la información extraída por OCR
        # Primero verificamos si hay información del proveedor en el formato supplier_info
        if supplier_id and invoice_data.get("supplier_info"):
            supplier_info = invoice_data["supplier_info"]
            
            # Obtener datos actuales del proveedor para comparar
            current_vat = supplier_details[0].get('vat', '')
            current_street = supplier_details[0].get('street', '')
            current_city = supplier_details[0].get('city', '')
            current_zip = supplier_details[0].get('zip', '')
            
            logger.info(f"Datos actuales del proveedor ID {supplier_id}: VAT={current_vat}, Street={current_street}, City={current_city}, ZIP={current_zip}")
            
            # Verificar si hay campos que actualizar (vacíos o incompletos)
            if supplier_info.get("vat") and (not current_vat or len(current_vat) < 5):
                # Normalizar el formato del VAT/NIF
                vat = supplier_info["vat"].strip().upper().replace("-", "").replace(" ", "")
                # Asegurar que el NIF español comience con ES si no tiene prefijo
                if len(vat) <= 9 and not vat.startswith("ES") and not any(vat.startswith(p) for p in ["A", "B", "C", "D", "E", "F", "G", "H", "J", "N", "P", "Q", "R", "S", "U", "V", "W"]):
                    vat = f"ES{vat}"
                supplier_update_vals["vat"] = vat
                logger.info(f"Actualizando VAT del proveedor: {vat}")
            
            if supplier_info.get("street") and (not current_street or len(current_street) < 5):
                supplier_update_vals["street"] = supplier_info["street"]
                logger.info(f"Actualizando dirección del proveedor: {supplier_info['street']}")
            
            if supplier_info.get("city") and (not current_city or len(current_city) < 2):
                supplier_update_vals["city"] = supplier_info["city"]
                logger.info(f"Actualizando ciudad del proveedor: {supplier_info['city']}")
            
            if supplier_info.get("zip") and (not current_zip or len(current_zip) < 4):
                supplier_update_vals["zip"] = supplier_info["zip"]
                logger.info(f"Actualizando código postal del proveedor: {supplier_info['zip']}")
        
        # Verificar también el formato antiguo de datos de proveedor
        if invoice_data.get('supplier_vat') and not supplier_details[0].get('vat'):
            vat = invoice_data['supplier_vat'].strip().upper().replace("-", "").replace(" ", "")
            if len(vat) <= 9 and not vat.startswith("ES") and not any(vat.startswith(p) for p in ["A", "B", "C", "D", "E", "F", "G", "H", "J", "N", "P", "Q", "R", "S", "U", "V", "W"]):
                vat = f"ES{vat}"
            supplier_update_vals['vat'] = vat
            logger.info(f"Actualizando NIF/CIF del proveedor: {vat}")
            
        if invoice_data.get('supplier_address') and not supplier_details[0].get('street'):
            supplier_update_vals['street'] = invoice_data.get('supplier_address')
            logger.info(f"Actualizando dirección del proveedor: {invoice_data.get('supplier_address')}")
            
        if invoice_data.get('supplier_city') and not supplier_details[0].get('city'):
            supplier_update_vals['city'] = invoice_data.get('supplier_city')
            logger.info(f"Actualizando ciudad del proveedor: {invoice_data.get('supplier_city')}")
            
        if invoice_data.get('supplier_zip') and not supplier_details[0].get('zip'):
            supplier_update_vals['zip'] = invoice_data.get('supplier_zip')
            logger.info(f"Actualizando código postal del proveedor: {invoice_data.get('supplier_zip')}")
            
        if invoice_data.get('supplier_email') and not supplier_details[0].get('email'):
            supplier_update_vals['email'] = invoice_data.get('supplier_email')
            logger.info(f"Actualizando email del proveedor: {invoice_data.get('supplier_email')}")
            
        if invoice_data.get('supplier_phone') and not supplier_details[0].get('phone'):
            supplier_update_vals['phone'] = invoice_data.get('supplier_phone')
            logger.info(f"Actualizando teléfono del proveedor: {invoice_data.get('supplier_phone')}")
        
        # Si hay datos para actualizar, hacerlo
        if supplier_update_vals:
            try:
                logger.info(f"Actualizando datos del proveedor {supplier_id}: {json.dumps(supplier_update_vals)}")
                odoo_provider_service._execute_kw('res.partner', 'write', [[supplier_id], supplier_update_vals])
                
                # Volver a leer los datos del proveedor para verificar la actualización
                supplier_details = odoo_provider_service._execute_kw(
                    'res.partner', 'read', [[supplier_id]], {'fields': ['name', 'vat', 'street', 'city', 'zip', 'email', 'phone']}
                )
                logger.info(f"Datos del proveedor actualizados: {json.dumps(supplier_details[0])}")
            except Exception as e:
                logger.error(f"Error al actualizar datos del proveedor {supplier_id}: {e}", exc_info=True)
                # Intentar actualizar campo por campo para identificar el problema
                for field, value in supplier_update_vals.items():
                    try:
                        odoo_provider_service._execute_kw('res.partner', 'write', [[supplier_id], {field: value}])
                        logger.info(f"Campo {field} actualizado correctamente con valor {value}")
                    except Exception as e_field:
                        logger.error(f"Error al actualizar campo {field}: {e_field}")
        else:
            logger.info("No se requieren actualizaciones para el proveedor, datos ya completos")
            
        # Preparar líneas de factura
        invoice_lines = []
        if 'line_items' in invoice_data and isinstance(invoice_data['line_items'], list):
            for line_item in invoice_data['line_items']:
                # Verificar que line_item es un diccionario
                if isinstance(line_item, dict):
                    # Preparar línea de factura con los datos básicos
                    invoice_line = {
                        'product_name': line_item.get('product_name', line_item.get('name', 'Producto sin nombre')),
                        'quantity': line_item.get('quantity', 1.0),
                        'default_code': line_item.get('default_code', '')
                    }
                    
                    # Obtener información detallada del precio y proveedor
                    supplier_name = supplier_details[0]['name'] if supplier_details and supplier_details[0].get('name') else None
                    # Usar get_price_net directamente para obtener el precio neto
                    invoice_line['price_unit'] = get_price_net(supplier_name, line_item.get('price_unit', 0.0))
                    
                    # Obtener información detallada del precio y proveedor para logging
                    price_info = adjust_price_for_supplier(supplier_name, line_item.get('price_unit', 0.0))
                    
                    # Guardar información del proveedor detectado para logging
                    detected_provider = price_info['provider_matched']
                    if detected_provider:
                        logger.info(f"Proveedor detectado en configuración: {detected_provider}")
                    
                    # Añadir descuento si está presente
                    if 'discount' in line_item and line_item['discount'] is not None:
                        try:
                            # Normalizar el formato del descuento
                            discount_value = line_item['discount']
                            if isinstance(discount_value, str):
                                # Eliminar el símbolo % si existe
                                discount_value = discount_value.replace('%', '').strip()
                                # Limpiar y convertir a float
                                discount_value = ''.join(c for c in discount_value if c.isdigit() or c == '.')
                            
                            discount = float(discount_value)
                            if 0 <= discount <= 100:  # Validar que el descuento esté en un rango válido
                                invoice_line['discount'] = discount
                                logger.info(f"Añadiendo descuento de {discount}% a la línea de factura")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error al convertir descuento '{line_item.get('discount')}' a float: {e}")
                    
                    # Extraer y normalizar información de impuestos usando la nueva función mejorada
                    # Pasamos el supplier_name para que utilice la configuración específica del proveedor
                    tax_info = extract_tax_info(line_item, supplier_name)
                    
                    # Aplicar la información de impuestos normalizada
                    invoice_line['tax_type'] = tax_info['tax_type']
                    invoice_line['apply_recargo_equivalencia'] = tax_info['apply_recargo_equivalencia']
                    invoice_line['recargo_rate'] = tax_info['recargo_rate']
                    
                    # Si el proveedor fue detectado en la configuración, usar esa información
                    if price_info['provider_matched'] and not tax_info['supplier_matched']:
                        # La función de precio detectó el proveedor pero la de impuestos no
                        invoice_line['apply_recargo_equivalencia'] = price_info['aplica_recargo']
                        invoice_line['recargo_rate'] = price_info['recargo_rate']
                        logger.info(f"Aplicando configuración de recargo desde price_info: {price_info['aplica_recargo']} ({price_info['recargo_rate']}%)")
                    
                    # Registrar la información de impuestos detectada
                    logger.info(f"Impuesto detectado: {tax_info['tax_type']} ({tax_info['tax_rate']}%)")
                    if tax_info['apply_recargo_equivalencia']:
                        logger.info(f"Recargo de Equivalencia detectado y aplicado: {tax_info['recargo_rate']}%")
                    
                    invoice_lines.append(invoice_line)
        
        # Si no hay líneas específicas, crear una línea general
        if not invoice_lines and invoice_data.get('total_amount'):
            # Extraer y normalizar información de impuestos usando la nueva función mejorada
            # Crear un diccionario con los datos de impuestos disponibles en invoice_data
            tax_data = {
                'tax_type': invoice_data.get('tax_type', ''),
                'tax_rate': invoice_data.get('tax_rate', None),
                'apply_recargo_equivalencia': invoice_data.get('apply_recargo_equivalencia', None),
                'name': f"Factura {invoice_data.get('invoice_number', 'Sin número')}"
            }
            
            # Obtener el nombre del proveedor para usar la configuración específica
            supplier_name = supplier_details[0]['name'] if supplier_details and supplier_details[0].get('name') else None
            
            # Usar la función mejorada que tiene en cuenta la configuración del proveedor
            tax_info = extract_tax_info(tax_data, supplier_name)
            
            # Obtener información de precio para este proveedor
            if supplier_name and invoice_data.get('total_amount'):
                price_info = adjust_price_for_supplier(supplier_name, invoice_data.get('total_amount'))
                if price_info['provider_matched']:
                    logger.info(f"Proveedor detectado en configuración general: {price_info['provider_matched']}")
                    # Si el proveedor está en la configuración, usar su configuración de recargo
                    if not tax_info['supplier_matched']:
                        tax_info['apply_recargo_equivalencia'] = price_info['aplica_recargo']
                        tax_info['recargo_rate'] = price_info['recargo_rate']
                    logger.info(f"Aplicando configuración de recargo desde price_info: {price_info['aplica_recargo']} ({price_info['recargo_rate']}%)")
            
            # Crear la línea de factura con toda la información necesaria
            invoice_lines.append({
                'name': f"Factura {invoice_data.get('invoice_number', 'Sin número')}",
                'quantity': 1,
                'price_unit': get_price_net(supplier_name, invoice_data.get('subtotal', invoice_data.get('total_amount', 0.0))),
                'tax_type': tax_info['tax_type'],
                'apply_recargo_equivalencia': tax_info['apply_recargo_equivalencia']
            })
            
            logger.info(f"Creada línea general con impuesto {tax_info['tax_type']} ({tax_info['tax_rate']}%) y recargo de equivalencia: {tax_info['apply_recargo_equivalencia']}")
        
        # Asegurar que todas las líneas tengan los campos necesarios
        for line in invoice_lines:
            if 'tax_type' not in line:
                line['tax_type'] = 'iva_21'  # Por defecto IVA 21%
            if 'apply_recargo_equivalencia' not in line:
                line['apply_recargo_equivalencia'] = False
        
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
