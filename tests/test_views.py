import unittest
import sys
import os
import pandas as pd
from unittest.mock import patch, MagicMock

# Ajuste de ruta para que Python encuentre la carpeta 'src'
sys.path.append(os.getcwd())

# Importamos la clase base y las vistas
from src.views.base_view import Vista
from src.views.dashboard import VistaDashboard, obtener_comentario_estado, convertir_objetos_a_df
from src.views.inspeccion import VistaInspeccion

# Importamos modelos para simular datos
from src.models.concretos import MotorInduccion
from src.logical.estrategias import DesgasteLineal
from src.utils.enums import EstadoEquipo

class TestViewsLogic(unittest.TestCase):
    """Pruebas de la lógica pura de las vistas (Arquitectura y Datos)"""

    def test_arquitectura_vistas_abstractas(self):
        """Verifica que las vistas respeten el contrato de la Clase Abstracta (Polimorfismo)"""
        self.assertTrue(issubclass(VistaDashboard, Vista), "El Dashboard no hereda de Vista")
        self.assertTrue(issubclass(VistaInspeccion, Vista), "La Inspección no hereda de Vista")
        
        self.assertTrue(hasattr(VistaDashboard, 'render'), "Falta el método render en Dashboard")
        self.assertTrue(hasattr(VistaInspeccion, 'render'), "Falta el método render en Inspeccion")

    def test_obtener_comentario_estado(self):
        """Prueba la lógica de alertas según el nivel de desgaste y estado"""
        # Caso 1: Equipo operativo con poco desgaste
        self.assertEqual(obtener_comentario_estado(0.15, "OPERATIVO"), "✅ Óptimas condiciones.")
        
        # Caso 2: Equipo con desgaste avanzado pero operativo
        self.assertEqual(obtener_comentario_estado(0.75, "OPERATIVO"), "🟠 Desgaste avanzado.")
        
        # Caso 3: El equipo falla sin importar el porcentaje matemático
        self.assertEqual(obtener_comentario_estado(0.05, "FALLA"), "⚠️ ATENCIÓN: Equipo fuera de servicio.")

    def test_convertir_objetos_a_df(self):
        """Verifica que el diccionario de laboratorios se transforme correctamente a Pandas DataFrame"""
        estrategia = DesgasteLineal()
        motor = MotorInduccion("TEST-DF-01", "Motor Data", "2023-01-01", "5HP", "220V", 1800, estrategia)
        motor.estado = EstadoEquipo.OPERATIVO
        
        diccionario_mock = {"Laboratorio Mock": [motor]}
        df = convertir_objetos_a_df(diccionario_mock, 0)
        
        # Validaciones de la tabla generada
        self.assertIsInstance(df, pd.DataFrame, "La función no devolvió un DataFrame de Pandas")
        self.assertFalse(df.empty, "El DataFrame llegó vacío")
        self.assertEqual(len(df), 1, "Debería haber exactamente 1 fila en la tabla")
        self.assertEqual(df.iloc[0]["ID"], "TEST-DF-01")


class TestVistasRender(unittest.TestCase):
    """Pruebas avanzadas del método render() simulando (mockeando) Streamlit"""

    @patch('src.views.dashboard.st')
    def test_dashboard_llama_a_render_correctamente(self, mock_st):
        """Prueba que el método render() del Dashboard se ejecute sin colapsar la UI"""
        # 1. Configuramos el "falso" st.session_state
        mock_st.session_state = MagicMock()
        mock_st.session_state.trigger = 0
        mock_st.session_state.db_laboratorios = {} 
        
        # 2. Configuramos los tabs falsos
        mock_st.tabs.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        
        # 3. EL TRUCO MAGISTRAL: Enseñar a st.columns a devolver columnas simuladas
        def side_effect_columns(spec):
            # spec puede ser un entero (ej. 2) o una lista (ej. [1, 1])
            num = spec if isinstance(spec, int) else len(spec)
            mocks = []
            for _ in range(num):
                col_mock = MagicMock()
                # Prevenimos que los selectbox y text_input dentro de las columnas devuelvan Mocks
                col_mock.selectbox.return_value = "Otro / Genérico"
                col_mock.text_input.return_value = ""
                mocks.append(col_mock)
            return mocks
            
        mock_st.columns.side_effect = side_effect_columns

        # 4. Instanciamos la vista
        vista_dash = VistaDashboard()
        vista_dash._cargar_y_agrupar_desde_supabase = MagicMock(return_value={})
        
        # 5. Ejecutamos el render
        vista_dash.render()
        
        # 6. Validamos
        mock_st.title.assert_called_with("📊 Dashboard de Activos FIEE")
        self.assertTrue(mock_st.tabs.called, "El método render nunca creó las pestañas")

    @patch('src.views.inspeccion.st')
    def test_inspeccion_llama_a_render_correctamente(self, mock_st):
        """Prueba que el método render() de Inspección configure la cabecera y el formulario"""
        mock_st.session_state = MagicMock()
        mock_st.session_state.db_laboratorios = {}
        mock_st.text_input.return_value = ""
        
        vista_insp = VistaInspeccion()
        vista_insp.render()
        
        mock_st.header.assert_called_with("📲 Inspección Técnica (Estudiante)")
        self.assertTrue(mock_st.text_input.called, "Falta el input para el escáner QR")

if __name__ == '__main__':
    unittest.main()