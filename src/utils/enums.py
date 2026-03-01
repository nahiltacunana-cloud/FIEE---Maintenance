from enum import Enum

class EstadoEquipo(Enum):
    """
    Define los estados vitales del ciclo de vida de un activo.
    """
    OPERATIVO = "Operativo"
    EN_MANTENIMIENTO = "En Mantenimiento"
    FALLA = "En Falla"
    BAJA = "Dado de Baja"
    REPORTADO = "Reportado"
    # Este se puede mantener por compatibilidad con registros viejos
    REPORTADO_CON_FALLA = "Reportado con Falla"