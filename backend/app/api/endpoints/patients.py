from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json

from ...db.session import get_db
from ...api.deps import get_current_user
from ...models import User, ClinicalNote
from ...services.patient_service import PatientService
from ...services.notes.note_service import NoteService
from ...schemas.patient import PatientCreate, PatientResponse, PatientUpdate, PatientReport
from ...schemas.notes import NoteResponse
from ...schemas.timeline import TimelineEvent
from ...core.pdf_gen import generate_patient_pdf

router = APIRouter()

@router.post("/", response_model=PatientResponse)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check permissions
    return PatientService.create_patient(db, patient_in, creator_id=current_user.id)

@router.get("/", response_model=List[PatientResponse])
def read_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return PatientService.get_patients(db, user_id=current_user.id, skip=skip, limit=limit)

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
