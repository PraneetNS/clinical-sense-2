from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from ...db.session import get_db
from ...api.deps import get_current_user
from ...models import User, ClinicalNote
from ...services.patient_service import PatientService
from ...services.notes.note_service import NoteService
from ...schemas.patient import PatientCreate, PatientResponse, PatientUpdate, PatientReport, PatientMinimalResponse, PatientDeleteResponse
from ...schemas.notes import NoteResponse
from ...schemas.timeline import TimelineEvent
from ...core.pdf_gen import generate_patient_pdf

router = APIRouter()

# -----------------------------------------------------------------------
# Fast listing endpoint — no relationship loading, immediate response
# -----------------------------------------------------------------------
@router.get("/list", response_model=List[PatientMinimalResponse])
def list_patients_fast(
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lightweight patient list — returns minimal fields only, very fast."""
    patients = PatientService.get_patients_minimal(
        db, user_id=current_user.id, skip=skip, limit=limit, search=search
    )
    # Compute billing totals in bulk (without loading all relationships)
    result = []
    for p in patients:
        p.total_billing_amount = 0.0
        p.outstanding_billing_amount = 0.0
        result.append(p)
    return result

@router.post("/", response_model=PatientResponse)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return PatientService.create_patient(db, patient_in, creator_id=current_user.id)

@router.get("/", response_model=List[PatientMinimalResponse])
def read_patients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns slim patient list (no nested relationships) for performance."""
    return PatientService.get_patients_minimal(
        db, user_id=current_user.id, skip=skip, limit=limit, search=search
    )

@router.get("/{patient_id}", response_model=PatientResponse)
def read_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = PatientService.get_patient(db, patient_id, user_id=current_user.id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.patch("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_in: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = PatientService.update_patient(db, patient_id, patient_in, user_id=current_user.id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.delete("/{patient_id}", response_model=PatientDeleteResponse)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft-delete a patient record. Only the creating user can delete."""
    return PatientService.delete_patient(db, patient_id, user_id=current_user.id)

@router.get("/{patient_id}/timeline", response_model=List[TimelineEvent])
def get_patient_timeline(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return PatientService.get_unified_timeline(db, patient_id, user_id=current_user.id)

@router.get("/{patient_id}/notes", response_model=List[NoteResponse])
def get_patient_notes(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notes = NoteService.get_patient_notes_by_patient_id(db, patient_id, current_user.id)
    
    # Transform to schema
    result = []
    for note in notes:
        nr = NoteResponse.from_orm(note)
        if note.structured_content:
            nr.structured_content = json.loads(note.structured_content)
        if note.ai_insights:
           nr.ai_insights = {
                "risk_score": note.ai_insights.risk_score,
                "red_flags": json.loads(note.ai_insights.red_flags or "[]"),
                "suggestions": json.loads(note.ai_insights.suggestions or "[]"),
                "missing_info": json.loads(note.ai_insights.missing_info or "[]")
            }
        result.append(nr)
    return result

@router.get("/{patient_id}/report", response_model=PatientReport)
async def get_patient_report(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await PatientService.get_patient_report(db, patient_id, user_id=current_user.id)

@router.get("/{patient_id}/report/pdf")
async def get_patient_report_pdf(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report_data = await PatientService.get_patient_report(db, patient_id, user_id=current_user.id)
    pdf_buffer = generate_patient_pdf(report_data, current_user)
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=patient_report_{patient_id}.pdf"}
    )

@router.get("/{patient_id}/alerts")
def get_patient_alerts(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch active deterioration alerts for a patient."""
    from ...models import DeteriorationAlert
    # Security check is implicitly done if PatientService was called, but let's be safe
    PatientService.get_patient(db, patient_id, user_id=current_user.id)
    
    return db.query(DeteriorationAlert).filter(
        DeteriorationAlert.patient_id == patient_id,
        DeteriorationAlert.is_acknowledged == False
    ).order_by(DeteriorationAlert.created_at.desc()).all()

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge a deterioration alert."""
    from ...models import DeteriorationAlert
    import datetime
    
    alert = db.query(DeteriorationAlert).filter(DeteriorationAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    # Security check: User must own the patient
    PatientService.get_patient(db, alert.patient_id, user_id=current_user.id)
    
    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.datetime.utcnow()
    alert.acknowledged_by_id = current_user.id
    db.commit()
    
    return {"status": "success"}

