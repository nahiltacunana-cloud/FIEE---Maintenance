from src.models.concretos import MotorInduccion, Osciloscopio, Multimetro

class EquipoFactory:
    """
    Fábrica central para crear cualquier tipo de equipo usando constructores dinámicos.
    """

    # Diccionario que mapea el nombre del equipo con su función constructora
    _constructores = {
        "MotorInduccion": lambda item, det, est: MotorInduccion(
            item["id_activo"], item["modelo"], item["fecha_compra"],
            det.get("hp"), det.get("voltaje"), det.get("rpm"), est
        ),
        "Osciloscopio": lambda item, det, est: Osciloscopio(
            item["id_activo"], item["modelo"], item["fecha_compra"],
            det.get("ancho_banda"), est
        ),
        "Multimetro": lambda item, det, est: Multimetro(
            item["id_activo"], item["modelo"], item["fecha_compra"],
            det.get("precision"), det.get("es_digital", True), est
        )
    }

    @classmethod
    def registrar_tipo(cls, nombre, funcion_constructora):
        """
        Permite inyectar nuevos equipos dinámicamente desde fuera de la clase.
        """
        cls._constructores[nombre] = funcion_constructora

    @classmethod
    def crear_equipo(cls, tipo, item, detalles, estrategia):
        """
        Busca el constructor en el diccionario y ejecuta la creación instantáneamente.
        """
        constructor = cls._constructores.get(tipo)

        if not constructor:
            raise ValueError(f"Tipo de equipo no soportado por la fábrica: {tipo}")

        # Ejecutamos la función constructora pasándole los datos
        return constructor(item, detalles, estrategia)