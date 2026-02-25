from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.api.deps import get_db, get_current_user
from app.models import User, Patient, SecureMessage, PatientCommunication
from app.services.ai.ai_service import AIService
from pydantic import BaseModel
import datetime

router = APIRouter()
ai_service = AIService()

class MessageCreate(BaseModel):
    content: str
    direction: str = "Inbound" # Inbound (Patient) or Outbound (Doctor)

class CommunicationResponse(BaseModel):
    id: int
    simplified_diagnosis: str
    treatment_plan: str
    medication_explanation: str
    warning_signs: str
    next_steps: str | None
    language: str
    created_at: datetime.datetime

# --- PATIENT COMMUNICATION ---

@router.post("/patients/{patient_id}/summary", response_model=CommunicationResponse)
async def generate_patient_summary(
    patient_id: int,
    note_id: int,
    language: str = "en",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = db.query(PatientCommunication).filter(PatientCommunication.note_id == note_id).first()
    if note:
        return note # Return existing if already generated to avoid re-running

    # Get the note text (assuming we have access to Note model or service)
    # Since we don't have NoteService imported here, let's just query db directly for Note
    from app.models import ClinicalNote
    clinical_note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not clinical_note:
        raise HTTPException(status_code=404, detail="Clinical note not found")

    summary_data = await ai_service.generate_patient_communication(clinical_note.raw_content, language)
    
    if "error" in summary_data:
        raise HTTPException(status_code=500, detail="AI generation failed")

    communication = PatientCommunication(
        patient_id=patient_id,
        note_id=note_id,
        simplified_diagnosis=summary_data.get("simplified_diagnosis", ""),
        treatment_plan=str(summary_data.get("treatment_plan", "")),
        medication_explanation=str(summary_data.get("medication_explanation", "")),
        warning_signs=str(summary_data.get("warning_signs", "")),
        next_steps=str(summary_data.get("next_steps", "")),
        language=language
    )
    db.add(communication)
    db.commit()
    db.refresh(communication)
    return communication

# --- SECURE MESSAGING ---

@router.post("/patients/{patient_id}/messages")
async def send_message(
    patient_id: int,
    msg_in: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Analyze urgency if inbound
    urgency_data = {}
    if msg_in.direction == "Inbound":
        urgency_data = await ai_service.analyze_message_urgency(msg_in.content)

    message = SecureMessage(
        patient_id=patient_id,
        user_id=current_user.id, # Or target doctor if Inbound
        direction=msg_in.direction,
        content=msg_in.content,
        urgency_score=urgency_data.get("urgency_score", 0),
        category=urgency_data.get("category", "Routine"),
        flagged_keywords=str(urgency_data.get("flagged_keywords", [])),
        status="Unread"
    )
    
    # If inbound, draft response in background
    if msg_in.direction == "Inbound":
         # Use background task to draft response
         background_tasks.add_task(draft_response_task, db, message.id, msg_in.content)

    db.add(message)
    db.commit()
    db.refresh(message)
    return message

async def draft_response_task(db: Session, message_id: int, content: str):
    # Fetch message to ensure it exists and get patient context context
    # ideally we fetch patient history
    draft = await ai_service.draft_message_response(content, "Patient History Placeholder")
    
    msg = db.query(SecureMessage).filter(SecureMessage.id == message_id).first()
    if msg:
        msg.draft_response = draft.get("draft_response", "")
        db.commit()

@router.get("/patients/{patient_id}/messages")
async def get_messages(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(SecureMessage).filter(SecureMessage.patient_id == patient_id).order_by(SecureMessage.created_at.desc()).all()
