import math
from datetime import datetime
from src.interfaces.estrategias import IEstrategiaDesgaste 

class DesgasteLineal(IEstrategiaDesgaste):
    """
    Estrategia de cálculo basada en una depreciación constante anual.
    Ideal para mobiliario o equipos mecánicos simples.
    """
    def calcular(self, fecha_compra: str) -> float:
        anio_compra = int(fecha_compra.split("-")[0])
        anio_actual = datetime.now().year
        t = max(1, anio_actual - anio_compra)
        
        return round(min(t * 0.05, 1.0), 2)

class DesgasteExponencial(IEstrategiaDesgaste):
    """
    Estrategia para equipos con obsolescencia tecnológica acelerada.
    Aplica una curva exponencial de desgaste.
    """
    def calcular(self, fecha_compra: str) -> float:
        anio_compra = int(fecha_compra.split("-")[0])
        anio_actual = datetime.now().year
        t = max(1, anio_actual - anio_compra)
        
        indice = (math.exp(0.2 * t) - 1) / 10
        return round(min(indice, 1.0), 2)
