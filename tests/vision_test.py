import unittest
import sys
import os
from PIL import Image
import io

# Ajuste de ruta
sys.path.append(os.getcwd())

from src.services.vision_service import VisionService

class TestVisionIA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Cargamos el modelo una sola vez para todas las pruebas (ahorra tiempo)"""
        cls.servicio = VisionService()

    def test_carga_modelo_huggingface(self):
        """Verifica que el modelo se descargue y cargue correctamente de la nube"""
        self.assertTrue(self.servicio.modelo_cargado, "El modelo no pudo cargarse de Hugging Face")
        self.assertIsNotNone(self.servicio.model, "El objeto model de Torch es None")

    def test_analisis_imagen_dummy(self):
        """Prueba el flujo completo usando una imagen blanca creada en memoria"""
        # Creamos una imagen pequeña (100x100 blanco) para no cargar archivos
        img = Image.new('RGB', (100, 100), color='white')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)

        # Ejecutamos el análisis real
        resultado = self.servicio.analizar_estado(img_byte_arr)

        # Verificaciones del diccionario de respuesta
        self.assertIn("diagnostico", resultado)
        self.assertIn("alerta", resultado)
        self.assertIsInstance(resultado["alerta"], bool)
        self.assertNotEqual(resultado["diagnostico"], "ERROR", f"La IA falló: {resultado['detalle']}")

    def test_logica_diagnostico_limpio(self):
        """Verifica que el formateador de texto funcione correctamente"""
        # Probamos la función interna que decide si es anomalía o no
        res_ok = self.servicio._VisionService__procesar_diagnostico("Normal", 95.5)
        self.assertFalse(res_ok["alerta"])
        self.assertEqual(res_ok["diagnostico"], "OK: DENTRO DE PARAMETROS NORMALES")

        res_falla = self.servicio._VisionService__procesar_diagnostico("Motor_Burned", 88.0)
        self.assertTrue(res_falla["alerta"])
        self.assertEqual(res_falla["diagnostico"], "ANOMALÍA DETECTADA")

if __name__ == '__main__':
    unittest.main()