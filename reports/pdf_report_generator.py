from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak)

from logger import Logger
from reports.report_data_model import ReportDataModel
from settings import IMAGE_LOGO


class PDFReportGenerator:
    """Class to generate PDF reports from a ReportDataModel"""

    def __init__(self, file_name, data_model, method_name, report_type="summary", decimals=2):
        """
        Initialize the PDF report generator

        :param str file_name: Path where the PDF will be saved.
        :param ReportDataModel data_model: The data model containing all report information.
        :param str method_name: Name of the concrete mix design method (MCE, ACI, or DoE).
        :param str report_type: Type of report to generate ('summary' or 'full').
        :param int decimals: Number of decimal places for numeric values.
        """
        # Initialize the logger
        self.logger = Logger(__name__)

        self.file_name = file_name
        self.data_model = data_model
        self.method_name = method_name
        self.report_type = report_type.lower()
        self.decimals = decimals

        # Get common data from the model
        self.input_data = self.data_model.get_input_data()
        self.dosage_data = self.data_model.get_dosage_data()

        # Initialize attributes that will be conditionally populated
        self.adjusted_dosage_data = {}
        self.adjustment_notes = {}
        self.calculation_details = {}

        # Get and verify adjustment_notes
        temp_adjustment_notes = self.data_model.get_adjustment_notes()
        self.has_trial_mix_adjustments = self.data_model.has_trial_mix_adjustments(temp_adjustment_notes)
        if self.has_trial_mix_adjustments:
            self.adjusted_dosage_data = self.data_model.get_adjusted_dosage_data()
            self.adjustment_notes = self.data_model.get_adjustment_notes()

        # Check what type of report the user wants to print
        if self.report_type == "full":
            self.calculation_details = self.data_model.get_calculation_details()

        # Initialize ReportLab document
        self.doc = SimpleDocTemplate(
            self.file_name,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        # Initialization complete
        self.logger.info('PDF report generator initialized')

    def _setup_custom_styles(self):
        """Set up custom paragraph styles for the report"""

        # Modify pre-existing styles
        pass

    def format_value(self, value):
        """
        Format values according to their type and decimal configuration.

        :param value: A formatted value.
        :rtype: str
        """

        if isinstance(value, list):
            formatted_elements = []
            for item in value:
                if isinstance(item, bool):
                    formatted_elements.append("Sí" if item else "No")
                elif isinstance(item, (int, float)):
                    formatted_elements.append(f"{item:.{self.decimals}f}")
                else:
                    formatted_elements.append(str(item))
            return ", ".join(formatted_elements)
        elif isinstance(value, bool):
            return "Sí" if value else "No"
        elif isinstance(value, (int, float)):
            if value == 0:
                return "-"
            else:
                return f"{value:.{self.decimals}f}"
        elif value == "-" or value == "" or value is None:
            return "-"
        else:
            return str(value)

    def generate(self):
        """Generate the complete PDF report"""

        elements = []
        
        # Add title
        method_names = {
            "MCE": "Método del Manual del Concreto Estructural (2009)",
            "ACI": "Método del Comité 211 del Instituto Americano del Concreto (2022)",
            "DoE": "Método del Departamento de Medio Ambiente británico (1997)"
        }
        method_full_name = method_names.get(self.method_name, self.method_name)
        title = f"Diseño de Mezcla de Concreto: {method_full_name}"
        report_type_name = "Reporte Completo" if self.report_type == "full" else "Reporte Básico"
        
        elements.append(Paragraph(title, self.styles['Title']))
        elements.append(Paragraph(report_type_name, self.styles['Heading2']))
        elements.append(Spacer(width=0, height=0.5*cm))
        
        # # Add logo if it exists
        # if os.path.exists(IMAGE_LOGO):
        #     logo = Image(IMAGE_LOGO, width=3*cm, height=3*cm)
        #     elements.append(logo)
        #     elements.append(Spacer(width=0, height=0.1*cm))
        
        # Add general information
        if "Información general" in self.input_data:
            elements.append(Paragraph("Información general", self.styles['Heading3']))
            elements.append(Spacer(width=0, height=0.2*cm))
            
            general_info = self.input_data["Información general"]
            data = [[k, self.format_value(v)] for k, v in general_info.items()]
            
            table = Table(data, colWidths=[4*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(table)
            elements.append(Spacer(width=0, height=0.3*cm))
        
        # Add field requirements
        if "Condiciones de la obra" in self.input_data:
            elements.append(Paragraph("Condiciones de la obra", self.styles['Heading3']))
            elements.append(Spacer(width=0, height=0.2*cm))
            
            # Process nested dictionaries
            field_req = self.input_data["Condiciones de la obra"]
            for section_name, section_data in field_req.items():
                if isinstance(section_data, dict):
                    elements.append(Paragraph(section_name, self.styles['Heading4']))
                    data = []
                    for key, value in section_data.items():
                        if isinstance(value, dict):
                            # Handle nested dictionaries
                            for subkey, subvalue in value.items():
                                data.append([f"{key} - {subkey}", self.format_value(subvalue)])
                        else:
                            data.append([key, self.format_value(value)])
                    
                    table = Table(data, colWidths=[4*inch, 3*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ]))
                    
                    elements.append(table)
                    elements.append(Spacer(width=0, height=0.3*cm))
        
        # Add materials information
        for material_section in ["Materiales cementantes", "Agregado fino", "Agregado grueso", "Agua", "Aditivos"]:
            if material_section in self.input_data:
                elements.append(Paragraph(material_section, self.styles['Heading3']))
                elements.append(Spacer(width=0, height=0.2*cm))
                
                # Process nested dictionaries
                material_data = self.input_data[material_section]
                if isinstance(material_data, dict):
                    # Handle specific cases like grading analysis that might have special formatting
                    if material_section in ["Agregado fino", "Agregado grueso"] and "Granulometría" in material_data:
                        # First add non-grading sections
                        for subsection_name, subsection_data in material_data.items():
                            if subsection_name != "Granulometría":
                                elements.append(Paragraph(subsection_name, self.styles['Heading4']))
                                data = []
                                for key, value in subsection_data.items():
                                    data.append([key, self.format_value(value)])
                                
                                table = Table(data, colWidths=[4*inch, 3*inch])
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                                ]))
                                
                                elements.append(table)
                                elements.append(Spacer(width=0, height=0.3*cm))
                        
                        # Now add grading if it's a dictionary with passing data
                        if isinstance(material_data["Granulometría"], dict) and "Porcentaje acumulado pasante" in material_data["Granulometría"]:
                            elements.append(Paragraph("Granulometría", self.styles['Heading4']))
                            
                            passing_data = material_data["Granulometría"]["Porcentaje acumulado pasante"]
                            if isinstance(passing_data, dict):
                                # Create sieve analysis table
                                headers = ["Cedazo, ASTM E11 (ISO 565)", "Porcentaje acumulado pasante"]
                                data = [headers]
                                for sieve, passing in passing_data.items():
                                    data.append([sieve, self.format_value(passing)])
                                
                                table = Table(data, colWidths=[3*inch, 2.5*inch])
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                                ]))
                                
                                elements.append(table)
                                elements.append(Spacer(width=0, height=0.3*cm))
                            
                            # Add other grading properties
                            other_data = []
                            for key, value in material_data["Granulometría"].items():
                                if key != "Porcentaje acumulado pasante":
                                    other_data.append([key, self.format_value(value)])
                            
                            if other_data:
                                table = Table(other_data, colWidths=[4*inch, 3*inch])
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                                ]))
                                
                                elements.append(table)
                                elements.append(Spacer(width=0, height=0.3*cm))
                    elif material_section == "Agua":
                        water_info = self.input_data["Agua"]
                        data = [[k, self.format_value(v)] for k, v in water_info.items()]

                        table = Table(data, colWidths=[4 * inch, 3 * inch])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ]))

                        elements.append(table)
                        elements.append(Spacer(width=0, height=0.3*cm))
                    else:
                        # Standard nested dictionary handling
                        for subsection_name, subsection_data in material_data.items():
                            elements.append(Paragraph(subsection_name, self.styles['Heading4']))
                            data = []
                            
                            if isinstance(subsection_data, dict):
                                for key, value in subsection_data.items():
                                    data.append([key, self.format_value(value)])
                            else:
                                data.append([subsection_name, self.format_value(subsection_data)])
                            
                            table = Table(data, colWidths=[4*inch, 3*inch])
                            table.setStyle(TableStyle([
                                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ]))
                            
                            elements.append(table)
                            elements.append(Spacer(width=0, height=0.3*cm))
                
                elements.append(Spacer(width=0, height=0.3*cm))
        
        # Add page break before dosage section
        elements.append(PageBreak())
        
        # Add dosage data
        elements.append(Paragraph("Diseño de mezcla por metro cúbico", self.styles['Heading3']))
        elements.append(Spacer(width=0, height=0.2*cm))
        
        # Create dosage table
        dosage_headers = ["Material", "Volumen absoluto (L)", "Peso (kgf)",
                          "Volumen aparente (L)"] if self.method_name == "MCE" else ["Material", "Volumen absoluto (L)",
                                                                                     "Masa (kg)",
                                                                                     "Volumen aparente (L)"]
        dosage_data = [dosage_headers]
        
        for material, values in self.dosage_data.items():
            row = [
                material,
                self.format_value(values.get("abs_vol", "-")),
                self.format_value(values.get("content", "-")),
                self.format_value(values.get("volume", "-"))
            ]
            dosage_data.append(row)
        
        dosage_table = Table(dosage_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        dosage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(dosage_table)
        elements.append(Spacer(width=0, height=0.5*cm))
        
        # Add adjusted dosage if it exists
        if self.has_trial_mix_adjustments:
            elements.append(Paragraph("Mezcla ajustada por metro cúbico (después de mezclas de pruebas)", self.styles['Heading3']))
            elements.append(Spacer(width=0, height=0.2*cm))
            
            # Create adjusted dosage table
            adj_dosage_data = [dosage_headers]
            
            for material, values in self.adjusted_dosage_data.items():
                row = [
                    material,
                    self.format_value(values.get("abs_vol", "-")),
                    self.format_value(values.get("content", "-")),
                    self.format_value(values.get("volume", "-"))
                ]
                adj_dosage_data.append(row)
            
            adj_dosage_table = Table(adj_dosage_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            adj_dosage_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(adj_dosage_table)
            elements.append(Spacer(width=0, height=0.5*cm))
            
            # Add adjustment notes
            elements.append(Paragraph("Notas de ajustes realizados", self.styles['Heading3']))
            elements.append(Spacer(width=0, height=0.2*cm))
            
            # Process adjustment notes
            for section_name, section_data in self.adjustment_notes.items():
                elements.append(Paragraph(section_name, self.styles['Heading4']))
                data = []
                
                for key, value in section_data.items():
                    data.append([key, self.format_value(value)])
                
                table = Table(data, colWidths=[4*inch, 3*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                elements.append(table)
                elements.append(Spacer(width=0, height=0.3*cm))
        
        # Add calculation details for full report
        if self.report_type == "full" and hasattr(self, "calculation_details"):
            elements.append(PageBreak())
            elements.append(Paragraph("Detalles de los cálculos", self.styles['Heading3']))
            elements.append(Spacer(width=0, height=0.2*cm))
            
            # Process calculation details
            for section_name, section_data in self.calculation_details.items():
                elements.append(Paragraph(section_name, self.styles['Heading4']))
                data = []
                
                for key, value in section_data.items():
                    data.append([key, self.format_value(value)])
                
                table = Table(data, colWidths=[4*inch, 3*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                elements.append(table)
                elements.append(Spacer(width=0, height=0.5*cm))

        # # Header function
        # def draw_header(canvas, doc):
        #     """Add header to each page."""
        #
        #     canvas.saveState()
        #     canvas.setFont('Helvetica-Bold', 10)
        #     width, height = letter  # already imported
        #
        #     # Text centered 0.5" from the top edge
        #     canvas.drawCentredString(width / 2.0, height - 0.5 * inch,
        #                              "Concretus - Diseño y Dosificación de Mezclas de Concreto")
        #
        #     # Separator line, just below the text
        #     canvas.setLineWidth(0.5)
        #     canvas.line(72, height - 0.55*inch, width - 72, height - 0.55*inch)
        #
        #     canvas.restoreState()

        # Header function
        def draw_header(canvas, doc):
            """Add header (logo + title) to each page, both aligned at the same vertical position."""
            canvas.saveState()
            width, height = letter  # page size

            # Common configuration
            canvas.setFont('Helvetica-Bold', 12)
            title_text = "Concretus - Diseño y Dosificación de Mezclas de Concreto"

            # 1) Calculate the reference height (baseline of the text)
            y_text = height - 0.4 * inch

            # 2) Draw the title centered on that line
            canvas.drawCentredString(width / 2.0, y_text, title_text)

            # 3) Draw the logo on the right, adjusting its Y so that it is centered with the text
            logo_path = IMAGE_LOGO
            logo_width = 0.6 * inch
            logo_height = logo_width
            x_logo = width - doc.rightMargin - logo_width
            # To center vertically: we place the bottom of the logo a little below y_text
            y_logo = y_text - (logo_height - 10) / 2

            canvas.drawImage(
                logo_path,
                x_logo, y_logo,
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )

            # 4) Separator line just below y_text
            line_y = y_text - 0.2 * inch
            canvas.setLineWidth(0.5)
            canvas.line(
                doc.leftMargin,
                line_y,
                width - doc.rightMargin,
                line_y
            )

            canvas.restoreState()

        # Footer function
        def draw_footer(canvas, doc):
            """Add page numbers and footer to each page."""

            page_num = canvas.getPageNumber()
            date_text = datetime.now().strftime('%d/%m/%Y %H:%M')
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.drawCentredString(letter[0]/2, 0.75*inch, f"Página {page_num}") # page number centered below
            canvas.drawString(72, 0.75*inch, f"Generado: {date_text}") # date on the left
            canvas.restoreState()

        # Combine both into a single callback
        def draw_header_and_footer(canvas, doc):
            draw_header(canvas, doc)
            draw_footer(canvas, doc)

        # Build the PDF document
        self.doc.build(
            elements,
            onFirstPage=draw_header_and_footer,
            onLaterPages=draw_header_and_footer
        )
        return True