from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime


# --- AI / SOAP Schemas ---
class SOAPNote(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str

# --- Clinical Note Schemas ---
class NoteCreateRequest(BaseModel):
    raw_content: str = Field(
        ..., 
        min_length=10, 
        max_length=50000, 
        description="Raw clinical text must be between 10 and 50,000 characters."
    )
    title: Optional[str] = Field("Untitled Note", max_length=150)
    note_type: str = Field("SOAP", pattern="^(SOAP|PROGRESS|DISCHARGE)$")
    patient_id: Optional[int] = None
    idempotency_key: Optional[str] = Field(None, description="Unique key to prevent duplicate note creation.")

    @field_validator('raw_content')
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Clinical notes cannot be empty or only whitespace.')
        return v

class NoteResponse(BaseModel):
    id: int
    title: Optional[str]
    note_type: str
    patient_id: Optional[int]
    raw_content: str
    structured_content: Optional[Any]
    status: str
    created_at: datetime
    updated_at: datetime


    model_config = {"from_attributes": True}

class NoteUpdateRequest(BaseModel):
    title: Optional[str] = None
    structured_content: Optional[Any] = None
    status: Optional[str] = None # 'draft', 'finalized'
    patient_id: Optional[int] = None
