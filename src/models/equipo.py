import sys
import os

# Agregamos la ruta raíz para evitar errores de importación
sys.path.append(os.getcwd())
from datetime import datetime, timedelta
from src.utils.enums import EstadoEquipo

try:
    from src.interfaces.estrategias import IEstrategiaDesgaste
except ImportError:
    IEstrategiaDesgaste = object # Fallback para que no rompa si falla el import

class Equipo:
    def __init__(self, id_activo: str, modelo: str, fecha_compra: str, estrategia):
        """
        Constructor que implementa el Patrón Strategy.
        :param estrategia: Instancia de DesgasteLineal o DesgasteExponencial
        """
        self.id_activo = id_activo
        self.modelo = modelo
        self.fecha_compra = fecha_compra
        self.estado = EstadoEquipo.OPERATIVO
        self.historial_incidencias = []
        self.estrategia_desgaste = estrategia

    def calcular_obsolescencia(self) -> float:
        """
        Calcula el desgaste considerando la estrategia matemática y el ESTADO actual del equipo.
        """
        # 1. Caso base: Si no tiene estrategia asignada, es 0%
        if not hasattr(self, 'estrategia_desgaste') or self.estrategia_desgaste is None:
            return 0.0
            
        # 2. Cálculo matemático base (por tiempo/años desde la compra)
        valor_teorico = self.estrategia_desgaste.calcular(self.fecha_compra)
        
        # Obtenemos el estado actual en formato texto de forma segura
        estado_actual = str(self.estado.value).upper() if hasattr(self.estado, 'value') else str(self.estado).upper()
        
        # 3. REGLA 1: Si el equipo está DADO DE BAJA, está al 100% de obsolescencia
        if "BAJA" in estado_actual:
            return 1.0 

        # 4. REGLA 2: Si el equipo está en FALLA, lo forzamos al 98% (Rojo crítico)
        if "FALLA" in estado_actual:
            return 0.98 

        # 5. REGLA 3: Si está Operativo o En Mantenimiento, usamos la matemática
        # min(valor_teorico, 1.0) asegura que la matemática nunca devuelva más de 100%
        return min(valor_teorico, 1.0)
    
    def cambiar_estrategia(self, nueva_estrategia):
        """
        Permite cambiar la estrategia de cálculo en tiempo de ejecución.
        """
        self.estrategia_desgaste = nueva_estrategia

    def registrar_incidencia(self, descripcion: str):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.historial_incidencias.append({"fecha": fecha, "detalle": descripcion})

    def to_dict(self):
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
        Verifica si el equipo tiene 3 o más reportes en los últimos 7 días.
        Si es así, lo pasa a Mantenimiento automáticamente.
        Retorna True si cambió el estado, False si todo sigue normal.
        """
        # Si el equipo ya está roto o de baja, no hacemos nada
        estado_actual = str(self.estado.value).upper() if hasattr(self.estado, 'value') else str(self.estado).upper()
        if estado_actual in ["EN_MANTENIMIENTO", "FALLA", "BAJA"]:
            return False 

        # Calculamos la fecha de hace 7 días
        hace_una_semana = datetime.now() - timedelta(days=7)
        contador_quejas = 0

        # Revisamos el historial
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
                pass # Si falla al leer la fecha de algún registro viejo, lo ignoramos

        # LA REGLA DE ORO: Si hay 3 o más quejas...
        if contador_quejas >= 3:
            # Forzamos el estado a mantenimiento preventivo
            if hasattr(self.estado, 'name'):
                self.estado = "EN_MANTENIMIENTO" # O EstadoEquipo.EN_MANTENIMIENTO.name
            else:
                self.estado = "EN_MANTENIMIENTO"
            
            # Dejamos un registro automático del sistema
            self.historial_incidencias.append({
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "detalle": f"ALERTA DEL SISTEMA: El equipo superó el umbral de quejas ({contador_quejas} reportes en 7 días). Bloqueado por precaución."
            })
            return True # Avisamos que hubo un cambio automático
            
        return False