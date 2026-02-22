from src.repositories.equipo_repository import EquipoRepository
from src.models.concretos import MotorInduccion, Osciloscopio, Multimetro
from src.logical.estrategias import DesgasteLineal, DesgasteExponencial

def cargar_ejemplos():
    repo = EquipoRepository()
    estrategia_base = DesgasteLineal()
    
    print("⏳ Conectando a Supabase para cargar datos de ejemplo...")

    # --- DATOS DE EJEMPLO ORGANIZADOS POR LABORATORIO ---
    
    # 1. Laboratorio de Control
    mu1 = Multimetro("FLU-01", "Fluke 87V", "2024-01-20", "0.05%", True, estrategia_base)
    mu1.ubicacion = "Laboratorio de Control"

    # 2. Laboratorio de Circuitos
    
    o2 = Osciloscopio("OSC-Cir-02", "Keysight EDUX1002A", "2023-11-05", "70MHz", estrategia_base)
    o2.ubicacion = "Laboratorio de Circuitos"

    o1 = Osciloscopio("OSC-C-01", "Tektronix TBS1052", "2022-08-15", "50MHz", estrategia_base)
    o1.ubicacion = "Laboratorio de Circuitos"
    # 3. Laboratorio de Máquinas (Potencia)
    m2 = MotorInduccion("MOT-P-02", "WEG W22", "2021-03-10", "10HP", "440V", 3600, estrategia_base)
    m2.ubicacion = "Laboratorio de Máquinas"

    m1 = MotorInduccion("MOT-C-01", "Siemens 1LE1", "2023-05-10", "5HP", "220V", 1800, estrategia_base)
    m1.ubicacion = "Laboratorio de Máquinas" # Forzamos la ubicación
    # Simulamos un desgaste avanzado en este
    m2.historial_incidencias.append({"fecha": "2024-02-01", "detalle": "Ruido en rodamientos"})

    lista_equipos = [m1, o1, mu1, o2, m2]

    # --- GUARDADO EN BUCLE ---
    for equipo in lista_equipos:
        # Usamos el repositorio para guardar (esto mandará los datos a Supabase con la ubicación correcta)
        repo.guardar_equipo(equipo)
    print("✅ ¡Datos de ejemplo cargados! Ahora ve a tu Dashboard.")
if __name__ == "__main__":
    cargar_ejemplos()