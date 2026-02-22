import os
from supabase import create_client
from dotenv import load_dotenv

class EquipoRepository:
    def __init__(self):
        
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print("⚠️ ADVERTENCIA: No se encontraron las claves en .env")
            self.client = None
        else:
            self.client = create_client(url, key)

    def guardar_equipo(self, equipo):
        """Guarda un equipo NUEVO en Supabase"""
        if not self.client: return
        
        # 1. Preparar los Detalles Técnicos (JSONB)
        detalles = {}
        # Extraemos atributos específicos según el tipo
        if hasattr(equipo, 'hp'): detalles['hp'] = equipo.hp
        if hasattr(equipo, 'voltaje'): detalles['voltaje'] = equipo.voltaje
        if hasattr(equipo, 'rpm'): detalles['rpm'] = equipo.rpm
        if hasattr(equipo, 'ancho_banda'): detalles['ancho_banda'] = equipo.ancho_banda
        if hasattr(equipo, 'precision'): detalles['precision'] = equipo.precision
    

    # Si el objeto no tiene el atributo, por defecto usa 'Sin Ubicación'
        ubicacion_final = getattr(equipo, 'ubicacion', 'Sin Ubicación')
        datos_para_nube = {
            "id_activo": equipo.id_activo,
            "modelo": equipo.modelo,
            "tipo_equipo": type(equipo).__name__,
            "fecha_compra": str(equipo.fecha_compra),
    
    # --- CAMBIO CRÍTICO: Usar la ubicación real del equipo ---
            "ubicacion": getattr(equipo, 'ubicacion', 'Sin Ubicación'), 
            "estrategia_nombre": "DesgasteLineal" if "Lineal" in str(type(equipo.estrategia_desgaste)) else "DesgasteExponencial",
            "detalles_tecnicos": detalles,
            "historial_incidencias": equipo.historial_incidencias
}
        try:
            self.client.table("equipos").insert(datos_para_nube).execute()
            print(f"✅ Guardado en {ubicacion_final}: {equipo.modelo}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def leer_todos(self):
        """Descarga TODOS los equipos de la nube"""
        if not self.client: return []
        try:
            response = self.client.table("equipos").select("*").execute()
            return response.data # Devuelve una lista de diccionarios
        except Exception as e:
            print(f"❌ Error leyendo base de datos: {e}")
            return []

    def actualizar_equipo(self, equipo):
        """Actualiza un equipo existente (Para cuando agregas reportes o cambias estrategia)"""
        if not self.client: return

        datos_actualizados = {
            "historial_incidencias": equipo.historial_incidencias,
            "estrategia_nombre": "DesgasteLineal" if "Lineal" in str(type(equipo.estrategia_desgaste)) else "DesgasteExponencial"
        }
        
        try:
            # Busca por id_activo y actualiza
            self.client.table("equipos").update(datos_actualizados).eq("id_activo", equipo.id_activo).execute()
            print(f"✅ Actualizado: {equipo.modelo}")
        except Exception as e:
            print(f"❌ Error actualizando: {e}")