import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
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

# --- ENTREGABLE 7: BUILDER ---
from src.utils.reporte_builder import ReporteBuilder

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

# --- Función PDF Profesional (PATRÓN BUILDER) ---
def generar_pdf(equipo, lab):
    builder = ReporteBuilder()
    builder.agregar_titulo("ORDEN DE TRABAJO Y FICHA TÉCNICA")
    
    obs = equipo.calcular_obsolescencia()
    estado_actual = equipo.estado.name if hasattr(equipo.estado, 'name') else str(equipo.estado)
    
    datos = {
        "ID Activo": equipo.id_activo,
        "Modelo": equipo.modelo,
        "Ubicación": lab,
        "Fecha de Compra": str(equipo.fecha_compra),
        "Estado Actual": estado_actual,
        "Desgaste Calculado": f"{obs*100:.2f}%"
    }
    builder.agregar_cuerpo(datos)
    
    # HISTORIAL
    builder.pdf.ln(5)
    builder.pdf.set_font("helvetica", "B", 12)
    builder.pdf.cell(0, 10, "Historial de Mantenimiento e Incidencias:", new_x="LMARGIN", new_y="NEXT")
    builder.pdf.set_font("helvetica", "", 10)
    
    if equipo.historial_incidencias:
        for inc in equipo.historial_incidencias:
            fecha = inc.get('fecha', '-')
            texto = inc.get('detalle', '-')
            dictamen = inc.get('dictamen_ia', '')

            # --- PARCHE DE SEGURIDAD PARA EMOJIS ---
            # Limpiamos el texto principal del historial
            texto_seguro = str(texto).encode('latin-1', 'replace').decode('latin-1')
            
            # 1. Forzamos el cursor al margen izquierdo (10 mm)
            builder.pdf.set_x(10) 
            # 2. Usamos el texto SEGURO (sin emojis que rompan la fuente)
            builder.pdf.multi_cell(0, 6, f"[{fecha}] {texto_seguro}", new_x="LMARGIN", new_y="NEXT")
            
            if dictamen:
                # Limpiamos también el dictamen de la IA por si acaso
                dictamen_seguro = str(dictamen).encode('latin-1', 'replace').decode('latin-1')
                texto_dictamen = f"   >> Dictamen IA: {dictamen_seguro}"
                
                builder.pdf.set_font("helvetica", "I", 9)
                builder.pdf.set_x(10)
                builder.pdf.multi_cell(0, 6, texto_dictamen, new_x="LMARGIN", new_y="NEXT")
                builder.pdf.set_font("helvetica", "", 10)
                
            builder.pdf.ln(2)
    else:
        builder.pdf.set_x(10)
        builder.pdf.cell(0, 10, "Sin registros de mantenimiento.", new_x="LMARGIN", new_y="NEXT")

    # Firmas de autorización (Versión Admin)
    builder.agregar_firmas()
    
    return builder.compilar_pdf()

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

        tab_tabla, tab_detalle, tab_recup, tab_alta, tab_bajas = st.tabs(["📋 Inventario", "⚙️ Gestión Técnica", "🚑 Recuperación", "➕ Actualizar Inventario", "🪦 Histórico de Bajas"])

        # 1. TABLA GENERAL
        with tab_tabla:
            labs_con_datos = [k for k, v in st.session_state.db_laboratorios.items() if len(v) > 0]
            
            if labs_con_datos:
                opciones = ["🔍 VER TODOS"] + labs_con_datos
                filtro_lab = st.selectbox("Filtrar por Ubicación:", opciones)
                
                df = convertir_objetos_a_df(st.session_state.db_laboratorios, st.session_state.trigger)
                
                if not df.empty:
                    # 1. Quitamos la columna de objetos y filtramos los vivos
                    df_show = df.drop(columns=["OBJ_REF"])
                    df_show = df_show[df_show["Estado"] != "BAJA"] # <-- ¡EL FILTRO SALVADOR!
                    
                    if filtro_lab != "🔍 VER TODOS":
                        df_show = df_show[df_show["Ubicación"] == filtro_lab]
                    
                    st.dataframe(df_show, width="stretch", hide_index=True)
                    st.caption(f"Mostrando {len(df_show)} registros activos.")
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
                    estado_actual_str = eq_sel.estado.name if hasattr(eq_sel.estado, 'name') else str(eq_sel.estado)
                    st.info(f"Estado: **{estado_actual_str}**")
                    
                    st.markdown("#### 🤖 Inspección Visual")
                    img = st.file_uploader("Subir foto daño:", type=['jpg','png'], key=f"ia_{eq_sel.id_activo}")
                    if img and st.button("Analizar", key=f"btn_ia_{eq_sel.id_activo}"):
                        with st.spinner("Analizando imagen con IA... 🔍"):
                            vision = VisionService()
                            res = vision.analizar_quemadura(img)
                            
                            # 1. Extraemos los datos previniendo que la IA cambie los nombres
                            diag = res.get('diagnostico', res.get('dictamen', 'Sin diagnóstico'))
                            alerta = res.get('alerta', False)
                            es_critico = res.get('es_critico', alerta) 
                            
                            # 2. Guardamos en el historial
                            eq_sel.historial_incidencias.append({
                                "fecha": datetime.now().strftime("%Y-%m-%d"),
                                "detalle": "Inspección Visual IA", 
                                "dictamen_ia": diag
                            })
                            
                            # 3. Lógica de estados súper robusta
                            diagnostico_ia = str(diag).upper()
                            
                            if es_critico or any(p in diagnostico_ia for p in ["FALLA", "CRÍTIC", "QUEMADURA"]): 
                                eq_sel.estado = EstadoEquipo.FALLA.name      # <-- Forzamos a que sea String
                            elif alerta or any(p in diagnostico_ia for p in ["ANOMAL", "MANTENIMIENTO", "DESGASTE", "RIESGO"]):
                                eq_sel.estado = EstadoEquipo.EN_MANTENIMIENTO.name # <-- Forzamos a que sea String
                            
                            if eq_sel.verificar_umbral_quejas():
                                st.error("🚨 UMBRAL SUPERADO: El sistema ha bloqueado el equipo por precaución.")
                                time.sleep(4)

                            EquipoRepository().actualizar_equipo(eq_sel)
                            
                            # 5. Limpieza TOTAL de la memoria
                            st.cache_data.clear() 
                            if 'db_laboratorios' in st.session_state:
                                del st.session_state['db_laboratorios'] 
                            st.session_state.trigger = 1
                            
                            # 6. Mensaje de éxito y pausa estratégica para Supabase
                            estado_final = eq_sel.estado.name if hasattr(eq_sel.estado, 'name') else str(eq_sel.estado)
                            st.success(f"✅ Análisis completado. El equipo pasó a estado: {estado_final}")
                            time.sleep(1.5) 
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
                    st.markdown("#### 👨‍🔧 Acción Manual")
                    if estado_actual_str == "OPERATIVO":
                        if st.button("🔧 Enviar a Mantenimiento (Manual)", key=f"mant_man_{eq_sel.id_activo}"):
                            eq_sel.estado = EstadoEquipo.EN_MANTENIMIENTO.name
                            eq_sel.historial_incidencias.append({
                                "fecha": datetime.now().strftime("%Y-%m-%d"),
                                "detalle": "REPORTE MANUAL: Enviado a mantenimiento por quejas de usuarios."
                            })
                            EquipoRepository().actualizar_equipo(eq_sel)
                            st.cache_data.clear()
                            if 'db_laboratorios' in st.session_state:
                                del st.session_state['db_laboratorios']
                            st.session_state.trigger = 1
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
                    
                    st.markdown("---")
                    
                    # --- NUEVO BOTÓN DE DESCARGA (Entregable 7) ---
                    pdf_bytes = generar_pdf(eq_sel, getattr(eq_sel, 'ubicacion', 'Laboratorio FIEE'))
                    st.download_button(
                        label="📄 Descargar Ficha Técnica y Orden de Trabajo", 
                        data=pdf_bytes, 
                        file_name=f"Ficha_{eq_sel.id_activo}.pdf", 
                        mime="application/pdf",
                        key=f"dl_pdf_{eq_sel.id_activo}",
                        type="primary"
                    )

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
                        # Protección: leemos el estado independientemente de si es Enum o String
                        estado_str = e.estado.name if hasattr(e.estado, 'name') else str(e.estado)
                        if estado_str not in ["OPERATIVO", "BAJA"]:
                            observados.append((lab_n, e))
            
            if not observados:
                st.success("✅ Todo el inventario está operativo.")
            else:
                sel_obs = st.selectbox("Equipo a reparar:", range(len(observados)), format_func=lambda i: f"{observados[i][1].modelo} ({observados[i][1].estado.name if hasattr(observados[i][1].estado, 'name') else str(observados[i][1].estado)})")
                lab_origen, eq_rep = observados[sel_obs]
                
                with st.form("form_rep"):
                    st.write(f"Gestionando: **{eq_rep.modelo}** del **{lab_origen}**")
                    informe = st.text_area("Detalle Técnico o Motivo de Baja:")
                    
                    # Creamos dos columnas para los botones
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.form_submit_button("✅ Dar de Alta (Reingreso)"):
                            eq_rep.estado = EstadoEquipo.OPERATIVO.name
                            eq_rep.historial_incidencias.append({
                                "fecha": datetime.now().strftime("%Y-%m-%d"), 
                                "detalle": f"REPARACIÓN/ALTA: {informe}"
                            })
                            EquipoRepository().actualizar_equipo(eq_rep)
                            st.session_state.trigger = 1
                            st.rerun()
                            
                    with col2:
                        if st.form_submit_button("🚨 Dar de Baja (Descarte)"):
                            # CAMBIAMOS EL ESTADO A DADO DE BAJA
                            eq_rep.estado = "BAJA" 
                            eq_rep.historial_incidencias.append({
                                "fecha": datetime.now().strftime("%Y-%m-%d"), 
                                "detalle": f"BAJA DEFINITIVA: {informe}"
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
            with tab_bajas:
                st.subheader("🪦 Cementerio de Equipos (Histórico de Bajas)")
                st.markdown("Registro permanente de activos retirados por obsolescencia, daño irreparable o descarte.")
            
                df = convertir_objetos_a_df(st.session_state.db_laboratorios, st.session_state.trigger)
            
                if not df.empty:
                    df_caidos = df[df["Estado"] == "BAJA"].drop(columns=["OBJ_REF"])
                    if not df_caidos.empty:
                        st.dataframe(df_caidos, width="stretch", hide_index=True)
                        st.error(f"Total de equipos inactivos: {len(df_caidos)}")
                    else:
                        st.success("🌟 ¡Excelente! Ningún equipo ha sido dado de baja todavía.")
                else:
                    st.info("No hay datos en el sistema.")