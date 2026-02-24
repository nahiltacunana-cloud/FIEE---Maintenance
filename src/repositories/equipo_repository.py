import os
from supabase import create_client
from dotenv import load_dotenv

class EquipoRepository:
    """
    Repositorio encargado de la persistencia de datos en Supabase.
    Implementa operaciones CRUD para la entidad Equipo.
    """
    def __init__(self):
        
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            self.client = None
        else:
            self.client = create_client(url, key)

    def guardar_equipo(self, equipo):
        """Almacena un nuevo equipo con sus detalles técnicos dinámicos."""
        if not self.client: return

        detalles = {}
        # Extracción dinámica de atributos según el tipo de equipo (Patrón Metadata)
        if hasattr(equipo, 'hp'): detalles['hp'] = equipo.hp
        if hasattr(equipo, 'voltaje'): detalles['voltaje'] = equipo.voltaje
        if hasattr(equipo, 'rpm'): detalles['rpm'] = equipo.rpm
        if hasattr(equipo, 'ancho_banda'): detalles['ancho_banda'] = equipo.ancho_banda
        if hasattr(equipo, 'precision'): detalles['precision'] = equipo.precision
    
        ubicacion_final = getattr(equipo, 'ubicacion', 'Sin Ubicación')
        datos_para_nube = {
            "id_activo": equipo.id_activo,
            "modelo": equipo.modelo,
            "tipo_equipo": type(equipo).__name__,
            "fecha_compra": str(equipo.fecha_compra),
    
            "ubicacion": getattr(equipo, 'ubicacion', 'Sin Ubicación'), 
            "estrategia_nombre": "DesgasteLineal" if "Lineal" in str(type(equipo.estrategia_desgaste)) else "DesgasteExponencial",
            "detalles_tecnicos": detalles,
            "historial_incidencias": equipo.historial_incidencias
}
        try:
            self.client.table("equipos").insert(datos_para_nube).execute()
        except Exception as e:
            print(f"Error al registrar equipo en BD: {e}")

    def leer_todos(self):
        """Recupera la lista completa de activos desde la nube."""
        if not self.client: return []
        try:
            response = self.client.table("equipos").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error de lectura en base de datos: {e}")
            return []

    def actualizar_equipo(self, equipo):
        """Actualiza un equipo existente asegurando que los datos sean compatibles con Supabase"""
        if not self.client: 
            return
        
        # Normalización del estado (Enum a String)
        estado_final = equipo.estado.name if hasattr(equipo.estado, 'name') else str(equipo.estado)

        # Sanitización del historial para compatibilidad con JSONB
        historial_seguro = []
        for evento in equipo.historial_incidencias:
            if isinstance(evento, dict):
                historial_seguro.append(evento)
            elif hasattr(evento, '__dict__'):
                historial_seguro.append(evento.__dict__)
            else:
                historial_seguro.append(str(evento))

        datos_actualizados = {
            "historial_incidencias": historial_seguro,
            "estrategia_nombre": "DesgasteLineal" if "Lineal" in str(type(equipo.estrategia_desgaste)) else "DesgasteExponencial",
            "estado": estado_final
        }
        
        try:
            self.client.table("equipos").update(datos_actualizados).eq("id_activo", equipo.id_activo).execute()
        except Exception as e:
            print(f"Error al actualizar equipo {equipo.id_activo}: {e}")