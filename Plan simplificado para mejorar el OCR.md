Plan simplificado para mejorar el OCR local con Tesseract
Entiendo perfectamente. Vamos a enfocarnos en mejorar Tesseract paso a paso, manteniendo el flujo actual con Mistral como respaldo, y haciendo solo las mejoras más necesarias para obtener resultados aceptables que requieran mínima intervención manual.

Plan de acción inmediato (3-5 días)
Día 1: Actualizar Tesseract y configuración básica
Actualizar Tesseract a la última versión:
bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
sudo apt-get install -y tesseract-ocr-spa
Verificar la instalación:
bash
tesseract --version
tesseract --list-langs
Modificar la configuración básica en 
api/routes/ocr.py
:
Cambiar la configuración de Tesseract para usar el modo LSTM:
python
# Cambiar esta línea
text += pytesseract.image_to_string(processed_img, lang='spa', config='--dpi 300 --psm 6')

# Por esta configuración mejorada
text += pytesseract.image_to_string(processed_img, lang='spa', config='--oem 1 --psm 6 --dpi 300')
Día 2: Mejorar el preprocesamiento de imágenes
Mejorar la función de preprocesamiento en 
api/routes/ocr.py
:
python
def preprocess_image(image):
    # Convertir a array numpy si es necesario
    if not isinstance(image, np.ndarray):
        image = np.array(image)
    
    # Convertir a escala de grises
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    # Aplicar desenfoque gaussiano para reducir ruido
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Aplicar umbralización adaptativa (mejor que umbral fijo)
    binary = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Eliminar ruido con operaciones morfológicas
    kernel = np.ones((1, 1), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    return binary
Probar con algunas facturas para verificar la mejora en la calidad del OCR.
Día 3: Corrección de inclinación y mejoras específicas para facturas
Añadir corrección de inclinación (deskew):
python
def deskew_image(image):
    # Detectar bordes
    edges = cv2.Canny(image, 50, 150, apertureSize=3)
    
    # Detectar líneas
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    
    if lines is not None and len(lines) > 0:
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:  # Evitar división por cero
                angle = np.arctan((y2 - y1) / (x2 - x1)) * 180 / np.pi
                angles.append(angle)
        
        if angles:
            # Calcular ángulo promedio
            median_angle = np.median(angles)
            
            # Rotar imagen si el ángulo es significativo
            if abs(median_angle) > 0.5:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), 
                                        flags=cv2.INTER_CUBIC, 
                                        borderMode=cv2.BORDER_REPLICATE)
                return rotated
    
    return image
Integrar en el flujo de procesamiento:
python
def extract_text_from_pdf(pdf_path):
    # Convertir PDF a imágenes
    images = convert_from_path(pdf_path)
    
    # Preprocess images and extract text
    text = ""
    for img in images:
        # Aplicar preprocesamiento mejorado
        gray = preprocess_image(img)
        
        # Aplicar corrección de inclinación
        deskewed = deskew_image(gray)
        
        # OCR con configuración mejorada
        text += pytesseract.image_to_string(deskewed, lang='spa', 
                                          config='--oem 1 --psm 6 --dpi 300')
    
    return text
Día 4: Mejorar la extracción de datos específicos
Mejorar las expresiones regulares para códigos de producto NEVIR:
python
# Buscar códigos de producto NEVIR
nevir_codes = re.finditer(r'(?:NVR|N\s?V\s?R)[\s\-]+([A-Z0-9]{5,7})', text)
for match in nevir_codes:
    code = match.group(0).replace(' ', '')
    # Normalizar formato
    normalized_code = re.sub(r'(NVR|N\s?V\s?R)[\s\-]+', 'NVR-', code)
    # Añadir a líneas de factura
    # ...
Mejorar la detección de tablas para líneas de factura:
python
# Detectar líneas de producto en formato tabular
# Patrón más flexible para capturar variaciones en el formato
lines_pattern = r'([A-Z0-9\-]+)\s+(\d+)\s+([A-ZÁÉÍÓÚÑáéíóúñ\s\.\,\-]+)\s+(\d+[\.\,]\d+)'
lines_matches = re.finditer(lines_pattern, text)
Día 5: Pruebas y ajustes finales
Crear un script de prueba para comparar resultados:
python
def test_ocr_improvements():
    # Cargar facturas de prueba
    test_files = ["NEVIR - FacturaF2402846.pdf", "ABRILA - factura_32506198.pdf"]
    
    results = {}
    for file in test_files:
        # Procesar con configuración antigua
        old_text = process_with_old_config(file)
        
        # Procesar con configuración nueva
        new_text = process_with_new_config(file)
        
        # Guardar resultados para comparación
        results[file] = {
            "old": old_text,
            "new": new_text
        }
    
    return results
Ajustar parámetros según los resultados de las pruebas.
Integración con el flujo existente
Mantener compatibilidad con el código actual:
Añadir un parámetro para seleccionar el nivel de procesamiento
Mantener el flujo con Mistral como respaldo
Actualizar el endpoint /invoice para usar el OCR mejorado:
python
@router.post("/invoice")
async def process_invoice(
    file: UploadFile = File(...),
    ocr_method: str = Form("auto")  # "auto", "tesseract", "pdfxchange", "mistral"
):
    # Lógica existente...
    
    # Usar OCR mejorado si se selecciona tesseract
    if ocr_method == "tesseract" or ocr_method == "auto":
        # Usar el OCR mejorado
        text = extract_text_from_pdf_improved(temp_file_path)
    # Resto del código...
Próximos pasos después del OCR
Una vez mejorado el OCR, seguiremos con:

Mejorar la página de proveedores para crear/actualizar proveedores desde facturas
Optimizar la detección de líneas de productos para minimizar edición manual
Mejorar las páginas CRUD para productos y categorías
Implementar la subida de Excel con procesamiento por IA
Conclusión
Este plan simplificado se enfoca en las mejoras más importantes y rápidas para Tesseract, manteniendo el flujo actual y permitiendo una transición gradual. Cada paso es independiente y podemos evaluar los resultados antes de continuar con el siguiente.

