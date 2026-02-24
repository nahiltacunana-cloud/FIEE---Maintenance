from src.equipo_factory import EquipoFactory
from src.utils.enums import EstadoEquipo

class EquipoMapper:
    """
    Implementación del patrón Data Mapper.
    Transforma estructuras JSON de la base de datos en instancias de clases del dominio.
    """
    def __init__(self, estrategia_lineal, estrategia_exponencial):
        """Inyecta las estrategias disponibles para el cálculo de obsolescencia."""
        self.estr_lineal = estrategia_lineal
        self.estr_expo = estrategia_exponencial

    def mapear_lista(self, data_list):
        """Convierte una colección de registros en una lista de objetos Equipo."""
        objetos_convertidos = []
        
        for item in data_list:
            nuevo_obj = self._mapear_item(item)
            if nuevo_obj:
                objetos_convertidos.append(nuevo_obj)
                
        return objetos_convertidos

    def _mapear_item(self, item):
        """Lógica interna de transformación de un registro individual."""
        tipo = item.get("tipo_equipo")
        detalles = item.get("detalles_tecnicos", {})

        # Determinación de la estrategia inyectada
        nombre_est = item.get("estrategia_nombre", "Lineal")
        est_obj = self.estr_lineal if "Lineal" in nombre_est else self.estr_expo

        try:
            # Creación mediante Factory Pattern
            nuevo_obj = EquipoFactory.crear_equipo(
                tipo,
                item,
                detalles,
                est_obj
            )

            # Reconstrucción de atributos persistidos
            nuevo_obj.ubicacion = item.get("ubicacion", "Sin Asignar")
            # Asignación segura del estado desde el Enum
            estado_str = item.get("estado", "OPERATIVO")
            if hasattr(EstadoEquipo, estado_str):
                nuevo_obj.estado = getattr(EstadoEquipo, estado_str)
            else:
                # Fallback por seguridad si el texto no coincide exactamente
                nuevo_obj.estado = EstadoEquipo.OPERATIVO
            nuevo_obj.historial_incidencias = item.get("historial_incidencias", [])

            return nuevo_obj

        except Exception as e:
            # Log de error silencioso para producción
            print(f"Log: Error en mapeo de activo {item.get('id_activo', 'N/A')}: {e}")
            return None