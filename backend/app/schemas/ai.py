from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RiskAnalysisInput(BaseModel):
    note_content: Dict[str, Any] | str
    patient_history: Optional[str] = None
    medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    vitals: Optional[Dict[str, Any]] = None

class RiskAnalysisOutput(BaseModel):
    risk_score: str = Field(..., description="High, Medium, or Low")
    red_flags: List[str] = []
    suggestions: List[str] = []
    missing_info: List[str] = []

class DifferentialDiagnosisInput(BaseModel):
    symptoms: List[str]
    vitals: Optional[Dict[str, Any]] = None
    labs: Optional[List[str]] = None
    age: int
    gender: str
    history: Optional[str] = None

class DifferentialDiagnosisItem(BaseModel):
    condition: str
    reasoning: str
    suggested_tests: List[str]
    confidence: str # High/Medium/Low

class DifferentialDiagnosisOutput(BaseModel):
    differentials: List[DifferentialDiagnosisItem]

class CopilotInput(BaseModel):
    partial_note: str
    context: Optional[str] = None

class CopilotOutput(BaseModel):
    suggestions: List[str]
    warnings: List[str]
