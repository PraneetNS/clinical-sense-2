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
    return PatientService.get_patients(db, skip=skip, limit=limit)

@router.get("/{patient_id}", response_model=PatientResponse)
def read_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patient = PatientService.get_patient(db, patient_id)
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
    return PatientService.get_unified_timeline(db, patient_id)

@router.get("/{patient_id}/notes", response_model=List[NoteResponse])
def get_patient_notes(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Reusing timeline logic as it returns notes
    return get_patient_timeline(patient_id, db, current_user)

@router.get("/{patient_id}/report", response_model=PatientReport)
async def get_patient_report(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await PatientService.get_patient_report(db, patient_id)

@router.get("/{patient_id}/report/pdf")
async def get_patient_report_pdf(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report_data = await PatientService.get_patient_report(db, patient_id)
    pdf_buffer = generate_patient_pdf(report_data)
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=patient_report_{patient_id}.pdf"}
    )
