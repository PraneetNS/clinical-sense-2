from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

# --- Clinical Sub-Schemas ---
from .clinical import (
    AdmissionResponse,
    MedicalHistoryResponse,
    AllergyResponse,
    MedicationResponse,
    ProcedureResponse,
    DocumentResponse,
    TaskResponse,
    BillingItemResponse
)
from .notes import NoteResponse

# --- Patient Schemas ---

class PatientBase(BaseModel):
    name: str = Field(..., max_length=100)
    mrn: str = Field(..., max_length=20)
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, max_length=20)
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    insurance_provider: Optional[str] = Field(None, max_length=100)
    policy_number: Optional[str] = Field(None, max_length=50)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_relation: Optional[str] = Field(None, max_length=50)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    status: str = "Active"

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    mrn: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    insurance_provider: Optional[str] = None
    policy_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    status: Optional[str] = None

class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    
    admissions: List[AdmissionResponse] = []
    medical_history: List[MedicalHistoryResponse] = []
    allergies: List[AllergyResponse] = []
    medications: List[MedicationResponse] = []
    procedures: List[ProcedureResponse] = []
    documents: List[DocumentResponse] = []
    tasks: List[TaskResponse] = []
    billing_items: List[BillingItemResponse] = []
    
    total_billing_amount: float = 0.0
    outstanding_billing_amount: float = 0.0

    class Config:
        from_attributes = True

class PatientReport(BaseModel):
    patient: PatientResponse
    notes: List[NoteResponse]
    tasks: List[TaskResponse] = []
    documents: List[DocumentResponse] = []
    timeline: List[Any] = []
    summary: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
