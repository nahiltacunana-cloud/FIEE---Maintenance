import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime
from fpdf import FPDF

# --- IMPORTS PROPIOS ---
from src.views.base_view import Vista 
from src.models.equipo import Equipo 
from src.models.concretos import MotorInduccion, Osciloscopio, Multimetro
from src.logical.estrategias import DesgasteLineal, DesgasteExponencial
from src.repositories.equipo_repository import EquipoRepository 
from src.utils.enums import EstadoEquipo
from src.services.vision_service import VisionService
from src.services.predictive_service import PredictiveService

# --- NUEVOS IMPORTS PARA LA FACTORY Y EL MAPPER ---
from src.utils.mapper import EquipoMapper
from src.equipo_factory import EquipoFactory

# ==============================================================================
# 0. CLASE PARA EQUIPOS GENÉRICOS
# ==============================================================================
class EquipoGenerico(Equipo):
    def __init__(self, id_activo, modelo, fecha_compra, descripcion, estrategia_desgaste):
        super().__init__(id_activo, modelo, fecha_compra, estrategia_desgaste)
        self.descripcion = descripcion
        self.detalles_tecnicos = {"descripcion": descripcion}

# ==============================================================================
# 1. UTILIDADES
# ==============================================================================

def obtener_comentario_estado(obs_val, estado_str):
    est_upper = str(estado_str).upper()
    if any(palabra in est_upper for palabra in ["MANTENIMIENTO", "FALLA", "REPORTADO", "BAJA"]):
        return "⚠️ ATENCIÓN: Equipo fuera de servicio."
    if obs_val < 0.2: return "✅ Óptimas condiciones."
    elif obs_val < 0.5: return "🟡 Desgaste moderado."
    elif obs_val < 0.8: return "🟠 Desgaste avanzado."
    else: return "🔴 CRÍTICO: Riesgo inminente."

def convertir_objetos_a_df(_lista_equipos_dict, _trigger): 
    data = []
    if not _lista_equipos_dict or not isinstance(_lista_equipos_dict, dict): 
        return pd.DataFrame()

    for lab_nombre, lista_equipos in _lista_equipos_dict.items():
        if not isinstance(lista_equipos, list): continue 
        for eq in lista_equipos:
            obs_num = eq.calcular_obsolescencia()
            estado_actual = eq.estado.name if hasattr(eq.estado, 'name') else str(eq.estado)
            data.append({
                "ID": eq.id_activo,
                "Modelo": eq.modelo,
                "Tipo": type(eq).__name__, 
                "Ubicación": lab_nombre,
                "Estado": estado_actual,
                "Desgaste (%)": f"{obs_num * 100:.2f}%", 
                "Diagnóstico": obtener_comentario_estado(obs_num, estado_actual),
                "OBJ_REF": eq 
            })
    return pd.DataFrame(data)

# --- Función PDF Profesional ---
def generar_pdf(equipo, lab):
    pdf = FPDF()
    pdf.add_page()
    
    # TÍTULO
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'FICHA TECNICA: {equipo.modelo}', 0, 1, 'C')
    pdf.ln(5)

    # INFO GENERAL
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"ID Activo: {equipo.id_activo}", 0, 1)
    pdf.cell(0, 8, f"Ubicacion: {lab}", 0, 1)
    pdf.cell(0, 8, f"Fecha Compra: {equipo.fecha_compra}", 0, 1)
    pdf.cell(0, 8, f"Estado Actual: {equipo.estado.name}", 0, 1)
    
    # RESULTADOS
    obs = equipo.calcular_obsolescencia()
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, f"Nivel de Desgaste Calculado: {obs*100:.2f}%", 0, 1)
    pdf.ln(5)
    
    # HISTORIAL
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Historial de Mantenimiento e Incidencias:", 0, 1)
    pdf.set_font('Arial', '', 10)
    
    if equipo.historial_incidencias:
        for inc in equipo.historial_incidencias:
            fecha = inc.get('fecha', '-')
            # Limpieza de caracteres (emojis) para evitar crash
            texto = inc.get('detalle', '-').encode('latin-1', 'ignore').decode('latin-1')
            dictamen = inc.get('dictamen_ia', '')
            
            pdf.multi_cell(0, 6, f"[{fecha}] {texto}")
            if dictamen:
                dic_clean = dictamen.encode('latin-1', 'ignore').decode('latin-1')
                pdf.set_font('Arial', 'I', 9)
                pdf.multi_cell(0, 6, f"   >> Dictamen IA: {dic_clean}")
                pdf.set_font('Arial', '', 10)
            pdf.ln(2)
    else:
        pdf.cell(0, 10, "Sin registros de mantenimiento.", 0, 1)

    return pdf.output(dest='S').encode('latin-1', 'ignore')

# ==============================================================================
# 2. VISTA DASHBOARD
# ==============================================================================

class VistaDashboard(Vista):
    
    def _cargar_y_agrupar_desde_supabase(self):
        repo = EquipoRepository()
        datos_raw = repo.leer_todos()
        
        laboratorios_dict = {
            "Laboratorio de Control": [], "Laboratorio de Circuitos": [],
            "Laboratorio de Máquinas": [],
            "Laboratorio FIEE": [] 
        } 
        
        est_lineal = st.session_state.get('est_lineal', DesgasteLineal())
        est_expo = st.session_state.get('est_expo', DesgasteExponencial())

        if not datos_raw: return laboratorios_dict

        mapper = EquipoMapper(est_lineal, est_expo)
        equipos_lista = mapper.mapear_lista(datos_raw)

        for equipo in equipos_lista:
            ubicacion = getattr(equipo, 'ubicacion', 'Laboratorio FIEE')
            if ubicacion not in laboratorios_dict: 
                laboratorios_dict[ubicacion] = []
            laboratorios_dict[ubicacion].append(equipo)
            
        return laboratorios_dict

    def render(self):
        st.title("📊 Dashboard de Activos FIEE")
        st.markdown("---")

        if 'trigger' not in st.session_state: st.session_state.trigger = 0
        if 'est_lineal' not in st.session_state: st.session_state.est_lineal = DesgasteLineal()
        if 'est_expo' not in st.session_state: st.session_state.est_expo = DesgasteExponencial()

        es_lista_erronea = ('db_laboratorios' in st.session_state and not isinstance(st.session_state.db_laboratorios, dict))
        
        if 'db_laboratorios' not in st.session_state or st.session_state.trigger > 0 or es_lista_erronea:
            st.session_state.db_laboratorios = self._cargar_y_agrupar_desde_supabase()
            st.session_state.trigger = 0 

        tab_tabla, tab_detalle, tab_recup, tab_alta = st.tabs([
            "📋 Inventario", "⚙️ Gestión Técnica", "🚑 Recuperación", "➕ Actualizar Inventario"
        ])

        # 1. TABLA GENERAL
        with tab_tabla:
            labs_con_datos = [k for k, v in st.session_state.db_laboratorios.items() if len(v) > 0]
            
            if labs_con_datos:
                opciones = ["🔍 VER TODOS"] + labs_con_datos
                filtro_lab = st.selectbox("Filtrar por Ubicación:", opciones)
                
                df = convertir_objetos_a_df(st.session_state.db_laboratorios, st.session_state.trigger)
                
                if not df.empty:
                    df_show = df.drop(columns=["OBJ_REF"])
                    
                    if filtro_lab != "🔍 VER TODOS":
                        df_show = df_show[df_show["Ubicación"] == filtro_lab]
                    
                    st.dataframe(df_show, use_container_width=True, hide_index=True)
                    st.caption(f"Mostrando {len(df_show)} registros.")
                else:
                    st.info("No hay equipos registrados.")
            else:
                st.warning("No hay datos cargados (Inventario Vacío). Ve a la pestaña 'Alta Inventario' para comenzar.")

        # 2. GESTIÓN TÉCNICA
        with tab_detalle:
            labs_con_datos = [k for k, v in st.session_state.db_laboratorios.items() if len(v) > 0]
            
            if labs_con_datos:
                sel_lab_gestion = st.selectbox("Seleccionar Laboratorio:", labs_con_datos, key="sel_gest")
                equipo_list = st.session_state.db_laboratorios[sel_lab_gestion]
                
                idx = st.selectbox("Seleccionar Activo:", range(len(equipo_list)), 
                                   format_func=lambda i: f"{equipo_list[i].modelo} ({equipo_list[i].id_activo})")
                eq_sel = equipo_list[idx]
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.info(f"Estado: **{eq_sel.estado.name}**")
                    
                    st.markdown("#### 🤖 Inspección Visual")
                    img = st.file_uploader("Subir foto daño:", type=['jpg','png'], key=f"ia_{eq_sel.id_activo}")
                    if img and st.button("Analizar", key=f"btn_ia_{eq_sel.id_activo}"):
                        vision = VisionService()
                        res = vision.analizar_quemadura(img)
                        eq_sel.historial_incidencias.append({
                            "fecha": datetime.now().strftime("%Y-%m-%d"),
                            "detalle": f"IA: {res['alerta']}", "dictamen_ia": res['diagnostico']
                        })
                        if res.get('es_critico'): eq_sel.estado = EstadoEquipo.FALLA
                        EquipoRepository().actualizar_equipo(eq_sel)
                        st.session_state.trigger = 1
                        st.rerun()

                    st.markdown("---")
                    st.markdown("#### 🧠 Algoritmo de Desgaste")
                    est_actual_nombre = type(eq_sel.estrategia_desgaste).__name__
                    
                    modo_sel = st.radio("Modelo Matemático:", ["Lineal", "Exponencial"],
                                        index=0 if "Lineal" in est_actual_nombre else 1,
                                        horizontal=True, key=f"rad_{eq_sel.id_activo}")
                    
                    if st.button("🔄 Actualizar Cálculo", key=f"btn_calc_{eq_sel.id_activo}"):
                        nueva_est = st.session_state.est_lineal if modo_sel == "Lineal" else st.session_state.est_expo
                        eq_sel.cambiar_estrategia(nueva_est)
                        EquipoRepository().actualizar_equipo(eq_sel)
                        st.session_state.trigger = 1
                        st.success(f"Cambiado a modelo {modo_sel}")
                        time.sleep(1)
                        st.rerun()

                with c2:
                    obs = eq_sel.calcular_obsolescencia()
                    st.metric("Nivel de Desgaste Actual", f"{obs*100:.1f}%")
                    st.progress(min(obs, 1.0))
                    
                    st.markdown("---")
                    st.markdown("#### 🔮 Predicción IA de Falla")
                    
                    try:
                        predictor = PredictiveService()
                        fecha_estimada, grafico_fig = predictor.generar_prediccion(eq_sel)
                        
                        st.warning(f"⚠️ Fecha estimada de fallo crítico: **{fecha_estimada}**")
                        st.pyplot(grafico_fig) # Se muestra el gráfico predictivo
                    except Exception as e:
                        st.error(f"No se pudo generar la predicción: {e}")
                        st.info("Asegúrate de haber instalado scikit-learn y matplotlib en tu entorno.")
                    # ----------------------------------------
                    
                    st.markdown("---")
                    if st.button("📄 Generar Reporte PDF", key=f"pdf_{eq_sel.id_activo}"):
                        pdf_bytes = generar_pdf(eq_sel, eq_sel.ubicacion)
                        st.download_button("⬇️ Descargar PDF", pdf_bytes, file_name=f"Reporte_{eq_sel.id_activo}.pdf", mime="application/pdf")

                    with st.expander("Historial de Eventos", expanded=True):
                        for inc in eq_sel.historial_incidencias:
                            st.caption(f"{inc.get('fecha')} | {inc.get('detalle')}")
                            if 'dictamen_ia' in inc: st.code(inc['dictamen_ia'])
                            st.divider()
            else:
                st.info("No hay equipos para gestionar.")

        # 3. ZONA DE RECUPERACIÓN
        with tab_recup:
            st.subheader("🛠️ Mantenimiento Correctivo")
            observados = []
            if isinstance(st.session_state.db_laboratorios, dict):
                for lab_n, lista in st.session_state.db_laboratorios.items():
                    for e in lista:
                        if e.estado.name != "OPERATIVO": observados.append((lab_n, e))
            
            if not observados:
                st.success("✅ Todo el inventario está operativo.")
            else:
                sel_obs = st.selectbox("Equipo a reparar:", range(len(observados)), 
                                     format_func=lambda i: f"{observados[i][1].modelo} ({observados[i][1].estado.name})")
                lab_origen, eq_rep = observados[sel_obs]
                
                with st.form("form_rep"):
                    st.write(f"Reparando: **{eq_rep.modelo}** del **{lab_origen}**")
                    informe = st.text_area("Detalle Técnico de la Reparación:")
                    if st.form_submit_button("✅ Dar de Alta (Reingreso)"):
                        eq_rep.estado = EstadoEquipo.OPERATIVO
                        eq_rep.historial_incidencias.append({
                            "fecha": datetime.now().strftime("%Y-%m-%d"), "detalle": f"REPARACIÓN: {informe}"
                        })
                        EquipoRepository().actualizar_equipo(eq_rep)
                        st.session_state.trigger = 1
                        st.rerun()

        # 4. ALTA INVENTARIO
        with tab_alta:
            st.subheader("➕ Nuevo Ingreso")
            LABS_POSIBLES = ["Laboratorio de Control", "Laboratorio de Circuitos", "Laboratorio de Máquinas", "Laboratorio FIEE"]
            
            c_lab, c_tipo = st.columns(2)
            lab_dest = c_lab.selectbox("Destino:", LABS_POSIBLES)
            
            equipos_por_lab = {
                "Laboratorio de Circuitos": ["Osciloscopio", "Multimetro"],
                "Laboratorio de Máquinas": ["MotorInduccion", "Multimetro"],
                "Laboratorio de Control": ["Osciloscopio", "Multimetro", "MotorInduccion"],
                "Laboratorio FIEE": ["MotorInduccion", "Osciloscopio", "Multimetro"]
            }
            
            # Buscamos qué equipos le tocan al laboratorio seleccionado, 
            # y le sumamos la opción genérica al final.
            opts = equipos_por_lab.get(lab_dest, []) + ["Otro / Genérico"]
            
            tipo_sel = c_tipo.selectbox("Tipo:", opts, key=f"t_{lab_dest}")
            
            with st.form("alta"):
                m = st.text_input("Modelo")
                f = st.date_input("Fecha")
                
                # --- CAMPOS DINÁMICOS SEGÚN EL TIPO DE EQUIPO ---
                st.markdown("**Especificaciones Técnicas**")
                
                # Variables por defecto para capturar los datos
                hp_in, volt_in, rpm_in = "", "", 0
                ancho_in = ""
                prec_in = ""
                extra_in = ""

                if "Motor" in tipo_sel:
                    col1, col2, col3 = st.columns(3)
                    hp_in = col1.text_input("Potencia (ej. 5HP)", value="5HP")
                    volt_in = col2.text_input("Voltaje (ej. 220V)", value="220V")
                    rpm_in = col3.number_input("RPM", min_value=0, value=1800)
                elif "Osciloscopio" in tipo_sel:
                    ancho_in = st.text_input("Ancho de Banda (ej. 100MHz)", value="100MHz")
                elif "Multimetro" in tipo_sel:
                    prec_in = st.text_input("Precisión (ej. 1%)", value="1%")
                else:
                    extra_in = st.text_input("Descripción o Detalle Extra")
                
                # --- BOTÓN DE GUARDAR ---
                if st.form_submit_button("Guardar"):
                    nid = f"EQ-{random.randint(1000,9999)}"
                    f_s = f.strftime("%Y-%m-%d")
                    new = None
                    
                    item_data = {"id_activo": nid, "modelo": m, "fecha_compra": f_s}
                    detalles_data = {}
                    
                    # Armamos los detalles con lo que el usuario escribió en el formulario
                    if "Motor" in tipo_sel:
                        detalles_data = {"hp": hp_in, "voltaje": volt_in, "rpm": rpm_in}
                        new = EquipoFactory.crear_equipo("MotorInduccion", item_data, detalles_data, st.session_state.est_lineal)
                    elif "Osciloscopio" in tipo_sel:
                        detalles_data = {"ancho_banda": ancho_in}
                        new = EquipoFactory.crear_equipo("Osciloscopio", item_data, detalles_data, st.session_state.est_lineal)
                    elif "Multimetro" in tipo_sel:
                        detalles_data = {"precision": prec_in, "es_digital": True}
                        new = EquipoFactory.crear_equipo("Multimetro", item_data, detalles_data, st.session_state.est_lineal)
                    else: 
                        new = EquipoGenerico(nid, m, f_s, extra_in, st.session_state.est_lineal)
                    
                    new.ubicacion = lab_dest
                    EquipoRepository().guardar_equipo(new)
                    st.session_state.trigger = 1
                    st.rerun()