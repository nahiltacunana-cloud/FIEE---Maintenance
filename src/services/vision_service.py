import os
import io
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

class VisionService:
    """
    Servicio de Visión Computacional conectado a Hugging Face en la nube.
    """
    def __init__(self):
        """Constructor: Inicializa el cerebro de visión artificial."""
        # Repositorio de Hugging Face
        self.__model_path = "NahilSisai/vit-mantenimiento-fiee" 
        
        self.processor = None
        self.model = None
        self.modelo_cargado = False
        
        print("\n" + "="*50)
        print(f"🚀 [VISION SERVICE] Conectando con IA en la nube...")
        self.__cargar_modelo()
        print("="*50 + "\n")

    def __cargar_modelo(self):
        """Descarga/Carga los pesos y el procesador desde Hugging Face."""
        print(f"🔍 Repositorio objetivo: {self.__model_path}")
        
        try:
            self.processor = AutoImageProcessor.from_pretrained(self.__model_path)
            self.model = AutoModelForImageClassification.from_pretrained(self.__model_path)
            self.modelo_cargado = True
            print("Modelo cargado exitosamente desde la nube.")
        except Exception as e:
            print(f"Error al conectar con Hugging Face: {e}")

    def analizar_estado(self, datos_imagen):
        """Realiza la inferencia sobre una imagen."""
        if not self.modelo_cargado:
            return self.__respuesta_error("IA no disponible. Verifique conexión a internet.")
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

    def analizar_quemadura(self, datos_imagen):
        return self.analizar_estado(datos_imagen)

    def __preprocesar(self, data):
        if hasattr(data, 'read'):
            data.seek(0)
            return Image.open(io.BytesIO(data.read())).convert("RGB")
        return Image.open(data).convert("RGB")

    def __procesar_diagnostico(self, etiqueta: str, confianza: float):
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
