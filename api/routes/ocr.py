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
import re
from ..services.auth_service import auth_service
from ..services.odoo_service import odoo_service

router = APIRouter(prefix="/api/v1", tags=["ocr"])

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
    invoice_data = {
        'number': None,
        'date': None,
        'partner_name': None,
        'amount_total': 0.0,
        'lines': [],
        'due_dates': [],
        'customer_order_ref': None
    }

    print("OCR Extracted Text for Invoice Processing:")
    print(text[:2000] + "..." if len(text) > 2000 else text)

    # Extract invoice number
    invoice_num_match = re.search(r'FECHA \| FACTURA CLIENTE N\.LF\. TELEFONO[\s\S]*?(\d{8,})', text, re.IGNORECASE)
    if invoice_num_match:
        invoice_data['number'] = invoice_num_match.group(1)
        print(f"Invoice Number Match: {invoice_data['number']}")
    else:
        invoice_num_match = re.search(r'(?:FACTURA|Nº FACTURA|N\. FACTURA|FACTURA N\.|Nº)[\s:]*([0-9]+)', text, re.IGNORECASE)
        if invoice_num_match:
            invoice_data['number'] = invoice_num_match.group(1)
            print(f"Invoice Number Match (Fallback 1): {invoice_data['number']}")
        else:
            invoice_num_match = re.search(r'(\d{8,})', text)
            if invoice_num_match:
                invoice_data['number'] = invoice_num_match.group(0)
                print(f"Invoice Number Match (Fallback 2): {invoice_data['number']}")
            else:
                print("No Invoice Number Match Found")
                invoice_data['number'] = "Unknown"

    # Extract invoice date
    date_match = re.search(r'FECHA \| FACTURA CLIENTE N\.LF\. TELEFONO[\s\S]*?(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
    if date_match:
        invoice_data['date'] = date_match.group(1)
        print(f"Date Match: {invoice_data['date']}")
    else:
        date_match = re.search(r'(?:FECHA|Fecha factura)[\s:]*(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
        if date_match:
            invoice_data['date'] = date_match.group(1)
            print(f"Date Match (Fallback): {invoice_data['date']}")
        else:
            print("No Date Match Found")

    # Extract supplier name (partner_name)
    supplier_match = re.search(r'(?:A\s+)?([A-Z\s\.]+)\s*(?:C\.I\.F\.|CIF)', text, re.IGNORECASE)
    if supplier_match:
        invoice_data['partner_name'] = supplier_match.group(1).strip()
        print(f"Supplier Name Match: {invoice_data['partner_name']}")
    else:
        supplier_match = re.search(r'ALMCE S\.L\.', text, re.IGNORECASE)
        if supplier_match:
            invoice_data['partner_name'] = supplier_match.group(0)
            print(f"Supplier Name Match (Fallback): {invoice_data['partner_name']}")
        else:
            invoice_data['partner_name'] = "ALMCE S.L."
            print("No Supplier Name Match Found, Using Default: ALMCE S.L.")

    # Extract total amount
    total_match = re.search(r'Vencimientos:[\s\S]*?(\d+\.?\d{0,2})', text, re.IGNORECASE)
    if total_match:
        try:
            invoice_data['amount_total'] = float(total_match.group(1).replace(',', '.'))
            print(f"Total Amount Match: {invoice_data['amount_total']}")
        except ValueError:
            invoice_data['amount_total'] = 0.0
            print("Total Amount Match Found but Conversion Failed")
    else:
        total_match = re.search(r'(?:TOTAL FRA\.|TOTAL FACTURA|TOTAL €|TOTAL)[\s:]*(\d+\.?\d{0,2})', text, re.IGNORECASE)
        if total_match:
            try:
                invoice_data['amount_total'] = float(total_match.group(1).replace(',', '.'))
                print(f"Total Amount Match (Fallback 1): {invoice_data['amount_total']}")
            except ValueError:
                invoice_data['amount_total'] = 0.0
                print("Total Amount Match (Fallback 1) Found but Conversion Failed")
        else:
            total_match = re.search(r'(\d+\.?\d{0,2})\s*(?:€|$)', text, re.MULTILINE)
            if total_match:
                for match in re.finditer(r'(\d+\.?\d{0,2})\s*(?:€|$)', text, re.MULTILINE):
                    try:
                        amount = float(match.group(1).replace(',', '.'))
                        if amount > invoice_data['amount_total']:
                            invoice_data['amount_total'] = amount
                            print(f"Total Amount Match (Fallback 2): {invoice_data['amount_total']}")
                    except ValueError:
                        continue
                if invoice_data['amount_total'] == 0.0:
                    print("Total Amount Match (Fallback 2) Found but Conversion Failed")
            else:
                print("No Total Amount Match Found")

    # Extract due dates
    due_date_match = re.search(r'(?:Vencimientos|VENCIMIENTO|Vto\.)[\s:]*(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
    if due_date_match:
        invoice_data['due_dates'] = [due_date_match.group(1)]
        print(f"Due Date Match: {invoice_data['due_dates']}")
    else:
        print("No Due Date Match Found")

    # Extract product lines (basic approach, can be improved)
    lines_matches = re.findall(r'([A-Za-z0-9\s,]+?),\s*(\d+)\s+(\d+\.?\d{0,2})\s+(\d+\.?\d{0,2})', text)
    for match in lines_matches:
        description = match[0].strip()
        qty = int(match[1])
        price_unit = float(match[2].replace(',', '.'))
        invoice_data['lines'].append({
            'name': description,
            'quantity': qty,
            'price_unit': price_unit
        })
        print(f"Product Line Match: {description}, Qty: {qty}, Price: {price_unit}")
    if not lines_matches:
        lines_matches = re.findall(r'([A-Za-z0-9\s,]+?)\s+(\d+)\s+(\d+\.?\d{0,2})', text)
        for match in lines_matches:
            description = match[0].strip()
            if "Calentador" in description or "CCATP" in description:  # Filter for relevant product descriptions
                try:
                    qty = int(match[1])
                    price_unit = float(match[2].replace(',', '.'))
                    invoice_data['lines'].append({
                        'name': description,
                        'quantity': qty,
                        'price_unit': price_unit
                    })
                    print(f"Product Line Match (Fallback): {description}, Qty: {qty}, Price: {price_unit}")
                except ValueError:
                    continue
        if not invoice_data['lines']:
            print("No Product Lines Match Found")

    # Extract customer order reference
    order_ref_match = re.search(r'Ped\.\s+([0-9]+[A-Za-z0-9-]*)', text, re.IGNORECASE)
    if order_ref_match:
        invoice_data['customer_order_ref'] = order_ref_match.group(1)
        print(f"Customer Order Reference Match: {invoice_data['customer_order_ref']}")
    else:
        order_ref_match = re.search(r'(?:Ped\.|Pedido|Ref\.)[\s:]*([0-9]+[A-Za-z0-9-]*)', text, re.IGNORECASE)
        if order_ref_match:
            invoice_data['customer_order_ref'] = order_ref_match.group(1)
            print(f"Customer Order Reference Match (Fallback): {invoice_data['customer_order_ref']}")
        else:
            print("No Customer Order Reference Match Found")

    return invoice_data

@router.post("/invoice")
async def process_invoice(file: UploadFile = File(...)):
    print("Processing invoice endpoint called. File: ", file.filename)
    try:
        # Read file content
        content = await file.read()
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)

        # Perform OCR and extract text
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(content)
        processed_images = [preprocess_image(img) for img in images]
        text = ''.join([pytesseract.image_to_string(img, lang='spa', config='--dpi 300 --psm 6') for img in processed_images])

        # Extract structured data from OCR text
        invoice_data = extract_invoice_data(text)

        # Search for supplier ID using the extracted partner name
        supplier = odoo_service.get_supplier_by_name(invoice_data['partner_name'])
        supplier_id = supplier['id'] if supplier else None

        if supplier_id is None:
            raise HTTPException(status_code=404, detail=f"Supplier {invoice_data['partner_name']} not found in Odoo")

        # Create invoice in Odoo
        invoice_id = odoo_service.create_invoice(supplier_id=supplier_id, invoice_data=invoice_data)

        return {"message": "Invoice processed successfully", "invoice_id": invoice_id, "extracted_data": invoice_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
