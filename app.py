import streamlit as st
import sys
import os

# 1. Ajuste de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from supabase import create_client

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
        # Conectamos a Supabase usando los secretos seguros
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        self.supabase = create_client(url, key)

    def autenticar(self, correo, contrasena):
        try:
            # 1. Intentamos entrar al sistema de seguridad oficial de Supabase
            res = self.supabase.auth.sign_in_with_password({
                "email": correo, 
                "password": contrasena
            })

            # GUARDAMOS LA SESIÓN PARA QUE STREAMLIT NO LA OLVIDE
            if res.session:
                st.session_state['access_token'] = res.session.access_token
                st.session_state['refresh_token'] = res.session.refresh_token

            # 2. Si tiene éxito, buscamos sus datos en la tabla
            if res.user:
                perfil = self.supabase.table("usuarios").select("rol", "es_primera_vez").eq("correo", correo).single().execute()
                
                st.session_state["autenticado"] = True
                st.session_state["usuario_actual"] = res.user.email 
                st.session_state["rol_actual"] = perfil.data.get("rol", "estudiante")
                st.session_state["primera_vez"] = perfil.data.get("es_primera_vez", False)
                return True
                
        except Exception as e:
            st.error(f"Detalle del error técnico: {e}")
            return False

    def actualizar_contrasena(self, nueva_clave):
        """Actualiza la clave en Supabase Auth y quita la bandera en la tabla."""
        try:
            # RESTAURAMOS LA SESIÓN ANTES DE CAMBIAR LA CLAVE
            if 'access_token' in st.session_state and 'refresh_token' in st.session_state:
                self.supabase.auth.set_session(
                    st.session_state['access_token'], 
                    st.session_state['refresh_token']
                )

            # 1. Cambiamos la clave real en la bóveda de Supabase
            self.supabase.auth.update_user({"password": nueva_clave})
            
            # 2. Actualizamos la bandera en nuestra tabla de usuarios (USANDO CORREO)
            usuario_auth = self.supabase.auth.get_user()
            if usuario_auth and usuario_auth.user:
                correo_usuario = usuario_auth.user.email
                self.supabase.table("usuarios").update({"es_primera_vez": False}).eq("correo", correo_usuario).execute()
                
                # 3. Actualizamos la memoria de la app
                st.session_state["primera_vez"] = False
                return True
                
        except Exception as e:
            st.error(f"Error al actualizar la contraseña: {e}")
            return False

    def cerrar_sesion(self):
        self.supabase.auth.sign_out() # Cerramos sesión en el servidor
        st.session_state["autenticado"] = False
        st.session_state["usuario_actual"] = None
        st.session_state["rol_actual"] = None
        st.session_state["primera_vez"] = False

    def esta_autenticado(self):
        return st.session_state.get("autenticado", False)

class VistaLogin:
    def __init__(self, servicio_auth: ServicioAutenticacion):
        self.servicio_auth = servicio_auth

    def render(self):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.title("🔒 Acceso Restringido")
            
            tab_login, tab_ayuda = st.tabs(["🔑 Iniciar Sesión", "❓ Soy nuevo / Problemas"])
            
            with tab_login:
                with st.form("form_login"):
                    usuario = st.text_input("👤 Correo (@uni.pe)")
                    contrasena = st.text_input("🔑 Contraseña", type="password")
                    btn_entrar = st.form_submit_button("Ingresar", use_container_width=True)
                    
                    if btn_entrar:
                        if self.servicio_auth.autenticar(usuario, contrasena):
                            st.rerun()
            
            with tab_ayuda:
                st.markdown("### ¿Problemas de acceso?")
                st.markdown("""
                * **Si eres nuevo:** El Administrador debe crearte una cuenta primero con una clave temporal.
                * **Si olvidaste tu clave:** Por el momento, solicita al Administrador (Docente) el restablecimiento de tu clave temporal.
                """)
                st.markdown("---")

class VistaActualizarClave:
    """Nueva vista de seguridad que fuerza el cambio de contraseña."""
    def __init__(self, servicio_auth: ServicioAutenticacion):
        self.servicio_auth = servicio_auth

    def render(self):
        st.warning("⚠️ Por políticas de seguridad, debes cambiar tu contraseña temporal antes de acceder al sistema.")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.subheader("🔑 Establecer Credencial Definitiva")
            with st.form("form_cambio_clave"):
                nueva = st.text_input("Nueva Contraseña", type="password")
                confirma = st.text_input("Confirma Contraseña", type="password")
                btn_actualizar = st.form_submit_button("Actualizar y Entrar", use_container_width=True)

                if btn_actualizar:
                    if nueva != confirma:
                        st.error("Las contraseñas no coinciden.")
                    elif len(nueva) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres.")
                    else:
                        if self.servicio_auth.actualizar_contrasena(nueva):
                            st.success("¡Contraseña actualizada con éxito!")
                            st.rerun()

# ==============================================================================
# 2. CONTROLADOR PRINCIPAL DE LA APLICACIÓN
# ==============================================================================
class AplicacionFIEE:
    def __init__(self):
        self.servicio_auth = ServicioAutenticacion()
        self._inicializar_estado()

    def _inicializar_estado(self):
        if 'db_laboratorios' not in st.session_state:
            st.session_state.est_lineal = DesgasteLineal()
            st.session_state.est_expo = DesgasteExponencial()
            
            repo = EquipoRepository()
            datos_crudos = repo.leer_todos()
            
            if datos_crudos:
                mapper = EquipoMapper(st.session_state.est_lineal, st.session_state.est_expo)
                st.session_state.db_laboratorios = mapper.mapear_lista(datos_crudos)
            else:
                st.warning("Base de datos vacía o desconectada. Iniciando vacío.")
                st.session_state.db_laboratorios = {}

    def ejecutar(self):
        with st.sidebar:
            st.title("🏭 Sistema FIEE")
            st.info("Sistema de Gestión de Activos v1.0")

        vista_actual = None

        # 1. CANDADO PRINCIPAL
        if not self.servicio_auth.esta_autenticado():
            vista_actual = VistaLogin(self.servicio_auth)
        
        # 2. CANDADO SECUNDARIO: Forzar cambio de clave por primera vez
        elif st.session_state.get("primera_vez", False):
            vista_actual = VistaActualizarClave(self.servicio_auth)

        # 3. ACCESO CONCEDIDO: Mostrar menú según su ROL
        else:
            with st.sidebar:
                rol_usuario = st.session_state.get('rol_actual', 'estudiante')
                st.success(f"👤 Usuario: **{st.session_state.get('usuario_actual')}**\n\n🛡️ Rol: **{rol_usuario.capitalize()}**")
                
                if rol_usuario in ["docente", "trabajador"]:
                    opciones_menu = ["Dashboard (Docentes/Admin)", "Inspección (Estudiantes/Técnicos)"]
                else: 
                    opciones_menu = ["Inspección (Estudiantes/Técnicos)"]
                
                opcion = st.radio("Navegación:", opciones_menu)
                
                if st.button("Cerrar Sesión", use_container_width=True):
                    self.servicio_auth.cerrar_sesion()
                    st.rerun()

            if opcion == "Inspección (Estudiantes/Técnicos)":
                vista_actual = VistaInspeccion()
            elif opcion == "Dashboard (Docentes/Admin)":
                vista_actual = VistaDashboard()

        # Polimorfismo puro (Renderiza Login, Cambio de Clave, Inspección o Dashboard)
        if vista_actual:
            vista_actual.render()

# ==============================================================================
# 3. PUNTO DE ENTRADA
# ==============================================================================
if __name__ == "__main__":
    app = AplicacionFIEE()
    app.ejecutar()