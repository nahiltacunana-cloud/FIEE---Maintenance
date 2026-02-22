from src.logical.estrategias import DesgasteLineal, DesgasteExponencial
from src.models.concretos import Osciloscopio

def verificar_entrega():
    print("=== SISTEMA DE VERIFICACIÓN: ENTREGABLE 3 ===\n")

    # 1. Instanciar las estrategias (Hito 4)
    lineal = DesgasteLineal()
    exponencial = DesgasteExponencial()

    # 2. Crear equipos inyectando la estrategia por constructor (Hito 3)
    # Usamos una fecha de hace 4 años (2022) para ver el desgaste
    print("Creando equipos con estrategias inyectadas...")
    
    osc_basico = Osciloscopio("OSC-01", "Rigol 1000", "2022-01-01", "50MHz", lineal)
    osc_avanzado = Osciloscopio("OSC-02", "Keysight X", "2022-01-01", "200MHz", exponencial)

    # 3. Calcular y mostrar resultados
    print(f"\n[EQUIPO 1 - LINEAL]")
    print(f"Modelo: {osc_basico.modelo}")
    print(f"Índice de Obsolescencia: {osc_basico.calcular_obsolescencia()}")

    print(f"\n[EQUIPO 2 - EXPONENCIAL]")
    print(f"Modelo: {osc_avanzado.modelo}")
    print(f"Índice de Obsolescencia: {osc_avanzado.calcular_obsolescencia()}")

    # 4. Demostración de cambio dinámico (Opcional, muy pro)
    print("\nCambiando estrategia de Equipo 2 a Lineal en tiempo de ejecución...")
    osc_avanzado.cambiar_estrategia(lineal)
    print(f"Nuevo índice (Equipo 2 ahora lineal): {osc_avanzado.calcular_obsolescencia()}")

if __name__ == "__main__":
    try:
        verificar_entrega()
    except Exception as e:
        print(f"Error en la verificación: {e}")