from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from io import BytesIO
from datetime import datetime

def generate_patient_pdf(report_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'HospitalTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.teal,
        spaceAfter=20,
        alignment=1 # Center
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.darkblue,
        spaceBefore=15,
        spaceAfter=10,
        borderPadding=5,
        borderWidth=1,
        borderColor=colors.lightgrey,
        borderRadius=5
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold'
    )

    elements = []
    
    patient = report_data['patient']
    
    # Header
    elements.append(Paragraph("Clinical Documentation Assistant", title_style))
    elements.append(Paragraph(f"Patient Summary Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Demographics Section
    elements.append(Paragraph("Patient Demographics", section_style))
    demo_data = [
        [Paragraph("Name:", label_style), patient.name, Paragraph("MRN:", label_style), patient.mrn],
        [Paragraph("DOB:", label_style), patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else 'N/A', Paragraph("Gender:", label_style), patient.gender or 'N/A'],
        [Paragraph("Phone:", label_style), patient.phone_number or 'N/A', Paragraph("Address:", label_style), patient.address or 'N/A'],
    ]
    t = Table(demo_data, colWidths=[80, 150, 80, 150])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(t)
    
    # Allergies
    if patient.allergies:
        elements.append(Paragraph("Allergies", section_style))
        alg_data = [["Allergen", "Reaction", "Severity"]]
        for alg in patient.allergies:
            alg_data.append([alg.allergen, alg.reaction or 'N/A', alg.severity or 'N/A'])
        
        t = Table(alg_data, colWidths=[150, 150, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        elements.append(t)

    # Medications
    if patient.medications:
        elements.append(Paragraph("Current Medications", section_style))
        med_data = [["Medication", "Dosage", "Frequency", "Status"]]
        for med in patient.medications:
            med_data.append([med.name, med.dosage or 'N/A', med.frequency or 'N/A', med.status])
        
        t = Table(med_data, colWidths=[150, 100, 100, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        elements.append(t)

    # Procedures
    if patient.procedures:
        elements.append(Paragraph("Procedures", section_style))
        proc_data = [["Procedure", "Date", "Notes"]]
        for proc in patient.procedures:
            proc_data.append([proc.name, proc.date.strftime('%Y-%m-%d'), proc.notes or ''])
        
        t = Table(proc_data, colWidths=[150, 100, 210])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        elements.append(t)

    # Billing
    if patient.billing_items:
        elements.append(Paragraph("Billing Information", section_style))
        bill_data = [["Item", "Code", "Cost ($)", "Status"]]
        for item in patient.billing_items:
            bill_data.append([item.item_name, item.code or 'N/A', f"{item.cost:.2f}", item.status])
        
        bill_data.append(["", "TOTAL:", f"{patient.total_billing_amount:.2f}", ""])
        bill_data.append(["", "OUTSTANDING:", f"{patient.outstanding_billing_amount:.2f}", ""])
        
        t = Table(bill_data, colWidths=[150, 80, 100, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (-3,-2), (-2,-1), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-3), 0.5, colors.grey)
        ]))
        elements.append(t)

    # Notes Summary
    if report_data['notes']:
        elements.append(Paragraph("Clinical Notes Summary", section_style))
        for note in report_data['notes']:
            elements.append(Paragraph(f"<b>{note.title}</b> ({note.created_at.strftime('%Y-%m-%d')})", styles['Normal']))
            elements.append(Paragraph(note.raw_content[:500] + ("..." if len(note.raw_content) > 500 else ""), styles['Italic']))
            elements.append(Spacer(1, 10))

    # Documents Summary
    if report_data.get('documents'):
        elements.append(Paragraph("Clinical Documents", section_style))
        doc_data = [["Title", "Type", "Summary"]]
        for d in report_data['documents']:
            doc_data.append([d.title, d.file_type or 'N/A', Paragraph(d.summary or '', styles['Normal'])])
        
        t = Table(doc_data, colWidths=[120, 80, 280])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))
        elements.append(t)

    # Tasks & Follow-ups
    if report_data.get('tasks'):
        elements.append(Paragraph("Tasks & Follow-ups", section_style))
        task_data = [["Description", "Due Date", "Status"]]
        for task in report_data['tasks']:
            task_data.append([Paragraph(task.description, styles['Normal']), task.due_date.strftime('%Y-%m-%d') if task.due_date else 'N/A', task.status])
        
        t = Table(task_data, colWidths=[300, 100, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        elements.append(t)

    # Timeline Visualization
    if report_data.get('timeline'):
        elements.append(Paragraph("Clinical Timeline (Chronological)", section_style))
        timeline_data = [["Date", "Event", "Details"]]
        for ev in report_data['timeline'][:20]: # Show last 20 events
            timeline_data.append([
                ev['timestamp'].strftime('%Y-%m-%d %H:%M'),
                ev['type'].upper(),
                Paragraph(ev['title'], styles['Normal'])
            ])
        
        t = Table(timeline_data, colWidths=[100, 80, 300])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        elements.append(t)

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<b>Disclaimer:</b> AI-assisted documentation. No medical advice provided. This report reflects the authoritative patient record as of " + datetime.now().strftime('%Y-%m-%d %H:%M') + ".", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
