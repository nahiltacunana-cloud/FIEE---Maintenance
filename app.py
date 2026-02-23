import streamlit as st
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 2. Imports del Modelo (Backend)
from src.models.concretos import Osciloscopio, Multimetro, MotorInduccion
from src.logical.estrategias import DesgasteLineal, DesgasteExponencial
from src.repositories.equipo_repository import EquipoRepository
from src.utils.mapper import EquipoMapper

# 3. Imports de las Vistas (Frontend POO)
from src.views.inspeccion import VistaInspeccion
from src.views.dashboard import VistaDashboard

st.set_page_config(page_title="FIEE Maintenance OOP", page_icon="🏭", layout="wide")

# ==============================================================================
# 1. SERVICIOS Y VISTAS DE SEGURIDAD
# ==============================================================================
class ServicioAutenticacion:
    def __init__(self):
        self.usuarios_permitidos = {
            "admin": "fiee123",
            "profesor": "uni2024"
        }

    def autenticar(self, usuario, contrasena):
        if self.usuarios_permitidos.get(usuario) == contrasena:
            st.session_state["autenticado"] = True
            st.session_state["usuario_actual"] = usuario
            return True
        return False

    def cerrar_sesion(self):
        st.session_state["autenticado"] = False
        st.session_state["usuario_actual"] = None

    def esta_autenticado(self):
        return st.session_state.get("autenticado", False)

class VistaLogin:
    def __init__(self, servicio_auth: ServicioAutenticacion):
        self.servicio_auth = servicio_auth

    def render(self):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            st.title("🔒 Acceso Restringido")
            st.markdown("Área exclusiva para Docentes y Administradores.")
            
            with st.form("form_login"):
                usuario = st.text_input("👤 Usuario")
                contrasena = st.text_input("🔑 Contraseña", type="password")
                btn_entrar = st.form_submit_button("Ingresar", use_container_width=True)
                
                if btn_entrar:
                    if self.servicio_auth.autenticar(usuario, contrasena):
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas. Intente de nuevo.")

# ==============================================================================
# 2. CONTROLADOR PRINCIPAL DE LA APLICACIÓN (NUEVO)
# ==============================================================================
class AplicacionFIEE:
    """Clase principal que orquesta la inicialización y el enrutamiento de vistas."""
    
    def __init__(self):
        self.servicio_auth = ServicioAutenticacion()
        self._inicializar_estado() # Se llama automáticamente al instanciar

    def _inicializar_estado(self):
        """Encapsula la lógica de conexión a base de datos y variables globales."""
        if 'db_laboratorios' not in st.session_state:
            st.session_state.est_lineal = DesgasteLineal()
            st.session_state.est_expo = DesgasteExponencial()
            
            repo = EquipoRepository()
            datos_crudos = repo.leer_todos()
            
            if datos_crudos:
                mapper = EquipoMapper(st.session_state.est_lineal, st.session_state.est_expo)
                st.session_state.db_laboratorios = mapper.mapear_lista(datos_crudos)
            else:
                st.warning("⚠️ Base de datos vacía o desconectada. Iniciando vacío.")
                st.session_state.db_laboratorios = {}

    def ejecutar(self):
        """Dibuja la interfaz principal y aplica el polimorfismo de las vistas."""
        with st.sidebar:
            st.title("Sistema FIEE")
            st.info("Sistema de Gestión de Activos v1.0")
            opcion = st.radio("Seleccione Perfil:", ["Estudiante / Técnico", "Docente / Admin"])

        vista_actual = None

        if opcion == "Estudiante / Técnico":
            vista_actual = VistaInspeccion()

        elif opcion == "Docente / Admin":
            if not self.servicio_auth.esta_autenticado():
                vista_actual = VistaLogin(self.servicio_auth)
            else:
                with st.sidebar:
                    st.success(f"👤 Conectado como: **{st.session_state.get('usuario_actual')}**")
                    if st.button("🚪 Cerrar Sesión", use_container_width=True):
                        self.servicio_auth.cerrar_sesion()
                        st.rerun()
                
                vista_actual = VistaDashboard()

        # Polimorfismo puro
        if vista_actual:
            vista_actual.render()

# ==============================================================================
# 3. PUNTO DE ENTRADA
# ==============================================================================
if __name__ == "__main__":
    app = AplicacionFIEE()
    app.ejecutar()                                                                                              