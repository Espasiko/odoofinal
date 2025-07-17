"""
Biblioteca de prompts específicos para proveedores
Este módulo proporciona prompts optimizados para diferentes proveedores
"""
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ProviderPrompts:
    """Clase para gestionar prompts específicos por proveedor"""
    
    @staticmethod
    def get_provider_by_name(name: str) -> Optional[str]:
        """
        Detecta el proveedor basado en el nombre
        
        Args:
            name: Nombre del proveedor
            
        Returns:
            Optional[str]: Código del proveedor o None si no se reconoce
        """
        if not name:
            return None
            
        name_lower = name.lower()
        
        # Mapeo de nombres a códigos de proveedor
        provider_mappings = {
            'nevir': 'NEVIR',
            'nev': 'NEVIR',
            'abrila': 'ABRILA',
            'mi electro': 'MIELECTRO',
            'mielectro': 'MIELECTRO',
        }
        
        # Buscar coincidencias
        for key, value in provider_mappings.items():
            if key in name_lower:
                return value
                
        return None
    
    @staticmethod
    def get_provider_by_vat(vat: str) -> Optional[str]:
        """
        Detecta el proveedor basado en el NIF/CIF
        
        Args:
            vat: NIF/CIF del proveedor
            
        Returns:
            Optional[str]: Código del proveedor o None si no se reconoce
        """
        if not vat:
            return None
            
        # Eliminar espacios y convertir a mayúsculas
        vat = vat.upper().replace(" ", "").replace("-", "")
        
        # Mapeo de NIF/CIF a códigos de proveedor
        vat_mappings = {
            'A28966307': 'NEVIR',
            'A28968307': 'NEVIR',  # Posible error común
            'B04957403': 'ELPELOTAZO',  # El Pelotazo (cliente)
            '75236270G': 'ELPELOTAZO',  # Antonio Plaza Bonachera (cliente)
        }
        
        return vat_mappings.get(vat)
    
    @staticmethod
    def detect_provider_from_ocr(ocr_text: str, initial_data: Dict[str, Any] = None) -> Optional[str]:
        """
        Detecta el proveedor basado en el texto OCR y los datos iniciales
        
        Args:
            ocr_text: Texto OCR completo
            initial_data: Datos iniciales extraídos
            
        Returns:
            Optional[str]: Código del proveedor o None si no se reconoce
        """
        if not ocr_text and not initial_data:
            return None
        
        logger = logging.getLogger(__name__)
        detected_provider = None
            
        # Intentar detectar por nombre de proveedor en los datos iniciales
        if initial_data and "supplier_name" in initial_data:
            provider_code = ProviderPrompts.get_provider_by_name(initial_data["supplier_name"])
            if provider_code:
                logger.info(f"Proveedor detectado por nombre: {provider_code}")
                detected_provider = provider_code
                
        # Intentar detectar por NIF/CIF en los datos iniciales
        if not detected_provider and initial_data and "supplier_vat" in initial_data:
            provider_code = ProviderPrompts.get_provider_by_vat(initial_data["supplier_vat"])
            if provider_code:
                logger.info(f"Proveedor detectado por NIF/CIF: {provider_code}")
                detected_provider = provider_code
                
        # Si tenemos texto OCR, buscar patrones conocidos
        if not detected_provider and ocr_text:
            ocr_text_lower = ocr_text.lower()
            
            # Diccionario de patrones de texto por proveedor
            provider_patterns = {
                "NEVIR": [
                    "nevir", "nvr-", "a28966307", "a-28966307", "a28968307",  # CIF correcto y error común
                    "francisco rabal", "alcalá de henares",  # Dirección
                    "congelador vertical", "frigorífico doble puerta",  # Productos típicos
                    "combi total no frost", "lavadora vapor", "horno eléctrico"  # Más productos
                ],
                "ABRILA": [
                    "abrila", "abr-", "b12345678",  # Nombre y posible CIF
                    "electrodomésticos abrila", "abrila electrodomésticos"
                ],
                "MIELECTRO": [
                    "mi electro", "mielectro", "mi-electro", 
                    "distribución electrodomésticos", "mayorista electro"
                ]
            }
            
            # Contar coincidencias para cada proveedor
            matches = {}
            for provider, patterns in provider_patterns.items():
                matches[provider] = 0
                for pattern in patterns:
                    if pattern in ocr_text_lower:
                        matches[provider] += 1
            
            # Seleccionar el proveedor con más coincidencias (si hay al menos 2)
            best_provider = None
            best_matches = 1  # Mínimo 2 coincidencias para considerar válido
            
            for provider, count in matches.items():
                if count > best_matches:
                    best_provider = provider
                    best_matches = count
            
            if best_provider:
                logger.info(f"Proveedor detectado por patrones en texto OCR: {best_provider} con {best_matches} coincidencias")
                detected_provider = best_provider
                
            # Buscar CIF/NIF conocidos como último recurso
            if not detected_provider:
                normalized_text = ocr_text_lower.replace(" ", "").replace("-", "")
                if "a28966307" in normalized_text or "a28968307" in normalized_text:
                    logger.info("Proveedor NEVIR detectado por CIF en texto OCR")
                    detected_provider = "NEVIR"
                
        return detected_provider
        
    @staticmethod
    def get_system_prompt_for_provider(provider_code: str) -> str:
        """
        Obtiene el prompt de sistema específico para un proveedor
        
        Args:
            provider_code: Código del proveedor
            
        Returns:
            str: Prompt de sistema para el proveedor
        """
        # Prompt base para todos los proveedores
        base_prompt = """Eres un asistente especializado en OCR para facturas españolas. Extrae TODO el texto visible de la imagen, manteniendo el formato original lo mejor posible. Incluye todo número, tabla, fecha, nombre, y cualquier texto visible.

INSTRUCCIONES ESPECÍFICAS:

1. DATOS DEL PROVEEDOR:
   - Busca el nombre, NIF/CIF, dirección, teléfono y email del proveedor en la parte superior izquierda de la factura
   - Mantén el formato exacto de la dirección

2. DATOS DEL CLIENTE:
   - El cliente es siempre "EL PELOTAZO" con nombre completo "BONACHERA PLAZA, ANTONIO (04744)"
   - CIF/NIF: 75236270G
   - Dirección completa: CRTRA DE ALICUN 172, ROQUETAS DE MAR, 04740, ALMERÍA, ESPAÑA
   - No confundas los datos del cliente con los del proveedor

3. IMPUESTOS:
   - Busca la sección de impuestos en la parte inferior derecha
   - Distingue claramente entre:
     * Base Imponible (subtotal sin impuestos)
     * IVA (normalmente 21%)
     * Recargo de Equivalencia (normalmente 5,2%)
     * Total Factura (suma de todo lo anterior)
   - Indica el porcentaje aplicado para cada impuesto

4. LÍNEAS DE PRODUCTOS:
   - Extrae todas las líneas con su código, descripción, cantidad, precio unitario y total
   - Indica si hay descuentos aplicados
   - Mantén el formato exacto de las descripciones

5. DISTINGUE CLARAMENTE ENTRE:
   - Albarán (documento de entrega)
   - Factura (documento de cobro)
   - Pedido (documento de solicitud)

No omitas ninguna información y mantén la estructura original del documento lo mejor posible."""

        # Prompts específicos por proveedor
        provider_prompts = {
            'NEVIR': base_prompt + """

INSTRUCCIONES ESPECÍFICAS PARA FACTURAS NEVIR:
1. El CIF correcto de NEVIR es A28966307 (no confundir con A28968307)
2. Los códigos de producto NEVIR SIEMPRE comienzan con "NVR-" seguido de caracteres alfanuméricos
3. Ejemplos correctos: NVR-5525CVSD, NVR-5615DDE, NVR-5607CTNFIDE, NVR-WMFL1280INA-BC
4. Verifica CUIDADOSAMENTE cada código, distinguiendo entre números y letras similares (0/O, 1/I, 5/S)
5. Presta especial atención a los guiones y caracteres especiales
6. Las facturas NEVIR suelen incluir Recargo de Equivalencia (5,2%) además del IVA (21%)""",

            'ABRILA': base_prompt + """

INSTRUCCIONES ESPECÍFICAS PARA FACTURAS ABRILA:
1. Verifica que el CIF sea el correcto
2. Los códigos de producto suelen tener un formato específico
3. Presta especial atención a los descuentos aplicados
4. Las facturas pueden incluir gastos de envío separados""",

            'MIELECTRO': base_prompt + """

INSTRUCCIONES ESPECÍFICAS PARA FACTURAS MI ELECTRO:
1. Verifica que el CIF sea el correcto
2. Los códigos de producto suelen tener un formato numérico
3. Presta especial atención a las promociones y ofertas especiales
4. Las facturas suelen incluir condiciones de garantía específicas""",
        }
        
        # Devolver el prompt específico o el base si no hay específico
        return provider_prompts.get(provider_code, base_prompt)
    
    @staticmethod
    def get_user_prompt_for_provider(provider_code: str, ocr_text: str, initial_data: Dict[str, Any]) -> str:
        """
        Obtiene el prompt de usuario específico para un proveedor
        
        Args:
            provider_code: Código del proveedor
            ocr_text: Texto extraído por OCR
            initial_data: Datos iniciales extraídos
            
        Returns:
            str: Prompt de usuario para el proveedor
        """
        # Prompt base para todos los proveedores
        base_prompt = f"""Analiza el siguiente texto extraído por OCR de un documento comercial y extrae todos los datos relevantes.
        
TEXTO OCR:
{ocr_text}

DATOS INICIALES (pueden contener errores u omisiones):
{initial_data}

INSTRUCCIONES:
1. Primero, identifica qué tipo de documento es (factura, albarán, presupuesto, etc.)
2. Extrae TODOS los datos relevantes según el tipo de documento
3. Presta especial atención a números de referencia, fechas, importes y líneas de productos
4. Corrige cualquier error en los datos iniciales
5. Asegúrate de que los importes son valores numéricos y las fechas están en formato YYYY-MM-DD

Devuelve un objeto JSON completo y corregido con los datos del documento."""

        # Prompts específicos por proveedor
        provider_user_prompts = {
            'NEVIR': f"""Analiza el siguiente texto extraído por OCR de una factura NEVIR y extrae todos los datos relevantes.
        
TEXTO OCR:
{ocr_text}

DATOS INICIALES (pueden contener errores u omisiones):
{initial_data}

INSTRUCCIONES ESPECÍFICAS PARA NEVIR:
1. PROVEEDOR:
   - El CIF correcto de NEVIR es A28966307 (no confundir con A28968307)
   - La dirección correcta es: Calle Francisco Rabal, 3, 28806 Alcalá de Henares, Madrid

2. CLIENTE:
   - El cliente SIEMPRE es "EL PELOTAZO" con nombre completo "BONACHERA PLAZA, ANTONIO (04744)"
   - El NIF del cliente es 75236270G
   - La dirección del cliente es CRTRA DE ALICUN 172, ROQUETAS DE MAR, 04740, ALMERÍA
   - IMPORTANTE: El cliente aparece en la parte superior derecha de la factura

3. CÓDIGOS DE PRODUCTO:
   - Los códigos de producto NEVIR SIEMPRE comienzan con "NVR-" seguido de caracteres alfanuméricos
   - Formato correcto de ejemplos: NVR-5525CVSD, NVR-5615DDE, NVR-5607CTNFIDE, NVR-WMFL1280INA-BC
   - NUNCA deben contener "SEP" o "MAR" en el código (estos son errores comunes de OCR)
   - Verifica cuidadosamente cada código y corrige según el patrón correcto

4. IMPUESTOS:
   - SIEMPRE separa el IVA (21%) del Recargo de Equivalencia (5,2%)
   - Calcula: IVA = Base Imponible * 0.21
   - Calcula: Recargo = Base Imponible * 0.052
   - Verifica que IVA + Recargo = Total Impuestos

5. DOCUMENTOS:
   - Distingue claramente entre número de factura, número de albarán y número de pedido
   - El número de factura suele tener formato FXXYYYYY donde XX es el año
   - Asegúrate de que las fechas están en formato YYYY-MM-DD

Devuelve un objeto JSON completo y corregido con los datos de la factura NEVIR, asegurándote de que todos los códigos de producto y los impuestos están correctamente estructurados.""",

            'ABRILA': f"""Analiza el siguiente texto extraído por OCR de una factura ABRILA y extrae todos los datos relevantes.
        
TEXTO OCR:
{ocr_text}

DATOS INICIALES (pueden contener errores u omisiones):
{initial_data}

INSTRUCCIONES ESPECÍFICAS PARA ABRILA:
1. PROVEEDOR:
   - Verifica el CIF correcto de ABRILA
   - Extrae la dirección completa del proveedor

2. CLIENTE:
   - El cliente SIEMPRE es "EL PELOTAZO" con nombre completo "BONACHERA PLAZA, ANTONIO (04744)"
   - El NIF del cliente es 75236270G
   - La dirección del cliente es CRTRA DE ALICUN 172, ROQUETAS DE MAR, 04740, ALMERÍA
   - IMPORTANTE: No confundas los datos del cliente con los del proveedor

3. PRODUCTOS Y DESCUENTOS:
   - Presta especial atención a los descuentos aplicados por línea y globales
   - Extrae correctamente los códigos de producto y referencias
   - Verifica que las cantidades y precios son correctos

4. IMPUESTOS:
   - Separa el IVA del Recargo de Equivalencia si aplica
   - Verifica que los impuestos calculados coinciden con los totales

5. DOCUMENTOS:
   - Distingue claramente entre número de factura, número de albarán y número de pedido
   - Asegúrate de que las fechas están en formato YYYY-MM-DD

Devuelve un objeto JSON completo y corregido con los datos de la factura ABRILA.""",
        }
        
        # Añadir prompt para MIELECTRO
        provider_user_prompts['MIELECTRO'] = f"""Analiza el siguiente texto extraído por OCR de una factura MIELECTRO y extrae todos los datos relevantes.
        
TEXTO OCR:
{ocr_text}

DATOS INICIALES (pueden contener errores u omisiones):
{initial_data}

INSTRUCCIONES ESPECÍFICAS PARA MIELECTRO:
1. PROVEEDOR:
   - Verifica el CIF correcto de MIELECTRO
   - Extrae la dirección completa del proveedor

2. CLIENTE:
   - El cliente SIEMPRE es "EL PELOTAZO" con nombre completo "BONACHERA PLAZA, ANTONIO (04744)"
   - El NIF del cliente es 75236270G
   - La dirección del cliente es CRTRA DE ALICUN 172, ROQUETAS DE MAR, 04740, ALMERÍA
   - IMPORTANTE: No confundas los datos del cliente con los del proveedor

3. PRODUCTOS:
   - Extrae correctamente los códigos de producto y referencias
   - Verifica que las cantidades y precios son correctos
   - Presta atención a los modelos y marcas de los electrodomésticos

4. IMPUESTOS:
   - Separa el IVA del Recargo de Equivalencia si aplica
   - Verifica que los impuestos calculados coinciden con los totales

5. DOCUMENTOS:
   - Distingue claramente entre número de factura, número de albarán y número de pedido
   - Asegúrate de que las fechas están en formato YYYY-MM-DD

Devuelve un objeto JSON completo y corregido con los datos de la factura MIELECTRO."""
        
        # Devolver el prompt específico o el base si no hay específico
        return provider_user_prompts.get(provider_code, base_prompt)

# Instancia global de la clase
provider_prompts = ProviderPrompts()
