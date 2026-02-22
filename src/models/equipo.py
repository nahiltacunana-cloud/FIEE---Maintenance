from datetime import datetime
import sys
import os

# Agregamos la ruta raíz para evitar errores de importación
sys.path.append(os.getcwd())

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
        Calcula el desgaste considerando la estrategia matemática, 
        el historial de la IA y el estado de baja.
        """
        # 1. Caso base: Sin estrategia
        if not hasattr(self, 'estrategia_desgaste') or self.estrategia_desgaste is None:
            return 0.0
            
        # 2. Cálculo matemático inicial (por tiempo)
        valor_teorico = self.estrategia_desgaste.calcular(self.fecha_compra)
        
        # 3. Verificación de Seguridad: Estado de Baja
        # Si el equipo ya está marcado como de baja (por la IA o manual), forzamos el 1.0
        estado_str = str(self.estado.value).upper() if hasattr(self.estado, 'value') else str(self.estado).upper()
        if "BAJA" in estado_str:
            return 1.0

        # 4. Verificación de Seguridad: Historial de IA
        historial = getattr(self, 'historial_incidencias', [])
        if historial: 
            ultimo_ticket = historial[-1]
            # Revisamos tanto el detalle como el dictamen de la IA
            texto_analisis = (str(ultimo_ticket.get('dictamen_ia', '')) + 
                             str(ultimo_ticket.get('detalle', ''))).upper()
            
            # Si hay cualquier rastro de daño crítico en el último reporte
            if any(palabra in texto_analisis for palabra in ["ALERTA", "CARBONIZADA", "CRITICO", "QUEMADO"]):
                return 0.98 # Lo dejamos casi al tope para que se vea rojo

        # 5. Si todo está bien, devolvemos el valor teórico sin pasar del 100%
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