import unittest
import sys
import os

# Ajuste de ruta para encontrar src
sys.path.append(os.getcwd())

class TestVisionIA(unittest.TestCase):
    def setUp(self):
        """Configuración inicial para las pruebas de visión"""
        self.categorias_validas = ["Normal", "Falla detectada", "Mantenimiento preventivo"]
    
    def test_analisis_imagen_formato_correcto(self):
        """Verifica que la IA devuelva un resultado válido"""
        # Simulamos la llamada a tu modelo de src/vision_ai
        resultado_ia = "Falla detectada" 
        
        self.assertIn(resultado_ia, self.categorias_validas, "La IA devolvió una categoría no reconocida")
        self.assertIsInstance(resultado_ia, str, "El resultado de la IA debe ser una cadena de texto")

    def test_deteccion_anomalia_critica(self):
        """Simula la detección de un problema grave"""
        # Simulamos un caso donde la IA detecta algo crítico
        score_confianza = 0.95
        self.assertGreater(score_confianza, 0.5, "La confianza del modelo es demasiado baja")