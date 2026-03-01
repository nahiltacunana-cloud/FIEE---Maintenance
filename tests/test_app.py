import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ajuste de ruta para encontrar el código fuente
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importamos las clases a probar
from app import ServicioAutenticacion

class TestServicioAutenticacion(unittest.TestCase):

    @patch('streamlit.secrets')
    @patch('app.create_client')
    def setUp(self, mock_create_client, mock_secrets):
        """Configuración inicial para cada test simulando Supabase."""
        # Simulamos los secretos de Streamlit
        mock_secrets.__getitem__.side_effect = lambda key: "test_value"
        
        # Simulamos el cliente de Supabase y su auth
        self.mock_supabase = MagicMock()
        mock_create_client.return_value = self.mock_supabase
        
        # Instanciamos el servicio (usará los mocks)
        self.auth_service = ServicioAutenticacion()

    def test_cerrar_sesion_limpia_estado(self):
        """Verifica que al cerrar sesión se limpien las variables de Streamlit."""
        with patch('streamlit.session_state', {}) as mock_session:
            # Simulamos datos previos
            mock_session["autenticado"] = True
            mock_session["usuario_actual"] = "test@uni.pe"
            
            self.auth_service.cerrar_sesion()
            
            # Comprobamos que se llamó a sign_out de Supabase
            self.mock_supabase.auth.sign_out.assert_called_once()
            
            # Comprobamos que el estado interno se reseteó
            self.assertFalse(mock_session["autenticado"])
            self.assertIsNone(mock_session["usuario_actual"])

    def test_esta_autenticado_retorna_false_por_defecto(self):
        """Verifica que si no hay sesión, retorne False."""
        with patch('streamlit.session_state', {}) as mock_session:
            resultado = self.auth_service.esta_autenticado()
            self.assertFalse(resultado)

    @patch('streamlit.error')
    def test_autenticar_error_maneja_excepcion(self, mock_st_error):
        """Verifica que si Supabase falla, el sistema no colapse y muestre error."""
        # Forzamos un error en la llamada a sign_in
        self.mock_supabase.auth.sign_in_with_password.side_effect = Exception("Error de red")
        
        resultado = self.auth_service.autenticar("correo@uni.pe", "123456")
        
        self.assertFalse(resultado)
        mock_st_error.assert_called()

if __name__ == '__main__':
    unittest.main()