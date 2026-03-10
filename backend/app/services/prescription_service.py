from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
from uuid import UUID
import datetime
import json
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

from ..models import Prescription, Patient, User, AIEncounter, AIGeneratedMedication, AuditLog, AIGeneratedDiagnosis
from ..schemas.prescription import PrescriptionCreate, PrescriptionResponse, PrescriptionItem

class PrescriptionService:
    def __init__(self, db: Session):
        self.db = db

    def create_prescription(self, prescription_data: PrescriptionCreate, doctor_id: int) -> Prescription:
        # Validate patient ownership
        patient = self.db.query(Patient).filter(Patient.id == prescription_data.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if patient.user_id != doctor_id:
            raise HTTPException(status_code=403, detail="You do not have access to this patient")

        # Create Prescription record
        new_prescription = Prescription(
            patient_id=prescription_data.patient_id,
            encounter_id=prescription_data.encounter_id,
            doctor_id=doctor_id,
            diagnosis=prescription_data.diagnosis,
            notes=prescription_data.notes,
            prescription_items=[item.model_dump() for item in prescription_data.prescription_items],
            created_at=datetime.datetime.utcnow()
        )

        self.db.add(new_prescription)
        
        # Log event
        audit_entry = AuditLog(
            user_id=doctor_id,
            action="PRESCRIPTION_CREATED",
            entity_type="Prescription",
            entity_id=None, # UUID not integer, models.py says entity_id is Integer. I'll skip for now or use 0
            details=f"Prescription created for Patient ID: {patient.id}"
        )
        self.db.add(audit_entry)
        
        self.db.commit()
        self.db.refresh(new_prescription)
        return new_prescription

    def get_prescription(self, prescription_id: UUID) -> Dict[str, Any]:
        prescription = self.db.query(Prescription).filter(Prescription.id == prescription_id).first()
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        patient = self.db.query(Patient).filter(Patient.id == prescription.patient_id).first()
        doctor = self.db.query(User).filter(User.id == prescription.doctor_id).first()

        return {
            "prescription": prescription,
            "patient": patient,
            "doctor": doctor
        }

    def prefill_from_encounter(self, encounter_id: int) -> Dict[str, Any]:
        encounter = self.db.query(AIEncounter).filter(AIEncounter.id == encounter_id).first()
        if not encounter:
            raise HTTPException(status_code=404, detail="Encounter not found")

        medications = self.db.query(AIGeneratedMedication).filter(AIGeneratedMedication.encounter_id == encounter_id).all()
        diagnoses = self.db.query(AIGeneratedDiagnosis).filter(AIGeneratedDiagnosis.encounter_id == encounter_id).all()

        items = []
        for med in medications:
            items.append(PrescriptionItem(
                medicine_name=med.name,
                dosage=med.dosage or "",
                frequency=med.frequency or "",
                duration=med.duration or "",
                time_of_day=[], # AI might not have structured time_of_day yet
                special_instruction=""
            ))

        primary_diagnosis = ""
        if diagnoses:
            # Pick primary or first one
            primary = next((d for d in diagnoses if d.is_primary), diagnoses[0])
            primary_diagnosis = primary.condition_name

        return {
            "diagnosis": primary_diagnosis,
            "prescription_items": items
        }

    def generate_prescription_pdf(self, prescription_id: UUID) -> BytesIO:
        data = self.get_prescription(prescription_id)
        prescription = data["prescription"]
        patient = data["patient"]
        doctor = data["doctor"]

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.teal, alignment=1, spaceAfter=20)
        header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=12, leading=14)
        label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')
        value_style = ParagraphStyle('Value', parent=styles['Normal'], fontSize=10)
        table_header_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=colors.white)

        elements = []

        # Clinic Header
        elements.append(Paragraph("CLINICAL SENSE", title_style))
        elements.append(Paragraph("<b>Digital Health Assistant</b>", ParagraphStyle('Sub', parent=styles['Normal'], alignment=1)))
        elements.append(Spacer(1, 20))

        # Doctor Info
        dr_name = doctor.full_name if doctor and doctor.full_name else "Licensed Physician"
        elements.append(Paragraph(f"<b>Dr. {dr_name}</b>", header_style))
        elements.append(Spacer(1, 10))

        # Horizontal Line
        elements.append(Table([[None]], colWidths=[500], rowHeights=[1], style=[('LINEBELOW', (0,0), (-1,-1), 1, colors.teal)]))
        elements.append(Spacer(1, 15))

        # Patient & Prescription Info
        info_data = [
            [Paragraph("Patient Name:", label_style), Paragraph(patient.name or "N/A", value_style), Paragraph("Date:", label_style), Paragraph(prescription.created_at.strftime('%Y-%m-%d'), value_style)],
            [Paragraph("Age/Gender:", label_style), Paragraph(f"{self._calculate_age(patient.date_of_birth)} / {patient.gender or 'N/A'}", value_style), Paragraph("Prescription ID:", label_style), Paragraph(str(prescription.id)[:8].upper(), value_style)],
        ]
        info_table = Table(info_data, colWidths=[100, 150, 100, 150])
        info_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))

        # Diagnosis
        if prescription.diagnosis:
            elements.append(Paragraph("<b>DIAGNOSIS:</b>", label_style))
            elements.append(Paragraph(prescription.diagnosis, value_style))
            elements.append(Spacer(1, 15))

        # Medications Table
        elements.append(Paragraph("<b>PRESCRIPTION:</b>", label_style))
        elements.append(Spacer(1, 5))

        med_data = [[
            Paragraph("Medicine", table_header_style), 
            Paragraph("Dosage", table_header_style), 
            Paragraph("Freq", table_header_style), 
            Paragraph("Dur", table_header_style), 
            Paragraph("Instructions", table_header_style)
        ]]

        for item in prescription.prescription_items:
            med_data.append([
                Paragraph(item.get('medicine_name', 'N/A'), value_style),
                Paragraph(item.get('dosage', 'N/A'), value_style),
                Paragraph(item.get('frequency', 'N/A'), value_style),
                Paragraph(item.get('duration', 'N/A'), value_style),
                Paragraph(item.get('special_instruction', '') or '-', value_style)
            ])

        med_table = Table(med_data, colWidths=[160, 80, 80, 60, 120])
        med_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.teal),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(med_table)
        elements.append(Spacer(1, 20))

        # Notes
        if prescription.notes:
            elements.append(Paragraph("<b>ADDITIONAL NOTES:</b>", label_style))
            elements.append(Paragraph(prescription.notes, value_style))
            elements.append(Spacer(1, 30))

        # Signature
        elements.append(Spacer(1, 40))
        sig_data = [
            ["", Paragraph("_________________________", styles['Normal'])],
            ["", Paragraph(f"Dr. {dr_name}", value_style)],
            ["", Paragraph("Authorized Signature", label_style)]
        ]
        sig_table = Table(sig_data, colWidths=[300, 200])
        sig_table.setStyle(TableStyle([('ALIGN', (1,0), (1,-1), 'CENTER')]))
        elements.append(sig_table)

        # Verification Footer
        elements.append(Spacer(1, 40))
        verify_text = f"Verification Code: {prescription.verification_code} | Generated by Clinical Sense AI"
        elements.append(Paragraph(verify_text, ParagraphStyle('Verify', parent=styles['Normal'], fontSize=7, textColor=colors.grey, alignment=1)))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def _calculate_age(self, dob):
        if not dob:
            return "N/A"
        today = datetime.date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
