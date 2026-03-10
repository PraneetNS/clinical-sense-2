from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List, Any
from uuid import UUID

from ...db.session import get_db
from ...api.deps import get_current_user
from ...models import User
from ...schemas.prescription import PrescriptionCreate, PrescriptionResponse
from ...services.prescription_service import PrescriptionService

router = APIRouter()

@router.post("/create", response_model=PrescriptionResponse)
async def create_prescription(
    prescription_in: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PrescriptionService(db)
    return service.create_prescription(prescription_in, current_user.id)

@router.get("/{id}", response_model=PrescriptionResponse)
async def get_prescription(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PrescriptionService(db)
    result = service.get_prescription(id)
    # Check if the current user is the doctor who issued it or has access (e.g. admin)
    if result["prescription"].doctor_id != current_user.id:
        # Also allow if it's the patient's creator (just in case)
        if result["patient"].user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return result["prescription"]

@router.get("/prefill/{encounter_id}")
async def prefill_prescription(
    encounter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PrescriptionService(db)
    # Basic check for encounter ownership could be added here
    return service.prefill_from_encounter(encounter_id)

@router.get("/{id}/pdf")
async def get_prescription_pdf(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PrescriptionService(db)
    # Security check inside get_prescription called by generate_prescription_pdf handles basic existance
    # but we should double check access here too.
    data = service.get_prescription(id)
    if data["prescription"].doctor_id != current_user.id and data["patient"].user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    pdf_buffer = service.generate_prescription_pdf(id)
    
    headers = {
        'Content-Disposition': f'attachment; filename="prescription_{str(id)[:8]}.pdf"'
    }
    return Response(content=pdf_buffer.getvalue(), media_type="application/pdf", headers=headers)
