#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from api.services.mistral_ocr_service import get_mistral_ocr_service
    print("✓ Importación exitosa")
    
    service = get_mistral_ocr_service()
    print("✓ Servicio Mistral OCR inicializado correctamente")
    print(f"✓ Modelo configurado: {service.model}")
    print(f"✓ API Key configurada: {'Sí' if service.api_key else 'No'}")
    print(f"✓ Formatos soportados: {service.get_supported_formats()}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()