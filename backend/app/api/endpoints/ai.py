from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List
import json

from ...schemas import ai as ai_schemas
from ...services.ai.ai_service import AIService
from ... import models
from ...api import deps

router = APIRouter()

@router.post("/differential", response_model=ai_schemas.DifferentialDiagnosisOutput)
async def generate_differential(
    input_data: ai_schemas.DifferentialDiagnosisInput,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Generates differential diagnosis based on symptoms and patient data.
    """
    service = AIService()
    result = await service.generate_differential(
        symptoms=input_data.symptoms,
        vitals=input_data.vitals,
        age=input_data.age,
        gender=input_data.gender
    )
    
    # Store result in DB
    db_diff = models.DifferentialDiagnosis(
        user_id=current_user.id,
        input_data=input_data.json(),
        output_data=json.dumps(result)
    )
    db.add(db_diff)
    db.commit()
    
    return result

@router.post("/risk_analysis", response_model=ai_schemas.RiskAnalysisOutput)
async def analyze_risks(
    input_data: ai_schemas.RiskAnalysisInput,
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Ad-hoc risk analysis endpoint.
    """
    service = AIService()
    
    patient_context = {
        "history": input_data.patient_history,
        "medications": input_data.medications,
        "allergies": input_data.allergies,
        "vitals": input_data.vitals
    }
    
    if isinstance(input_data.note_content, str):
        try:
             note_content = json.loads(input_data.note_content)
        except:
             note_content = {"text": input_data.note_content}
    else:
        note_content = input_data.note_content

    return await service.analyze_risks(note_content, patient_context)

@router.post("/medico_legal", response_model=dict)
async def medico_legal_review(
    note_content: str,
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Analyzes note for medico-legal completeness.
    """
    service = AIService()
    return await service.medical_legal_review(note_content)

@router.post("/transcribe")
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Transcribes audio using Groq Whisper model.
    """
    import os
    import tempfile
    import groq
    from ...core.config import settings

    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API key not configured")

    client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
        content = await file.read()
        temp_audio.write(content)
        temp_audio_path = temp_audio.name
        
    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                file=(temp_audio_path, audio_file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
        return {"text": transcription.text, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(temp_audio_path)

from pydantic import BaseModel

class DifferentialChallengeRequest(BaseModel):
    diagnosis_name: str
    icd_code: str

@router.post("/differential/{encounter_id}/challenge")
async def challenge_differential(
    encounter_id: int,
    challenge: DifferentialChallengeRequest,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Challenges a specific diagnosis with an evidence-based prompt.
    """
    import groq
    import json
    from ...core.config import settings
    from ...models import AIEncounter

    encounter = db.query(AIEncounter).filter(AIEncounter.id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
        
    client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
    
    prompt = f"""
As an expert medical diagnostician, provide an evidence-based challenge for the following diagnosis:
Diagnosis: {challenge.diagnosis_name} (ICD-10: {challenge.icd_code})
Patient context: {encounter.soap_note}

You must return a strict JSON object with the following schema:
{{
    "supports": [{{"finding": string, "weight": "strong"|"moderate"|"weak", "reason": string}}],
    "against": [{{"finding": string, "weight": "strong"|"moderate"|"weak", "reason": string}}],
    "alternative_diagnoses": [string],
    "key_tests_to_differentiate": [string]
}}
"""

    try:
        completion = await client.chat.completions.create(
            model="llama-3-70b-8192",
            messages=[
                {"role": "system", "content": "You are an expert internal medicine diagnostician. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Challenge failed: {str(e)}")

@router.post("/encounters/{encounter_id}/send-portal-link")
async def send_portal_link(
    encounter_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Generates a secure PatientPortalLink and simulates sending it.
    """
    import secrets
    from datetime import datetime, timedelta
    from ...models import AIEncounter, PatientPortalLink
    
    encounter = db.query(AIEncounter).filter(AIEncounter.id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
        
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Invalidate old links for this encounter
    old_links = db.query(PatientPortalLink).filter(PatientPortalLink.encounter_id == encounter_id).all()
    for link in old_links:
        link.expires_at = datetime.utcnow()
        
    portal_link = PatientPortalLink(
        encounter_id=encounter_id,
        patient_id=encounter.patient_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    
    db.add(portal_link)
    db.commit()
    
    # In a real app we'd dispatch an email/SMS using SendGrid/Twilio
    link_url = f"http://localhost:3000/portal/view?token={token}"
    return {"status": "success", "message": "Portal link generated and sent to patient.", "link": link_url}
