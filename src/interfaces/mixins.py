import random

class IdentificableQR:
    def generar_qr(self) -> str:
        codigo = f"QR-{id(self)}"
        return f"📡 [QR SYSTEM] Identificado activo: {codigo}"

class AnalizadorPredictivo:
    def predecir_fallo(self) -> str:
        probabilidad = random.randint(15, 85)
        return f"🔮 [IA] Probabilidad de fallo: {probabilidad}% (Vibración anómala detectada)"

class InspectorVisual:
    def analizar_foto(self, ruta_imagen: str) -> dict:
        # Simulamos procesamiento de imagen
        return {"status": "OK", "detalles": "Lente frontal limpio, sin grietas visibles."}