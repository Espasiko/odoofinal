import os
import logging
import base64
import json
import tempfile
import mimetypes
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from pdf2image import convert_from_path
from pydantic import BaseModel, Field
from mistralai import Mistral
from mistralai import SystemMessage, UserMessage

from ..utils.config import config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Singleton instance
_mistral_free_ocr_service_instance = None

def get_mistral_free_ocr_service() -> 'MistralFreeOCRService':
    """
    Returns a singleton instance of MistralFreeOCRService
    """
    global _mistral_free_ocr_service_instance
    if _mistral_free_ocr_service_instance is None:
        _mistral_free_ocr_service_instance = MistralFreeOCRService()
    return _mistral_free_ocr_service_instance

# Definir el modelo de datos para facturas en Odoo
class InvoiceLine(BaseModel):
    name: str = Field(description="Descripción del producto o servicio")
    quantity: float = Field(description="Cantidad")
    price_unit: float = Field(description="Precio unitario")
    default_code: Optional[str] = Field(None, description="Código del producto")

class OdooInvoice(BaseModel):
    invoice_number: str = Field(description="Número de factura")
    invoice_date: str = Field(description="Fecha de la factura (formato DD/MM/YYYY)")
    due_date: Optional[str] = Field(None, description="Fecha de vencimiento (formato DD/MM/YYYY)")
    
    supplier_name: str = Field(description="Nombre del PROVEEDOR (quien emite la factura)")
    supplier_vat: Optional[str] = Field(None, description="CIF/NIF del proveedor")
    supplier_address: Optional[str] = Field(None, description="Dirección del proveedor")
    supplier_city: Optional[str] = Field(None, description="Ciudad del proveedor")
    supplier_zip: Optional[str] = Field(None, description="Código postal del proveedor")
    supplier_email: Optional[str] = Field(None, description="Email del proveedor")
    supplier_phone: Optional[str] = Field(None, description="Teléfono del proveedor")
    
    customer_name: Optional[str] = Field(None, description="Nombre del CLIENTE (quien recibe la factura)")
    customer_vat: Optional[str] = Field(None, description="CIF/NIF del cliente")
    
    total_amount: float = Field(description="Importe total con impuestos")
    tax_amount: Optional[float] = Field(None, description="Importe de impuestos")
    subtotal: Optional[float] = Field(None, description="Subtotal sin impuestos")
    
    payment_terms: Optional[str] = Field(None, description="Condiciones de pago")
    customer_order_ref: Optional[str] = Field(None, description="Referencia de pedido del cliente")
    
    line_items: list[InvoiceLine] = Field(default_factory=list, description="Líneas de productos/servicios")
class MistralFreeOCRService:
    """
    Servicio para integración con Mistral OCR API gratuita
    Utiliza Document Annotation para extraer datos estructurados de facturas
    Integra agentes de Mistral para análisis avanzado de facturas
    """
    
    def __init__(self):
        self.api_key = config.MISTRAL_API_KEY
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY no está configurada en las variables de entorno")
        
        # Ya no usamos una instancia persistente del cliente, la creamos en cada método
        # para asegurar que siempre se usa la versión más reciente de la API
        self.ocr_model = "pixtral-12b-2409"  # Modelo multimodal abierto con capacidad de visión
        self.chat_model = "mistral-small-2506"  # Modelo para chat (versión abierta)
    
    def get_supported_formats(self) -> list[str]:
        """
        Devuelve los formatos de archivo soportados
        """
        return ['.pdf', '.jpg', '.jpeg', '.png']
    
    def validate_file_size(self, file_path: str) -> bool:
        """
        Valida que el archivo no exceda el límite de tamaño (50MB)
        """
        max_size_mb = 50
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        return file_size_mb <= max_size_mb
    
    def process_invoice_file(self, file_path: str) -> Dict[str, Any]:
        """
        Procesa un archivo de factura (PDF o imagen) y extrae datos estructurados
        usando la API de Mistral Chat y luego mejora los resultados
        con un agente especializado en análisis de facturas
        """
        try:
            # Validar tamaño de archivo
            if not self.validate_file_size(file_path):
                return {
                    'success': False,
                    'error': "El archivo excede el límite de 50MB"
                }
                
            # Detectar si es PDF y convertirlo a imagen
            if file_path.lower().endswith('.pdf'):
                logger.info(f"Procesando PDF: {file_path}")
                # Convertir PDF a imagen para OCR
                images = convert_from_path(file_path)
                
                if not images:
                    return {'success': False, 'error': 'No se pudieron extraer imágenes del PDF'}
                
                # Guardar la primera página como imagen temporal
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    temp_image_path = temp_file.name
                
                images[0].save(temp_image_path, 'PNG')
                
                # Leer la imagen en base64
                with open(temp_image_path, 'rb') as image_file:
                    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                
                # Eliminar el archivo temporal
                try:
                    os.unlink(temp_image_path)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar imagen temporal: {e}")
            else:
                # Si ya es una imagen, leerla directamente
                with open(file_path, 'rb') as image_file:
                    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            logger.info("Enviando documento a Mistral API usando chat con imagen")
            
            # Crear cliente Mistral
            api_key = config.MISTRAL_API_KEY
            mistral_client = Mistral(api_key=api_key)
            
            # Usar el modelo de chat con imágenes - incluir información del cliente
            system_prompt = """Eres un asistente especializado en OCR para facturas. Extrae TODO el texto visible de la imagen, manteniendo el formato original lo mejor posible. Incluye todo número, tabla, fecha, nombre, y cualquier texto visible. Presta especial atención a:

1. Número de factura
2. Fecha de factura
3. Fecha de vencimiento
4. Datos del proveedor (nombre, NIF/CIF, dirección, teléfono, email)
5. Datos del cliente (El Pelotazo, NIF B04957403)
6. Líneas de productos (código, descripción, cantidad, precio unitario, descuentos)
7. Subtotales, impuestos y total
8. Método de pago y condiciones
9. Algunas facturas presentan los precios con iva , otros solo la iva y puedes aprender de los formatos que vas procesando para ser mas correcto y eficiente. 
No omitas ninguna información. El documento pertenece a la empresa 'El Pelotazo' de Antonio Plaza Bonachera con NIF B04957403 y SIEMPRE ES EL CLIENTE"""
            
            # Preparar los mensajes
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extrae el texto completo de esta factura. Necesito identificar claramente todos los datos importantes como número de factura, fecha, proveedor, productos y totales."},
                        {"type": "image_url", "image_url": f"data:image/png;base64,{image_base64}"}
                    ]
                }
            ]
            
            # Enviar a la API de chat
            response = mistral_client.chat.complete(
                model="pixtral-12b-2409",
                messages=messages
            )
            
            # Extraer texto de la respuesta
            markdown_text = response.choices[0].message.content
            logger.info(f"Texto OCR extraído: {len(markdown_text)} caracteres")
            logger.debug(f"Texto OCR (primeros 400 chars): {markdown_text[:400]}")
            
            # Extraer datos básicos de la factura
            invoice_data = self._extract_invoice_data_from_text(markdown_text)

            # Mejorar los datos con el agente de facturas
            enhanced_data, chat_response_text = self._process_with_invoice_agent(markdown_text, invoice_data, return_raw_response=True)
            logger.debug(f"Respuesta cruda del modelo de chat (primeros 400 chars): {chat_response_text[:400]}")
            logger.debug(f"JSON extraído: {json.dumps(enhanced_data, ensure_ascii=False)[:400]}")

            # Preparar resultado
            return {
                'success': True,
                'invoice_data': enhanced_data,
                'ocr_text': markdown_text
            }
        except Exception as e:
            logger.error(f"Error procesando PDF: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_ocr_text(self, response) -> str:
        """
        Extrae el texto OCR completo de la respuesta para procesamiento con agentes
        """
        try:
            # En la versión 1.9.1 del SDK, la respuesta tiene páginas con texto markdown
            if hasattr(response, 'pages') and len(response.pages) > 0:
                # Extraer el texto markdown de todas las páginas
                return "\n".join([page.markdown for page in response.pages if hasattr(page, 'markdown')])
            # Verificar otros formatos de respuesta
            elif hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                # Último recurso: convertir el objeto a string
                return str(response)
        except Exception as e:
            logger.error(f"Error extrayendo texto OCR: {e}")
            return ""
    
    def _process_with_invoice_agent(self, ocr_text: str, initial_data: Dict[str, Any], return_raw_response: bool = False) -> Dict[str, Any]:
        """
        Procesa el texto OCR con el modelo de chat de Mistral para mejorar y completar los datos extraídos
        """
        try:
            logger.info("Procesando factura con modelo de chat de Mistral")
            
            # Crear nuevo cliente Mistral
            api_key = config.MISTRAL_API_KEY
            mistral_client = Mistral(api_key=api_key)
                
            # Crear un prompt para el agente de documentos avanzado
            fecha_ejemplo = "2025-07-08"
            codigo_postal = "04721"
            system_prompt = f"""Eres un agente inteligente especializado en análisis de documentos comerciales para El Pelotazo (Antonio Plaza Bonachera).
        Tu misión es analizar el texto extraído por OCR, identificar el tipo de documento y extraer todos los datos relevantes.
        
        CONTEXTO IMPORTANTE:
        - Estamos en España, todos los importes están en EUROS (EUR)
        - El cliente es siempre: El Pelotazo (Antonio Plaza Bonachera), con NIF B04957403
        - Dirección del cliente: Carretera de Alicún, s/n, El Parador de las Hortichuelas, Almería, CP {codigo_postal}
        - Estamos procesando documentos para Odoo 18, que requiere datos muy específicos
        - Todos los datos monetarios deben ser valores numéricos sin símbolos de moneda
        
        CAPACIDADES COMO AGENTE:
        1. IDENTIFICACIÓN: Determina automáticamente si es una factura, albarán, presupuesto u otro documento
        2. ADAPTACIÓN: Ajusta tu estrategia de extracción según el tipo de documento identificado
        3. EXTRACCIÓN PRECISA: Extrae todos los datos relevantes con exactitud
        4. VALIDACIÓN: Verifica la coherencia de los datos (fechas válidas, cálculos correctos, etc.)
        5. NORMALIZACIÓN: Convierte fechas a formato YYYY-MM-DD y valores monetarios a números
        
        INSTRUCCIONES ESPECÍFICAS PARA FACTURAS:
        1. El número de factura debe extraerse EXACTAMENTE como aparece, sin alteraciones
        2. Las fechas deben convertirse a formato YYYY-MM-DD (ejemplo: {fecha_ejemplo})
        3. Extrae TODAS las líneas de productos con sus códigos, cantidades, precios y descuentos
        4. Los importes monetarios deben ser valores numéricos sin el símbolo de euro (ejemplo: 100.25)
        5. Identifica correctamente el régimen de IVA aplicado (general, reducido, superreducido)
        6. Captura el método y condiciones de pago exactos
        
        ESTRUCTURA DE DATOS PARA FACTURAS:
        {{
            "invoice_number": "Número exacto de factura",
            "invoice_date": "Fecha de la factura en formato YYYY-MM-DD",
            "due_date": "Fecha de vencimiento en formato YYYY-MM-DD",
            "supplier_name": "Nombre completo del proveedor",
            "supplier_vat": "NIF/CIF del proveedor",
            "supplier_address": "Dirección completa del proveedor",
            "supplier_city": "Ciudad del proveedor",
            "supplier_zip": "Código postal del proveedor",
            "customer_name": "El Pelotazo",
            "customer_vat": "B04957403",
            "subtotal": valor numérico sin símbolo de moneda,
            "tax_amount": valor numérico sin símbolo de moneda,
            "total_amount": valor numérico sin símbolo de moneda,
            "tax_rate": porcentaje de IVA aplicado (21, 10, 4, etc.),
            "payment_method": "Método de pago indicado en la factura",
            "payment_terms": "Condiciones de pago indicadas en la factura",
            "currency": "EUR",
            "line_items": [
                {{
                    "name": "Descripción exacta del producto",
                    "quantity": cantidad numérica,
                    "price_unit": precio unitario numérico sin símbolo de moneda,
                    "discount": porcentaje de descuento si existe (o 0 si no hay),
                    "default_code": "Código/referencia del producto",
                    "ean13": "Código EAN13 si está disponible",
                    "tax_rate": porcentaje de IVA aplicado a esta línea
                }}
            ]
        }}
        
        IMPORTANTE:
        - Devuelve SOLO los datos relevantes, no inventes información que no esté en el documento
        - Si algún dato no está disponible, déjalo como null o una cadena vacía
        - Asegúrate de que los cálculos son correctos (subtotal + impuestos = total)
        - No incluyas campos adicionales que no estén en la estructura solicitada
        """
            
            # Crear un prompt para el usuario que incluya el texto OCR y los datos iniciales
            user_prompt = f"""Analiza el siguiente texto extraído por OCR de un documento comercial y extrae todos los datos relevantes.
        
        TEXTO OCR:
        {ocr_text}
        
        DATOS INICIALES (pueden contener errores u omisiones):
        {json.dumps(initial_data, indent=2, ensure_ascii=False)}
        
        INSTRUCCIONES:
        1. Primero, identifica qué tipo de documento es (factura, albarán, presupuesto, etc.)
        2. Extrae TODOS los datos relevantes según el tipo de documento
        3. Presta especial atención a números de referencia, fechas, importes y líneas de productos
        4. Corrige cualquier error en los datos iniciales
        5. Asegúrate de que los importes son valores numéricos y las fechas están en formato YYYY-MM-DD
        
        Devuelve un objeto JSON completo y corregido con los datos del documento.
        """
            
            # Preparar la solicitud con el sistema de agente de facturas
            messages = [
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt)
            ]
            
            # Llamar al modelo de chat
            chat_response = mistral_client.chat.complete(
                model="mistral-small-2506",
                messages=messages
            )
            
            # Extraer respuesta
            response_text = chat_response.choices[0].message.content
            logger.info("Respuesta recibida del modelo de chat")
            
            # Extraer JSON de la respuesta
            enhanced_data = self._extract_json_from_text(response_text)
            if enhanced_data:
                logger.info("Datos de factura mejorados extraídos correctamente")
                if return_raw_response:
                    return enhanced_data, response_text
                return enhanced_data
            else:
                logger.warning("No se pudo extraer JSON de la respuesta del modelo. Usando datos iniciales")
                if return_raw_response:
                    return initial_data, response_text
                return initial_data
                
        except Exception as e:
            logger.error(f"Error procesando con agente de facturas: {str(e)}")
            return initial_data
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extrae objeto JSON de un texto, maneja casos donde el JSON está embebido en markdown
        """
        try:
            # Intentar encontrar JSON en el texto usando regex
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # Si no hay bloques de código, intentar parsear todo el texto como JSON
            try:
                return json.loads(text)
            except:
                pass
            
            # Intentar encontrar el primer { y último } para extraer JSON
            start = text.find('{')
            end = text.rfind('}')
            if start >= 0 and end > start:
                json_str = text[start:end+1]
                return json.loads(json_str)
                
            return {}
        except Exception as e:
            logger.error(f"Error extrayendo JSON de texto: {str(e)}")
            return {}
    def _extract_invoice_data_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extrae datos estructurados de factura desde texto OCR markdown
        Específicamente optimizado para facturas de Alfadyser
        """
        lines = text.split('\n')
        invoice_data = {
            "invoice_number": "",
            "invoice_date": "",
            "due_date": "",
            "supplier_name": "",
            "supplier_vat": "",
            "supplier_address": "",
            "supplier_city": "",
            "supplier_zip": "",
            "customer_name": "",
            "customer_vat": "",
            "total_amount": 0.0,
            "tax_amount": 0.0,
            "subtotal": 0.0,
            "customer_order_ref": "",
            "line_items": []
        }
        
        # Buscar número de factura específicamente para facturas Alfadyser (formato 25FVR-0012334)
        for line in lines:
            # Patrón para facturas Alfadyser (formato específico)
            matches = re.findall(r'\b(\d+[A-Z]+-\d+)\b', line)
            if matches:
                invoice_data["invoice_number"] = matches[0].strip()
                break
                
        # Si no se encontró con el patrón específico, buscar en encabezados de tablas
        if not invoice_data["invoice_number"]:
            for i, line in enumerate(lines):
                if '|  Número factura | Fecha | Cód. Cliente  |' in line and i + 2 < len(lines):
                    data_line = lines[i + 2]
                    if data_line.startswith('|'):
                        cells = [cell.strip() for cell in data_line.split('|') if cell.strip()]
                        if len(cells) >= 2:
                            invoice_data["invoice_number"] = cells[0].strip()
                            if len(cells) >= 3:
                                # Convertir fecha al formato ISO (YYYY-MM-DD)
                                date_str = cells[1].strip()
                                try:
                                    for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                                        try:
                                            date_obj = datetime.strptime(date_str, fmt)
                                            invoice_data["invoice_date"] = date_obj.strftime('%Y-%m-%d')
                                            break
                                        except ValueError:
                                            continue
                                except Exception:
                                    invoice_data["invoice_date"] = date_str
                            break
                            
        # Si todavía no tenemos número de factura, buscar patrones genéricos
        if not invoice_data["invoice_number"]:
            for line in lines:
                match = re.search(r'(?:Factura|Número)[\s:]*(\w+[-/]?\w*)', line, re.IGNORECASE)
                if match:
                    invoice_data["invoice_number"] = match.group(1).strip()
                    break
        
        # Buscar NIF/CIF del proveedor (formato común: letra + números)
        for line in lines:
            vat_matches = re.findall(r'\b[A-Z0-9]{1}[-\s]?\d{7,8}[-\s]?[A-Z0-9]{1}\b', line, re.IGNORECASE)
            if vat_matches:
                invoice_data["supplier_vat"] = vat_matches[0].replace(' ', '').replace('-', '')
                break
            if "NIF:" in line or "CIF:" in line or "N.I.F.:" in line:
                vat_matches = re.findall(r'(?:NIF|CIF|N\.I\.F\.):?\s*([A-Z0-9]{1}[-\s]?\d{7,8}[-\s]?[A-Z0-9]{1})', line, re.IGNORECASE)
                if vat_matches:
                    invoice_data["supplier_vat"] = vat_matches[0].replace(' ', '').replace('-', '')
                    break
        
        # Buscar fecha de factura si no la tenemos ya
        if not invoice_data["invoice_date"]:
            for line in lines:
                # Buscar texto que mencione fecha de factura
                if "fecha" in line.lower() and "factura" in line.lower():
                    # Extraer fechas en formato DD/MM/YYYY o DD-MM-YYYY
                    date_matches = re.findall(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b', line)
                    if date_matches:
                        date_str = date_matches[0]
                        try:
                            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                                try:
                                    date_obj = datetime.strptime(date_str, fmt)
                                    invoice_data["invoice_date"] = date_obj.strftime('%Y-%m-%d')
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            invoice_data["invoice_date"] = date_str
                        break
        
        # Lista de proveedores conocidos por nombre
        known_suppliers = {
            "ALFADYSER": "ALFADYSER",
            "CECOTEC": "CECOTEC",
            "BECKEN": "BECKEN-TEGALUXE",
            "TEGALUXE": "BECKEN-TEGALUXE",
            "JATA": "JATA",
            "ALMCE": "ALMCE S.L.",
            "ALMACENES": "ALMCE S.L.",
            "ABRILA": "ABRILA",
            "BSH": "BSH",
            "EAS JOHNSON": "EAS JOhNSON",
            "MI ELECTRO": "MI ELECTRO",
            "MIELECTRO": "MIELECTRO",
            "NEVIR": "NEVIR",
            "ORBEGOZO": "ORBEGOZO",
            "UFESA": "UFESA",
            "VITROKITCHEN": "VITROKITCHEN"
        }
        
        # Lista de clientes conocidos para evitar confusiones
        known_customers = ["EL PELOTAZO", "ANTONIO BONACHERA", "CARRETERA DE ALICUN", "B04957403"]
        
        # Buscar nombre del proveedor en lista de proveedores conocidos
        supplier_found = False
        for line in lines:
            # Primero verificar si esta línea contiene información de un cliente conocido
            if any(customer.lower() in line.lower() for customer in known_customers):
                # Si encontramos un cliente conocido, lo guardamos pero seguimos buscando el proveedor
                if not invoice_data["customer_name"]:
                    for customer in known_customers:
                        if customer.lower() in line.lower():
                            invoice_data["customer_name"] = "EL PELOTAZO - ANTONIO BONACHERA"
                            break
                continue
            
            # Buscar proveedores conocidos
            for supplier_key, supplier_full_name in known_suppliers.items():
                if supplier_key.lower() in line.lower():
                    invoice_data["supplier_name"] = supplier_full_name
                    supplier_found = True
                    break
            
            if supplier_found:
                break
                
        # Si encontramos un nombre de cliente pero no de proveedor en una factura Alfadyser
        # Por defecto asignamos Alfadyser como proveedor si el formato del documento sugiere que es una factura suya
        if not supplier_found and invoice_data["customer_name"] and any("FVR-" in line for line in lines):
            invoice_data["supplier_name"] = "ALFADYSER S.L."
            supplier_found = True
                
        # Si no lo encontramos específicamente, buscar secciones de "proveedor" o en encabezados
        if not supplier_found:
            for i, line in enumerate(lines[:10]):  # Buscar en primeras líneas
                if len(line.strip()) > 5 and not line.startswith('|') and not re.match(r'^\d', line):
                    # Probablemente el nombre del proveedor en el encabezado
                    invoice_data["supplier_name"] = line.strip()
                    supplier_found = True
                    
                    # Buscar dirección en las siguientes líneas
                    if i + 1 < len(lines) and len(lines[i+1].strip()) > 0:
                        invoice_data["supplier_address"] = lines[i+1].strip()
                    break
        
        # Buscar importe total con IVA
        total_found = False
        for line in lines:
            # Buscar patrones específicos de totales
            if "total" in line.lower() or "importe" in line.lower():
                # Patrón para importes con símbolo € o EUR
                amount_matches = re.findall(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})(?:\s*€|\s*EUR)?', line)
                if amount_matches:
                    try:
                        # Normalizar separadores decimales y de miles
                        amount_str = amount_matches[-1].replace('.', '').replace(',', '.')
                        invoice_data["total_amount"] = float(amount_str)
                        total_found = True
                        break
                    except ValueError:
                        pass
        
        # Buscar en tablas de resumen de importes
        if not total_found:
            for i, line in enumerate(lines):
                if '|  Base imponible |' in line and i + 2 < len(lines):
                    for j in range(i+1, min(i+5, len(lines))):
                        data_line = lines[j]
                        if '| Total |' in data_line:
                            cells = [cell.strip() for cell in data_line.split('|') if cell.strip()]
                            if len(cells) >= 2:
                                try:
                                    # Extraer el último valor como importe total
                                    amount_str = cells[-1].replace('€', '').replace('.', '').replace(',', '.').strip()
                                    invoice_data["total_amount"] = float(amount_str)
                                    total_found = True
                                    break
                                except ValueError:
                                    pass
        
        # Buscar IVA y base imponible
        tax_amount_found = False
        subtotal_found = False
        
        # Buscar en líneas que mencionan IVA
        for line in lines:
            if "iva" in line.lower() or "i.v.a" in line.lower():
                # Extraer valor del IVA
                amount_matches = re.findall(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})(?:\s*€|\s*EUR)?', line)
                if amount_matches:
                    try:
                        # Normalizar separadores
                        amount_str = amount_matches[-1].replace('.', '').replace(',', '.')
                        invoice_data["tax_amount"] = float(amount_str)
                        tax_amount_found = True
                        break
                    except ValueError:
                        pass
        
        # Buscar base imponible
        for line in lines:
            if "base" in line.lower() and ("imponible" in line.lower() or "imp" in line.lower()):
                amount_matches = re.findall(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})(?:\s*€|\s*EUR)?', line)
                if amount_matches:
                    try:
                        amount_str = amount_matches[-1].replace('.', '').replace(',', '.')
                        invoice_data["subtotal"] = float(amount_str)
                        subtotal_found = True
                        break
                    except ValueError:
                        pass
        
        # Si tenemos total pero no tenemos alguno de los otros, hacer cálculos aproximados
        if total_found and not (tax_amount_found and subtotal_found):
            # Si tenemos base pero no IVA
            if subtotal_found and not tax_amount_found:
                # Asumimos IVA 21% (común en España)
                invoice_data["tax_amount"] = round(invoice_data["subtotal"] * 0.21, 2)
            # Si tenemos IVA pero no base
            elif tax_amount_found and not subtotal_found:
                # Calculamos la base aproximada
                invoice_data["subtotal"] = round(invoice_data["total_amount"] - invoice_data["tax_amount"], 2)
            # Si no tenemos ninguno, asumimos IVA 21%
            elif not tax_amount_found and not subtotal_found:
                # Base imponible = total / 1.21
                invoice_data["subtotal"] = round(invoice_data["total_amount"] / 1.21, 2)
                invoice_data["tax_amount"] = round(invoice_data["total_amount"] - invoice_data["subtotal"], 2)
        
        # Extraer líneas de productos/servicios (primero buscamos en tablas)
        product_lines = []
        table_found = False
        
        # Buscar tablas de productos
        for i, line in enumerate(lines):
            if '|  Referencia |' in line or '|  Código |' in line or '|  Descripción |' in line:
                # Determinamos los índices de las columnas
                header = line.split('|')
                col_indices = {}
                for j, col in enumerate(header):
                    col = col.strip().lower()
                    if 'referencia' in col or 'código' in col or 'ref' in col:
                        col_indices['code'] = j
                    elif 'descripción' in col or 'concepto' in col or 'detalle' in col:
                        col_indices['name'] = j
                    elif 'cantidad' in col or 'uds' in col:
                        col_indices['quantity'] = j
                    elif 'precio' in col or 'importe' in col or 'unitario' in col:
                        col_indices['price'] = j
                
                # Si encontramos al menos descripción y precio, procesamos la tabla
                if 'name' in col_indices and ('price' in col_indices or 'quantity' in col_indices):
                    table_found = True
                    
                    # Procesar filas de la tabla (excluyendo encabezados y líneas vacías)
                    for j in range(i+1, len(lines)):
                        row = lines[j]
                        if not row.startswith('|') or '---' in row:
                            continue
                        
                        cells = row.split('|')
                        if len(cells) < len(header):
                            continue
                        
                        # Crear línea de producto
                        product_line = {
                            "name": "",
                            "quantity": 1.0,
                            "price_unit": 0.0,
                            "default_code": ""
                        }
                        
                        # Extraer datos según las columnas identificadas
                        for key, idx in col_indices.items():
                            if idx < len(cells):
                                value = cells[idx].strip()
                                if key == 'name':
                                    product_line["name"] = value
                                elif key == 'code':
                                    product_line["default_code"] = value
                                elif key == 'quantity':
                                    try:
                                        # Normalizar el valor numérico
                                        value = value.replace('.', '').replace(',', '.')
                                        product_line["quantity"] = float(value)
                                    except ValueError:
                                        pass
                                elif key == 'price':
                                    try:
                                        # Normalizar y eliminar símbolo de moneda
                                        value = value.replace('€', '').replace('.', '').replace(',', '.').strip()
                                        product_line["price_unit"] = float(value)
                                    except ValueError:
                                        pass
                        
                        # Solo añadimos si tiene nombre y algún valor numérico
                        if product_line["name"] and (product_line["quantity"] > 0 or product_line["price_unit"] > 0):
                            product_lines.append(product_line)
        
        # Si no encontramos líneas en tablas, intentar encontrarlas en texto plano
        if not table_found and not product_lines:
            # Buscar líneas que coincidan con patrones de producto y precio
            for line in lines:
                # Buscar líneas con cantidad y precio
                match = re.search(r'(.+?)\s+(\d+(?:[.,]\d+)?)\s+(?:x\s+)?(\d+(?:[.,]\d+)?)', line)
                if match:
                    name = match.group(1).strip()
                    try:
                        qty = float(match.group(2).replace(',', '.'))
                        price = float(match.group(3).replace(',', '.'))
                        
                        product_lines.append({
                            "name": name,
                            "quantity": qty,
                            "price_unit": price,
                            "default_code": ""
                        })
                    except ValueError:
                        pass
        
        # Añadir las líneas de productos encontradas
        invoice_data["line_items"] = product_lines
        
        return invoice_data
