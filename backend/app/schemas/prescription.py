from pydantic import BaseModel, Field, UUID4
from typing import List, Optional
from datetime import datetime

class PrescriptionItem(BaseModel):
    medicine_name: str
    dosage: str
    frequency: str
    duration: str
    time_of_day: List[str] = Field(default_factory=list) # Morning, Afternoon, Night, etc.
    special_instruction: Optional[str] = None

class PrescriptionCreate(BaseModel):
    patient_id: int
    encounter_id: Optional[int] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    prescription_items: List[PrescriptionItem]

class PrescriptionResponse(BaseModel):
    id: UUID4
    patient_id: int
    encounter_id: Optional[int] = None
    doctor_id: int
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    prescription_items: List[PrescriptionItem]
    verification_code: UUID4
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
