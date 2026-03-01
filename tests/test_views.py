import unittest
import sys
import os
import pandas as pd
from unittest.mock import patch, MagicMock

# Ajuste de ruta para que Python encuentre la carpeta 'src'
sys.path.append(os.getcwd())

# Importamos la clase base y las vistas
from src.views.base_view import Vista
from src.views.dashboard import VistaDashboard, DashboardUtils 
from src.views.inspeccion import VistaInspeccion

# Importamos modelos para simular datos
from src.models.concretos import MotorInduccion
from src.logical.estrategias import DesgasteLineal
from src.utils.enums import EstadoEquipo

class TestViewsLogic(unittest.TestCase):
    """Pruebas de la lógica pura de las vistas (Arquitectura y Datos) ahora en POO"""

    def test_arquitectura_vistas_abstractas(self):
        """Verifica que las vistas respeten el contrato de la Clase Abstracta (Polimorfismo)"""
        self.assertTrue(issubclass(VistaDashboard, Vista), "El Dashboard no hereda de Vista")
        self.assertTrue(issubclass(VistaInspeccion, Vista), "La Inspección no hereda de Vista")
        
        self.assertTrue(hasattr(VistaDashboard, 'render'), "Falta el método render en Dashboard")
        self.assertTrue(hasattr(VistaInspeccion, 'render'), "Falta el método render en Inspeccion")

    def test_obtener_comentario_estado(self):
        """Prueba la lógica de alertas usando el método estático de DashboardUtils"""
        self.assertEqual(DashboardUtils.obtener_comentario_estado(0.15, "OPERATIVO"), "✅ Óptimas condiciones.")
        
        self.assertEqual(DashboardUtils.obtener_comentario_estado(0.75, "OPERATIVO"), "🟠 Desgaste avanzado.")
        
        self.assertEqual(DashboardUtils.obtener_comentario_estado(0.05, "FALLA"), "🛑 ESTADO: INACTIVO - En revisión técnica")
    
        self.assertEqual(DashboardUtils.obtener_comentario_estado(0.1, "REPORTADO"), "⚠️ ATENCIÓN: Reporte pendiente de validación")

    def test_convertir_objetos_a_df(self):
        """Verifica la transformación a DataFrame usando el método estático"""
        estrategia = DesgasteLineal()
        motor = MotorInduccion("TEST-DF-01", "Motor Data", "2023-01-01", "5HP", "220V", 1800, estrategia)
        motor.estado = EstadoEquipo.OPERATIVO
        
        diccionario_mock = {"Laboratorio Mock": [motor]}
        
        df = DashboardUtils.convertir_objetos_a_df(diccionario_mock, 0)
        
        self.assertIsInstance(df, pd.DataFrame, "La función no devolvió un DataFrame de Pandas")
        self.assertFalse(df.empty, "El DataFrame llegó vacío")
        self.assertEqual(df.iloc[0]["ID"], "TEST-DF-01")


class TestVistasRender(unittest.TestCase):
    """Pruebas del método render() simulando Streamlit"""

    @patch('src.views.dashboard.st')
    def test_dashboard_llama_a_render_correctamente(self, mock_st):
        mock_st.session_state = MagicMock()
        mock_st.session_state.trigger = 0
        mock_st.session_state.db_laboratorios = {} 
        
        mock_st.tabs.return_value = [MagicMock() for _ in range(5)]
        
        def side_effect_columns(spec):
            num = spec if isinstance(spec, int) else len(spec)
            mocks = []
            for _ in range(num):
                col_mock = MagicMock()
                col_mock.selectbox.return_value = "Otro / Genérico"
                col_mock.text_input.return_value = ""
                mocks.append(col_mock)
            return mocks
            
        mock_st.columns.side_effect = side_effect_columns

        vista_dash = VistaDashboard()
        vista_dash._cargar_y_agrupar_desde_supabase = MagicMock(return_value={})
        
        vista_dash.render()
        
        mock_st.title.assert_called_with("📊 Dashboard de Activos FIEE")
        self.assertTrue(mock_st.tabs.called)

    @patch('src.views.inspeccion.st')
    def test_inspeccion_llama_a_render_correctamente(self, mock_st):
        mock_st.session_state = MagicMock()
        mock_st.session_state.db_laboratorios = {}
        mock_st.text_input.return_value = ""
        
        vista_insp = VistaInspeccion()
        vista_insp.render()
        
        mock_st.header.assert_called_with("📲 Inspección Técnica (Estudiante)")
        self.assertTrue(mock_st.text_input.called)

if __name__ == '__main__':
    unittest.main()