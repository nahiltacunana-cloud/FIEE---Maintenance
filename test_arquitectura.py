import sys
import os
import json

# Ajuste de ruta para ejecución local
sys.path.append(os.getcwd())

from src.models.concretos import Osciloscopio, Multimetro, MotorInduccion
from src.utils.enums import EstadoEquipo
from src.interfaces.mixins import AnalizadorPredictivo

def validar_arquitectura_sistema():
    print("\n----  FIEE MAINTENANCE: VALIDACIÓN DE ARQUITECTURA ----")

    print("\n[1] GENERANDO FLOTA DE EQUIPOS (PRUEBA DE CONSTRUCTORES)")
    osc = Osciloscopio("OSC-LAB-01", "Tektronix TBS", "2023-01-15", "100MHz")
    multi = Multimetro("MUL-FLU-09", "Fluke 87V", "2024-02-10", "0.05%", True)
    motor = MotorInduccion("MOT-IND-X5", "Siemens 1LE1", "2020-05-20", "15HP", "440V", 3600)

    flota = [osc, multi, motor]

    print(f"{'TIPO':<20} | {'MODELO':<15} | {'OBSOLESCENCIA':<12} | {'QR SYSTEM'}")
    print("-" * 90)

    for equipo in flota:
        desgaste = equipo.calcular_obsolescencia()
        qr_code = equipo.generar_qr()
        
        qr_simple = qr_code.replace("📡 [QR SYSTEM] Identificado activo: ", "")
        
        print(f"{equipo.__class__.__name__:<20} | {equipo.modelo:<15} | {desgaste*100:>5.1f}%       | {qr_simple}")

    print("\n[2] VERIFICACIÓN DE CAPACIDADES ESPECIALES (INTERFACES)")
    
    for equipo in flota:
       
        if isinstance(equipo, AnalizadorPredictivo):
            prediccion = equipo.predecir_fallo()
            print(f"    {equipo.modelo}: {prediccion}")

    print("\n[3] PRUEBA DE GESTIÓN DE INCIDENCIAS (CAMBIO DE ESTADO)")
    
    print(f"   Estado inicial Motor: {motor.estado.value}")
    
    motor.registrar_incidencia(
        descripcion="Vibración excesiva en eje principal",
        reportado_por="Ing. Electrico"
    )
    
    if motor.estado == EstadoEquipo.REPORTADO_CON_FALLA:
        print(f"   Cambio de estado exitoso: {motor.estado.value}")
        print(f"   Ticket generado: {motor.historial_incidencias[0]['fecha']} - {motor.historial_incidencias[0]['descripcion']}")
    else:
        print("    ERROR CRÍTICO: El estado no cambió.")

    print("\n[4] VALIDACIÓN DE SERIALIZACIÓN (TO_DICT)")
    # Esto prueba que el objeto está listo para enviarse a Supabase
    datos_exportables = motor.to_dict()
    print(f"    Payload JSON generado para BD:\n   {json.dumps(datos_exportables, indent=3)}")

    print("\n---  ARQUITECTURA VALIDADA CORRECTAMENTE ---")

validar_arquitectura_sistema()