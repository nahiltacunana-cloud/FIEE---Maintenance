import streamlit as st
import pandas as pd
import random
import time
import requests
import os
import tempfile
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
from src.utils.mapper import EquipoMapper
from src.equipo_factory import EquipoFactory
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

class DashboardUtils:
    """
    Clase utilitaria para la vista del Dashboard.
    Encapsula lógica de formato, transformación de datos a DataFrames 
    """

    @staticmethod
    def obtener_comentario_estado(obs_val, estado_str):
        est_upper = str(estado_str).upper()
        if est_upper in ["EN_MANTENIMIENTO", "FALLA"]:
            return "🛑 ESTADO: INACTIVO - En revisión técnica"
        elif "REPORTADO" in est_upper:
            return "⚠️ ATENCIÓN: Reporte pendiente de validación"
        elif "BAJA" in est_upper:
            return "✖️ EQUIPO RETIRADO: No disponible"
        #Caso OPERATIVO
        if obs_val < 0.2: 
            return "✅ Óptimas condiciones."
        elif obs_val < 0.5: 
            return "🟡 Desgaste moderado."
        elif obs_val < 0.8: 
            return "🟠 Desgaste avanzado."
        else: 
            return "🔴 CRÍTICO: Riesgo inminente de falla."

    @staticmethod
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
                    "Diagnóstico": DashboardUtils.obtener_comentario_estado(obs_num, estado_actual), # FÍJATE AQUÍ: Llamamos a la función con el nombre de la clase
                    "OBJ_REF": eq 
                })
        return pd.DataFrame(data)

    # --- Función PDF Profesional (PATRÓN BUILDER) ---
    @staticmethod
    def generar_pdf(equipo, lab, imagen_bytes=None): 
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
        
        # 1. FOTO PRINCIPAL

        # 2. SECCIÓN DE HISTORIAL
        builder.pdf.ln(5)
        builder.pdf.set_font("helvetica", "B", 12)
        builder.pdf.cell(0, 10, "Historial de Mantenimiento e Incidencias:", new_x="LMARGIN", new_y="NEXT")
        builder.pdf.set_font("helvetica", "", 10)
        
        if equipo.historial_incidencias:
            for inc in equipo.historial_incidencias:
                fecha = inc.get('fecha', '-')
                texto = inc.get('detalle', '-')
                dictamen = inc.get('dictamen_ia', '')

                # --- TEXTO DE LA INCIDENCIA ---
                texto_seguro = str(texto).encode('latin-1', 'replace').decode('latin-1')
                builder.pdf.set_x(10) 
                builder.pdf.multi_cell(0, 6, f"[{fecha}] {texto_seguro}", new_x="LMARGIN", new_y="NEXT")
                
                # --- DICTAMEN IA ---
                if dictamen:
                    dictamen_seguro = str(dictamen).encode('latin-1', 'replace').decode('latin-1')
                    builder.pdf.set_font("helvetica", "I", 9)
                    builder.pdf.set_x(10)
                    builder.pdf.multi_cell(0, 6, f"   >> Dictamen IA: {dictamen_seguro}", new_x="LMARGIN", new_y="NEXT")
                    builder.pdf.set_font("helvetica", "", 10)
                
                # --- EVIDENCIA VISUAL EN EL HISTORIAL ---
                if 'url_foto' in inc and inc['url_foto']:
                    url = inc['url_foto']
                    try:
                        # Descargamos la foto de Supabase rápidamente
                        respuesta = requests.get(url, timeout=5)
                        if respuesta.status_code == 200:
                            # La guardamos en un archivo temporal seguro
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                                tmp.write(respuesta.content)
                                tmp_path = tmp.name
                            
                            # La dibujamos en el PDF (con un ancho de 80 y un poco indentada)
                            builder.pdf.ln(2)
                            builder.pdf.image(tmp_path, x=20, w=80) 
                            
                            # Borramos el archivo temporal para no llenar el disco duro
                            os.remove(tmp_path)
                    except Exception as e:
                        builder.pdf.set_text_color(255, 0, 0) # Rojo
                        builder.pdf.set_x(20)
                        builder.pdf.multi_cell(0, 6, "[Error al cargar evidencia visual]", new_x="LMARGIN", new_y="NEXT")
                        builder.pdf.set_text_color(0, 0, 0) # Volver a negro
        
                builder.pdf.ln(4) # Espacio antes de la siguiente incidencia
                builder.pdf.line(10, builder.pdf.get_y(), 200, builder.pdf.get_y()) # Línea separadora
                builder.pdf.ln(4)
        else:
            builder.pdf.set_x(10)
            builder.pdf.cell(0, 10, "Sin registros de mantenimiento.", new_x="LMARGIN", new_y="NEXT")

        # Firmas de autorización (Versión Admin)
        if builder.pdf.get_y() > 240: 
            builder.pdf.add_page()
            builder.agregar_firmas()
        else:
            builder.agregar_firmas()
        return bytes(builder.pdf.output())

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
                
                df = DashboardUtils.convertir_objetos_a_df(st.session_state.db_laboratorios, st.session_state.trigger)
                
                if not df.empty:
                    # 1. Quitamos la columna de objetos y filtramos los vivos
                    df_show = df.drop(columns=["OBJ_REF"])
                    df_show = df_show[df_show["Estado"] != "BAJA"]
                    
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
                            url_foto_publica = ""
                            try:
                                repo = EquipoRepository() 
                                if repo.client:
                                    nombre_archivo = f"dash_{eq_sel.id_activo}_{int(time.time())}.png"
                                    
                                    repo.client.storage.from_("evidencias").upload(
                                        nombre_archivo, 
                                        img.getvalue(), 
                                        {"content-type": img.type}
                                    )
                                    url_foto_publica = repo.client.storage.from_("evidencias").get_public_url(nombre_archivo)
                            except Exception as e:
                                pass 
                            eq_sel.historial_incidencias.append({
                                "fecha": datetime.now().strftime("%Y-%m-%d"),
                                "detalle": "Inspección Visual IA por docente", 
                                "dictamen_ia": diag,
                                "url_foto": url_foto_publica
                            })
                            
                            # 3. Lógica de decisión Inteligente (Human-in-the-Loop)
                            if alerta:
                                # CAMINO 1: IA detecta falla evidente en la foto
                                eq_sel.estado = EstadoEquipo.EN_MANTENIMIENTO.name
                                inc_detalle = "IA confirmó anomalía visual. Automático a mantenimiento."
                            else:
                                # CAMINO 3: IA no detecta falla, pero hay reporte. Pasa a duda/Triaje
                                eq_sel.estado = "REPORTADO"
                                inc_detalle = "Inspección IA no concluyente. Requiere Triaje manual."
                                
                            # Actualizamos el último registro del historial con la conclusión
                            eq_sel.historial_incidencias[-1]["detalle"] = inc_detalle
                            
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
                    st.markdown("#### 👨‍🔧 Acción Manual y Triaje")
                    # 1. Si está operativo, el profesor puede levantar un reporte directo (Pasa a REPORTADO)
                    if estado_actual_str == "OPERATIVO":
                        st.info("💡 Si el equipo falla o ya cumplió su ciclo de vida, levanta un reporte aquí.")
    
                        motivo = st.text_input("¿Por qué reportas este equipo? (Opcional):", placeholder="Ej: Falla interna, muy viejo...")
    
                        if st.button("🚩 Levantar Reporte (Enviar a Triaje)", key=f"mant_man_{eq_sel.id_activo}"):
                            usuario_actual = st.session_state.get("usuario", "docente")
                            eq_sel.estado = "REPORTADO"
                            eq_sel.historial_incidencias.append({
                                "fecha": datetime.now().strftime("%Y-%m-%d"),
                                "detalle": f"REPORTE MANUAL por {usuario_actual}. Motivo: {motivo}. Pendiente de Triaje."
                            })
        
                            EquipoRepository().actualizar_equipo(eq_sel)
                            st.cache_data.clear()
                            if 'db_laboratorios' in st.session_state:
                                del st.session_state['db_laboratorios']
                            st.session_state.trigger = 1
                            st.rerun()

                    # 2. ZONA DE TRIAJE: Si el equipo está reportado, el admin decide
                    elif estado_actual_str == "REPORTADO":
                        st.warning("⚠️ Este equipo está en TRIAJE. Requiere revisión.")    
                        col_t1, col_t2 = st.columns(2)
                        with col_t1:
                            if st.button("✅ Falsa Alarma", key=f"btn_ok_{eq_sel.id_activo}", type="secondary", use_container_width=True):
                                eq_sel.estado = EstadoEquipo.OPERATIVO.name
                                eq_sel.historial_incidencias.append({
                                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                                    "detalle": "TRIAJE: Reporte desestimado. Vuelve a Operativo."
                                })
                                EquipoRepository().actualizar_equipo(eq_sel)
                                st.cache_data.clear()
                                if 'db_laboratorios' in st.session_state:
                                    del st.session_state['db_laboratorios']
                                st.session_state.trigger = 1
                                st.rerun()
                                
                        with col_t2:
                            if st.button("🔧 Confirmar Mantenimiento", key=f"btn_bad_{eq_sel.id_activo}", type="primary", use_container_width=True):
                                eq_sel.estado = EstadoEquipo.EN_MANTENIMIENTO.name
                                eq_sel.historial_incidencias.append({
                                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                                    "detalle": "TRIAJE: Falla confirmada. Pasa a Mantenimiento."
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
                        st.pyplot(grafico_fig) 
                    except Exception as e:
                        st.error(f"No se pudo generar la predicción: {e}")
                
                    st.markdown("---")
                
                # --- GENERACIÓN DEL PDF ACTUALIZADO ---
                    try:
                        imagen_pura = img.getvalue() if (img is not None) else None
                        pdf_bytes = DashboardUtils.generar_pdf(
                            equipo=eq_sel,
                            lab=getattr(eq_sel, 'ubicacion', 'Laboratorio FIEE'),
                            imagen_bytes=imagen_pura
                        )
                    
                        if pdf_bytes:
                            st.download_button(
                                label="📄 Descargar Ficha Técnica Actualizada",
                                data=pdf_bytes,
                                file_name=f"Ficha_{eq_sel.id_activo}.pdf",
                                mime="application/pdf",
                                key=f"btn_pdf_{eq_sel.id_activo}_{len(eq_sel.historial_incidencias)}"
                            )
                    except Exception as e:
                        st.error(f"Error al crear PDF: {e}")

                    with st.expander("Historial de Eventos", expanded=True):
                        for inc in eq_sel.historial_incidencias:
                            st.caption(f"{inc.get('fecha')} | {inc.get('detalle')}")
                            
                            if 'dictamen_ia' in inc: 
                                st.code(inc['dictamen_ia'])
                            
                            if 'url_foto' in inc and inc['url_foto']:
                                st.image(inc['url_foto'], width=250, caption="Evidencia del Reporte")
                                
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
                        if estado_str == "EN_MANTENIMIENTO":
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
                            st.cache_data.clear()
                            if 'db_laboratorios' in st.session_state:
                                del st.session_state['db_laboratorios']
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
                            st.cache_data.clear()
                            if 'db_laboratorios' in st.session_state:
                                del st.session_state['db_laboratorios']
                            st.session_state.trigger = 1
                            st.rerun()

        # 4. ALTA INVENTARIO
        with tab_alta:
            st.subheader("➕ Nuevo Ingreso")
            LABS_POSIBLES = ["Laboratorio de Control", "Laboratorio de Circuitos", "Laboratorio de Máquinas"]
            
            c_lab, c_tipo = st.columns(2)
            lab_dest = c_lab.selectbox("Destino:", LABS_POSIBLES)
            
            equipos_por_lab = {
                "Laboratorio de Circuitos": ["Osciloscopio", "Multimetro"],
                "Laboratorio de Máquinas": ["MotorInduccion", "Multimetro"],
                "Laboratorio de Control": ["Osciloscopio", "Multimetro", "MotorInduccion"],
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
            
                df = DashboardUtils.convertir_objetos_a_df(st.session_state.db_laboratorios, st.session_state.trigger)
            
                if not df.empty:
                    df_caidos = df[df["Estado"] == "BAJA"].drop(columns=["OBJ_REF"])
                    if not df_caidos.empty:
                        st.dataframe(df_caidos, width="stretch", hide_index=True)
                        st.error(f"Total de equipos inactivos: {len(df_caidos)}")
                    else:
                        st.success("🌟 ¡Excelente! Ningún equipo ha sido dado de baja todavía.")
                else:
                    st.info("No hay datos en el sistema.")