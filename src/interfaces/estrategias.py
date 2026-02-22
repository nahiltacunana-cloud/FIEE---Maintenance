from abc import ABC, abstractmethod

class IEstrategiaDesgaste(ABC):
    """
    Interfaz para el Patrón Strategy.
    Define el contrato que deben seguir todas las formas de cálculo de obsolescencia.
    """
    @abstractmethod
    def calcular(self, fecha_compra: str) -> float:
        pass