from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Request, Body
import numpy as np
from PIL import Image
import pytesseract
import os
import uuid
from typing import Dict, Any, Optional, List
import cv2
import logging
from pdf2image import convert_from_path
import re
from ..services.auth_service import auth_service
from ..services.odoo_service import odoo_service

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])

logger = logging.getLogger(__name__)

# Almacén temporal para resultados OCR (en producción debería usar una base de datos)
ocr_results_cache = {}

def preprocess_image(image, doc_type='general'):
    """
    Preprocesa una imagen para mejorar la calidad del OCR.
    
    Args:
        image: Imagen de entrada (PIL Image o numpy array)
        doc_type: Tipo de documento ('general', 'factura', 'nevir', 'abrila', 'bsh')
    
    Returns:
        Imagen preprocesada optimizada para OCR
    """
    # Convertir a array numpy si es necesario
    if not isinstance(image, np.ndarray):
        image = np.array(image)
    
    # Convertir a escala de grises si es necesario
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    # Normalizar el histograma para mejorar el contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # Aplicar diferentes técnicas según el tipo de documento
    if doc_type.lower() in ['nevir', 'factura']:
        # Para facturas NEVIR: umbralización adaptativa más agresiva
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 15, 8
        )
        
        # Operaciones morfológicas para limpiar el ruido
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
    elif doc_type.lower() in ['abrila', 'bsh']:
        # Para facturas con más detalles finos: umbralización más suave
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Operaciones morfológicas para preservar detalles
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
    else:  # Caso general
        # Umbralización adaptativa estándar
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Operaciones morfológicas para limpiar el ruido
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    return binary

def deskew_image(image):
    """
    Corrige la inclinación de la imagen para mejorar el OCR.
    Utiliza la transformada de Hough para detectar líneas y calcular el ángulo de inclinación.
    """
    # Asegurarse de que la imagen es binaria
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    else:
        _, binary = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    # Detectar bordes con parámetros optimizados
    edges = cv2.Canny(binary, 50, 200, apertureSize=3)
    
    # Detectar líneas con parámetros ajustados para mejor detección
    lines = cv2.HoughLinesP(
        edges, 
        rho=1, 
        theta=np.pi/180, 
        threshold=80,  # Umbral más bajo para detectar más líneas
        minLineLength=50,  # Líneas más cortas para documentos con texto
        maxLineGap=20  # Mayor tolerancia a huecos
    )
    
    if lines is not None and len(lines) > 0:
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:  # Evitar división por cero
                # Calcular ángulo en grados
                angle = np.arctan((y2 - y1) / (x2 - x1)) * 180 / np.pi
                # Solo considerar ángulos horizontales (cercanos a 0°)
                if abs(angle) < 30:
                    angles.append(angle)
        
        if angles:
            # Usar la mediana para ser más robusto frente a valores atípicos
            median_angle = np.median(angles)
            
            # Solo corregir si el ángulo es significativo pero no demasiado grande
            if 0.5 < abs(median_angle) < 10:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(
                    image, 
                    M, 
                    (w, h), 
                    flags=cv2.INTER_CUBIC, 
                    borderMode=cv2.BORDER_REPLICATE
                )
                return rotated
    
    return image

def detect_document_type(image):
    """
    Detecta automáticamente el tipo de documento basado en el contenido de la imagen.
    
    Args:
        image: Imagen de entrada (PIL Image)
        
    Returns:
        Tipo de documento detectado ('nevir', 'abrila', 'bsh', 'general')
    """
    # Convertir a texto para buscar palabras clave
    text = pytesseract.image_to_string(image, lang='spa')
    text = text.upper()
    
    if 'NEVIR' in text:
        return 'nevir'
    elif 'ABRILA' in text or 'FABRILAMP' in text:
        return 'abrila'
    elif 'BOSCH' in text or 'BSH' in text or 'SIEMENS' in text or 'BALAY' in text:
        return 'bsh'
    else:
        return 'general'

def get_optimal_tesseract_config(doc_type='general'):
    """
    Devuelve la configuración óptima de Tesseract según el tipo de documento.
    
    Args:
        doc_type: Tipo de documento ('general', 'factura', 'nevir', 'abrila', 'bsh')
        
    Returns:
        Configuración de Tesseract como string
    """
    # Configuración base para todos los documentos
    base_config = '--dpi 300'
    
    # Configuraciones específicas por tipo de documento
    if doc_type.lower() == 'nevir':
        # Para facturas NEVIR: enfocado en precisión de códigos de producto
        return f'{base_config} --oem 1 --psm 6 -c preserve_interword_spaces=1'
    
    elif doc_type.lower() == 'abrila':
        # Para facturas ABRILA: mejor para tablas y estructura
        return f'{base_config} --oem 1 --psm 6 -c textord_tabfind_find_tables=1'
    
    elif doc_type.lower() == 'bsh':
        # Para facturas BSH: mejor para texto denso y estructurado
        return f'{base_config} --oem 1 --psm 4 -c textord_min_linesize=2.5'
    
    else:  # Configuración general
        return f'{base_config} --oem 1 --psm 6'

def extract_text_from_pdf(pdf_path, detect_type=True):
    """
    Extrae texto de un PDF usando OCR con configuración mejorada y adaptativa.
    
    Args:
        pdf_path: Ruta al archivo PDF
        detect_type: Si se debe detectar automáticamente el tipo de documento
        
    Returns:
        Texto extraído del PDF
    """
    # Convertir PDF a imágenes con alta resolución
    images = convert_from_path(pdf_path, dpi=300)
    
    # Detectar tipo de documento en la primera página si está habilitado
    doc_type = 'general'
    if detect_type and images:
        doc_type = detect_document_type(images[0])
        logger.info(f"Tipo de documento detectado: {doc_type}")
    
    # Obtener configuración óptima de Tesseract
    tesseract_config = get_optimal_tesseract_config(doc_type)
    
    # Preprocesar imágenes y extraer texto
    text = ""
    for i, img in enumerate(images):
        logger.info(f"Procesando página {i+1}/{len(images)}")
        
        # Aplicar preprocesamiento específico para el tipo de documento
        processed_img = preprocess_image(img, doc_type)
        
        # Aplicar corrección de inclinación
        deskewed_img = deskew_image(processed_img)
        
        # Extraer texto con configuración optimizada
        page_text = pytesseract.image_to_string(
            deskewed_img, 
            lang='spa', 
            config=tesseract_config
        )
        
        text += page_text + "\n\n"
    
    return text

def extract_invoice_data(text, pdf_path=None):
    """
    Extract structured data from OCR text
    """
    # Initialize invoice data
    invoice_data = {
        'number': 'Unknown',
        'date': None,
        'partner_name': 'Unknown Supplier',
        'amount_total': 0.0,
        'lines': [],
        'due_dates': [],
        'customer_order_ref': None
    }
    
    # Extract invoice number
    invoice_number_match = re.search(r'Factura[:\s]+([A-Za-z0-9\-]+)', text) or \
                          re.search(r'Nº Factura[:\s]+([A-Za-z0-9\-]+)', text) or \
                          re.search(r'FACTURA[:\s]+([A-Za-z0-9\-]+)', text)
    if invoice_number_match:
        invoice_data['number'] = invoice_number_match.group(1).strip()
    
    # Extract date
    date_match = re.search(r'Fecha[:\s]+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})', text) or \
                re.search(r'Date[:\s]+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})', text) or \
                re.search(r'FECHA[:\s]+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})', text)
    if date_match:
        invoice_data['date'] = date_match.group(1)
    
    # Extract supplier name
    if "NEVIR" in text:
        invoice_data['partner_name'] = "NEVIR S.A."
    elif "ABRILA" in text:
        invoice_data['partner_name'] = "ABRILA DISTRIBUCIONES S.L."
    else:
        supplier_match = re.search(r'Proveedor[:\s]+([A-Za-z0-9\s\.]+)', text)
        if supplier_match:
            invoice_data['partner_name'] = supplier_match.group(1).strip()
    
    # Extract total amount
    total_match = re.search(r'Total[:\s]+(\d+[\.,]\d+)', text, re.IGNORECASE) or \
                 re.search(r'TOTAL FACTURA[:\s]+(\d+[\.,]\d+)', text) or \
                 re.search(r'Importe total[:\s]+(\d+[\.,]\d+)', text)
    if total_match:
        amount_str = total_match.group(1).replace(',', '.')
        try:
            invoice_data['amount_total'] = float(amount_str)
        except ValueError:
            logger.error(f"Error converting amount: {amount_str}")
    
    # Extract invoice lines
    # This is a simplified approach, you might need to adjust based on your invoice format
    product_lines = []
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Look for lines with product code, quantity and price
        if re.search(r'[A-Z0-9\-]{5,}\s+\d+\s+', line):
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 3:
                product_code = parts[0].strip()
                try:
                    quantity = int(parts[1].strip())
                    price_str = parts[-1].replace(',', '.').strip()
                    price = float(price_str) if price_str else 0.0
                    
                    # Extract description from the middle parts
                    description = ' '.join(parts[2:-1]) if len(parts) > 3 else "Unknown Product"
                    
                    product_lines.append({
                        'product_code': product_code,
                        'name': description,
                        'quantity': quantity,
                        'price_unit': price / quantity if quantity else 0.0,
                        'price_subtotal': price
                    })
                except (ValueError, IndexError) as e:
                    logger.error(f"Error parsing product line: {line}, Error: {e}")
    
    invoice_data['lines'] = product_lines
    
    # Extract customer order reference
    order_ref_match = re.search(r'Su pedido[:\s]+([A-Za-z0-9\-]+)', text) or \
                     re.search(r'Pedido cliente[:\s]+([A-Za-z0-9\-]+)', text)
    if order_ref_match:
        invoice_data['customer_order_ref'] = order_ref_match.group(1).strip()
    
    # Extract payment method
    payment_method_match = re.search(r'Forma de pago[:\s]+([A-Za-z0-9\s\-]+)', text)
    if payment_method_match:
        payment_method = payment_method_match.group(1).strip()
        print("OCR: Forma de pago encontrada:", payment_method)
        
        # Map payment method to Odoo payment terms
        if "CONTADO" in payment_method.upper():
            invoice_data['payment_term'] = "Contado"
        elif "30" in payment_method and "60" in payment_method:
            invoice_data['payment_term'] = "30/60 días"
        elif "30" in payment_method:
            invoice_data['payment_term'] = "30 días"
        elif "60" in payment_method:
            invoice_data['payment_term'] = "60 días"
        elif "90" in payment_method:
            invoice_data['payment_term'] = "90 días"
        else:
            print("OCR: No se encontró coincidencia para forma de pago")

    return invoice_data

# Function to evaluate OCR quality
def evaluate_ocr_quality(text):
    if not text:
        return 0
        
    # Criterios de calidad
    quality_score = 0
        
    # 1. Detecta número de factura
    if re.search(r'[Ff]actura\s*[Nn].*\s*[0-9]+', text) or re.search(r'[Nn].*\s*[Ff]actura\s*[0-9]+', text):
        quality_score += 0.2
            
    # 2. Detecta fecha
    if re.search(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', text):
        quality_score += 0.2
            
    # 3. Detecta importes con formato de moneda
    if re.search(r'\d+[\.,]\d{2}\s*[€$]', text) or re.search(r'[€$]\s*\d+[\.,]\d{2}', text):
        quality_score += 0.2
            
    # 4. Detecta tablas o líneas de productos
    if re.search(r'(cantidad|uds|unidades|uds\.)[^\n]*\n[^\n]*(precio|importe)', text, re.IGNORECASE):
        quality_score += 0.2
            
    # 5. Detecta IVA o impuestos
    if re.search(r'(IVA|IGIC|impuesto)[^\n]*\d+[\.,]\d{2}', text, re.IGNORECASE):
        quality_score += 0.2
            
    return quality_score

@router.post("/invoice")
async def process_invoice(
    file: UploadFile = File(...),
    ocr_method: str = Form("auto"),  # Opciones: "auto", "tesseract", "pdfxchange"
):
    print(f"Processing invoice endpoint called. File: {file.filename}, Method: {ocr_method}")
    try:
        # Read file content
        content = await file.read()
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)

        # Inicializar variables para resultados
        invoice_data = None
        ocr_text = None
        ocr_quality = 0
        method_used = None
        doc_type = 'general'

        # Estrategia basada en el método seleccionado
        if ocr_method == "auto" or ocr_method == "tesseract":
            # Intentar primero con Tesseract optimizado
            try:
                # Importar el módulo de OCR optimizado
                from api.ocr_optimizado import extract_text_from_pdf as extract_optimized_text, extract_structured_data
                
                # Perform OCR and extract text with automatic document type detection
                ocr_text, doc_type = extract_optimized_text(file_path, detect_type=True, use_cache=True)
                print(f"OCR text extracted with Tesseract optimizado (tipo documento: {doc_type})")
                
                # Guardar una copia del texto OCR para análisis
                os.makedirs("/home/espasiko/mainmanusodoo/manusodoo-roto/resultados_ocr", exist_ok=True)
                result_filename = os.path.splitext(os.path.basename(file_path))[0] + "_optimizado.txt"
                with open(f"/home/espasiko/mainmanusodoo/manusodoo-roto/resultados_ocr/{result_filename}", "w") as f:
                    f.write(ocr_text)
                
                # Evaluar calidad
                tesseract_quality = evaluate_ocr_quality(ocr_text)
                
                # Extraer datos estructurados con el nuevo validador
                structured_data = extract_structured_data(ocr_text, doc_type)
                
                if tesseract_quality >= 0.6 or ocr_method == "tesseract":
                    # La calidad es suficiente o se forzó el uso de Tesseract
                    # Combinar datos estructurados con el extractor tradicional
                    base_invoice_data = extract_invoice_data(ocr_text, file_path)
                    
                    # Enriquecer los datos con la información estructurada del nuevo validador
                    if base_invoice_data:
                        # Priorizar datos validados del nuevo extractor
                        for key, value in structured_data.items():
                            if value is not None and key in base_invoice_data:
                                base_invoice_data[key] = value
                        
                        # Añadir campos adicionales del nuevo extractor
                        if 'tax_info' in structured_data and structured_data['tax_info']:
                            base_invoice_data['tax_info'] = structured_data['tax_info']
                        
                        if 'product_codes' in structured_data and structured_data['product_codes']:
                            base_invoice_data['product_codes'] = structured_data['product_codes']
                    
                    invoice_data = base_invoice_data
                    method_used = "tesseract_optimizado"
                    ocr_quality = tesseract_quality
                    print(f"Using Tesseract OCR optimizado results (quality: {tesseract_quality:.2f})")
            except Exception as e:
                print(f"Error with Tesseract OCR optimizado: {e}")
                # Intentar con el método original si falla el optimizado
                try:
                    ocr_text = extract_text_from_pdf(file_path, detect_type=True)
                    tesseract_quality = evaluate_ocr_quality(ocr_text)
                    invoice_data = extract_invoice_data(ocr_text, file_path)
                    method_used = "tesseract"
                    ocr_quality = tesseract_quality
                    print(f"Using fallback Tesseract OCR results (quality: {tesseract_quality:.2f})")
                except Exception as e2:
                    print(f"Error with fallback Tesseract OCR: {e2}")
        
        # Si no tenemos datos válidos y no se forzó Tesseract, intentar con PDF-XChange
        if (invoice_data is None or ocr_quality < 0.6) and ocr_method != "tesseract":
            try:
                # Importar el servicio de PDF-XChange
                from api.services.pdfxchange_ocr_service import PDFXChangeOCRService
                
                # Crear instancia del servicio
                pdfx_service = PDFXChangeOCRService()
                
                # Procesar con PDF-XChange
                with open(file_path, "rb") as f:
                    pdf_content = f.read()
                
                pdfx_text = await pdfx_service.process_pdf(pdf_content, file.filename)
                print("OCR text extracted with PDF-XChange")
                
                # Evaluar calidad
                pdfx_quality = evaluate_ocr_quality(pdfx_text)
                
                # Extraer datos de la factura
                pdfx_invoice_data = pdfx_service.extract_invoice_data(pdfx_text)
                
                # Usar resultados de PDF-XChange
                invoice_data = pdfx_invoice_data
                ocr_text = pdfx_text
                method_used = "pdfxchange"
                ocr_quality = pdfx_quality
                print(f"Using PDF-XChange OCR results (quality: {pdfx_quality:.2f})")
            except Exception as e:
                print(f"Error with PDF-XChange OCR: {e}")
                
                # Si falló PDF-XChange y no tenemos datos de Tesseract, intentar nuevamente con Tesseract mejorado
                if invoice_data is None and ocr_method != "pdfxchange":
                    # Detectar el tipo de documento a partir del nombre del archivo
                    doc_type = "general"
                    filename_lower = file.filename.lower()
                    
                    if "nevir" in filename_lower:
                        doc_type = "nevir"
                    elif "abrila" in filename_lower or "fabrilamp" in filename_lower:
                        doc_type = "abrila"
                    elif "bosch" in filename_lower or "bsh" in filename_lower or "siemens" in filename_lower or "balay" in filename_lower:
                        doc_type = "bsh"
                    
                    logger.info(f"Intentando OCR mejorado con tipo de documento: {doc_type}")
                    
                    # Usar configuración específica para el tipo de documento
                    ocr_text = extract_text_from_pdf(file_path, detect_type=True)
                    invoice_data = extract_invoice_data(ocr_text, file_path)
                    method_used = "tesseract_mejorado_fallback"
                    ocr_quality = evaluate_ocr_quality(ocr_text)
                    
                    # Guardar una copia del texto OCR para análisis
                    os.makedirs("/home/espasiko/mainmanusodoo/manusodoo-roto/resultados_ocr", exist_ok=True)
                    result_filename = os.path.splitext(os.path.basename(file_path))[0] + "_mejorado_fallback.txt"
                    with open(f"/home/espasiko/mainmanusodoo/manusodoo-roto/resultados_ocr/{result_filename}", "w") as f:
                        f.write(ocr_text)
        
        # Si no tenemos datos válidos, devolver error
        if invoice_data is None:
            return {"error": "No se pudo extraer información de la factura"}
        
        # Generar ID único para este resultado
        result_id = str(uuid.uuid4())
        
        # Guardar en caché
        ocr_results_cache[result_id] = {
            "invoice_data": invoice_data,
            "ocr_text": ocr_text,
            "ocr_quality": ocr_quality,
            "method_used": method_used,
            "file_path": file_path,
            "file_name": file.filename,
            "doc_type": doc_type if 'doc_type' in locals() else 'general'
        }
        
        # Return results
        return {
            "result_id": result_id,
            "invoice_data": invoice_data,
            "ocr_text": ocr_text,
            "ocr_quality": ocr_quality,
            "method_used": method_used
        }
        
    except Exception as e:
        print(f"Error processing invoice: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass


@router.post("/invoice/verify", response_model=None)
async def verify_invoice_data(result_id: str = Body(...), verified_data: Dict[str, Any] = Body(...)):
    """
    Verifica y guarda los datos de la factura corregidos manualmente
    """
    if result_id not in ocr_results_cache:
        raise HTTPException(status_code=404, detail="Resultado OCR no encontrado")
    
    # Actualizar los datos verificados
    ocr_results_cache[result_id]["invoice_data"] = verified_data
    ocr_results_cache[result_id]["manually_verified"] = True
    
    return {"message": "Invoice data verified and saved successfully"}


@router.get("/invoice/result/{result_id}")
async def get_ocr_result(result_id: str):
    """
    Obtiene los resultados del OCR por ID para visualización y verificación
    """
    if result_id not in ocr_results_cache:
        raise HTTPException(status_code=404, detail="Resultado OCR no encontrado")
    
    return ocr_results_cache[result_id]


@router.put("/invoice/result/{result_id}")
async def update_ocr_result(result_id: str, updated_data: Dict[str, Any] = Body(...)):
    """
    Actualiza los datos extraídos del OCR después de la verificación manual
    """
    if result_id not in ocr_results_cache:
        raise HTTPException(status_code=404, detail="Resultado OCR no encontrado")
    
    # Actualizar solo los datos de la factura, no el texto OCR ni otros metadatos
    if "invoice_data" in updated_data:
        ocr_results_cache[result_id]["invoice_data"] = updated_data["invoice_data"]
        ocr_results_cache[result_id]["manually_verified"] = True
    
    return {"message": "Datos actualizados correctamente", "result_id": result_id}


@router.post("/invoice/process-verified/{result_id}")
async def process_verified_invoice(result_id: str, invoice_data: Dict[str, Any] = Body(None), supplier_id: int = Body(None), update_if_exists: bool = Body(False)):
    """
    Procesa una factura verificada y la guarda en Odoo
    
    Args:
        result_id: ID del resultado OCR
        invoice_data: Datos de la factura verificados manualmente (opcional)
        supplier_id: ID del proveedor seleccionado manualmente (opcional)
        update_if_exists: Si se debe actualizar la factura si ya existe
    """
    if result_id not in ocr_results_cache:
        raise HTTPException(status_code=404, detail="Resultado OCR no encontrado")
    
    result = ocr_results_cache[result_id]
    
    # Si se proporcionan datos nuevos, actualizar los datos en caché
    if invoice_data:
        result["invoice_data"] = invoice_data
        result["manually_verified"] = True
    
    # Verificar si los datos han sido verificados manualmente
    if not result.get("manually_verified", False):
        raise HTTPException(status_code=400, detail="Los datos de la factura no han sido verificados manualmente")
    
    try:
        # Importar el servicio de importación de facturas
        from api.services.invoice_import_service import InvoiceImportService
        
        # Crear instancia del servicio
        invoice_service = InvoiceImportService()
        
        # Obtener los datos de la factura
        invoice_data_to_process = result["invoice_data"]
        
        # Si se proporciona un ID de proveedor, reemplazar el existente
        if supplier_id:
            invoice_data_to_process["supplier_id"] = supplier_id
        
        # Procesar la factura con los datos verificados
        invoice_id = await invoice_service.import_invoice(invoice_data_to_process, update_if_exists=update_if_exists)
        
        # Actualizar el resultado con el ID de la factura creada
        ocr_results_cache[result_id]["odoo_invoice_id"] = invoice_id
        
        return {
            "message": "Factura procesada y guardada en Odoo correctamente",
            "invoice_id": invoice_id
        }
    except Exception as e:
        logger.error(f"Error al procesar la factura: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la factura: {str(e)}")