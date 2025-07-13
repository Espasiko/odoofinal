"""
Cliente para la API de Mistral OCR
"""
import logging
import base64
import os
import json
from typing import Dict, Any, Optional
from mistralai import Mistral
from mistralai import SystemMessage, UserMessage

from ..utils.config import config

logger = logging.getLogger(__name__)

class MistralOCRClient:
    """Cliente para interactuar con la API de Mistral para OCR"""
    
    def __init__(self):
        """Inicializa el cliente con la API key de Mistral"""
        self.api_key = config.MISTRAL_API_KEY
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY no está configurada en las variables de entorno")
        
        # Modelos disponibles
        self.ocr_model = "pixtral-12b-2409"  # Modelo multimodal abierto con capacidad de visión
        self.chat_model = "mistral-small-2506"  # Modelo para chat (versión abierta)
    
    def get_client(self) -> Mistral:
        """
        Crea una nueva instancia del cliente Mistral
        
        Returns:
            Mistral: Cliente de Mistral API
        """
        return Mistral(api_key=self.api_key)
    
    def extract_text_from_image(self, image_base64: str) -> str:
        """
        Extrae texto de una imagen usando el modelo multimodal de Mistral
        
        Args:
            image_base64: Imagen en formato base64
            
        Returns:
            str: Texto extraído de la imagen
        """
        try:
            # Crear cliente Mistral
            mistral_client = self.get_client()
            
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
                model=self.ocr_model,
                messages=messages
            )
            
            # Extraer texto de la respuesta
            markdown_text = response.choices[0].message.content
            logger.info(f"Texto OCR extraído: {len(markdown_text)} caracteres")
            logger.debug(f"Texto OCR (primeros 400 chars): {markdown_text[:400]}")
            
            return markdown_text
        except Exception as e:
            logger.error(f"Error en extract_text_from_image: {str(e)}")
            return ""
    
    def process_with_invoice_agent(self, ocr_text: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa el texto OCR con el modelo de chat de Mistral para mejorar y completar los datos extraídos
        
        Args:
            ocr_text: Texto extraído por OCR
            initial_data: Datos iniciales extraídos
            
        Returns:
            Dict[str, Any]: Datos mejorados
        """
        try:
            logger.info("Procesando factura con modelo de chat de Mistral")
            
            # Crear nuevo cliente Mistral
            mistral_client = self.get_client()
                
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
                model=self.chat_model,
                messages=messages
            )
            
            # Extraer respuesta
            response_text = chat_response.choices[0].message.content
            logger.info("Respuesta recibida del modelo de chat")
            
            # Extraer JSON de la respuesta
            from .json_extraction_service import extract_json_from_text
            enhanced_data = extract_json_from_text(response_text)
            
            if enhanced_data:
                logger.info("Datos de factura mejorados extraídos correctamente")
                return enhanced_data
            else:
                logger.warning("No se pudo extraer JSON de la respuesta del modelo. Usando datos iniciales")
                return initial_data
                
        except Exception as e:
            logger.error(f"Error procesando con agente de facturas: {str(e)}")
            return initial_data

# Instancia global del cliente
mistral_ocr_client = MistralOCRClient()
