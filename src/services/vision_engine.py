import cv2
import numpy as np
from PIL import Image

class VisionService:
    @staticmethod
    def analizar_integridad(uploaded_file):
        if uploaded_file is None: return "SÍN FOTO"
        try:
            img = Image.open(uploaded_file).convert('L')
            img_np = np.array(img)
            media = np.mean(img_np)
            
            # RECALIBRACIÓN: Subimos el umbral de 30 a 60 para detectar oscuridad real
            if media < 60: 
                return "CRÍTICA: Oscuridad excesiva (Baja relación señal/ruido)"
            if media > 225: 
                return "CRÍTICA: Imagen quemada (Saturación)"
                
            return "ESTADO ÓPTIMO"
        except Exception as e:
            # Aplicamos el "Blindaje" solicitado: retornar UNKNOWN en lugar de crashear
            return f"UNKNOWN: {str(e)}"