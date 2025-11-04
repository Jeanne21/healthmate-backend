# app/report_generator.py
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
import logging

from app.firebase_client import FirebaseClient

logger = logging.getLogger(__name__)

class ReportGenerator:
    """PDF Report Generator for health tracker application"""
    
    def __init__(self):
        self.firebase_client = FirebaseClient()
        self.styles = getSampleStyleSheet()
        # Add custom styles
        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generate_pdf_report(self, user_id, report_type="combined"):
        """
        Generate a PDF report for the user
        
        Args:
            user_id (str): The user ID
            report_type (str): Type of report - "medications", "measurements", or "combined"
            
        Returns:
            BytesIO: PDF file as a byte stream
        """
        
        try:
            # Get user data
            print(f"Generating PDF for user_id: {user_id}")
            user = self.firebase_client.get_user(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")
            
            # Create a BytesIO buffer
            buffer = io.BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Container for PDF elements
            elements = []
            
            # Add report title and timestamp
            report_title = "Health Tracker Report"
            if report_type == "medications":
                report_title = "Medication Report"
            elif report_type == "measurements":
                report_title = "Measurements Report"
                
            elements.append(Paragraph(f"{report_title}", self.styles["Title"]))
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles["CustomNormal"]))
            user_display_name = user.get('name') or user.get('dependent_name') or 'Unknown'
            elements.append(Paragraph(f"User: {user_display_name}", self.styles["CustomNormal"]))
            elements.append(Spacer(1, 0.25*inch))
            
            # Add content based on report type
            if report_type in ["medications", "combined"]:
                self._add_medications_section(elements, user_id)
                
            if report_type in ["measurements", "combined"]:
                if report_type == "combined":
                    elements.append(PageBreak())
                self._add_measurements_section(elements, user_id)
            
            # Build the PDF
            doc.build(elements)
            
            # Reset buffer position to the beginning
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def _add_medications_section(self, elements, user_id):
        """Add medications section to the PDF"""
        # Add section title
        elements.append(Paragraph("Medication History", self.styles["CustomHeading1"]))
        elements.append(Spacer(1, 0.1*inch))
        
        # Get all medications
        medications = self.firebase_client.get_medications(user_id)
        
        if not medications:
            elements.append(Paragraph("No medication data available.", self.styles["CustomNormal"]))
            return
        
        # Define table data
        medication_data = [["Medication Name", "Dosage", "Frequency (hours)", "Last Taken", "Next Dose"]]
        
        # Add medication entries
        for med in medications:
            last_taken = med.get('last_taken')
            if isinstance(last_taken, datetime):
                last_taken_str = last_taken.strftime('%Y-%m-%d %H:%M')
            else:
                last_taken_str = str(last_taken) if last_taken else "N/A"
                
            next_dose = med.get('next_dose')
            if isinstance(next_dose, datetime):
                next_dose_str = next_dose.strftime('%Y-%m-%d %H:%M')
            else:
                next_dose_str = str(next_dose) if next_dose else "N/A"
                
            medication_data.append([
                med.get('name', 'Unknown'),
                med.get('dosage', 'N/A'),
                str(med.get('frequency', 'N/A')),
                last_taken_str,
                next_dose_str
            ])
        
        # Create table
        medication_table = Table(medication_data, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1.5*inch, 1.5*inch])
        
        # Style the table
        medication_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(medication_table)
        elements.append(Spacer(1, 0.25*inch))
    
    def _add_measurements_section(self, elements, user_id):
        """Add measurements section to the PDF"""
        # Add section title
        elements.append(Paragraph("Health Measurements", self.styles["CustomHeading1"]))
        elements.append(Spacer(1, 0.1*inch))
        
        # Get all measurements (no limit for report)
        measurements = self.firebase_client.get_measurements(user_id, limit=1000)
        
        if not measurements:
            elements.append(Paragraph("No measurement data available.", self.styles["CustomNormal"]))
            return
        
        # Group measurements by type
        measurement_types = {}
        for m in measurements:
            m_type = m.get('type')
            if m_type not in measurement_types:
                measurement_types[m_type] = []
            measurement_types[m_type].append(m)
        
        # Add each measurement type
        for m_type, m_data in measurement_types.items():
            elements.append(Paragraph(f"{m_type.title() if m_type else 'Unknown'} Measurements", self.styles["Heading2"]))
            elements.append(Spacer(1, 0.1*inch))
            
            # Define table data
            table_data = [["Date/Time", "Value", "Unit", "Notes"]]
            
            # Sort measurements by timestamp
            m_data.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
            
            # Add measurement entries
            for m in m_data:
                timestamp = m.get('timestamp')
                if isinstance(timestamp, datetime):
                    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M')
                else:
                    timestamp_str = str(timestamp) if timestamp else "N/A"
                    
                table_data.append([
                    timestamp_str,
                    str(m.get('value', 'N/A')),
                    m.get('unit', 'N/A'),
                    m.get('notes', '')
                ])
            
            # Create table
            m_table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 3*inch])
            
            # Style the table
            m_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(m_table)
            elements.append(Spacer(1, 0.25*inch))