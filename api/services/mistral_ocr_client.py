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
            system_prompt = """Eres un asistente especializado en OCR para facturas españolas. Extrae TODO el texto visible de la imagen, manteniendo el formato original lo mejor posible. Incluye todo número, tabla, fecha, nombre, y cualquier texto visible.

INSTRUCCIONES ESPECÍFICAS:

1. DATOS DEL PROVEEDOR:
   - Busca el nombre, NIF/CIF, dirección, teléfono y email del proveedor en la parte superior izquierda de la factura
   - Para facturas NEVIR, verifica que el CIF sea A28966307 (no confundir con A28968307)
   - Para facturas FABRILAMP ILUMINACIÓN S.L., busca el CIF y datos completos en la cabecera
   - Mantén el formato exacto de la dirección

2. DATOS DEL CLIENTE:
   - Busca los datos del cliente en la parte superior derecha de la factura
   - El cliente puede aparecer como "BONACHERA PLAZA, ANTONIO" (con código 04744) o "El Pelotazo"
   - El NIF/CIF puede ser 75236270G o B04957403
   - La dirección debe incluir "CRTA ALICUN 172, 04740 ROQUETAS DE MAR ALMERÍA"
   Para facturas de FABRILAMP ILUMINACIÓN S.L.:
   - El cliente SIEMPRE es "BONACHERA PLAZA, ANTONIO" con NIF 75236270G
   - El cliente está en la parte superior derecha de la factura
   - El IVA es siempre 21% sin recargo de equivalencia
   - Los descuentos aparecen como porcentajes (10%) en cada línea
   - Los códigos de producto son numéricos (ej: 142591403)
   - Los precios unitarios aparecen en la columna "Precio" o "Importe" de la tabla de productos
   - NUNCA devuelvas precios en 0, busca detenidamente los precios en la factura
   - Para productos FABRILAMP, los códigos son numéricos (ejemplo: 142591403)
   - Verifica CUIDADOSAMENTE cada código, distinguiendo entre números y letras similares (0/O, 1/I, 5/S)
   - Presta especial atención a los guiones y caracteres especiales

3. CÓDIGOS DE PRODUCTO:
   - Para productos NEVIR, los códigos SIEMPRE comienzan con "NVR-" seguido de caracteres alfanuméricos
   - Ejemplos correctos: NVR-5525CVSD, NVR-5615DDE, NVR-5607CTNFIDE, NVR-WMFL1280INA-BC
   - Para productos FABRILAMP, los códigos son numéricos (ejemplo: 142591403)
   - Verifica CUIDADOSAMENTE cada código, distinguiendo entre números y letras similares (0/O, 1/I, 5/S)
   - Presta especial atención a los guiones y caracteres especiales

4. IMPUESTOS:
   - Busca la sección de impuestos en la parte inferior derecha
   - Distingue claramente entre:
     * Base Imponible (subtotal sin impuestos)
     * IVA (normalmente 21%)
     * Recargo de Equivalencia (normalmente 5,2%)
     * Total Factura (suma de todo lo anterior)
   - Indica el porcentaje aplicado para cada impuesto
   - Para facturas FABRILAMP: el IVA es SIEMPRE 21% y NO hay recargo de equivalencia

5. LÍNEAS DE PRODUCTOS:
   - Extrae todas las líneas con su código, descripción, cantidad, precio unitario y total
   - Indica si hay descuentos aplicados
   - Mantén el formato exacto de las descripciones

No omitas ninguna información y mantén la estructura original del documento lo mejor posible."""
            
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
            
            # Enviar a la API de chat con temperatura 0 para máxima precisión
            response = mistral_client.chat.complete(
                model=self.ocr_model,
                messages=messages,
                temperature=0.0  # Temperatura 0 para máxima precisión y determinismo
            )
            
            # Extraer texto de la respuesta
            markdown_text = response.choices[0].message.content
            logger.info(f"Texto OCR extraído: {len(markdown_text)} caracteres")
            logger.debug(f"Texto OCR (primeros 400 chars): {markdown_text[:400]}")
            
            return markdown_text
        except Exception as e:
            logger.error(f"Error en extract_text_from_image: {str(e)}")
            return ""
    
    def process_with_invoice_agent(self, ocr_text: str, initial_data: Dict[str, Any], provider_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa el texto OCR con el modelo de chat de Mistral para mejorar y completar los datos extraídos
        
        Args:
            ocr_text: Texto extraído por OCR
            initial_data: Datos iniciales extraídos
            provider_info: Información previa del proveedor (opcional)
            
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
            
            # Información adicional del proveedor si está disponible
            provider_context = ""
            if provider_info:
                if 'supplier_name' in provider_info and provider_info['supplier_name']:
                    provider_context += f"\nPROVEEDOR IDENTIFICADO: {provider_info['supplier_name']}"
                if 'supplier_vat' in provider_info and provider_info['supplier_vat']:
                    provider_context += f"\nNIF/CIF DEL PROVEEDOR: {provider_info['supplier_vat']}"
            
            system_prompt = f"""# INSTRUCCIONES PARA EXTRACCIÓN DE DATOS DE FACTURAS

Eres un asistente especializado en extracción precisa de datos de facturas españolas. Tu tarea es analizar el texto extraído por OCR y extraer todos los datos relevantes en formato JSON estructurado.{provider_context}

## CONTEXTO IMPORTANTE
- Cliente: El cliente es ANTONIO PLAZA BONACHERA (NIF: 75236270G) o EL PELOTAZO (ELECTRO HOGAR)
- Direcciones conocidas del cliente:
  * CARRETERA DE ALICÚN, 172, 04740 ROQUETAS DE MAR (ALMERÍA)
  * PLAZA PLAYA PARAÍSO, 2 BAJO J, 04720 AGUADULCE (ALMERÍA)
- Todos los proveedores aplican IVA 21%
- La mayoría de proveedores aplican Recargo de Equivalencia 5,2%

## PROVEEDORES CONOCIDOS
Identifica primero el proveedor mediante su CIF/NIF, logo o formato de factura:

1. NEVIR (A28966307): Códigos de producto formato NVR-XXXXX
2. ALFADYSER (B60165441): Formato factura 25FVR-XXXXXX, fecha DD/MM/YY
3. ALMCE (B-14851582): Formato factura numérico (25000XXX), fecha DD/MM/YY
4. BSH/BALAY (A-28893550): Formato factura numérico largo, fecha DD.MM.YYYY
5. CECOTEC (ESB97937890): Formato factura 245S1-XXXXXXXX, fecha DD/MM/YY
6. EAS ELECTRIC (B54143177): Formato factura FVN2501-XXXXX-XXXXX, fecha DD/MM/YYYY
7. ELECTRO DIRECTO (B90199779): Formato factura 00-XXXXXX, fecha DD/MM/YYYY
8. JATA: Formato factura XXXXX-XXXXX, imagen posiblemente rotada
9. SONIFER: Formato factura numérico (10054XXX), fecha DD/MM/YY
10. JYSK (B64935604): Formato factura numérico largo (601XXXXXX), fecha DD.MM.YYYY
11. VITROKITCHEN: Formato factura SERIE/FACTURA XXXX XXXX, fecha DD/MM/YYYY
12. WORTEN: Códigos de producto numéricos (7552539, 7700304)
13. MASTER CADENA: Formato factura 625RXXXXXXX, fecha DD/MM/YY

## EXTRACCIÓN DE DATOS
Extrae y estructura los siguientes datos:

1. DATOS DEL PROVEEDOR:
   - Nombre completo
   - CIF/NIF (validar formato español)
   - Dirección completa
   - Teléfono y email (si están disponibles)

2. DATOS DEL CLIENTE:
   - Nombre (ANTONIO PLAZA BONACHERA o EL PELOTAZO)
   - NIF (75236270G)
   - Dirección (identifica cuál de las dos direcciones conocidas se usa)

3. DATOS DE LA FACTURA:
   - Número de factura (respeta el formato específico del proveedor)
   - Fecha de emisión (normaliza a formato YYYY-MM-DD)
   - Fecha de vencimiento (normaliza a formato YYYY-MM-DD)
   - Forma de pago
   - Referencia/Albarán (si existe)

4. LÍNEAS DE PRODUCTOS:
   - Código de producto (respeta el formato específico del proveedor)
   - Descripción
   - Cantidad
   - Precio unitario (sin IVA)
   - Descuento (si aplica)
   - Importe línea (sin IVA)

5. IMPUESTOS Y TOTALES:
   - Base imponible
   - IVA (21%)
   - Recargo de equivalencia (5,2% si aplica)
   - Total factura

## VALIDACIONES ESPECÍFICAS

1. VALIDACIÓN DE CIF/NIF:
   - Corrige errores comunes de OCR (O por 0, I por 1, etc.)
   - Verifica el dígito de control para CIF/NIF españoles
   - Para NEVIR, si el CIF es similar a A28966307 pero con errores, corrige a A28966307

2. VALIDACIÓN DE FECHAS:
   - Detecta los formatos DD/MM/YYYY, DD/MM/YY y DD.MM.YYYY
   - Normaliza todas las fechas a formato YYYY-MM-DD
   - Verifica que las fechas sean lógicas (no futuras ni muy antiguas)

3. VALIDACIÓN DE CÓDIGOS DE PRODUCTO:
   - Para NEVIR: formato NVR-XXXXX
   - Para otros proveedores: respeta su formato específico

4. VALIDACIÓN DE TOTALES:
   - Verifica que la suma de líneas coincida con la base imponible
   - Verifica que base × 0.21 = importe IVA
   - Verifica que base × 0.052 = recargo equivalencia (si aplica)
   - Verifica que base + IVA + recargo = total factura
        
        ESTRUCTURA DE DATOS PARA FACTURAS:
        {{
            "invoice_number": "Número exacto de factura",
            "invoice_date": "Fecha de la factura en formato YYYY-MM-DD",
            "due_date": "Fecha de vencimiento en formato YYYY-MM-DD",
            
            "supplier_name": "Nombre completo del proveedor",
            "supplier_vat": "NIF/CIF del proveedor (verifica que para NEVIR sea A28966307)",
            "supplier_address": "Dirección completa del proveedor",
            "supplier_city": "Ciudad del proveedor",
            "supplier_zip": "Código postal del proveedor",
            
            "customer_name": "Nombre del cliente (BONACHERA PLAZA, ANTONIO o El Pelotazo)",
            "customer_vat": "NIF/CIF del cliente (75236270G o B04957403)",
            "customer_address": "Dirección del cliente (CRTA ALICUN 172)",
            "customer_city": "Ciudad del cliente (ROQUETAS DE MAR)",
            "customer_zip": "Código postal del cliente (04740)",
            
            "subtotal": valor numérico sin símbolo de moneda,
            "tax_amount": valor numérico sin símbolo de moneda (solo IVA),
            "recargo_equivalencia": valor numérico del recargo de equivalencia (5,2%),
            "total_amount": valor numérico sin símbolo de moneda,
            
            "tax_rate": porcentaje de IVA aplicado (21, 10, 4, etc.),
            "recargo_rate": porcentaje de recargo de equivalencia (normalmente 5.2),
            
            "payment_method": "Método de pago indicado en la factura",
            "payment_terms": "Condiciones de pago indicadas en la factura",
            "currency": "EUR",
            
            "line_items": [
                {{
                    "name": "Descripción exacta del producto",
                    "quantity": cantidad numérica,
                    "price_unit": precio unitario numérico sin símbolo de moneda,
                    "discount": porcentaje de descuento si existe (o 0 si no hay),
                    "default_code": "Código/referencia del producto (para NEVIR debe seguir patrón NVR-XXXXX)",
                    "ean13": "Código EAN13 si está disponible",
                    "tax_rate": porcentaje de IVA aplicado a esta línea,
                    "recargo_rate": porcentaje de recargo de equivalencia aplicado a esta línea
                }}
            ]
        }}
        
        IMPORTANTE:
        - Devuelve SOLO los datos relevantes, no inventes información que no esté en el documento
        - Si algún dato no está disponible, déjalo como null o una cadena vacía
        - Asegúrate de que los cálculos son correctos (subtotal + impuestos = total)
        - No incluyas campos adicionales que no estén en la estructura solicitada
        """
            
            # Identificar campos verificados por humano
            verified_fields = [k.replace('_verified', '') for k in initial_data.keys() if k.endswith('_verified')]
            verified_data_info = ""
            
            if verified_fields:
                verified_data_info = "\n\nCAMPOS VERIFICADOS POR HUMANO (NO MODIFICAR):\n"
                for field in verified_fields:
                    if field in initial_data:
                        verified_data_info += f"- {field}: {initial_data[field]}\n"
                logger.info(f"Campos verificados por humano incluidos en el prompt: {', '.join(verified_fields)}")
            
            # Crear un prompt para el usuario que incluya el texto OCR y los datos iniciales
            user_prompt = f"""Analiza el siguiente texto extraído por OCR de un documento comercial y extrae todos los datos relevantes.
        
        TEXTO OCR:
        {ocr_text}
        
        DATOS INICIALES (pueden contener errores u omisiones):
        {json.dumps(initial_data, indent=2, ensure_ascii=False)}{verified_data_info}
        
        INSTRUCCIONES:
        1. Primero, identifica qué tipo de documento es (factura, albarán, presupuesto, etc.)
        2. Extrae TODOS los datos relevantes según el tipo de documento
        3. Presta especial atención a números de referencia, fechas, importes y líneas de productos
        4. Corrige cualquier error en los datos iniciales EXCEPTO los campos verificados por humano
        5. IMPORTANTE: NO MODIFIQUES los campos verificados por humano bajo ninguna circunstancia
        6. Asegúrate de que los importes son valores numéricos y las fechas están en formato YYYY-MM-DD
        
        Devuelve un objeto JSON completo y corregido con los datos del documento.
        """
            
            # Preparar la solicitud con el sistema de agente de facturas
            messages = [
                SystemMessage(content=system_prompt),
                UserMessage(content=user_prompt)
            ]
            
            # Llamar al modelo de chat con temperatura 0 para máxima precisión
            chat_response = mistral_client.chat.complete(
                model=self.chat_model,
                messages=messages,
                temperature=0.0  # Temperatura 0 para máxima precisión y determinismo
            )
            
            # Extraer respuesta
            response_text = chat_response.choices[0].message.content
            logger.info("Respuesta recibida del modelo de chat")
            
            # Extraer JSON de la respuesta
            from .json_extraction_service import extract_json_from_text
            enhanced_data = extract_json_from_text(response_text)
            
            if enhanced_data:
                logger.info("Datos de factura mejorados extraídos correctamente")
                
                # Preservar los campos verificados por humano
                verified_fields = [k.replace('_verified', '') for k in initial_data.keys() if k.endswith('_verified')]
                if verified_fields:
                    logger.info(f"Preservando campos verificados por humano: {', '.join(verified_fields)}")
                    for field in verified_fields:
                        if field in initial_data:
                            # Restaurar el valor original verificado por humano
                            enhanced_data[field] = initial_data[field]
                            # Mantener la marca de verificado
                            enhanced_data[f"{field}_verified"] = True
                            logger.info(f"Campo {field} preservado con valor: {initial_data[field]}")
                
                return enhanced_data
            else:
                logger.warning("No se pudo extraer JSON de la respuesta del modelo. Usando datos iniciales")
                return initial_data
                
        except Exception as e:
            logger.error(f"Error procesando con agente de facturas: {str(e)}")
            return initial_data

# Instancia global del cliente
mistral_ocr_client = MistralOCRClient()
