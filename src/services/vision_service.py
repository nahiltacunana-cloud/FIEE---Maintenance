import cv2
import numpy as np

class VisionService:
    def analizar_quemadura(self, image_path_or_buffer):
        """
        Versión V2.2: Con bandera booleana para evitar confusiones en el Dashboard.
        """
        try:
            # 1. Cargar la imagen (Tu lógica original)
            if hasattr(image_path_or_buffer, 'read'): 
                # Resetear el puntero del archivo por si acaso se leyó antes
                image_path_or_buffer.seek(0)
                file_bytes = np.asarray(bytearray(image_path_or_buffer.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, 1)
            else:
                img = cv2.imread(image_path_or_buffer)

            if img is None:
                return {"alerta": "ERROR", "diagnostico": "Imagen no legible", "es_critico": False}

            # 2. Procesamiento (Tu lógica original)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Umbral ajustado a 45 como pediste
            umbral_oscuridad = 45 
            
            pixeles_totales = gray.size
            pixeles_oscuros = np.count_nonzero(gray < umbral_oscuridad)
            
            porcentaje_quemado = (pixeles_oscuros / pixeles_totales) * 100

            # 3. Decisión (AQUÍ ESTÁ LA CLAVE)
            if porcentaje_quemado > 25.0:
                return {
                    "alerta": "🚨 ALERTA CRÍTICA",
                    "diagnostico": f"Zona CARBONIZADA detectada ({porcentaje_quemado:.1f}%).",
                    "es_critico": True  # <--- ESTO ES LO QUE NECESITAMOS (SEMÁFORO ROJO)
                }
            else:
                return {
                    "alerta": "✅ ESTADO NORMAL",
                    "diagnostico": f"Superficie limpia ({porcentaje_quemado:.1f}% oscuridad).",
                    "es_critico": False # <--- ESTO ES LO QUE NECESITAMOS (SEMÁFORO VERDE)
                }

        except Exception as e:
            return {"alerta": "ERROR", "diagnostico": f"Fallo IA: {str(e)}", "es_critico": False}
