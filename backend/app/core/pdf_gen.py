from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from io import BytesIO
from datetime import datetime

def generate_patient_pdf(report_data, doctor=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    
    # Premium Custom styles
    header_style = ParagraphStyle(
        'HospitalName',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor("#0f172a"), # Slate 900
        spaceAfter=2,
        alignment=0 # Left
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.teal,
        fontName='Helvetica-Bold',
        letterSpacing=2,
        spaceAfter=20,
        alignment=0 # Left
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.teal,
        fontName='Helvetica-Bold',
        spaceBefore=20,
        spaceAfter=12,
        borderPadding=0,
        borderWidth=0,
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#64748b") # Slate 500
    )

    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#1e293b") # Slate 800
    )

    summary_box_style = ParagraphStyle(
        'SummaryBox',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        leftIndent=10,
        rightIndent=10,
        leading=14
    )

    print("Starting elements collection")
    elements = []
    patient = report_data['patient']
    print(f"Patient name: {patient.name}")
    
    # 1. Professional Header
    elements.append(Paragraph("CLINICAL INTELLIGENCE", header_style))
    elements.append(Paragraph("AUTOMATED HEALTHCARE DOCUMENTATION SYSTEM", subtitle_style))
    
    # Horizonatal Rule
    elements.append(Table([[None]], colWidths=[500], rowHeights=[1], style=[('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0"))]))
    elements.append(Spacer(1, 15))
    
    p_name = patient.name or "Unknown Patient"
    p_mrn = patient.mrn or "N/A"
    p_gender = patient.gender or "N/A"
    p_phone = patient.phone_number or "N/A"
    p_insurance = patient.insurance_provider or "N/A"

    # 2. Report metadata & Patient Info in a clean grid
    report_info = [
        [Paragraph("PATIENT RECORD SUMMARY", label_style), ""],
        [Paragraph("Report ID:", label_style), Paragraph(f"REF-{p_mrn}-{datetime.now().strftime('%y%m%d')}", value_style)],
        [Paragraph("Generated:", label_style), Paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'), value_style)],
    ]
    meta_table = Table(report_info, colWidths=[100, 400])
    meta_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # Patient Details Table
    elements.append(Paragraph("Patient Identification", section_style))
    demo_data = [
        [Paragraph("FULL NAME", label_style), Paragraph("DATE OF BIRTH", label_style), Paragraph("MRN", label_style)],
        [Paragraph(p_name, value_style), 
         Paragraph(patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else 'N/A', value_style), 
         Paragraph(p_mrn, value_style)],
        [Paragraph("GENDER", label_style), Paragraph("CONTACT", label_style), Paragraph("INSURANCE", label_style)],
        [Paragraph(p_gender, value_style), 
         Paragraph(p_phone, value_style), 
         Paragraph(p_insurance, value_style)]
    ]
    t = Table(demo_data, colWidths=[166, 166, 166])
    t.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('BOTTOMPADDING', (0,0), (-1,-1), 5), ('TOPPADDING', (0,0), (-1,-1), 5)]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # AI Clinical Synthesis (Boxed)
    if report_data.get('summary'):
        elements.append(Paragraph("Executive Clinical Synthesis", section_style))
        print("Processing summary")
        summary_val = report_data['summary']
        summary_text = summary_val if isinstance(summary_val, str) else summary_val.get('summary', str(summary_val))
        print(f"Summary text: {summary_text[:50]}...")
        summary_table = Table([[Paragraph(summary_text, summary_box_style)]], colWidths=[500])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('LEFTPADDING', (0,0), (-1,-1), 15), ('RIGHTPADDING', (0,0), (-1,-1), 15),
            ('TOPPADDING', (0,0), (-1,-1), 15), ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 10))

    # Clinical Alerts (Allergies)
    if patient.allergies:
        elements.append(Paragraph("Allergies & Adverse Reactions", section_style))
        alg_data = [[Paragraph("ALLERGEN", label_style), Paragraph("REACTION", label_style), Paragraph("SEVERITY", label_style)]]
        for alg in patient.allergies:
            sev_color = colors.red if alg.severity == 'High' or alg.severity == 'Severe' else colors.orange if alg.severity == 'Medium' else colors.black
            alg_data.append([alg.allergen, alg.reaction or 'N/A', Paragraph(alg.severity or 'N/A', ParagraphStyle('Sev', parent=value_style, textColor=sev_color))])
        t = Table(alg_data, colWidths=[200, 200, 100])
        t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#cbd5e1")), ('BOTTOMPADDING', (0,0), (-1,-1), 5), ('TOPPADDING', (0,0), (-1,-1), 5)]))
        elements.append(t)

    # Medical History
    if patient.medical_history:
        print("Processing medical history")
        elements.append(Paragraph("Medical History & Chronic Conditions", section_style))
        hist_data = [[Paragraph("CONDITION", label_style), Paragraph("DIAGNOSIS DATE", label_style), Paragraph("STATUS", label_style)]]
        for h in patient.medical_history:
            hist_data.append([h.condition_name or "N/A", h.diagnosis_date.strftime('%Y-%m-%d') if h.diagnosis_date else 'N/A', h.status or "N/A"])
        t = Table(hist_data, colWidths=[250, 150, 100])
        t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#cbd5e1")), ('BOTTOMPADDING', (0,0), (-1,-1), 5)]))
        elements.append(t)

    # Medications
    if patient.medications:
        print("Processing medications")
        elements.append(Paragraph("Current Active Medications", section_style))
        med_data = [[Paragraph("MEDICATION", label_style), Paragraph("DOSAGE", label_style), Paragraph("FREQUENCY", label_style), Paragraph("STATUS", label_style)]]
        for med in patient.medications:
            if med.status == 'Active':
                med_data.append([med.name or "N/A", med.dosage or 'N/A', med.frequency or 'N/A', med.status])
        if len(med_data) > 1:
            t = Table(med_data, colWidths=[160, 100, 140, 100])
            t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#cbd5e1")), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
            elements.append(t)

    # Procedures
    if patient.procedures:
        elements.append(Paragraph("Surgical & Procedure History", section_style))
        proc_data = [[Paragraph("PROCEDURE", label_style), Paragraph("DATE", label_style), Paragraph("NOTES", label_style)]]
        for proc in patient.procedures:
            proc_data.append([proc.name, proc.date.strftime('%Y-%m-%d'), Paragraph(proc.notes or '-', value_style)])
        t = Table(proc_data, colWidths=[150, 100, 250])
        t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#cbd5e1")), ('BOTTOMPADDING', (0,0), (-1,-1), 5)]))
        elements.append(t)

    # Recent Clinical Notes (Detailed)
    if report_data.get('notes'):
        print("Processing recently clinical notes")
        elements.append(Paragraph("Provider Documentation", section_style))
        for note in report_data['notes'][:3]: # Last 3 notes
            note_title = (note.title or "Untitled Note").upper()
            note_date = note.created_at.strftime('%Y-%m-%d %H:%M') if note.created_at else "N/A"
            elements.append(Paragraph(f"<b>{note_title}</b> | {note_date}", label_style))
            elements.append(Paragraph(note.raw_content or "No content available.", ParagraphStyle('NoteBody', parent=styles['Normal'], fontSize=9, leading=12, spaceAfter=10)))
            elements.append(Spacer(1, 5))

    # AI Generated Encounters (New)
    if report_data.get('encounters'):
        print("Processing AI encounters")
        elements.append(Paragraph("AI-Generated Clinical Encounters (Drafts)", section_style))
        for enc in report_data['encounters'][:3]: # Last 3 AI encounters
            enc_status = (enc.get('status') or "Draft").upper()
            enc_soap = enc.get('soap') or {}
            enc_box = [
                [Paragraph(f"<b>CHIEF COMPLAINT:</b> {enc.get('chief_complaint') or 'N/A'}", value_style)],
                [Paragraph(f"<b>STATUS:</b> {enc_status} | <b>CONFIRMED:</b> {'YES' if enc.get('is_confirmed') else 'NO'}", label_style)],
                [Paragraph(f"<b>SOAP Summary:</b> {(enc_soap.get('assessment') or 'No assessment available')[:200]}...", value_style)]
            ]
            t = Table(enc_box, colWidths=[500])
            t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")), ('LEFTPADDING', (0,0), (-1,-1), 10), ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5)]))
            elements.append(t)
            elements.append(Spacer(1, 10))

    # Tasks & Care Plan
    if report_data.get('tasks'):
        elements.append(Paragraph("Care Plan & Pending Tasks", section_style))
        task_data = [[Paragraph("TASK DESCRIPTION", label_style), Paragraph("DUE DATE", label_style), Paragraph("PRIORITY", label_style)]]
        for task in report_data['tasks']:
            if task.status != 'Completed':
                p_color = colors.red if task.priority == 'High' else colors.orange if task.priority == 'Medium' else colors.black
                task_data.append([Paragraph(task.description or "No description provided.", value_style), task.due_date.strftime('%Y-%m-%d') if task.due_date else 'N/A', Paragraph(task.priority or "Normal", ParagraphStyle('TaskP', parent=value_style, textColor=p_color))])
        if len(task_data) > 1:
            t = Table(task_data, colWidths=[300, 100, 100])
            t.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#cbd5e1")), ('BOTTOMPADDING', (0,0), (-1,-1), 5)]))
            elements.append(t)

    # Financial Summary
    elements.append(Paragraph("Financial Summary", section_style))
    total_billed = float(patient.total_billing_amount or 0)
    total_outstanding = float(patient.outstanding_billing_amount or 0)
    bill_data = [
        [Paragraph("TOTAL BILLED AMOUNT", label_style), Paragraph("OUTSTANDING BALANCE", label_style)],
        [Paragraph(f"${total_billed:,.2f}", value_style), Paragraph(f"${total_outstanding:,.2f}", value_style)]
    ]
    t = Table(bill_data, colWidths=[250, 250])
    elements.append(t)

    # Risks & Alerts
    if report_data.get('risks'):
        elements.append(Paragraph("Risk Assessment & Safety Analysis", section_style))
        r = report_data['risks'][0]
        risk_color = colors.red if r.risk_level == 'High' or r.risk_level == 'Critical' else colors.orange if r.risk_level == 'Medium' else colors.green
        r_level = (r.risk_level or "Unknown").upper()
        risk_data = [
            [Paragraph("READMISSION RISK LEVEL", label_style), Paragraph(r_level, ParagraphStyle('RiskValue', parent=value_style, textColor=risk_color, fontName='Helvetica-Bold'))],
            [Paragraph("RISK SCORE", label_style), Paragraph(f"{r.risk_score or 0}%", value_style)],
            [Paragraph("CONTRIBUTING FACTORS", label_style), Paragraph(r.contributing_factors or 'Minimal clinical risk factors detected.', value_style)],
        ]
        t = Table(risk_data, colWidths=[150, 350])
        t.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
        elements.append(t)

    # 5. Authorizing Signature Section
    elements.append(Spacer(1, 40))

    
    # Signature block
    dr_name = (doctor.full_name if doctor and doctor.full_name else "Attending Physician").upper()
    sig_data = [
        ["", ""],
        [Paragraph("_______________________________________", styles['Normal']), Paragraph(datetime.now().strftime('%Y-%m-%d'), value_style)],
        [Paragraph(f"<b>DR. {dr_name}</b>", value_style), Paragraph("DATE OF AUTHORIZATION", label_style)],
        [Paragraph("Electronically Signed / Authorized Representative", label_style), ""]
    ]
    sig_table = Table(sig_data, colWidths=[350, 150])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    
    # Seal or Verification stamp (Simulated)
    elements.append(Table([[sig_table, Paragraph("<b>VERIFIED</b><br/><font size=8>SECURITY CLEARANCE ALPHA</font>", ParagraphStyle('Seal', parent=styles['Normal'], textColor=colors.teal, alignment=1, borderPadding=10, borderWidth=2, borderColor=colors.teal))]], colWidths=[400, 100]))

    # Footer Disclaimer
    elements.append(Spacer(1, 40))
    disclaimer = "<b>CONFIDENTIALITY NOTICE:</b> This clinical report contains privileged and confidential medical information. AI algorithms assisted in the synthesis of this document. Ultimate clinical responsibility remains with the authorizing physician. Unauthorized distribution is a violation of HIPAA/Healthcare privacy regulations."
    elements.append(Paragraph(disclaimer, ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=7, textColor=colors.grey, alignment=1)))
    
    print("Building document")
    try:
        doc.build(elements)
    except Exception as e:
        print(f"CRASH during doc.build: {e}")
        import traceback
        traceback.print_exc()
        raise e
    print("Document built successfully")
    buffer.seek(0)
    return buffer
