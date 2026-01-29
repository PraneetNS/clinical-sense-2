from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- Admission ---
class AdmissionBase(BaseModel):
    admission_date: datetime
    discharge_date: Optional[datetime] = None
    reason: str = Field(..., max_length=1000)
    ward: Optional[str] = Field(None, max_length=50)
    room: Optional[str] = Field(None, max_length=20)
    status: str = Field("Active", max_length=20)

class AdmissionCreate(AdmissionBase):
    pass

class AdmissionResponse(AdmissionBase):
    id: int
    patient_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Medical History ---
class MedicalHistoryBase(BaseModel):
    condition_name: str
    diagnosis_date: Optional[datetime] = None
    status: str
    notes: Optional[str] = None

class MedicalHistoryCreate(MedicalHistoryBase):
    pass

class MedicalHistoryResponse(MedicalHistoryBase):
    id: int
    patient_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Allergy ---
class AllergyBase(BaseModel):
    allergen: str
    reaction: Optional[str] = None
    severity: Optional[str] = None

class AllergyCreate(AllergyBase):
    pass

class AllergyUpdate(BaseModel):
    allergen: Optional[str] = None
    reaction: Optional[str] = None
    severity: Optional[str] = None

class AllergyResponse(AllergyBase):
    id: int
    patient_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Medication ---
class MedicationBase(BaseModel):
    name: str = Field(..., max_length=100)
    dosage: Optional[str] = Field(None, max_length=50)
    frequency: Optional[str] = Field(None, max_length=50)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = Field("Active", max_length=20)
    source_note_id: Optional[int] = None

class MedicationCreate(MedicationBase):
    pass

class MedicationResponse(MedicationBase):
    id: int
    patient_id: int
    prescribed_by_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Procedure ---
class ProcedureBase(BaseModel):
    name: str
    code: Optional[str] = None
    date: datetime = datetime.utcnow()
    notes: Optional[str] = None
    admission_id: Optional[int] = None
    source_note_id: Optional[int] = None

class ProcedureCreate(ProcedureBase):
    pass

class ProcedureResponse(ProcedureBase):
    id: int
    patient_id: int
    performer_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Document ---
class DocumentBase(BaseModel):
    title: str
    file_type: Optional[str] = None
    file_url: str
    summary: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    patient_id: int
    uploader_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Task ---
class TaskBase(BaseModel):
    description: str
    due_date: Optional[datetime] = None
    status: str = "Pending"

class TaskCreate(TaskBase):
    assigned_to_id: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    patient_id: Optional[int]
    assigned_to_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Billing Item ---
class BillingItemBase(BaseModel):
    item_name: str
    code: Optional[str] = None
    cost: float
    status: str = "Pending"

class BillingItemCreate(BillingItemBase):
    pass

class BillingItemResponse(BillingItemBase):
    id: int
    patient_id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- Update Schemas ---
class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    source_note_id: Optional[int] = None

class ProcedureUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    date: Optional[datetime] = None
    notes: Optional[str] = None
    admission_id: Optional[int] = None
    source_note_id: Optional[int] = None

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    file_type: Optional[str] = None
    file_url: Optional[str] = None
    summary: Optional[str] = None

class TaskUpdate(BaseModel):
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    assigned_to_id: Optional[int] = None

class BillingItemUpdate(BaseModel):
    item_name: Optional[str] = None
    code: Optional[str] = None
    cost: Optional[float] = None
    status: Optional[str] = None
