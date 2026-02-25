from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class PatientCommunicationResponse(BaseModel):
    id: int
    simplified_diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    medication_explanation: Optional[str] = None
    warning_signs: Optional[str] = None
    next_steps: Optional[str] = None
    language: str = "en"
    created_at: datetime
    
    class Config:
        from_attributes = True

class SecureMessageResponse(BaseModel):
    id: int
    direction: str
    content: str
    urgency_score: int = 0
    category: str = "Routine"
    flagged_keywords: Optional[str] = None
    draft_response: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ShiftHandoverResponse(BaseModel):
    id: int
    shift_type: str
    content: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReadmissionRiskResponse(BaseModel):
    id: int
    risk_score: int
    risk_level: str
    contributing_factors: Optional[str] = None
    prevention_recommendations: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
