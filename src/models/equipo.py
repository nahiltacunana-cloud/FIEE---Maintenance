import sys
import os
from datetime import datetime, timedelta
from src.utils.enums import EstadoEquipo

# Asegurar que el sistema reconozca la ruta raíz para imports
sys.path.append(os.getcwd())

try:
    from src.interfaces.estrategias import IEstrategiaDesgaste
except ImportError:
    # Fallback de seguridad para evitar que el sistema colapse si falla el import
    IEstrategiaDesgaste = object

class Equipo:
    """
    Clase base que representa un activo de laboratorio.
    Implementa el Patrón Strategy para obsolescencia y lógica de supervisión automática.
    """
    def __init__(self, id_activo: str, modelo: str, fecha_compra: str, estrategia):
        self.id_activo = id_activo
        self.modelo = modelo
        self.fecha_compra = fecha_compra
        self.estado = EstadoEquipo.OPERATIVO
        self.historial_incidencias = []
        self.estrategia_desgaste = estrategia

    def calcular_obsolescencia(self) -> float:
        """
        Calcula el desgaste basándose en la estrategia matemática y reglas de negocio.
        """
        if not hasattr(self, 'estrategia_desgaste') or self.estrategia_desgaste is None:
            return 0.0
            
        valor_teorico = self.estrategia_desgaste.calcular(self.fecha_compra)
        
        estado_actual = str(self.estado.value).upper() if hasattr(self.estado, 'value') else str(self.estado).upper()
        # Reglas críticas de negocio
        if "BAJA" in estado_actual:
            return 1.0 

        if "FALLA" in estado_actual:
            return 0.98 

        return min(valor_teorico, 1.0)
    
    def cambiar_estrategia(self, nueva_estrategia):
        """Permite la variación del algoritmo de cálculo en tiempo de ejecución."""
        self.estrategia_desgaste = nueva_estrategia

    def registrar_incidencia(self, descripcion: str):
        """Añade un nuevo evento al historial con marca de tiempo."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.historial_incidencias.append({"fecha": fecha, "detalle": descripcion})

    def to_dict(self):
        """Serializa el objeto para almacenamiento en base de datos."""
        return {
            "id": self.id_activo,
            "modelo": self.modelo,
            "fecha_compra": self.fecha_compra,
            "estado": self.estado.value,
            "indice_obsolescencia": self.calcular_obsolescencia(),
            "incidencias": self.historial_incidencias
        }
    def verificar_umbral_quejas(self) -> bool:
        """
        Supervisor automático: Bloquea el equipo si recibe 3+ quejas en 7 días.
        Reinicia el conteo si detecta un mantenimiento previo (REINGRESO/ALTA).
        """
        estado_actual = str(self.estado.value).upper() if hasattr(self.estado, 'value') else str(self.estado).upper()
        if estado_actual in ["EN_MANTENIMIENTO", "FALLA", "BAJA"]:
            return False 

        hace_una_semana = datetime.now() - timedelta(days=7)
        contador_quejas = 0

        historial = getattr(self, 'historial_incidencias', [])
        for incidencia in historial:
            detalle = incidencia.get('detalle', '').upper()
            if "REINGRESO" in detalle or "ALTA" in detalle:
                contador_quejas = 0
                continue
            fecha_str = incidencia.get('fecha', '')
            try:
                # Extraemos solo el YYYY-MM-DD (los primeros 10 caracteres)
                if len(fecha_str) >= 10:
                    fecha_inc = datetime.strptime(fecha_str[:10], "%Y-%m-%d")
                    # Si la queja es de esta semana, la contamos
                    if fecha_inc >= hace_una_semana:
                        contador_quejas += 1
            except Exception:
                pass 

        if contador_quejas >= 3:
            if hasattr(self.estado, 'name'):
                self.estado = "EN_MANTENIMIENTO" 
            else:
                self.estado = "EN_MANTENIMIENTO"
            
            self.historial_incidencias.append({
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "detalle": f"ALERTA DEL SISTEMA: El equipo superó el umbral de quejas ({contador_quejas} reportes en 7 días). Bloqueado por precaución."
            })
            return True
            
        return False