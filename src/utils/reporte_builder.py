import io
from fpdf import FPDF

class PlantillaFIEE(FPDF):
    """Maneja la identidad visual institucional en cada página del PDF."""
    def header(self):
        # Logo o Texto de Encabezado
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, "Facultad de Ingeniería Eléctrica y Electrónica - UNI", align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("helvetica", "I", 10)
        self.cell(0, 8, "Sistema Automatizado de Gestión de Activos", align="C", new_x="LMARGIN", new_y="NEXT")
        
        # Línea divisoria decorativa
        self.set_draw_color(0, 80, 180) # Azul FIEE
        self.line(10, 30, 200, 30)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Documento generado automáticamente - Página {self.page_no()}/{{nb}}", align="C")

class ReporteBuilder:
    """Implementa el patrón Builder para la construcción paso a paso de reportes técnicos."""
    def __init__(self):
        self.pdf = PlantillaFIEE()
        self.pdf.alias_nb_pages() # Habilita el conteo total de páginas {nb}
        self.pdf.add_page()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        
    def agregar_titulo(self, titulo="REPORTE TÉCNICO DE INCIDENCIA"):
        self.pdf.set_font("helvetica", "B", 16)
        self.pdf.set_text_color(0)
        self.pdf.cell(0, 15, titulo.upper(), align="C", new_x="LMARGIN", new_y="NEXT")
        self.pdf.ln(5)
        return self

    def agregar_cuerpo(self, datos_equipo: dict):
        """Añade la tabla de datos técnicos del activo."""
        self.pdf.set_font("helvetica", "B", 12)
        self.pdf.set_fill_color(240, 240, 240)
        self.pdf.cell(0, 10, "1. Información General del Activo:", new_x="LMARGIN", new_y="NEXT", fill=True)
        
        self.pdf.set_font("helvetica", "", 11)
        for clave, valor in datos_equipo.items():
            self.pdf.set_font("helvetica", "B", 11)
            self.pdf.cell(50, 8, f" {clave}:", border=1)
            self.pdf.set_font("helvetica", "", 11)
            self.pdf.cell(0, 8, f" {valor}", border=1, new_x="LMARGIN", new_y="NEXT")
        
        self.pdf.ln(5)
        return self

    def agregar_evidencia(self, imagen_bytes):
        """Adjunta la captura de pantalla o foto de la inspección."""
        if imagen_bytes:
            self.pdf.set_font("helvetica", "B", 12)
            self.pdf.cell(0, 10, "2. Evidencia de la Inspección con IA:", new_x="LMARGIN", new_y="NEXT")
            try:
                # Se posiciona la imagen centrada
                imagen_io = io.BytesIO(imagen_bytes.getvalue())
                self.pdf.image(imagen_io, w=90, x=60) 
            except Exception as e:
                self.pdf.set_font("helvetica", "I", 10)
                self.pdf.cell(0, 10, f"(No se pudo renderizar la imagen: {str(e)})", new_x="LMARGIN", new_y="NEXT")
            self.pdf.ln(5)
        return self

    def agregar_firmas(self):
        """Genera el bloque de validación legal/técnica."""
        self.pdf.ln(20)
        self.pdf.set_font("helvetica", "B", 10)
        # Líneas y etiquetas de firma
        pos_y = self.pdf.get_y()
        self.pdf.line(20, pos_y + 10, 90, pos_y + 10)
        self.pdf.line(120, pos_y + 10, 190, pos_y + 10)
        
        self.pdf.ln(12)
        self.pdf.cell(90, 5, "Firma del Responsable Técnico", align="C")
        self.pdf.cell(100, 5, "Sello de Laboratorio FIEE", align="C")
        return self

    def compilar_pdf(self) -> bytes:
        """Finaliza el proceso y exporta los bytes del documento."""
        return bytes(self.pdf.output())