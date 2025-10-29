import pytesseract
from PIL import Image
import cv2
import numpy as np
import io

class ImageProcessor:
    def __init__(self):
        # Configurar caminho do tesseract se necessário
        # pytesseract.pytesseract.tesseract_cmd = r'<path_to_tesseract>'
        pass
    
    def preprocess_image(self, image):
        """Melhora a imagem para OCR"""
        # Converter para array numpy
        img = np.array(image)
        
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # Aplicar filtro para melhorar qualidade
        processed = cv2.medianBlur(gray, 3)
        
        return Image.fromarray(processed)
    
    def extract_text_from_image(self, image):
        """Extrai texto da imagem usando OCR"""
        try:
            # Pré-processar imagem
            processed_image = self.preprocess_image(image)
            
            # Configurar OCR para português
            custom_config = r'--oem 3 --psm 6 -l por'
            
            # Extrair texto
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            return text.strip()
        
        except Exception as e:
            print(f"Erro no processamento de imagem: {e}")
            return ""
