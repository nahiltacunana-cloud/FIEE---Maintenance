from src.models.equipo import Equipo
from src.interfaces.mixins import IdentificableQR, AnalizadorPredictivo

# --- TIPO 1: ELECTRÓNICA DE LABORATORIO ---
class Osciloscopio(Equipo, IdentificableQR):
    """
    Representa equipos de medición de señales eléctricas.
    Hereda capacidades de identificación por QR.
    """
    def __init__(self, id_activo, modelo, fecha, ancho_banda, estrategia):
        super().__init__(id_activo, modelo, fecha, estrategia)
        self.ancho_banda = ancho_banda
    

# --- TIPO 2: INSTRUMENTACIÓN PORTÁTIL ---
class Multimetro(Equipo, IdentificableQR):
    """
    Instrumentación portátil para medición de magnitudes eléctricas.
    """
    def __init__(self, id_activo, modelo, fecha, precision, es_digital: bool, estrategia):
        super().__init__(id_activo, modelo, fecha, estrategia)
        self.precision = precision
        self.es_digital = es_digital

# --- TIPO 3: POTENCIA Y CONTROL ---
class MotorInduccion(Equipo, IdentificableQR, AnalizadorPredictivo):
    """
    Equipos de potencia que requieren análisis predictivo de vibraciones.
    Utiliza herencia múltiple para combinar Mixins de QR y Predicción.
    """
    def __init__(self, id_activo, modelo, fecha, hp, voltaje, rpm, estrategia):
        super().__init__(id_activo, modelo, fecha, estrategia)
        self.hp = hp
        self.voltaje = voltaje
        self.rpm = rpm