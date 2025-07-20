#!/usr/bin/env python3
"""
Endpoint de depuración para OCR que muestra los datos crudos extraídos
"""
import os
import logging
import tempfile
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import base64

from ..services.mistral_free_ocr_service import get_mistral_free_ocr_service
from ..services.tabula_extraction_service import TabulaExtractionService
from ..services.ocr_validator import OCRValidator

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router
debug_ocr_router = APIRouter(prefix="/api/v1/debug-ocr", tags=["debug"])

# Modelo para solicitud de extracción raw
class RawExtractionRequest(BaseModel):
    file_base64: str
    filename: str

@debug_ocr_router.post("/raw-extraction")
async def raw_extraction(request: RawExtractionRequest):
    """
    Endpoint para extraer datos crudos de OCR y Tabula sin procesamiento de IA
    
    Parámetros:
    - file_base64: Archivo en formato base64
    - filename: Nombre del archivo
    
    Retorna los datos crudos extraídos por OCR y Tabula sin ningún procesamiento de IA
    """
    try:
        # Obtener servicios
        mistral_free_ocr_service = get_mistral_free_ocr_service()
        tabula_extraction_service = TabulaExtractionService()
        from ..services.mistral_ocr_client import mistral_ocr_client
        
        # Obtener extensión del archivo
        file_extension = os.path.splitext(request.filename)[1].lower()
        supported_formats = mistral_free_ocr_service.get_supported_formats()
        
        if file_extension not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Formato de archivo no soportado. Formatos soportados: {', '.join(supported_formats)}"
            )
        
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file_path = temp_file.name
            file_content = base64.b64decode(request.file_base64)
            temp_file.write(file_content)
        
        # Extraer texto OCR directamente
        ocr_text = ""
        ocr_data = {}
        
        try:
            # Convertir a base64 para el cliente OCR si es necesario
            if file_extension.lower() in ['.jpg', '.jpeg', '.png']:
                image_base64 = request.file_base64
                ocr_text = mistral_ocr_client.extract_text_from_image(image_base64)
            else:
                # Para PDFs, usar el extractor de texto integrado
                from ..services.pdf_text_extraction import extract_text_from_pdf
                ocr_text = extract_text_from_pdf(temp_file_path)
            
            # Extraer datos básicos del texto OCR
            from ..services.ocr_data_extraction import extract_basic_invoice_data
            ocr_data = extract_basic_invoice_data(ocr_text)
            
        except Exception as e:
            logger.error(f"Error al extraer texto OCR: {str(e)}")
        
        # Extraer datos con Tabula si es un PDF
        tabula_data = {}
        tables = []
        
        if file_extension.lower() == '.pdf':
            try:
                # Extraer datos con Tabula
                tabula_data = tabula_extraction_service.extract_invoice_data(temp_file_path)
                
                # Extraer tablas crudas
                import tabula
                
                # Probar primero con método stream (para tablas sin líneas)
                stream_tables = tabula.read_pdf(
                    temp_file_path, 
                    pages='all', 
                    multiple_tables=True,
                    lattice=False,
                    stream=True,
                    guess=True
                )
                
                # Si no se encuentran tablas con stream, probar con lattice
                lattice_tables = []
                if not stream_tables:
                    lattice_tables = tabula.read_pdf(
                        temp_file_path, 
                        pages='all', 
                        multiple_tables=True,
                        lattice=True,
                        stream=False
                    )
                
                # Combinar resultados
                raw_tables = stream_tables + lattice_tables if lattice_tables else stream_tables
                
                # Filtrar tablas vacías
                raw_tables = [table for table in raw_tables if not table.empty]
                
                # Reemplazar NaN por cadenas vacías antes de convertir a dict para evitar errores JSON
                tables = [table.fillna("").to_dict() for table in raw_tables]
                
                logger.info(f"Se encontraron {len(tables)} tablas en el PDF usando método stream/lattice")
                
            except Exception as e:
                logger.error(f"Error al extraer datos con Tabula: {str(e)}")
        
        # Eliminar archivo temporal
        try:
            os.unlink(temp_file_path)
        except Exception as e:
            logger.error(f"Error al eliminar archivo temporal: {str(e)}")
        
        # Preparar respuesta
        response = {
            "success": True,
            "message": "Extracción cruda completada",
            "filename": request.filename,
            "file_type": file_extension,
            "ocr_text": ocr_text,
            "ocr_data": ocr_data,
            "tabula_data": tabula_data,
            "tables": tables
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error en raw-extraction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el archivo: {str(e)}"
        )

@debug_ocr_router.post("/process-invoice")
async def process_invoice_debug(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    supplier_name: Optional[str] = Form(None),
    supplier_vat: Optional[str] = Form(None),
    customer_name: Optional[str] = Form(None),
    customer_vat: Optional[str] = Form(None),
    invoice_number: Optional[str] = Form(None)
):
    """
    Endpoint de depuración para procesar una factura con OCR gratuito y mostrar datos crudos
    
    Permite proporcionar datos verificados por humano que tendrán prioridad sobre los datos extraídos por OCR.
    Los datos verificados por humano se marcarán con un sufijo _verified = True y no serán modificados
    durante el proceso de validación y corrección.
    
    Parámetros:
    - file: Archivo PDF o imagen de la factura
    - supplier_name: Nombre del proveedor verificado por humano (opcional)
    - supplier_vat: NIF/CIF del proveedor verificado por humano (opcional)
    - customer_name: Nombre del cliente verificado por humano (opcional)
    - customer_vat: NIF/CIF del cliente verificado por humano (opcional)
    - invoice_number: Número de factura verificado por humano (opcional)
    """
    try:
        # Obtener servicios
        mistral_free_ocr_service = get_mistral_free_ocr_service()
        tabula_extraction_service = TabulaExtractionService()
        
        # Validar formato de archivo
        file_extension = os.path.splitext(file.filename)[1].lower()
        supported_formats = mistral_free_ocr_service.get_supported_formats()
        
        if file_extension not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Formato de archivo no soportado. Formatos soportados: {', '.join(supported_formats)}"
            )
        
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(await file.read())
        
        # Información verificada por humano (si se proporciona)
        provider_info = {}
        if supplier_name:
            provider_info['supplier_name'] = supplier_name
        if supplier_vat:
            provider_info['supplier_vat'] = supplier_vat
        if customer_name:
            provider_info['customer_name'] = customer_name
        if customer_vat:
            provider_info['customer_vat'] = customer_vat
        if invoice_number:
            provider_info['invoice_number'] = invoice_number
            
        # Registrar los datos verificados proporcionados
        if provider_info:
            logger.info(f"Datos verificados por humano proporcionados: {provider_info}")
        else:
            logger.info("No se proporcionaron datos verificados por humano")
        
        # Procesar archivo con OCR
        logger.info(f"Procesando archivo con OCR: {file.filename}")
        ocr_result = mistral_free_ocr_service.process_invoice_file(temp_file_path, provider_info)
        
        # Guardar datos crudos de OCR
        raw_ocr_data = ocr_result.get('raw_ocr_data', {})
        raw_ocr_text = ocr_result.get('raw_ocr_text', '')
        
        # Mejorar los datos con Tabula si es un PDF
        raw_tabula_data = {}
        raw_tabula_tables = []
        
        if file_extension.lower() == '.pdf':
            try:
                logger.info(f"Mejorando datos con Tabula para: {file.filename}")
                tabula_data = tabula_extraction_service.enhance_invoice_data(
                    ocr_result.get('invoice_data', {}),
                    temp_file_path
                )
                
                # Guardar los datos crudos de Tabula
                raw_tabula_data = tabula_data.copy()
                
                # Guardar las tablas originales extraídas por Tabula
                try:
                    import tabula
                    raw_tables = tabula.read_pdf(temp_file_path, pages='all', multiple_tables=True)
                    raw_tabula_tables = [table.to_dict() for table in raw_tables]
                except Exception as table_err:
                    logger.error(f"Error al extraer tablas crudas: {str(table_err)}")
                
                # Realizar validación cruzada entre OCR y Tabula
                logger.info("Realizando validación cruzada entre OCR y Tabula")
                validator = OCRValidator()
                validated_data = validator.cross_validate_ocr_tabula(
                    ocr_result.get('invoice_data', {}),
                    tabula_data
                )
                
                # Verificar cálculos matemáticos
                logger.info("Verificando cálculos matemáticos")
                validator.verify_tax_calculations(validated_data)
                validator.verify_line_sum(validated_data)
                logger.info("Verificación de cálculos completada")
                
                # Actualizar los datos de factura con los validados
                ocr_result['invoice_data'] = validated_data
                
            except Exception as e:
                logger.error(f"Error al mejorar datos con Tabula: {str(e)}")
                # Continuamos con los datos originales sin mejorar
                logger.info("Continuando con los datos OCR originales sin mejoras de Tabula")
        
        # Eliminar archivo temporal en segundo plano
        background_tasks.add_task(os.unlink, temp_file_path)
        
        # Preparar respuesta con todos los datos crudos
        response = {
            "success": True,
            "message": "Factura procesada exitosamente con depuración OCR",
            "filename": file.filename,
            "file_type": file_extension,
            "processed_by": "admin",  # Por ahora hardcoded
            "invoice_data": ocr_result.get('invoice_data', {}),
            "raw_data": {
                "ocr_text": raw_ocr_text,
                "ocr_data": raw_ocr_data,
                "tabula_data": raw_tabula_data,
                "tabula_tables": raw_tabula_tables
            },
            "ocr_confidence": ocr_result.get('ocr_confidence', 'unknown'),
            "ocr_id": ocr_result.get('ocr_id', 'unknown')
        }
        
        return JSONResponse(content=response)
    
    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP
        raise http_exc
    except Exception as e:
        # Registrar error y devolver respuesta de error
        logger.error(f"Error al procesar factura: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error al procesar factura: {str(e)}"}
        )
