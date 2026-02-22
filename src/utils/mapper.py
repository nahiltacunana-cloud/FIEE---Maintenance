from src.equipo_factory import EquipoFactory
from src.utils.enums import EstadoEquipo

class EquipoMapper:
    """
    Implementación del patrón Data Mapper.
    Se encarga de transformar diccionarios JSON a objetos de dominio de la FIEE.
    """
    
    def __init__(self, estrategia_lineal, estrategia_exponencial):
        # Inyectamos las estrategias al instanciar la clase
        self.estr_lineal = estrategia_lineal
        self.estr_expo = estrategia_exponencial

    def mapear_lista(self, data_list):
        """
        Recibe una lista de diccionarios y devuelve una lista de objetos.
        """
        objetos_convertidos = []
        
        for item in data_list:
            nuevo_obj = self._mapear_item(item)
            if nuevo_obj:
                objetos_convertidos.append(nuevo_obj)
                
        return objetos_convertidos

    def _mapear_item(self, item):
        """
        Método privado que encapsula la lógica de convertir UN solo elemento.
        """
        tipo = item.get("tipo_equipo")
        detalles = item.get("detalles_tecnicos", {})

        # Selección de estrategia usando las propiedades inyectadas
        nombre_est = item.get("estrategia_nombre", "Lineal")
        est_obj = self.estr_lineal if "Lineal" in nombre_est else self.estr_expo

        try:
            # Uso de nuestro Factory
            nuevo_obj = EquipoFactory.crear_equipo(
                tipo,
                item,
                detalles,
                est_obj
            )

            # Asignación de datos comunes a todos los equipos
            nuevo_obj.ubicacion = item.get("ubicacion", "Sin Asignar")

            estado_str = item.get("estado", "OPERATIVO")
            if hasattr(EstadoEquipo, estado_str):
                nuevo_obj.estado = getattr(EstadoEquipo, estado_str)

            nuevo_obj.historial_incidencias = item.get("historial_incidencias", [])

            return nuevo_obj

        except Exception as e:
            print(f"❌ Error mapeando objeto {item.get('id_activo')}: {e}")
            return None