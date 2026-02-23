import io
from fpdf import FPDF

class PlantillaFIEE(FPDF):
    """Clase interna para manejar la cabecera y pie de página de todas las hojas."""
    def header(self):
        self.set_font("helvetica", "B", 14)
        # Título centrado
        self.cell(0, 10, "Facultad de Ingeniería Eléctrica y Electrónica - UNI", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("helvetica", "I", 10)
        self.cell(0, 8, "Sistema Automatizado de Mantenimiento", align="C", new_x="LMARGIN", new_y="NEXT")
        self.line(10, 30, 200, 30)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

class ReporteBuilder:
    def __init__(self):
        """Inicializa el documento PDF vacío."""
        self.pdf = PlantillaFIEE()
        self.pdf.add_page()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        
    def agregar_titulo(self, titulo="REPORTE TÉCNICO DE INCIDENCIA"):
        self.pdf.set_font("helvetica", "B", 16)
        self.pdf.cell(0, 15, titulo, align="C", new_x="LMARGIN", new_y="NEXT")
        self.pdf.ln(5)
        return self

    def agregar_cuerpo(self, datos_equipo: dict):
        """Añade los datos técnicos usando un diccionario."""
        self.pdf.set_font("helvetica", "B", 12)
        self.pdf.cell(0, 10, "1. Datos del Activo:", new_x="LMARGIN", new_y="NEXT")
        
        self.pdf.set_font("helvetica", "", 11)
        for clave, valor in datos_equipo.items():
            self.pdf.cell(50, 8, f"{clave}:", border=1, fill=False)
            self.pdf.cell(0, 8, f" {valor}", border=1, new_x="LMARGIN", new_y="NEXT")
        
        self.pdf.ln(5)
        return self

    def agregar_evidencia(self, imagen_bytes):
        """Incrusta la foto desde la memoria RAM (sin guardarla en disco)."""
        if imagen_bytes:
            self.pdf.set_font("helvetica", "B", 12)
            self.pdf.cell(0, 10, "2. Evidencia Visual:", new_x="LMARGIN", new_y="NEXT")
            try:
                # FPDF2 permite leer imágenes directamente de bytes
                imagen_io = io.BytesIO(imagen_bytes.getvalue())
                self.pdf.image(imagen_io, w=100)
            except Exception as e:
                self.pdf.set_font("helvetica", "I", 10)
                self.pdf.cell(0, 10, f"(Error al cargar imagen: {str(e)})", new_x="LMARGIN", new_y="NEXT")
            self.pdf.ln(5)
        return self

    def agregar_firmas(self):
        """Añade el footer para las firmas correspondientes."""
        self.pdf.ln(30)
        self.pdf.set_font("helvetica", "B", 10)
        # Líneas de firma
        self.pdf.cell(90, 10, "_______________________", align="C")
        self.pdf.cell(90, 10, "_______________________", align="C", new_x="LMARGIN", new_y="NEXT")
        # Textos debajo de la línea
        self.pdf.cell(90, 5, "Firma del Estudiante/Técnico", align="C")
        self.pdf.cell(90, 5, "Sello y Conformidad FIEE", align="C")
        return self

    def compilar_pdf(self) -> bytes:
        """Construye el PDF y lo devuelve como binario para Streamlit."""
        # output() sin parámetros en FPDF2 devuelve un bytearray
        return bytes(self.pdf.output())