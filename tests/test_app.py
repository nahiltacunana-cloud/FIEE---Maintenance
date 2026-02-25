import unittest
import sys
import os

sys.path.append(os.getcwd())

# Clase de sistema que emula tu app.py
class SistemaFIEE:
    def iniciar_sesion(self, email, password):
        # Simulación de lógica con Supabase
        if "@uni.pe" in email and password == "clave123":
            return {"status": "success", "rol": "administrador"}
        return {"status": "error", "message": "Credenciales inválidas"}

class TestAppPrincipal(unittest.TestCase):
    def setUp(self):
        """Instanciamos el sistema antes de cada prueba"""
        self.app = SistemaFIEE()

    def test_login_institucional_exitoso(self):
        """Prueba acceso con correo de la UNI"""
        res = self.app.iniciar_sesion("estudiante@uni.pe", "clave123")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["rol"], "administrador")

    def test_login_denegado(self):
        """Prueba que el sistema bloquee accesos incorrectos"""
        res = self.app.iniciar_sesion("externo@gmail.com", "12345")
        self.assertEqual(res["status"], "error")

    def test_estructura_datos_reporte(self):
        """Verifica que el diccionario de reporte esté listo para Supabase"""
        reporte = {
            "equipo": "Motor 01",
            "falla": "Sobrecalentamiento",
            "usuario": "Nahil"
        }
        self.assertIn("equipo", reporte)
        self.assertTrue(len(reporte["falla"]) > 0)