import unittest
import sys
import os
import json

# Ajuste de ruta
sys.path.append(os.getcwd())

from src.models.concretos import Osciloscopio, Multimetro, MotorInduccion
from src.utils.enums import EstadoEquipo
from src.interfaces.mixins import AnalizadorPredictivo

class TestArquitecturaSistema(unittest.TestCase):

    def test_flota_y_obsolescencia(self):
        """[1] Valida constructores y cálculo de obsolescencia"""
        osc = Osciloscopio("OSC-LAB-01", "Tektronix TBS", "2023-01-15", "100MHz")
        motor = MotorInduccion("MOT-IND-X5", "Siemens 1LE1", "2020-05-20", "15HP", "440V", 3600)
        
        # En lugar de solo print, usamos assert para que Python verifique
        self.assertGreaterEqual(osc.calcular_obsolescencia(), 0)
        self.assertIn("Identificado activo", osc.generar_qr())

    def test_cambio_estado_motor(self):
        """[3] Valida gestión de incidencias"""
        motor = MotorInduccion("MOT-IND-X5", "Siemens 1LE1", "2020-05-20", "15HP", "440V", 3600)
        motor.registrar_incidencia(descripcion="Vibración excesiva", reportado_por="Ing. Electrico")
        
        # Esto es lo que busca unittest:
        self.assertEqual(motor.estado, EstadoEquipo.REPORTADO_CON_FALLA)

    def test_serializacion_json(self):
        """[4] Valida que el diccionario para Supabase sea correcto"""
        motor = MotorInduccion("MOT-IND-X5", "Siemens 1LE1", "2020-05-20", "15HP", "440V", 3600)
        datos = motor.to_dict()
        self.assertIsInstance(datos, dict)
        self.assertEqual(datos['id_equipo'], "MOT-IND-X5")

if __name__ == '__main__':
    unittest.main()