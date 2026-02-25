import unittest
import sys
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Ajuste de ruta
sys.path.append(os.getcwd())

from src.services.predictive_service import PredictiveService
from src.models.concretos import MotorInduccion
from src.logical.estrategias import DesgasteLineal

class TestPredictiveService(unittest.TestCase):
    def setUp(self):
        """Preparamos el servicio y un equipo de prueba"""
        self.service = PredictiveService()
        self.estrategia = DesgasteLineal()
        # Creamos un motor comprado hace 2 años (730 días)
        fecha_hace_2_anos = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        self.motor = MotorInduccion("TEST-01", "Motor IA", fecha_hace_2_anos, "10HP", "220V", 1800, self.estrategia)

    def test_generar_prediccion_logica(self):
        """Verifica que la fecha estimada sea en el futuro y el gráfico exista"""
        fecha_falla, fig = self.service.generar_prediccion(self.motor)
        
        # Convertimos la fecha calculada para comparar
        fecha_dt = datetime.strptime(fecha_falla, "%Y-%m-%d")
        
        # 1. El modelo debe predecir una falla DESPUÉS de hoy
        self.assertGreater(fecha_dt, datetime.now(), "La IA predijo una falla en el pasado")
        
        # 2. El objeto retornado debe ser un gráfico de Matplotlib
        self.assertIsInstance(fig, plt.Figure, "No se generó el objeto de gráfico correctamente")

    def test_prediccion_con_fecha_invalida(self):
        """Verifica que el sistema rechace correctamente fechas mal formateadas lanzando ValueError"""
        self.motor.fecha_compra = "fecha-corrupta"
        
        with self.assertRaises(ValueError):
            self.service.generar_prediccion(self.motor)

if __name__ == '__main__':
    unittest.main()