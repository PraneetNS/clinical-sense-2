from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
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
