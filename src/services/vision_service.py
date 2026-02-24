import os
import io
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

class VisionService:
    """
    Servicio de Visión Computacional basado en Transformers para el 
    diagnóstico automatizado de daños en componentes físicos.
    """
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
        """Localiza dinámicamente el directorio del modelo pre-entrenado."""
        directorio_actual = os.path.abspath(os.path.dirname(__file__))
        
        for _ in range(4):
            posible_ruta = os.path.join(directorio_actual, "vision_ai", "modelo")
            if os.path.exists(posible_ruta):
                return posible_ruta
            directorio_actual = os.path.dirname(directorio_actual)
            
        return os.path.join(os.getcwd(), "vision_ai", "modelo")

    def __cargar_modelo(self):
        """Carga los pesos y el procesador del modelo ViT (Vision Transformer)."""
        print(f"🔍 Ruta detectada: {self.__model_path}")
        
        if os.path.exists(self.__model_path):
            try:
                self.processor = AutoImageProcessor.from_pretrained(self.__model_path)
                self.model = AutoModelForImageClassification.from_pretrained(self.__model_path)
                self.modelo_cargado = True
            except Exception as e:
                print(f"Log: Error en carga de tensores IA: {e}")
        else:
            print(f"Log: Repositorio de modelos no localizado en {self.__model_path}")

    def analizar_estado(self, datos_imagen):
        """
        Realiza la inferencia sobre una imagen para detectar anomalías físicas.
        :param datos_imagen: Archivo de imagen o buffer de bytes.
        :return: dict con el diagnóstico y nivel de confianza.
        """
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
    # Mantenemos este nombre por si las vistas aún lo requieren
    def analizar_quemadura(self, datos_imagen):
        return self.analizar_estado(datos_imagen)

    def __preprocesar(self, data):
        """Prepara la imagen para el formato de entrada del Transformer."""
        if hasattr(data, 'read'):
            data.seek(0)
            return Image.open(io.BytesIO(data.read())).convert("RGB")
        return Image.open(data).convert("RGB")

    def __procesar_diagnostico(self, etiqueta: str, confianza: float):
        """Lógica de decisión basada en el mapeo de etiquetas del modelo."""
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
