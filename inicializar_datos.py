import sys
import os

sys.path.append(os.getcwd())

from src.repositories.equipo_repository import EquipoRepository
from src.models.concretos import MotorInduccion, Osciloscopio, Multimetro
from src.logical.estrategias import DesgasteLineal

class InicializadorBaseDatos:
    """
    Clase encargada de poblar (Seeder) la base de datos inicial.
    Demuestra encapsulamiento y responsabilidad única.
    """
    
    def __init__(self):
        self.repo = EquipoRepository()
        self.estrategia_base = DesgasteLineal()
        self.lista_equipos = []

    def _preparar_laboratorio_control(self):
        mu1 = Multimetro("FLU-01", "Fluke 87V", "2024-01-20", "0.05%", True, self.estrategia_base)
        mu1.ubicacion = "Laboratorio de Control"
        self.lista_equipos.append(mu1)

    def _preparar_laboratorio_circuitos(self):
        o1 = Osciloscopio("OSC-C-01", "Tektronix TBS1052", "2022-08-15", "50MHz", self.estrategia_base)
        o1.ubicacion = "Laboratorio de Circuitos"
        
        o2 = Osciloscopio("OSC-Cir-02", "Keysight EDUX1002A", "2023-11-05", "70MHz", self.estrategia_base)
        o2.ubicacion = "Laboratorio de Circuitos"
        self.lista_equipos.extend([o1, o2])

    def _preparar_laboratorio_maquinas(self):
        m1 = MotorInduccion("MOT-C-01", "Siemens 1LE1", "2023-05-10", "5HP", "220V", 1800, self.estrategia_base)
        m1.ubicacion = "Laboratorio de Máquinas"
        
        m2 = MotorInduccion("MOT-P-02", "WEG W22", "2021-03-10", "10HP", "440V", 3600, self.estrategia_base)
        m2.ubicacion = "Laboratorio de Máquinas"
        m2.historial_incidencias.append({"fecha": "2024-02-01", "detalle": "Ruido en rodamientos"})
        self.lista_equipos.extend([m1, m2])

    def ejecutar_carga(self):
        print("⏳ Preparando los objetos en memoria...")
        self._preparar_laboratorio_control()
        self._preparar_laboratorio_circuitos()
        self._preparar_laboratorio_maquinas()

        print("🚀 Conectando a Supabase para inyectar datos...")
        for equipo in self.lista_equipos:
            self.repo.guardar_equipo(equipo)


# --- Punto de Entrada Seguro ---
if __name__ == "__main__":

    PERMITIR_EJECUCION = False
    
    if PERMITIR_EJECUCION:
        seeder = InicializadorBaseDatos()
        seeder.ejecutar_carga()
    else:
        print("Tabla con datos")