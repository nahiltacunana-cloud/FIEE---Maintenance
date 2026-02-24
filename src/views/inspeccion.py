import streamlit as st
import time
import os
from datetime import datetime, timedelta
from src.views.base_view import Vista
from src.utils.enums import EstadoEquipo
from src.repositories.equipo_repository import EquipoRepository # <--- NUEVO
from src.utils.reporte_builder import ReporteBuilder # <--- NUEVO: Entregable 7

try:
    from src.services.vision_service import VisionService
except ImportError:
    VisionService = None

class VistaInspeccion(Vista):
    def render(self):
        st.header("📲 Inspección Técnica (Estudiante)")
        st.markdown("---")

        # --- CARGA AUTÓNOMA DE DATOS ---
        # Si el estudiante entra directo y la BD no está cargada, la descargamos.
        if 'db_laboratorios' not in st.session_state or not isinstance(st.session_state.db_laboratorios, dict):
            from src.views.dashboard import VistaDashboard
            st.session_state.db_laboratorios = VistaDashboard()._cargar_y_agrupar_desde_supabase()
            st.session_state.trigger = 0
        # -------------------------------

        # 1. SIMULACIÓN DE ESCANEO QR
        qr_input = st.text_input("🔫 Escanear Código QR (ID del Activo):", placeholder="Ej: MOT-01").strip()

        equipo_encontrado = None
        lab_ubicacion = None

        # Buscamos el equipo
        if qr_input and isinstance(st.session_state.db_laboratorios, dict):
            for lab, lista_equipos in st.session_state.db_laboratorios.items():
                for eq in lista_equipos:
                    if eq.id_activo == qr_input:
                        equipo_encontrado = eq
                        lab_ubicacion = lab
                        break
        
        # 2. SI ENCUENTRA EL EQUIPO -> MUESTRA FICHA TÉCNICA
        if equipo_encontrado:
            st.success(f"✅ Equipo Identificado: {equipo_encontrado.modelo}")
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                with c1:
                    if "Motor" in type(equipo_encontrado).__name__:
                         st.image("https://cdn-icons-png.flaticon.com/512/3662/3662819.png", width=80)
                    else:
                         st.image("https://cdn-icons-png.flaticon.com/512/9626/9626649.png", width=80)
                
                with c2:
                    st.write(f"**📍 Ubicación:** {lab_ubicacion}")
                    st.write(f"**🚦 Estado:** {equipo_encontrado.estado.value}")
                    obs = equipo_encontrado.calcular_obsolescencia()
                    vida_restante = max(0, 1.0 - obs)
                    st.progress(vida_restante, text=f"Vida Útil Restante: {vida_restante*100:.1f}%")

            st.divider()

            # 3. FORMULARIO DE REPORTE DE AVERÍA
            st.subheader("🚨 Reportar Incidencia")
            
            with st.form("mi_formulario"):
                usuario = st.text_input("Tu Nombre / Código:", "Estudiante-01")
                descripcion = st.text_area("Descripción del problema:", placeholder="El equipo hace un ruido extraño...")
                st.write("📸 **Evidencia Visual (Opcional)**")
                col_cam, col_upload = st.columns(2)
                foto_cam = col_cam.camera_input("Tomar Foto")
                foto_upl = col_upload.file_uploader("Subir Imagen", type=["jpg", "png", "jpeg"])
                
                enviar = st.form_submit_button("📢 Enviar Reporte")

            if enviar:
                    if not descripcion:
                        st.warning("⚠️ Por favor describe el problema.")
                    else:
                        foto_final = foto_cam if foto_cam else foto_upl
                        dictamen_ia = "Sin análisis visual."

                        # --- BLOQUE VISIÓN ---
                        if foto_final:
                            with st.spinner("Procesando evidencia..."):
                                time.sleep(1.5)
                                temp_filename = "temp_vision.jpg"
                                with open(temp_filename, "wb") as f: f.write(foto_final.getbuffer())
                                
                                try:
                                    if VisionService:
                                        servicio = VisionService()
                                        # Llamamos a la IA
                                        resultado = servicio.analizar_estado(foto_final)
                                        
                                        # Extraemos los datos de forma segura con .get()
                                        diag = resultado.get('diagnostico', 'Sin diagnóstico')
                                        det = resultado.get('detalle', '')
                                        alerta = resultado.get('alerta', False)
                                        
                                        # Armamos el texto final
                                        diagnostico_ia = str(diag).upper()
                                        dictamen_ia = f"IA: {diagnostico_ia} - {det}"
                                        
                                        diagnostico_ia = str(resultado.get('diagnostico', '')).upper()
                                        if resultado.get('es_critico'):
                                            equipo_encontrado.estado = EstadoEquipo.FALLA
                                        elif "ANOMAL" in diagnostico_ia:
                                            equipo_encontrado.estado = EstadoEquipo.EN_MANTENIMIENTO
                                        EquipoRepository().actualizar_equipo(equipo_encontrado)
                                        st.session_state.trigger = 1
                                            
                                    else:
                                        dictamen_ia = "IA no conectada."
                                
                                except Exception as e:
                                    dictamen_ia = f"Error en IA: {str(e)}"
                                finally:
                                    if os.path.exists(temp_filename): os.remove(temp_filename)

                        # --- GUARDADO EN HISTORIAL (Siempre se guarda) ---
                        detalle_log = f"Reportado por {usuario}: {descripcion}"
                        equipo_encontrado.registrar_incidencia(detalle_log)
                        ultimo_ticket = equipo_encontrado.historial_incidencias[-1]
                        ultimo_ticket['dictamen_ia'] = dictamen_ia
                        
                        if equipo_encontrado.verificar_umbral_quejas():
                            st.error("🚨 LÍMITE ALCANZADO: El equipo ha recibido 3 reportes recientes y pasará a Mantenimiento Automático.")
                            time.sleep(4)

                        # --- PERSISTENCIA SUPABASE ---
                        repo = EquipoRepository()
                        repo.actualizar_equipo(equipo_encontrado)
                        # --- PERSISTENCIA SUPABASE ---
                        repo = EquipoRepository()
                        repo.actualizar_equipo(equipo_encontrado)

                        st.success("✅ Reporte registrado y guardado en la Nube.")

                        # --- ENTREGABLE 7: GENERACIÓN DEL PDF TIPO TICKET ---
                        try:
                            # 1. Construimos el PDF en RAM
                            builder = ReporteBuilder()
                            builder.agregar_titulo("TICKET DE REPORTE - ESTUDIANTE")
                            texto_ia_pdf = dictamen_ia[:55] + "..." if len(dictamen_ia) > 55 else dictamen_ia
                            datos_ticket = {
                                "ID Activo": equipo_encontrado.id_activo,
                                "Equipo": equipo_encontrado.modelo,
                                "Ubicación": lab_ubicacion,
                                "Reportado por": usuario,
                                "Descripción": descripcion,
                                "Diagnóstico IA": texto_ia_pdf
                            }
                            builder.agregar_cuerpo(datos_ticket)
                            
                            # Mensaje de cierre
                            builder.pdf.set_font("helvetica", "I", 10)
                            builder.pdf.cell(0, 10, "Este comprobante confirma el registro de su reporte. Gracias por ayudar a la FIEE.", new_x="LMARGIN", new_y="NEXT")
                            
                            # 2. Obtenemos los bytes del archivo
                            pdf_bytes = builder.compilar_pdf()
                            
                            # 3. Mostramos el botón de descarga
                            st.download_button(
                                label="⬇️ Descargar Comprobante de Reporte (PDF)",
                                data=pdf_bytes,
                                file_name=f"Comprobante_{equipo_encontrado.id_activo}.pdf",
                                mime="application/pdf",
                                type="primary"
                            )
                        except Exception as e:
                            st.error(f"Error al generar el PDF: {e}")
                        # ---------------------------------------------------
                        
                        # --- LIMPIEZA DE MEMORIA PARA ACTUALIZAR EL DASHBOARD ---
                        st.session_state.trigger = st.session_state.get('trigger', 0) + 1
                        st.cache_data.clear()
                        if 'db_laboratorios' in st.session_state:
                            del st.session_state['db_laboratorios']
                        
        elif qr_input:
            st.error("❌ Código QR no encontrado en la base de datos.")