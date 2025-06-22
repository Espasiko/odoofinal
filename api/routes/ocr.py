from fastapi import APIRouter, File, UploadFile, HTTPException
import cv2
import numpy as np
from PIL import Image
import pytesseract
import io
import os
import tempfile
from invoice2data import extract_data
from invoice2data.extract.loader import read_templates

router = APIRouter(prefix="/api/v1", tags=["ocr"])

from ..services.auth_service import auth_service
from ..services.odoo_service import odoo_service

# Function to preprocess image using OpenCV
def preprocess_image(image):
    # Convert PIL image to OpenCV format
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    # Convert to grayscale
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    # Apply threshold to get image with only black and white
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    # Convert back to PIL Image
    result_image = Image.fromarray(cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB))
    return result_image

# Function to extract invoice data using invoice2data with custom templates
def extract_invoice_data_with_template(file_path, supplier_name):
    # Load templates from a directory or define here
    templates_dir = "/home/espasiko/mainmanusodoo/manusodoo-roto/api/templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Example template for ALMCE - to be expanded for other suppliers
    almce_template_path = os.path.join(templates_dir, "almce.yml")
    if not os.path.exists(almce_template_path):
        with open(almce_template_path, 'w') as f:
            f.write("""
issuer: ALMCE
fields:
  invoice_number:
    - FA\d+
    - '25000\d{3}'
  date: \d{2}/\d{2}/\d{2,4}
  amount_total: 'Total: .*?(\d+\.\d{2})'
keywords:
  - ALMCE
  - Factura
            """)
    
    templates = read_templates(templates_dir)
    data = extract_data(file_path, templates=templates)
    return data

# Function to extract invoice data from OCR text
def extract_invoice_data(text):
    lines = text.split('\n')
    invoice_data = {
        'number': '',
        'date': '',
        'partner_name': '',
        'amount_total': 0.0,
        'lines': [],
        'due_dates': [],
        'customer_order_ref': ''
    }
    import re
    print("OCR Extracted Text for Invoice Processing:")
    print(text[:2000] + "..." if len(text) > 2000 else text)
    for i, line in enumerate(lines):
        line = line.strip()
        line_lower = line.lower()
        # Extract invoice number with higher priority
        if not invoice_data['number'] and ('factura' in line_lower or 'albaran' in line_lower or 'pedido' in line_lower or 'fa' in line_lower or 'nº' in line_lower or 'numero' in line_lower or 'num.' in line_lower or 'fact.' in line_lower):
            parts = line.split()
            for j, part in enumerate(parts):
                if re.match(r'(FA)?\d{8}', part) or re.match(r'FA\d+', part):
                    invoice_data['number'] = part
                    break
                elif re.match(r'\d{5,8}', part) and 'factura' in line_lower:
                    invoice_data['number'] = part
                    break
            if not invoice_data['number']:
                for part in parts:
                    if 'fa' in part.lower():
                        invoice_data['number'] = part
                        break
        # Extract date
        if not invoice_data['date']:
            date_match = re.search(r'\d{2}[/-]\d{2}[/-]\d{2,4}', line)
            if date_match:
                invoice_data['date'] = date_match.group(0).replace('-', '/')
        # Extract supplier name
        if not invoice_data['partner_name'] and any(kw in line_lower for kw in ['almce', 's.l.', 's.a.', 'proveedor', 'empresa', 'sociedad']):
            parts = line.split()
            name_parts = []
            for part in parts:
                if any(kw in part.lower() for kw in ['almce', 's.l.', 's.a.']):
                    name_parts.append(part)
            if name_parts:
                invoice_data['partner_name'] = ' '.join(name_parts)
        # Extract total amount with broader keywords
        if invoice_data['amount_total'] == 0.0 and any(kw in line_lower for kw in ['total', 'importe', 'base', 'iva', 'neto', 'pagar', 'subtotal']):
            total_match = re.search(r'(\d+\.?\d{0,2})', line)
            if total_match:
                try:
                    invoice_data['amount_total'] = float(total_match.group(1))
                except ValueError:
                    pass
        # Extract product lines (basic pattern)
        if re.match(r'^\d+\s', line) and len(line.split()) > 2:
            invoice_data['lines'].append(line)
        # Extract due dates
        if 'vencimiento' in line_lower or 'pago' in line_lower:
            date_match = re.search(r'\d{2}[/-]\d{2}[/-]\d{2,4}', line)
            if date_match:
                invoice_data['due_dates'].append(date_match.group(0).replace('-', '/'))
        # Extract customer order reference
        if not invoice_data['customer_order_ref'] and any(kw in line_lower for kw in ['pedido', 'referencia', 'orden', 'cliente', 'ref.', 'po']):
            parts = line.split()
            for part in parts:
                if re.match(r'PO-\d+', part) or re.match(r'\d{6,}', part):
                    invoice_data['customer_order_ref'] = part
                    break
    return invoice_data

@router.post("/invoice")
async def process_invoice(file: UploadFile = File(...)):
    try:
        # Read file content
        content = await file.read()
        
        # Convert PDF to image for preprocessing
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(content)
        processed_images = [preprocess_image(img) for img in images]
        
        # Extract text with optimized Tesseract parameters
        text = ''.join([pytesseract.image_to_string(img, lang='spa', config='--dpi 300 --psm 6') for img in processed_images])
        
        # Save file temporarily for invoice2data processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Try extracting data with invoice2data template
        template_data = extract_invoice_data_with_template(temp_file_path, "ALMCE")
        os.unlink(temp_file_path)  # Clean up temp file
        
        # Fallback to manual extraction if template fails
        if not template_data or 'invoice_number' not in template_data:
            invoice_data = extract_invoice_data(text)
        else:
            invoice_data = {
                'number': template_data.get('invoice_number', ''),
                'date': template_data.get('date', ''),
                'partner_name': 'ALMCE S.L.',  # Hardcoded for now
                'amount_total': float(template_data.get('amount_total', 0.0)) if template_data.get('amount_total') else 0.0,
                'lines': [],  # To be expanded in template
                'due_dates': [],
                'customer_order_ref': ''
            }
        
        if not invoice_data['partner_name']:
            supplier = odoo_service.get_supplier_by_name(invoice_data['partner_name'])
            if supplier:
                invoice_data['partner_name'] = supplier['name']
        
        invoice_id = odoo_service.create_invoice(invoice_data)
        return {"message": "Invoice processed successfully", "invoice_id": invoice_id, "extracted_data": invoice_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing invoice: {str(e)}")
