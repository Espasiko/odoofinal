from fastapi import APIRouter, File, UploadFile, HTTPException
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
    # opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    # Convert to grayscale
    # gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    # Apply threshold to get image with only black and white
    # thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    # Convert back to PIL Image
    # result_image = Image.fromarray(cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB))
    return image

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
    - FA\\d+
    - '25000\\d{3}'
  date: \\d{2}/\\d{2}/\\d{2,4}
  amount_total: 'Total: .*?(\\d+\\.\\d{2})'
  partner_name: 'Cliente: (.*)'
  customer_order_ref: 'Pedido: (.*)'
keywords:
  - ALMCE
  - Factura
            """)
    
    templates = read_templates(templates_dir)
    data = extract_data(file_path, templates=templates)
    print(f"OCR: Datos extraídos con plantilla para {supplier_name}: {data}")
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
        'customer_order_ref': None,
        'customer_name': None,
        'customer_address': None,
        'total_imp': 0.0,
        'importe_percentage': 0.0,
        'base_iva_percentage': 0.0,
        'rec_percentage': 0.0,
        'total_fra': 0.0,
        'payment_method': None
    }

    print("OCR: Texto extraído para procesamiento de factura (primeros 2000 caracteres):")
    print(text[:2000] + "..." if len(text) > 2000 else text)

    # Extract invoice number
    invoice_num_match = re.search(r'FECHA \| FACTURA CLIENTE N\.I\.F\. TELÉFONO[\s\S]*?(\d{8,})', text, re.IGNORECASE)
    if invoice_num_match:
        invoice_data['number'] = invoice_num_match.group(1)
        print(f"OCR: Coincidencia de número de factura: {invoice_data['number']}")
    else:
        invoice_num_match = re.search(r'(?:FACTURA|Nº FACTURA|N\. FACTURA|FACTURA N\.|Nº)[\s:]*([0-9]+)', text, re.IGNORECASE)
        if invoice_num_match:
            invoice_data['number'] = invoice_num_match.group(1)
            print(f"OCR: Coincidencia de número de factura (Fallback 1): {invoice_data['number']}")
        else:
            invoice_num_match = re.search(r'(\d{8,})', text)
            if invoice_num_match:
                invoice_data['number'] = invoice_num_match.group(0)
                print(f"OCR: Coincidencia de número de factura (Fallback 2): {invoice_data['number']}")
            else:
                print("OCR: No se encontró coincidencia para número de factura")
                invoice_data['number'] = "Unknown"

    # Extract invoice date
    date_match = re.search(r'FECHA \| FACTURA CLIENTE N\.I\.F\. TELÉFONO[\s\S]*?(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
    if date_match:
        invoice_data['date'] = date_match.group(1)
        print(f"OCR: Coincidencia de fecha: {invoice_data['date']}")
    else:
        date_match = re.search(r'(?:FECHA|Fecha factura)[\s:]*(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
        if date_match:
            invoice_data['date'] = date_match.group(1)
            print(f"OCR: Coincidencia de fecha (Fallback): {invoice_data['date']}")
        else:
            print("OCR: No se encontró coincidencia para fecha")

    # Extract supplier name (partner_name)
    supplier_match = re.search(r'(?:A \s+)?([A-Z\s\.]+)\s*(?:C\.I\.F\.|CIF)', text, re.IGNORECASE)
    if supplier_match:
        invoice_data['partner_name'] = supplier_match.group(1).strip()
        print(f"OCR: Coincidencia de nombre de proveedor: {invoice_data['partner_name']}")
    else:
        supplier_match = re.search(r'ALMCE S\.L\.', text, re.IGNORECASE)
        if supplier_match:
            invoice_data['partner_name'] = supplier_match.group(0)
            print(f"OCR: Coincidencia de nombre de proveedor (Fallback): {invoice_data['partner_name']}")
        else:
            invoice_data['partner_name'] = "ALMCE S.L."
            print("OCR: No se encontró coincidencia para nombre de proveedor, utilizando valor por defecto: ALMCE S.L.")

    # Extract customer name and address
    customer_match = re.search(r'^(?:ANTONIO PLAZA BONACHERA|EL PELOTAZO)[\s\S]*?(?=PÁG\.)', text, re.MULTILINE)
    if customer_match:
        customer_text = customer_match.group(0).strip()
        customer_lines = customer_text.splitlines()
        if customer_lines:
            invoice_data['customer_name'] = customer_lines[0].strip()
            print(f"OCR: Coincidencia de nombre de cliente: {invoice_data['customer_name']}")
            if len(customer_lines) > 1:
                invoice_data['customer_address'] = ' '.join(customer_lines[1:]).strip()
                print(f"OCR: Coincidencia de dirección de cliente: {invoice_data['customer_address']}")
    else:
        customer_match = re.search(r'EL PELOTAZO[\s\S]*?(?=PÁG\.)', text, re.MULTILINE)
        if customer_match:
            customer_text = customer_match.group(0).strip()
            customer_lines = customer_text.splitlines()
            if customer_lines:
                invoice_data['customer_name'] = customer_lines[0].strip()
                print(f"OCR: Coincidencia de nombre de cliente (Fallback): {invoice_data['customer_name']}")
                if len(customer_lines) > 1:
                    invoice_data['customer_address'] = ' '.join(customer_lines[1:]).strip()
                    print(f"OCR: Coincidencia de dirección de cliente (Fallback): {invoice_data['customer_address']}")
        else:
            print("OCR: No se encontró coincidencia para nombre o dirección de cliente")

    # Extract total amount
    total_match = re.search(r'TOTAL FRA\.\s*€[\s\S]*?(\d+,?\d{0,3}\.?\d{0,2})', text, re.IGNORECASE)
    if total_match:
        try:
            invoice_data['amount_total'] = float(total_match.group(1).replace(',', ''))
            invoice_data['total_fra'] = invoice_data['amount_total']
            print(f"OCR: Coincidencia de monto total: {invoice_data['amount_total']}")
        except ValueError:
            invoice_data['amount_total'] = 0.0
            invoice_data['total_fra'] = 0.0
            print("OCR: Coincidencia de monto total encontrada pero falló la conversión")
    else:
        total_match = re.search(r'(?:TOTAL FRA\.|TOTAL FACTURA|TOTAL €|TOTAL)[\s:]*(\d+,?\d{0,3}\.?\d{0,2})', text, re.IGNORECASE)
        if total_match:
            try:
                invoice_data['amount_total'] = float(total_match.group(1).replace(',', ''))
                invoice_data['total_fra'] = invoice_data['amount_total']
                print(f"OCR: Coincidencia de monto total (Fallback 1): {invoice_data['amount_total']}")
            except ValueError:
                invoice_data['amount_total'] = 0.0
                invoice_data['total_fra'] = 0.0
                print("OCR: Coincidencia de monto total (Fallback 1) encontrada pero falló la conversión")
        else:
            total_match = re.search(r'(\d+,?\d{0,3}\.?\d{0,2})\s*(?:€|$)', text, re.MULTILINE)
            if total_match:
                max_amount = 0.0
                for match in re.finditer(r'(\d+,?\d{0,3}\.?\d{0,2})\s*(?:€|$)', text, re.MULTILINE):
                    try:
                        amount = float(match.group(1).replace(',', ''))
                        if amount > max_amount and amount < 10000:  # Filtrar valores razonables
                            max_amount = amount
                            print(f"OCR: Coincidencia de monto total (Fallback 2): {max_amount}")
                    except ValueError:
                        continue
                invoice_data['amount_total'] = max_amount
                invoice_data['total_fra'] = max_amount
                if invoice_data['amount_total'] == 0.0:
                    print("OCR: Coincidencia de monto total (Fallback 2) encontrada pero falló la conversión")
            else:
                print("OCR: No se encontró coincidencia para monto total")

    # Extract due dates
    due_date_match = re.search(r'(?:Vencimientos|VENCIMIENTO|Vto\.)[\s:]*(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)
    if due_date_match:
        invoice_data['due_dates'] = [due_date_match.group(1)]
        print(f"OCR: Coincidencia de fecha de vencimiento: {invoice_data['due_dates']}")
    else:
        print("OCR: No se encontró coincidencia para fecha de vencimiento")

    # Extract product lines with specific pattern for ALMCE invoice
    lines_matches = re.findall(r'([A-Z0-9]+)\s+([^\n]+?)\s+(\d+)\s+(\d+\.?\d{0,2})\s+(\d+\.?\d{0,2})', text)
    for match in lines_matches:
        code = match[0].strip()
        description = match[1].strip()
        try:
            qty = int(match[2])
            price_unit = float(match[3].replace(',', '.'))
            total = float(match[4].replace(',', '.'))
            if qty > 0 and qty < 100 and price_unit > 0 and total > 0:  # Filtrar valores razonables
                invoice_data['lines'].append({
                    'name': f"{code} - {description}",
                    'quantity': qty,
                    'price_unit': price_unit
                })
                print(f"OCR: Coincidencia de línea de producto: {code} - {description}, Cantidad: {qty}, Precio: {price_unit}, Total: {total}")
        except ValueError:
            continue
    if not lines_matches:
        lines_matches = re.findall(r'([A-Z0-9]+)\s+([^\n]+?)\s+(\d+)\s+(\d+\.?\d{0,2})', text)
        for match in lines_matches:
            code = match[0].strip()
            description = match[1].strip()
            try:
                qty = int(match[2])
                price_unit = float(match[3].replace(',', '.'))
                if qty > 0 and qty < 100 and price_unit > 0:  # Filtrar valores razonables
                    invoice_data['lines'].append({
                        'name': f"{code} - {description}",
                        'quantity': qty,
                        'price_unit': price_unit
                    })
                    print(f"OCR: Coincidencia de línea de producto (Fallback): {code} - {description}, Cantidad: {qty}, Precio: {price_unit}")
            except ValueError:
                continue
        if not invoice_data['lines']:
            print("OCR: No se encontraron coincidencias para líneas de producto")

    # Extract customer order reference
    order_ref_match = re.search(r'Ped\.\s+([0-9]+[A-Za-z0-9-]*)', text, re.IGNORECASE)
    if order_ref_match:
        invoice_data['customer_order_ref'] = order_ref_match.group(1)
        print(f"OCR: Coincidencia de referencia de pedido del cliente: {invoice_data['customer_order_ref']}")
    else:
        order_ref_match = re.search(r'(?:Ped\.|Pedido|Ref\.)[\s:]*([0-9]+[A-Za-z0-9-]*)', text, re.IGNORECASE)
        if order_ref_match:
            invoice_data['customer_order_ref'] = order_ref_match.group(1)
            print(f"OCR: Coincidencia de referencia de pedido del cliente (Fallback): {invoice_data['customer_order_ref']}")
        else:
            print("OCR: No se encontró coincidencia para referencia de pedido del cliente")

    # Extract totals table data
    totals_match = re.search(r'TOTAL IMP\.\s*[\%\s]*IMPORTE\s*BASE\s*[\%\s]*I\.V\.A\.\s*[\%\s]*REC\.\s*TOTAL\s*FRA\.\s*[\s\S]*?(\d+[,.]?\d{0,3}[,.]?\d{0,2})\s+(\d+[,.]?\d{0,2})\s+(\d+[,.]?\d{0,2})\s+(\d+[,.]?\d{0,3}[,.]?\d{0,2})\s+(\d+[,.]?\d{0,3}[,.]?\d{0,2})', text, re.IGNORECASE)
    if totals_match:
        try:
            invoice_data['total_imp'] = float(totals_match.group(1).replace(',', '').replace('.', ''))
            invoice_data['importe_percentage'] = float(totals_match.group(2).replace(',', '.').replace('.', '.'))
            invoice_data['base_iva_percentage'] = float(totals_match.group(3).replace(',', '.').replace('.', '.'))
            invoice_data['rec_percentage'] = float(totals_match.group(4).replace(',', '').replace('.', ''))
            invoice_data['total_fra'] = float(totals_match.group(5).replace(',', '').replace('.', ''))
            invoice_data['amount_total'] = invoice_data['total_fra']
            print(f"OCR: Coincidencia de tabla de totales - TOTAL IMP.: {invoice_data['total_imp']}, % IMPORTE: {invoice_data['importe_percentage']}, BASE % I.V.A.: {invoice_data['base_iva_percentage']}, % REC.: {invoice_data['rec_percentage']}, TOTAL FRA.: {invoice_data['total_fra']}")
        except ValueError:
            print("OCR: Coincidencia de tabla de totales encontrada pero falló la conversión")
    else:
        # Intentar una búsqueda más específica para BASE, IVA, % y REC con patrones más flexibles
        base_match = re.search(r'BASE\s*[\S]*\s*(\d+[,.]?\d{0,3}[,.]?\d{0,2})', text, re.IGNORECASE)
        if base_match:
            try:
                invoice_data['total_imp'] = float(base_match.group(1).replace(',', '').replace('.', ''))
                print(f"OCR: Coincidencia de BASE: {invoice_data['total_imp']}")
            except ValueError:
                print("OCR: Coincidencia de BASE encontrada pero falló la conversión")

        iva_match = re.search(r'I\.V\.A\.\s*[\S]*\s*(\d+[,.]?\d{0,3}[,.]?\d{0,2})', text, re.IGNORECASE)
        if iva_match:
            try:
                invoice_data['importe_percentage'] = float(iva_match.group(1).replace(',', '').replace('.', ''))
                print(f"OCR: Coincidencia de I.V.A.: {invoice_data['importe_percentage']}")
            except ValueError:
                print("OCR: Coincidencia de I.V.A. encontrada pero falló la conversión")

        percentage_match = re.search(r'%\s*IMPORTE\s*[\S]*\s*(\d+[,.]?\d{0,2})', text, re.IGNORECASE)
        if percentage_match:
            try:
                invoice_data['base_iva_percentage'] = float(percentage_match.group(1).replace(',', '.').replace('.', '.'))
                print(f"OCR: Coincidencia de % IMPORTE: {invoice_data['base_iva_percentage']}")
            except ValueError:
                print("OCR: Coincidencia de % IMPORTE encontrada pero falló la conversión")

        rec_match = re.search(r'%\s*REC\.\s*[\S]*\s*(\d+[,.]?\d{0,3}[,.]?\d{0,2})', text, re.IGNORECASE)
        if rec_match:
            try:
                invoice_data['rec_percentage'] = float(rec_match.group(1).replace(',', '').replace('.', ''))
                print(f"OCR: Coincidencia de % REC.: {invoice_data['rec_percentage']}")
            except ValueError:
                print("OCR: Coincidencia de % REC. encontrada pero falló la conversión")

        if not (base_match and iva_match and percentage_match and rec_match):
            print("OCR: No se encontraron todas las coincidencias para tabla de totales")

    # Extract payment method
    payment_match = re.search(r'Forma de Pago[\s:]*([A-Za-z0-9\s]+)', text, re.IGNORECASE)
    if payment_match:
        invoice_data['payment_method'] = payment_match.group(1).strip()
        print(f"OCR: Coincidencia de forma de pago: {invoice_data['payment_method']}")
    else:
        payment_match = re.search(r'GIRO A 30 DIAS', text, re.IGNORECASE)
        if payment_match:
            invoice_data['payment_method'] = payment_match.group(0)
            print(f"OCR: Coincidencia de forma de pago (Fallback): {invoice_data['payment_method']}")
        else:
            print("OCR: No se encontró coincidencia para forma de pago")

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
            # Crear proveedor si no existe
            supplier_id = odoo_service.create_supplier(invoice_data['partner_name'])
            if supplier_id is None:
                raise HTTPException(status_code=404, detail=f"Supplier {invoice_data['partner_name']} not found in Odoo and could not be created")

        # Create invoice in Odoo
        invoice_id = odoo_service.create_invoice(supplier_id=supplier_id, invoice_data=invoice_data)

        return {"message": "Invoice processed successfully", "invoice_id": invoice_id, "extracted_data": invoice_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
