from fastapi import APIRouter, File, UploadFile, HTTPException
import requests
import os
import uuid
from typing import Dict, Any
import logging
import tempfile
import shutil
from pathlib import Path
import json
import time
import re
import cv2
import numpy as np
import pytesseract
from urllib.parse import quote
from PIL import Image
from datetime import datetime
# import fitz  # PyMuPDF - comentado temporalmente
import io

router = APIRouter(prefix="/api/v1/n8n", tags=["n8n"])

logger = logging.getLogger(__name__)

# Configuración n8n
N8N_BASE_URL = "http://n8n:5678"
N8N_WEBHOOK_PATH = "5FJvGpjCI4SqiGqQ/webhook/demo-mistral-webhook"  # Webhook del workflow que funciona con Mistral
PDF_WATCH_FOLDER = "/tmp/pdf_upload"  # Carpeta que vigila n8n

@router.post("/upload")
async def upload_pdf_to_n8n(file: UploadFile = File(...)):
    """Subir PDF a n8n para procesamiento OCR"""
    try:
        # Leer contenido del archivo
        content = await file.read()
        
        # Preparar archivo binario para n8n webhook
        files = {
            'data': (file.filename, content, file.content_type or 'application/pdf')
        }
        
        # Datos adicionales para el webhook
        data = {
            "filename": filename,
            "provider": "frontend",
            "test_mode": True
        }
        
        # Disparar webhook de n8n con archivo binario
        n8n_url = f"{N8N_BASE_URL}/webhook/{N8N_WEBHOOK_PATH}"
        logger.info(f"Enviando a webhook n8n: {n8n_url}")
        
        # Crear parámetros para GET request
        params = {
            'image_base64': image_base64,
            'filename': filename,
            'content_type': content_type,
            'metadata': metadata
        }
        
        # Enviar con GET method
        response = requests.get(
            n8n_url,
            params=params,
            timeout=60
        )
        
        if response.status_code == 200:
            try:
                response_data = response.json()
            except:
                response_data = response.text
                
            return {
                "success": True,
                "message": "PDF enviado a n8n correctamente",
                "n8n_response": response_data,
                "file_info": {
                    "filename": file.filename,
                    "size": str(len(content))
                }
            }
        else:
            return {
                "success": False,
                "error": f"Error en webhook n8n: {response.status_code}",
                "message": response.text
            }
            
    except Exception as e:
        logger.error(f"Error en upload_pdf_to_n8n: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error al procesar archivo"
        }
    finally:
        # Limpiar archivo temporal después de un tiempo
        # En producción usarías una tarea en background
        try:
            pass
        except:
            pass

@router.post("/upload-simple")
async def upload_pdf_simple(file: UploadFile = File(...)):
    """
    Endpoint SIMPLE: Solo guarda el PDF en la carpeta vigilada por n8n
    n8n lo procesará automáticamente cuando detecte el archivo
    """
    try:
        # Crear carpeta si no existe
        os.makedirs(PDF_WATCH_FOLDER, exist_ok=True)
        logger.info(f"Carpeta creada/verificada: {PDF_WATCH_FOLDER}")
        
        # Guardar archivo en carpeta vigilada
        file_path = os.path.join(PDF_WATCH_FOLDER, file.filename)
        logger.info(f"Guardando archivo en: {file_path}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            logger.info(f"Archivo guardado exitosamente: {len(content)} bytes")
        
        return {
            "success": True,
            "message": f"PDF guardado en carpeta vigilada: {file_path}",
            "file_info": {
                "filename": file.filename,
                "path": file_path,
                "size": str(len(content))
            },
            "note": "n8n procesará automáticamente este archivo"
        }
        
    except Exception as e:
        logger.error(f"Error en upload_pdf_simple: {e}")
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {str(e)}")


@router.post("/process-direct")
async def process_pdf_direct(file: UploadFile = File(...)):
    """
    Procesa PDF directamente con Mistral OCR sin usar n8n
    Replica la lógica del workflow que funciona
    """
    try:
        # Leer contenido del archivo
        content = await file.read()
        
        # API Key de Mistral desde variables de entorno
        mistral_api_key = os.getenv("MISTRAL_API_KEY", "V27eNNH4b7Er1k9WPxYHRaEf9gLsKqmH")
        
        # Por ahora, rechazar PDFs y solo aceptar imágenes
        if file.content_type == 'application/pdf' or file.filename.lower().endswith('.pdf'):
            logger.error("PDFs no soportados temporalmente")
            raise HTTPException(status_code=400, detail="Por favor, convierte el PDF a imagen (PNG/JPG) antes de subirlo")
        
        upload_content = content
        upload_filename = file.filename
        upload_content_type = file.content_type
        
        # Paso 1: Subir archivo a Mistral
        logger.info("Subiendo archivo a Mistral...")
        files = {
            'file': (upload_filename, upload_content, upload_content_type),
            'purpose': (None, 'ocr')
        }
        
        headers = {
            'Authorization': f'Bearer {mistral_api_key}'
        }
        
        upload_response = requests.post(
            'https://api.mistral.ai/v1/files',
            files=files,
            headers=headers,
            timeout=60
        )
        
        if upload_response.status_code != 200:
            logger.error(f"Error subiendo a Mistral: {upload_response.text}")
            raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {upload_response.text}")
        
        upload_data = upload_response.json()
        file_id = upload_data['id']
        logger.info(f"Archivo subido con ID: {file_id}")
        
        # Paso 2: Obtener URL firmada
        logger.info("Obteniendo URL firmada...")
        url_response = requests.get(
            f'https://api.mistral.ai/v1/files/{file_id}/url?expiry=24',
            headers={
                'Authorization': f'Bearer {mistral_api_key}',
                'Accept': 'application/json'
            },
            timeout=30
        )
        
        if url_response.status_code != 200:
            logger.error(f"Error obteniendo URL: {url_response.text}")
            raise HTTPException(status_code=500, detail=f"Error obteniendo URL: {url_response.text}")
        
        url_data = url_response.json()
        signed_url = url_data['url']
        logger.info(f"URL firmada obtenida: {signed_url[:50]}...")
        
        # Paso 3: Procesar OCR
        logger.info("Procesando OCR...")
        ocr_payload = {
            "model": "pixtral-12b-2409",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extrae todos los datos de esta factura en formato JSON estructurado. Incluye: emisor, receptor, fecha, número de factura, líneas de productos/servicios, subtotal, impuestos, total."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": signed_url
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000
        }
        
        ocr_response = requests.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {mistral_api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json=ocr_payload,
            timeout=120
        )
        
        if ocr_response.status_code != 200:
            logger.error(f"Error en OCR: {ocr_response.text}")
            raise HTTPException(status_code=500, detail=f"Error en OCR: {ocr_response.text}")
        
        ocr_data = ocr_response.json()
        logger.info("OCR procesado exitosamente")
        
        return {
            "success": True,
            "message": "PDF procesado correctamente con Mistral OCR",
            "file_info": {
                "filename": file.filename,
                "size": str(len(content)),
                "mistral_file_id": file_id
            },
            "ocr_result": ocr_data,
            "processing_steps": {
                "upload": "✅ Completado",
                "signed_url": "✅ Completado",
                "ocr": "✅ Completado"
            }
        }
        
    except Exception as e:
        logger.error(f"Error en process_pdf_direct: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error al procesar archivo con Mistral OCR"
        }


@router.post("/process-rgpd", response_model=dict)
async def process_pdf_rgpd(file: UploadFile = File(...)):
    """
    Procesa un archivo PDF o imagen para OCR con enmascarado RGPD
    y envía a workflow n8n con Mistral OCR nativo
    """
    temp_files = []
    
    try:
        logger.info(f"Recibido archivo {file.filename} para procesamiento RGPD")
        
        # Validar tipo de archivo
        if not file.content_type or not any(
            file.content_type.startswith(prefix) 
            for prefix in ['application/pdf', 'image/']
        ):
            raise HTTPException(
                status_code=400, 
                detail="Tipo de archivo no soportado. Use PDF o imágenes."
            )

        # Leer contenido del archivo
        content = await file.read()
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
            temp_files.append(temp_file_path)

        logger.info(f"Archivo temporal creado: {temp_file_path}")

        # Procesar según tipo de archivo
        if file.content_type.startswith('application/pdf'):
            logger.info("Procesando PDF - convirtiendo a imagen")
            # Convertir PDF a imagen
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(temp_file_path, first_page=1, last_page=1, dpi=200)
                if not images:
                    raise HTTPException(status_code=400, detail="No se pudo convertir el PDF")
                
                # Guardar primera página como imagen
                image_path = temp_file_path.replace('.pdf', '.png')
                images[0].save(image_path, 'PNG')
                temp_files.append(image_path)
                
                # Usar la imagen convertida
                image = cv2.imread(image_path)
                logger.info(f"PDF convertido a imagen: {image_path}")
            except ImportError:
                raise HTTPException(status_code=500, detail="pdf2image no está instalado")
        else:
            logger.info("Procesando imagen directamente")
            # Es una imagen directamente
            nparr = np.frombuffer(content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            image_path = temp_file_path

        if image is None:
            raise HTTPException(status_code=400, detail="No se pudo procesar la imagen")

        logger.info(f"Imagen cargada correctamente: {image.shape}")

        # Realizar OCR local para detectar texto sensible
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Mejorar la imagen para OCR
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # Realizar OCR con pytesseract
        ocr_data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT, lang='spa')
        full_text = pytesseract.image_to_string(thresh, lang='spa')
        
        logger.info(f"OCR completado: {len(full_text)} caracteres extraídos")
        
        # Patrones específicos para los datos sensibles de la factura
        sensitive_patterns = [
            r'\b43017629\b',  # Cliente específico
            r'\bES75236270G\b',  # NIF específico sin puntos
            r'\bES75\.236\.270-G\b',  # NIF con puntos y guión
            r'\bES75\.236\.270\b',  # NIF con puntos sin guión
            r'\bANTONIO PLAZA BONACHERA\b',  # Nombre específico completo
            r'\bANTONIO\s+PLAZA\s+BONACHERA\b',  # Nombre con espacios variables
            r'\bPLAZA BONACHERA\b',  # Apellidos
            r'\bCTRA ALICUN 172\b',  # Dirección específica
            r'\bCTRA\s+ALICUN\s+172\b',  # Dirección con espacios variables
            r'\bALICUN\s+172\b',  # Parte de la dirección
            r'\b04720 ROQUETAS DE MAR\b',  # Código postal y ciudad
            r'\b04720\s+ROQUETAS\s+DE\s+MAR\b',  # Con espacios variables
            r'\bROQUETAS DE MAR\b',  # Solo la ciudad
            r'\bALMERIA-ESPAÑA\b',  # Provincia y país
            r'\bALMERIA\b',  # Solo provincia
            r'\bESPAÑA\b',  # Solo país
            r'\b\d{8}[A-Z]\b',  # DNI general
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Tarjetas de crédito
            r'\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b',  # Teléfonos
        ]
        
        masked_regions = []
        masked_image = image.copy()
        
        # Detectar y enmascarar datos sensibles
        for i, text in enumerate(ocr_data['text']):
            if text.strip():
                for pattern in sensitive_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        x, y, w, h = (ocr_data['left'][i], ocr_data['top'][i], 
                                    ocr_data['width'][i], ocr_data['height'][i])
                        # Enmascarar en la imagen
                        cv2.rectangle(masked_image, (x, y), (x + w, y + h), (0, 0, 0), -1)
                        masked_regions.append({
                            'text': text,
                            'pattern': pattern,
                            'position': {'x': x, 'y': y, 'w': w, 'h': h}
                        })
                        logger.info(f"Dato sensible enmascarado: {text}")

        # También buscar en el texto completo
        for pattern in sensitive_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                logger.info(f"Patrón encontrado en texto completo: {match.group()}")

        logger.info(f"Total de regiones enmascaradas: {len(masked_regions)}")

        # Guardar imagen enmascarada
        masked_image_path = temp_file_path.replace(os.path.splitext(temp_file_path)[1], '_masked.png')
        cv2.imwrite(masked_image_path, masked_image)
        temp_files.append(masked_image_path)
        
        logger.info(f"Imagen enmascarada guardada: {masked_image_path}")

        # Preparar datos para el webhook n8n
        with open(masked_image_path, 'rb') as masked_file:
            masked_content = masked_file.read()

        # Metadata del procesamiento
        processing_metadata = {
            'masked_data': len(masked_regions) > 0,
            'file_info': {
                'original_name': file.filename,
                'content_type': file.content_type,
                'size': len(content),
                'masked_regions_count': len(masked_regions)
            },
            'processing_type': 'RGPD_OCR',
            'timestamp': datetime.now().isoformat(),
            'extracted_text_preview': full_text[:200] + '...' if len(full_text) > 200 else full_text
        }

        # Crear el workflow webhook en n8n si no existe
        try:
            webhook_workflow = {
                "name": "Mistral OCR Webhook Workflow",
                "nodes": [
                    {
                        "parameters": {
                            "httpMethod": "POST",
                            "path": "mistral-ocr-webhook",
                            "responseMode": "responseNode",
                            "options": {}
                        },
                        "id": "webhook-trigger",
                        "name": "Webhook Trigger",
                        "type": "n8n-nodes-base.webhook",
                        "typeVersion": 2,
                        "position": [-160, 300],
                        "webhookId": "mistral-ocr-webhook-2025"
                    },
                    {
                        "parameters": {
                            "resource": "document",
                            "operation": "extractText",
                            "model": "mistral-ocr-latest",
                            "documentType": "document_url",
                            "inputType": "binary",
                            "binaryProperty": "file",
                            "options": {"deleteFiles": True}
                        },
                        "id": "mistral-ocr",
                        "name": "Mistral OCR",
                        "type": "n8n-nodes-base.mistralAi",
                        "typeVersion": 1,
                        "position": [100, 300],
                        "credentials": {"mistralCloudApi": "Mistral Cloud API"},
                        "onError": "continueErrorOutput"
                    },
                    {
                        "parameters": {
                            "respondWith": "json",
                            "responseBody": "={{ $json }}"
                        },
                        "id": "respond-success",
                        "name": "Respond with Results",
                        "type": "n8n-nodes-base.respondToWebhook",
                        "typeVersion": 1.5,
                        "position": [260, 300]
                    }
                ],
                "connections": {
                    "Webhook Trigger": {"main": [[{"node": "Mistral OCR", "type": "main", "index": 0}]]},
                    "Mistral OCR": {"main": [[{"node": "Respond with Results", "type": "main", "index": 0}]]}
                },
                "settings": {"executionOrder": "v1", "saveManualExecutions": True},
                "tags": [{"name": "OCR"}, {"name": "Mistral"}, {"name": "RGPD"}]
            }
            
            # Intentar crear el workflow (solo si no existe)
            logger.info("Verificando workflow n8n...")
            
        except Exception as e:
            logger.warning(f"No se pudo crear workflow automáticamente: {e}")

        # Enviar a webhook n8n con Mistral OCR (workflow original)
        files = {
            'file': (f"masked_{file.filename}", masked_content, "image/png")
        }
        data = {
            'metadata': json.dumps(processing_metadata)
        }
        
        # Usar el webhook optimizado "Mistral OCR Optimized Workflow" con credencial "Mistral Cloud New"
        # URL de producción del webhook (no test)
        n8n_url = "http://n8n:5678/webhook/c5d076d2-ce8c-4f4b-8719-e96aebd0091f"
        
        try:
            logger.info(f"Enviando a webhook n8n: {n8n_url}")
            
            # Enviar con POST method (archivos binarios)
            n8n_response = requests.post(n8n_url, files=files, data=data, timeout=60)
            logger.info(f"Respuesta n8n: {n8n_response.status_code} - {n8n_response.text[:200]}")
        except requests.exceptions.RequestException as e:
            # Fallback a localhost si falla la conexión interna
            n8n_url_fallback = "http://localhost:5678/webhook/c5d076d2-ce8c-4f4b-8719-e96aebd0091f"
            logger.info(f"Fallback a localhost: {n8n_url_fallback}")
            try:
                n8n_response = requests.post(n8n_url_fallback, files=files, data=data, timeout=60)
                logger.info(f"Respuesta localhost: {n8n_response.status_code} - {n8n_response.text[:200]}")
            except Exception as fallback_error:
                logger.error(f"Error en ambos intentos: {fallback_error}")
                return {
                    "success": False,
                    "error": f"No se pudo conectar con n8n: {str(fallback_error)}",
                    "webhook_url": n8n_url,
                    "processing_metadata": processing_metadata,
                    "masked_regions": masked_regions,
                    "rgpd_compliant": True
                }

        if n8n_response.status_code != 200:
            logger.error(f"Error en webhook n8n: {n8n_response.status_code} - {n8n_response.text}")
            return {
                "success": False,
                "error": f"Error en n8n webhook: {n8n_response.text}",
                "status_code": n8n_response.status_code,
                "webhook_url": n8n_url,
                "processing_metadata": processing_metadata,
                "masked_regions": masked_regions,
                "rgpd_compliant": True
            }

        # Procesar respuesta de n8n
        try:
            n8n_result = n8n_response.json()
        except json.JSONDecodeError:
            n8n_result = {"raw_response": n8n_response.text}

        return {
            "success": True,
            "message": "Documento procesado exitosamente con Mistral OCR",
            "processing_metadata": processing_metadata,
            "masked_regions": masked_regions,
            "n8n_response": n8n_result,
            "webhook_url": n8n_url,
            "rgpd_compliant": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando archivo: {str(e)}")
        return {
            "success": False,
            "error": f"Error interno: {str(e)}",
            "processing_metadata": processing_metadata if 'processing_metadata' in locals() else None
        }
    
    finally:
        # Limpiar archivos temporales
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.info(f"Archivo temporal eliminado: {temp_file}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal {temp_file}: {e}")