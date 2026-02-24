import os
import io
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

class VisionService:
    def __init__(self):
        """Constructor: Inicializa el cerebro de visión artificial."""
        self.__model_path = self.__obtener_ruta_modelo()
        self.processor = None
        self.model = None
        self.modelo_cargado = False
        
        print("\n" + "="*50)
        print(f"🚀 [VISION SERVICE] Iniciando carga de IA...")
        self.__cargar_modelo()
        print("="*50 + "\n")

    def __obtener_ruta_modelo(self) -> str:
        """
        RASTREADOR INDESTRUCTIBLE: Escanea las carpetas hacia arriba 
        hasta encontrar 'vision_ai/modelo'.
        """
        # Empezamos donde está este archivo físico
        directorio_actual = os.path.abspath(os.path.dirname(__file__))
        
        # Subimos hasta 4 niveles buscando la carpeta
        for _ in range(4):
            posible_ruta = os.path.join(directorio_actual, "vision_ai", "modelo")
            if os.path.exists(posible_ruta):
                return posible_ruta
            # Si no está, subimos un nivel de carpeta
            directorio_actual = os.path.dirname(directorio_actual)
            
        # Si falla todo, asumimos una ruta por defecto
        return os.path.join(os.getcwd(), "vision_ai", "modelo")

    def __cargar_modelo(self):
        """Carga el modelo Vision Transformer de forma privada."""
        print(f"🔍 Ruta detectada: {self.__model_path}")
        
        if os.path.exists(self.__model_path):
            try:
                self.processor = AutoImageProcessor.from_pretrained(self.__model_path)
                self.model = AutoModelForImageClassification.from_pretrained(self.__model_path)
                self.modelo_cargado = True
                print(f"✅ ¡ÉXITO! Modelo de diagnóstico cargado y listo para usar.")
            except Exception as e:
                print(f"❌ ERROR CRÍTICO al leer los archivos de la IA: {e}")
        else:
            print(f"⚠️ ALERTA: La carpeta sigue sin existir en esa ruta.")

    def analizar_estado(self, datos_imagen):
        """Punto de entrada para analizar CUALQUIER tipo de daño."""
        if not self.modelo_cargado:
            return self.__respuesta_error("IA no disponible. Revise la terminal.")

        try:
            imagen = self.__preprocesar(datos_imagen)
            inputs = self.processor(images=imagen, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilidades = F.softmax(outputs.logits, dim=-1)[0]
                clase_idx = outputs.logits.argmax(-1).item()
            
            confianza = probabilidades[clase_idx].item() * 100
            etiqueta_raw = self.model.config.id2label[clase_idx]
            
            return self.__procesar_diagnostico(etiqueta_raw, confianza)
        except Exception as e:
            return self.__respuesta_error(str(e))

    # --- ALIAS DE COMPATIBILIDAD ---
    # Por si tu archivo inspeccion.py todavía usa este nombre viejo
    def analizar_quemadura(self, datos_imagen):
        return self.analizar_estado(datos_imagen)

    def __preprocesar(self, data):
        """Convierte la entrada en una imagen compatible."""
        if hasattr(data, 'read'):
            data.seek(0)
            return Image.open(io.BytesIO(data.read())).convert("RGB")
        return Image.open(data).convert("RGB")

    def __procesar_diagnostico(self, etiqueta: str, confianza: float):
        """Determina si hay anomalía basándose en palabras clave."""
        etiqueta_clean = etiqueta.lower()
        palabras_falla = ["quemado", "danado", "damaged", "burned", "roto", "broken", "falla"]
        
        es_anomalo = any(falla in etiqueta_clean for falla in palabras_falla)
        
        return {
            "diagnostico": "ANOMALÍA DETECTADA" if es_anomalo else "OK: DENTRO DE PARAMETROS NORMALES",
            "detalle": f"Clasificación: {etiqueta.title()} ({confianza:.1f}%)",
            "alerta": es_anomalo
        }

    def __respuesta_error(self, msj):
        return {"diagnostico": "ERROR", "detalle": msj, "alerta": False}
