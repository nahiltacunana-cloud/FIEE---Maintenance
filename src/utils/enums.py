from enum import Enum

class EstadoEquipo(Enum):
    OPERATIVO = "Operativo"
    REPORTADO_CON_FALLA = "Reportado con Falla"
    EN_MANTENIMIENTO = "En Mantenimiento"
    FALLA = "En Falla"
    BAJA = "Dado de Baja"